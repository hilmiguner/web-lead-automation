from datetime import datetime, timezone

import pytest

from web_lead_automation.pages.Outreach_Assistant import (
    follow_up_datetime,
    follow_up_rows,
    main,
)
from web_lead_automation.storage.crm import LeadStatus, TrackedLead


def test_outreach_page_exposes_main_without_running_on_import() -> None:
    assert callable(main)


def test_follow_up_datetime_resolves_presets_in_utc() -> None:
    now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)

    assert follow_up_datetime("Takip planlama", now=now) is None
    assert follow_up_datetime("Yarın", now=now) == datetime(
        2026, 9, 10, 12, 0, tzinfo=timezone.utc
    )
    assert follow_up_datetime("3 gün sonra", now=now) == datetime(
        2026, 9, 12, 12, 0, tzinfo=timezone.utc
    )


def test_follow_up_datetime_rejects_unknown_or_naive_time() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        follow_up_datetime("30 gün sonra")

    with pytest.raises(ValueError, match="timezone-aware"):
        follow_up_datetime("Yarın", now=datetime(2026, 9, 9, 12, 0))


def test_follow_up_rows_prefers_persisted_business_name() -> None:
    timestamp = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
    lead = TrackedLead(
        id=1,
        external_place_id="place-123",
        status=LeadStatus.CONTACTED,
        note="",
        created_at=timestamp,
        updated_at=timestamp,
        display_name="Örnek Kuaför",
        last_contact_at=timestamp,
        contact_note="WhatsApp gönderildi",
        follow_up_at=timestamp,
    )

    rows = follow_up_rows((lead,))

    assert rows[0]["İşletme"] == "Örnek Kuaför"
    assert rows[0]["Görüşme notu"] == "WhatsApp gönderildi"
    assert rows[0]["Place ID"] == "place-123"
