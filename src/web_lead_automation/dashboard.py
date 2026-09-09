"""Streamlit dashboard for the MVP lead-search workflow."""

from __future__ import annotations

from typing import Iterable

import streamlit as st

from web_lead_automation.config import get_settings
from web_lead_automation.services.lead_finder import LeadFinder
from web_lead_automation.services.lead_history import LeadHistoryService, LeadWithHistory
from web_lead_automation.services.places import (
    GooglePlacesClient,
    GooglePlacesError,
)
from web_lead_automation.storage.crm import LeadRepository


SECTOR_PRESETS = (
    "Kuaför / Berber",
    "Güzellik Merkezi",
    "Oto Servis",
    "Emlak Ofisi",
    "Nakliyat Firması",
    "Düğün Salonu / Organizasyon",
    "Yapı / Tadilat",
    "Özel sektör yaz",
)

SECTOR_QUERY_MAP = {
    "Kuaför / Berber": "kuaför berber",
    "Güzellik Merkezi": "güzellik merkezi",
    "Oto Servis": "oto servis",
    "Emlak Ofisi": "emlak ofisi",
    "Nakliyat Firması": "nakliyat firması",
    "Düğün Salonu / Organizasyon": "düğün salonu organizasyon",
    "Yapı / Tadilat": "yapı tadilat",
}

DEFAULT_LOCATIONS = (
    "Gemlik Bursa",
    "Nilüfer Bursa",
    "Osmangazi Bursa",
    "Yıldırım Bursa",
    "Özel bölge yaz",
)


def resolve_sector_query(preset: str, custom_sector: str) -> str:
    """Resolve the effective Google Places sector query."""

    if preset == "Özel sektör yaz":
        return custom_sector.strip()
    return SECTOR_QUERY_MAP.get(preset, preset).strip()


def resolve_location_query(preset: str, custom_location: str) -> str:
    """Resolve the effective Google Places location query."""

    if preset == "Özel bölge yaz":
        return custom_location.strip()
    return preset.strip()


def lead_rows(leads: Iterable[LeadWithHistory]) -> list[dict[str, object]]:
    """Convert enriched leads into Streamlit-friendly table rows."""

    rows: list[dict[str, object]] = []
    for item in leads:
        place = item.lead.place
        rows.append(
            {
                "Skor": item.lead.score,
                "İşletme": place.display_name,
                "Telefon": place.national_phone_number or "—",
                "Rating": place.rating if place.rating is not None else "—",
                "Yorum": place.user_rating_count or 0,
                "Website": "Listelenmiyor",
                "CRM": item.status.value,
                "Daha Önce Görüldü": "Evet" if item.seen_before else "Hayır",
                "Adres": place.formatted_address or "—",
                "Google Maps": place.google_maps_uri or "",
                "Place ID": place.place_id,
            }
        )
    return rows


def run_dashboard() -> None:
    """Render the Streamlit MVP dashboard."""

    st.set_page_config(
        page_title="Web Lead Automation",
        page_icon="🔎",
        layout="wide",
    )

    st.title("Web Lead Automation")
    st.caption("Web sitesi Google Places'ta listelenmeyen yerel işletmeleri bul ve satış önceliğine göre sırala.")

    settings = get_settings()

    left, right = st.columns(2)
    with left:
        location_preset = st.selectbox("Bölge", DEFAULT_LOCATIONS, index=0)
        custom_location = ""
        if location_preset == "Özel bölge yaz":
            custom_location = st.text_input("Özel bölge", placeholder="Örn. Mudanya Bursa")

    with right:
        sector_preset = st.selectbox("Sektör", SECTOR_PRESETS, index=0)
        custom_sector = ""
        if sector_preset == "Özel sektör yaz":
            custom_sector = st.text_input("Özel sektör", placeholder="Örn. veteriner")

    page_size = st.slider(
        "Tek aramada istenecek işletme sayısı",
        min_value=5,
        max_value=20,
        value=settings.google_places_page_size,
        step=5,
    )

    if not st.button("Lead Ara", type="primary", use_container_width=True):
        st.info("Başlamak için bölge ve sektör seçip **Lead Ara** butonuna bas.")
        return

    sector = resolve_sector_query(sector_preset, custom_sector)
    location = resolve_location_query(location_preset, custom_location)

    if not sector or not location:
        st.error("Bölge ve sektör boş bırakılamaz.")
        return

    if not settings.google_places_api_key:
        st.error(
            "Google Places API anahtarı bulunamadı. `.env` dosyasına "
            "`GOOGLE_PLACES_API_KEY=...` ekle."
        )
        return

    repository = LeadRepository(settings.lead_db_path)
    repository.initialize()

    try:
        with st.spinner("İşletmeler aranıyor ve skorlanıyor..."):
            with GooglePlacesClient(
                api_key=settings.google_places_api_key,
                timeout_seconds=settings.google_places_timeout_seconds,
                default_page_size=settings.google_places_page_size,
            ) as places_client:
                search_result = LeadFinder(places_client).search(
                    sector=sector,
                    location=location,
                    page_size=page_size,
                )
            result = LeadHistoryService(repository).record_search_result(search_result)
    except (GooglePlacesError, ValueError) as exc:
        st.error(str(exc))
        return

    if not result.leads:
        st.warning("Bu sorguda Google Places'ta websitesi listelenmeyen uygun lead bulunamadı.")
        return

    st.success(f"{len(result.leads)} uygun lead bulundu.")

    rows = lead_rows(result.leads)
    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Skor": st.column_config.NumberColumn("Skor", min_value=0, max_value=100),
            "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="Aç"),
            "Place ID": None,
        },
    )

    top = result.leads[0]
    st.subheader("En yüksek skorlu lead")
    st.write(f"**{top.lead.place.display_name} — {top.lead.score}/100**")
    st.write("Skor nedenleri:")
    for reason in top.lead.reasons:
        st.write(f"- {reason.message}")

    if result.next_page_token:
        st.caption("Google Places bu sorgu için ek sonuç sayfası olduğunu bildirdi. Pagination desteği sonraki dashboard geliştirmelerinde UI'a eklenecek.")


def main() -> None:
    run_dashboard()


if __name__ == "__main__":
    main()
