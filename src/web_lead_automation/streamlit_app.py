"""Streamlit dashboard for the MVP lead-search workflow."""

from __future__ import annotations

import streamlit as st

from web_lead_automation.config import Settings, get_settings
from web_lead_automation.services.lead_finder import LeadFinder
from web_lead_automation.services.lead_history import LeadHistoryService
from web_lead_automation.services.places import GooglePlacesClient, GooglePlacesError
from web_lead_automation.storage.crm import LeadRepository
from web_lead_automation.ui_models import (
    SECTOR_PRESETS,
    leads_to_table_rows,
    resolve_sector_query,
)


def search_leads(*, settings: Settings, sector: str, location: str):
    """Execute one complete search and CRM-history enrichment cycle."""

    repository = LeadRepository(settings.lead_db_path)
    repository.initialize()

    with GooglePlacesClient(
        api_key=settings.google_places_api_key,
        timeout_seconds=settings.google_places_timeout_seconds,
        default_page_size=settings.google_places_page_size,
    ) as places_client:
        raw_result = LeadFinder(places_client).search(
            sector=sector,
            location=location,
            page_size=settings.google_places_page_size,
        )

    return LeadHistoryService(repository).record_search_result(raw_result)


def main() -> None:
    """Render the Streamlit MVP dashboard."""

    st.set_page_config(
        page_title="Web Lead Automation",
        page_icon="🔎",
        layout="wide",
    )

    settings = get_settings()

    st.title("Web Lead Automation")
    st.caption(
        "Web sitesi Google Places'ta listelenmeyen yerel işletmeleri bul, "
        "puanla ve satış için önceliklendir."
    )

    if not settings.google_places_api_key:
        st.warning(
            "GOOGLE_PLACES_API_KEY tanımlı değil. `.env` dosyasına API anahtarını "
            "eklemeden gerçek işletme araması yapılamaz."
        )

    with st.form("lead_search_form"):
        left, right = st.columns(2)
        with left:
            location = st.text_input(
                "Bölge",
                value="Gemlik Bursa",
                placeholder="Örn. Gemlik Bursa",
            )
        with right:
            sector_preset = st.selectbox(
                "Sektör",
                options=tuple(SECTOR_PRESETS),
                index=0,
            )

        custom_sector = ""
        if sector_preset == "Özel Sektör":
            custom_sector = st.text_input(
                "Özel sektör adı",
                placeholder="Örn. psikolog",
            )

        submitted = st.form_submit_button(
            "Lead Ara",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            sector = resolve_sector_query(sector_preset, custom_sector)
            normalized_location = location.strip()
            if not normalized_location:
                raise ValueError("Bölge boş bırakılamaz.")

            with st.spinner("İşletmeler aranıyor ve skorlanıyor..."):
                result = search_leads(
                    settings=settings,
                    sector=sector,
                    location=normalized_location,
                )

            st.session_state["lead_rows"] = leads_to_table_rows(result.leads)
            st.session_state["lead_query"] = f"{sector} — {normalized_location}"
            st.session_state["lead_next_page_token"] = result.next_page_token
        except (ValueError, GooglePlacesError) as exc:
            st.error(str(exc))

    rows = st.session_state.get("lead_rows", [])
    if not rows:
        if submitted:
            st.info("Bu aramada website'si listelenmeyen uygun lead bulunamadı.")
        else:
            st.info("Bölge ve sektör seçip `Lead Ara` butonuna bas.")
        return

    query_label = st.session_state.get("lead_query", "")
    st.subheader("Lead Sonuçları")
    if query_label:
        st.caption(query_label)

    metric_cols = st.columns(3)
    metric_cols[0].metric("Lead", len(rows))
    metric_cols[1].metric(
        "Telefonu Olan",
        sum(1 for row in rows if row["Telefon"] != "—"),
    )
    metric_cols[2].metric(
        "Daha Önce Görülen",
        sum(1 for row in rows if row["Daha Önce Görüldü"] == "Evet"),
    )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "Skor",
            "İşletme",
            "Website",
            "Telefon",
            "Rating",
            "Yorum",
            "CRM",
            "Daha Önce Görüldü",
            "Adres",
            "Google Maps",
        ),
        column_config={
            "Skor": st.column_config.NumberColumn("Skor", min_value=0, max_value=100),
            "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
            "Yorum": st.column_config.NumberColumn("Yorum", format="%d"),
            "Google Maps": st.column_config.LinkColumn(
                "Google Maps",
                display_text="Haritada Aç",
            ),
        },
    )

    if st.session_state.get("lead_next_page_token"):
        st.caption("Google Places'ta ek sonuçlar mevcut; sonraki sayfa desteği sonraki UI geliştirmelerinde eklenebilir.")


if __name__ == "__main__":
    main()
