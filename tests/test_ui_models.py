from datetime import datetime, timezone

import pytest

from web_lead_automation.services.lead_history import LeadWithHistory
from web_lead_automation.services.places import Place
from web_lead_automation.services.scoring import LeadScore, ScoreReason
from web_lead_automation.services.website_filter import WebsiteStatus
from web_lead_automation.storage.crm import LeadStatus
from web_lead_automation.ui_models import lead_to_table_row, resolve_sector_query


def _lead_with_history(*, seen_before: bool = False) -> LeadWithHistory:
    place = Place(
        place_id="place-123",
        display_name="Örnek Kuaför",
        formatted_address="Gemlik, Bursa",
        national_phone_number="0224 000 00 00",
        website_uri=None,
        rating=4.7,
        user_rating_count=84,
        types=("hair_salon",),
        google_maps_uri="https://maps.google.com/example",
    )
    score = LeadScore(
        place=place,
        score=92,
        website_status=WebsiteStatus.NO_WEBSITE_LISTED,
        reasons=(ScoreReason("website", 40, "test"),),
    )
    now = datetime(2026, 9, 9, 9, 0, tzinfo=timezone.utc)
    return LeadWithHistory(
        lead=score,
        seen_before=seen_before,
        status=LeadStatus.NEW,
        note="",
        first_seen_at=now,
        updated_at=now,
        was_contacted=False,
        is_closed=False,
    )


def test_resolve_sector_query_uses_preset() -> None:
    assert resolve_sector_query("Kuaför / Berber") == "kuaför berber"


def test_resolve_sector_query_requires_custom_value() -> None:
    with pytest.raises(ValueError):
        resolve_sector_query("Özel Sektör", "   ")

    assert resolve_sector_query("Özel Sektör", " psikolog ") == "psikolog"


def test_lead_to_table_row_exposes_mvp_columns() -> None:
    row = lead_to_table_row(_lead_with_history(seen_before=True))

    assert row["Skor"] == 92
    assert row["İşletme"] == "Örnek Kuaför"
    assert row["Website"] == "Listelenmiyor"
    assert row["Telefon"] == "0224 000 00 00"
    assert row["Rating"] == 4.7
    assert row["Yorum"] == 84
    assert row["CRM"] == "NEW"
    assert row["Daha Önce Görüldü"] == "Evet"
    assert row["Google Maps"] == "https://maps.google.com/example"
