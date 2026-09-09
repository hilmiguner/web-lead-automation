from datetime import datetime, timezone

from web_lead_automation.dashboard import (
    lead_rows,
    resolve_location_query,
    resolve_sector_query,
)
from web_lead_automation.services.lead_history import LeadWithHistory
from web_lead_automation.services.places import Place
from web_lead_automation.services.scoring import LeadScore, ScoreReason
from web_lead_automation.services.website_filter import WebsiteStatus
from web_lead_automation.storage.crm import LeadStatus


def _lead(*, seen_before: bool = False) -> LeadWithHistory:
    now = datetime.now(timezone.utc)
    return LeadWithHistory(
        lead=LeadScore(
            place=Place(
                place_id="place-1",
                display_name="Örnek Kuaför",
                formatted_address="Gemlik, Bursa",
                national_phone_number="0224 000 00 00",
                rating=4.7,
                user_rating_count=120,
                types=("hair_salon",),
                google_maps_uri="https://maps.google.com/example",
            ),
            score=100,
            website_status=WebsiteStatus.NO_WEBSITE_LISTED,
            reasons=(ScoreReason("website", 40, "No website (+40)."),),
        ),
        seen_before=seen_before,
        status=LeadStatus.NEW,
        note="",
        first_seen_at=now,
        updated_at=now,
        was_contacted=False,
        is_closed=False,
    )


def test_resolve_sector_query_uses_preset_mapping() -> None:
    assert resolve_sector_query("Kuaför / Berber", "") == "kuaför berber"


def test_resolve_sector_query_uses_custom_value() -> None:
    assert resolve_sector_query("Özel sektör yaz", " veteriner ") == "veteriner"


def test_resolve_location_query_uses_custom_value() -> None:
    assert resolve_location_query("Özel bölge yaz", " Mudanya Bursa ") == "Mudanya Bursa"


def test_lead_rows_exposes_sales_columns_without_persisting_place_data() -> None:
    row = lead_rows((_lead(),))[0]

    assert row["Skor"] == 100
    assert row["İşletme"] == "Örnek Kuaför"
    assert row["Website"] == "Listelenmiyor"
    assert row["CRM"] == "NEW"
    assert row["Daha Önce Görüldü"] == "Hayır"
    assert row["Place ID"] == "place-1"


def test_lead_rows_marks_previously_seen_leads() -> None:
    row = lead_rows((_lead(seen_before=True),))[0]
    assert row["Daha Önce Görüldü"] == "Evet"
