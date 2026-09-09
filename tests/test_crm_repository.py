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


def test_track_creates_new_lead_with_safe_defaults(tmp_path):
    repo = make_repo(tmp_path)

    lead, created = repo.track("place-123")

    assert created is True
    assert lead.external_place_id == "place-123"
    assert lead.status is LeadStatus.NEW
    assert lead.note == ""
    assert lead.created_at.tzinfo is not None
    assert lead.updated_at.tzinfo is not None


def test_track_is_idempotent_for_duplicate_place_id(tmp_path):
    repo = make_repo(tmp_path)
    first, first_created = repo.track("place-123")
    repo.update_status("place-123", LeadStatus.CONTACTED)
    repo.update_note("place-123", "Called the business")

    duplicate, duplicate_created = repo.track("place-123")

    assert first_created is True
    assert duplicate_created is False
    assert duplicate.id == first.id
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


def test_blank_place_id_is_rejected(tmp_path):
    repo = make_repo(tmp_path)

    with pytest.raises(ValueError):
        repo.track("   ")
