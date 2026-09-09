"""Pure presentation helpers shared by the Streamlit dashboard and tests."""

from __future__ import annotations

from typing import Final

from web_lead_automation.services.lead_history import LeadWithHistory


SECTOR_PRESETS: Final[dict[str, str]] = {
    "Kuaför / Berber": "kuaför berber",
    "Güzellik Merkezi": "güzellik merkezi",
    "Oto Servis": "oto servis",
    "Emlak Ofisi": "emlak ofisi",
    "Nakliyat": "nakliyat firması",
    "Düğün / Organizasyon": "düğün salonu organizasyon",
    "Yapı / Tadilat": "tadilat yapı firması",
    "Özel Sektör": "",
}


def resolve_sector_query(preset: str, custom_sector: str = "") -> str:
    """Resolve a UI preset to the text sent to Google Places."""

    if preset not in SECTOR_PRESETS:
        raise ValueError(f"Unknown sector preset: {preset}")

    preset_query = SECTOR_PRESETS[preset]
    if preset_query:
        return preset_query

    custom = custom_sector.strip()
    if not custom:
        raise ValueError("Özel sektör seçildiğinde sektör adı girilmelidir.")
    return custom


def lead_to_table_row(item: LeadWithHistory) -> dict[str, object]:
    """Convert a lead-history result into one dashboard table row."""

    place = item.lead.place
    return {
        "Skor": item.lead.score,
        "İşletme": place.display_name,
        "Website": "Listelenmiyor",
        "Telefon": place.national_phone_number or "—",
        "Rating": place.rating,
        "Yorum": place.user_rating_count or 0,
        "CRM": item.status.value,
        "Daha Önce Görüldü": "Evet" if item.seen_before else "Hayır",
        "Adres": place.formatted_address or "—",
        "Google Maps": place.google_maps_uri or "",
        "Place ID": place.place_id,
    }


def leads_to_table_rows(leads: tuple[LeadWithHistory, ...]) -> list[dict[str, object]]:
    """Convert search results to Streamlit-friendly rows in ranking order."""

    return [lead_to_table_row(item) for item in leads]
