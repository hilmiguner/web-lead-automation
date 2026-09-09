import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from web_lead_automation.storage.crm import (
    LeadNotFoundError,
    LeadRepository,
    LeadStatus,
)


def make_repo(tmp_path: Path) -> LeadRepository:
    repo = LeadRepository(tmp_path / "nested" / "leads.sqlite3")
    repo.initialize()
    return repo


def test_initialize_creates_database_and_parent_directory(tmp_path):
    db_path = tmp_path / "data" / "leads.sqlite3"
    repo = LeadRepository(db_path)

    repo.initialize()

    assert db_path.exists()


def test_initialize_migrates_existing_database_without_losing_crm_data(tmp_path):
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_place_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO leads (external_place_id, status, note, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("place-legacy", "CONTACTED", "keep me", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )

    repo = LeadRepository(db_path)
    repo.initialize()
    lead = repo.get_by_place_id("place-legacy")

    assert lead is not None
    assert lead.status is LeadStatus.CONTACTED
    assert lead.note == "keep me"
    assert lead.demo_url is None
    assert lead.display_name is None
    assert lead.last_contact_at is None
    assert lead.contact_note == ""
    assert lead.follow_up_at is None


def test_track_creates_new_lead_with_safe_defaults(tmp_path):
    repo = make_repo(tmp_path)

    lead, created = repo.track("place-123", display_name="Örnek Kuaför")

    assert created is True
    assert lead.external_place_id == "place-123"
    assert lead.display_name == "Örnek Kuaför"
    assert lead.status is LeadStatus.NEW
    assert lead.note == ""
    assert lead.demo_url is None
    assert lead.last_contact_at is None
    assert lead.contact_note == ""
    assert lead.follow_up_at is None
    assert lead.created_at.tzinfo is not None
    assert lead.updated_at.tzinfo is not None


def test_track_is_idempotent_and_refreshes_display_name(tmp_path):
    repo = make_repo(tmp_path)
    first, first_created = repo.track("place-123", display_name="Eski Ad")
    repo.update_status("place-123", LeadStatus.CONTACTED)
    repo.update_note("place-123", "Called the business")

    duplicate, duplicate_created = repo.track("place-123", display_name="Yeni Ad")

    assert first_created is True
    assert duplicate_created is False
    assert duplicate.id == first.id
    assert duplicate.display_name == "Yeni Ad"
    assert duplicate.status is LeadStatus.CONTACTED
    assert duplicate.note == "Called the business"
    assert len(repo.list()) == 1


def test_exists_and_get_by_place_id(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-123")

    assert repo.exists("place-123") is True
    assert repo.exists("missing") is False
    assert repo.get_by_place_id("place-123") is not None
    assert repo.get_by_place_id("missing") is None


def test_status_and_note_updates_are_persisted(tmp_path):
    db_path = tmp_path / "leads.sqlite3"
    repo = LeadRepository(db_path)
    repo.initialize()
    repo.track("place-123")

    repo.update_status("place-123", LeadStatus.INTERESTED)
    updated = repo.update_note("place-123", "Requested a demo")

    reopened = LeadRepository(db_path)
    reopened.initialize()
    persisted = reopened.get_by_place_id("place-123")

    assert updated.status is LeadStatus.INTERESTED
    assert persisted is not None
    assert persisted.status is LeadStatus.INTERESTED
    assert persisted.note == "Requested a demo"


def test_demo_url_can_be_persisted_and_cleared(tmp_path):
    db_path = tmp_path / "leads.sqlite3"
    repo = LeadRepository(db_path)
    repo.initialize()
    repo.track("place-123")

    updated = repo.update_demo_url(
        "place-123",
        "https://demo-hub.netlify.app/ornek-kuafor-abc/",
    )
    assert updated.demo_url == "https://demo-hub.netlify.app/ornek-kuafor-abc/"

    reopened = LeadRepository(db_path)
    reopened.initialize()
    persisted = reopened.get_by_place_id("place-123")
    assert persisted is not None
    assert persisted.demo_url == "https://demo-hub.netlify.app/ornek-kuafor-abc/"

    cleared = reopened.update_demo_url("place-123", None)
    assert cleared.demo_url is None


def test_demo_url_requires_https(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-123")

    with pytest.raises(ValueError, match="HTTPS"):
        repo.update_demo_url("place-123", "http://example.test/demo")


def test_record_contact_moves_new_lead_to_contacted_and_persists_details(tmp_path):
    db_path = tmp_path / "leads.sqlite3"
    repo = LeadRepository(db_path)
    repo.initialize()
    repo.track("place-123", display_name="Örnek Kuaför")
    contacted_at = datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc)
    follow_up_at = contacted_at + timedelta(days=3)

    updated = repo.record_contact(
        "place-123",
        contact_note="  WhatsApp gönderildi  ",
        contacted_at=contacted_at,
        follow_up_at=follow_up_at,
    )

    reopened = LeadRepository(db_path)
    reopened.initialize()
    persisted = reopened.get_by_place_id("place-123")

    assert updated.status is LeadStatus.CONTACTED
    assert persisted is not None
    assert persisted.status is LeadStatus.CONTACTED
    assert persisted.last_contact_at == contacted_at
    assert persisted.contact_note == "WhatsApp gönderildi"
    assert persisted.follow_up_at == follow_up_at


def test_record_contact_does_not_downgrade_advanced_or_closed_status(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-interested")
    repo.update_status("place-interested", LeadStatus.INTERESTED)
    repo.track("place-won")
    repo.update_status("place-won", LeadStatus.WON)

    interested = repo.record_contact("place-interested")
    won = repo.record_contact("place-won")

    assert interested.status is LeadStatus.INTERESTED
    assert won.status is LeadStatus.WON


def test_record_contact_requires_follow_up_after_contact_time(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-123")
    contacted_at = datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="later"):
        repo.record_contact(
            "place-123",
            contacted_at=contacted_at,
            follow_up_at=contacted_at,
        )


def test_follow_up_list_returns_only_due_open_leads_in_due_order(tmp_path):
    repo = make_repo(tmp_path)
    as_of = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)

    repo.track("due-later", display_name="B Lead")
    repo.record_contact(
        "due-later",
        contacted_at=as_of - timedelta(days=2),
        follow_up_at=as_of - timedelta(hours=1),
    )
    repo.track("due-earlier", display_name="A Lead")
    repo.record_contact(
        "due-earlier",
        contacted_at=as_of - timedelta(days=3),
        follow_up_at=as_of - timedelta(hours=2),
    )
    repo.track("future")
    repo.record_contact(
        "future",
        contacted_at=as_of - timedelta(days=1),
        follow_up_at=as_of + timedelta(days=1),
    )
    repo.track("closed")
    repo.record_contact(
        "closed",
        contacted_at=as_of - timedelta(days=2),
        follow_up_at=as_of - timedelta(hours=3),
    )
    repo.update_status("closed", LeadStatus.LOST)

    due = repo.list_follow_ups_due(as_of=as_of)

    assert [lead.external_place_id for lead in due] == ["due-earlier", "due-later"]
    assert [lead.display_name for lead in due] == ["A Lead", "B Lead"]


def test_clear_follow_up_removes_lead_from_due_list(tmp_path):
    repo = make_repo(tmp_path)
    now = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
    repo.track("place-123")
    repo.record_contact(
        "place-123",
        contacted_at=now - timedelta(days=2),
        follow_up_at=now - timedelta(hours=1),
    )

    cleared = repo.clear_follow_up("place-123")

    assert cleared.follow_up_at is None
    assert repo.list_follow_ups_due(as_of=now) == ()


def test_contact_tracking_requires_timezone_aware_datetimes(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-123")

    with pytest.raises(ValueError, match="timezone-aware"):
        repo.record_contact(
            "place-123",
            contacted_at=datetime(2026, 9, 9, 10, 0),
        )


def test_update_changes_status_and_note_together(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-123")

    updated = repo.update(
        "place-123",
        status=LeadStatus.CONTACTED,
        note="  WhatsApp message sent  ",
    )

    assert updated.status is LeadStatus.CONTACTED
    assert updated.note == "WhatsApp message sent"


def test_list_can_filter_by_status(tmp_path):
    repo = make_repo(tmp_path)
    repo.track("place-new")
    repo.track("place-won")
    repo.update_status("place-won", LeadStatus.WON)

    won = repo.list(status=LeadStatus.WON)

    assert [lead.external_place_id for lead in won] == ["place-won"]


def test_update_unknown_lead_raises(tmp_path):
    repo = make_repo(tmp_path)

    with pytest.raises(LeadNotFoundError):
        repo.update_status("missing", LeadStatus.LOST)

    with pytest.raises(LeadNotFoundError):
        repo.record_contact("missing")


def test_blank_place_id_is_rejected(tmp_path):
    repo = make_repo(tmp_path)

    with pytest.raises(ValueError):
        repo.track("   ")
