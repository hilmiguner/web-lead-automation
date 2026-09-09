from datetime import datetime, timezone

from web_lead_automation.dashboard import (
    apply_tracked_state,
    find_lead_by_place_id,
    lead_detail_label,
    lead_rows,
    replace_result_lead,
    resolve_location_query,
    resolve_sector_query,
)
from web_lead_automation.services.lead_history import (
    LeadSearchWithHistoryResult,
    LeadWithHistory,
)
from web_lead_automation.services.places import Place
from web_lead_automation.services.scoring import LeadScore, ScoreReason
from web_lead_automation.services.website_filter import WebsiteStatus
from web_lead_automation.storage.crm import LeadStatus, TrackedLead


def _lead(
    *,
    place_id: str = "place-1",
    name: str = "Örnek Kuaför",
    status: LeadStatus = LeadStatus.NEW,
    seen_before: bool = False,
    note: str = "",
) -> LeadWithHistory:
    now = datetime.now(timezone.utc)
    return LeadWithHistory(
        lead=LeadScore(
            place=Place(
                place_id=place_id,
                display_name=name,
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
        status=status,
        note=note,
        first_seen_at=now,
        updated_at=now,
        was_contacted=status is not LeadStatus.NEW,
        is_closed=status in {LeadStatus.WON, LeadStatus.LOST},
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


def test_lead_detail_label_includes_name_score_and_status() -> None:
    label = lead_detail_label(_lead(status=LeadStatus.INTERESTED))
    assert label == "Örnek Kuaför — 100/100 — INTERESTED"


def test_find_lead_by_place_id_returns_matching_item() -> None:
    first = _lead(place_id="place-1")
    second = _lead(place_id="place-2", name="İkinci İşletme")

    assert find_lead_by_place_id((first, second), "place-2") is second
    assert find_lead_by_place_id((first, second), "missing") is None


def test_apply_tracked_state_refreshes_crm_flags_and_note() -> None:
    item = _lead()
    now = datetime.now(timezone.utc)
    tracked = TrackedLead(
        id=1,
        external_place_id="place-1",
        status=LeadStatus.WON,
        note="Site sold",
        created_at=now,
        updated_at=now,
    )

    updated = apply_tracked_state(item, tracked)

    assert updated.status is LeadStatus.WON
    assert updated.note == "Site sold"
    assert updated.was_contacted is True
    assert updated.is_closed is True
    assert updated.updated_at == now


def test_replace_result_lead_preserves_order_and_pagination() -> None:
    first = _lead(place_id="place-1")
    second = _lead(place_id="place-2", name="İkinci İşletme")
    result = LeadSearchWithHistoryResult(
        leads=(first, second),
        next_page_token="next-token",
    )
    updated_second = _lead(
        place_id="place-2",
        name="İkinci İşletme",
        status=LeadStatus.CONTACTED,
        note="Called",
    )

    updated_result = replace_result_lead(result, updated_second)

    assert [item.lead.place.place_id for item in updated_result.leads] == [
        "place-1",
        "place-2",
    ]
    assert updated_result.leads[1].status is LeadStatus.CONTACTED
    assert updated_result.leads[1].note == "Called"
    assert updated_result.next_page_token == "next-token"
