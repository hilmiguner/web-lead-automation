"""Streamlit dashboard for the MVP lead-search workflow."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

import streamlit as st

from web_lead_automation.config import get_settings
from web_lead_automation.services.lead_finder import LeadFinder
from web_lead_automation.services.lead_history import (
    CLOSED_STATUSES,
    CONTACTED_STATUSES,
    LeadHistoryService,
    LeadSearchWithHistoryResult,
    LeadWithHistory,
)
from web_lead_automation.services.places import GooglePlacesClient, GooglePlacesError
from web_lead_automation.services.website_filter import WebsiteStatus
from web_lead_automation.storage.crm import LeadRepository, LeadStatus, TrackedLead


SEARCH_RESULT_SESSION_KEY = "lead_search_result"
SELECTED_PLACE_SESSION_KEY = "selected_place_id"
FLASH_SESSION_KEY = "crm_flash_message"

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
                "Rating": place.rating,
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


def filter_leads(
    leads: Iterable[LeadWithHistory],
    *,
    website_only: bool = True,
    min_score: int = 0,
    phone_only: bool = False,
    statuses: Iterable[LeadStatus] | None = None,
) -> tuple[LeadWithHistory, ...]:
    """Apply dashboard filters without triggering another Places API request."""

    if not 0 <= min_score <= 100:
        raise ValueError("min_score must be between 0 and 100.")

    status_filter = set(LeadStatus if statuses is None else statuses)
    filtered: list[LeadWithHistory] = []

    for item in leads:
        if website_only and item.lead.website_status is not WebsiteStatus.NO_WEBSITE_LISTED:
            continue
        if item.lead.score < min_score:
            continue
        if phone_only and not (item.lead.place.national_phone_number or "").strip():
            continue
        if item.status not in status_filter:
            continue
        filtered.append(item)

    return tuple(filtered)


def lead_detail_label(item: LeadWithHistory) -> str:
    """Human-friendly selectbox label for one lead."""

    name = item.lead.place.display_name or item.lead.place.place_id
    return f"{name} — {item.lead.score}/100 — {item.status.value}"


def find_lead_by_place_id(
    leads: Iterable[LeadWithHistory],
    place_id: str,
) -> LeadWithHistory | None:
    """Find one enriched lead by Google Place ID."""

    return next(
        (item for item in leads if item.lead.place.place_id == place_id),
        None,
    )


def apply_tracked_state(
    item: LeadWithHistory,
    tracked: TrackedLead,
) -> LeadWithHistory:
    """Refresh an in-memory lead with the latest persistent CRM state."""

    return replace(
        item,
        status=tracked.status,
        note=tracked.note,
        first_seen_at=tracked.created_at,
        updated_at=tracked.updated_at,
        was_contacted=tracked.status in CONTACTED_STATUSES,
        is_closed=tracked.status in CLOSED_STATUSES,
    )


def replace_result_lead(
    result: LeadSearchWithHistoryResult,
    updated: LeadWithHistory,
) -> LeadSearchWithHistoryResult:
    """Replace one lead in a cached search result without changing its order."""

    place_id = updated.lead.place.place_id
    return replace(
        result,
        leads=tuple(
            updated if item.lead.place.place_id == place_id else item
            for item in result.leads
        ),
    )


def run_dashboard() -> None:
    """Render the Streamlit MVP dashboard."""

    st.set_page_config(
        page_title="Web Lead Automation",
        page_icon="🔎",
        layout="wide",
    )

    st.title("Web Lead Automation")
    st.caption(
        "Web sitesi Google Places'ta listelenmeyen yerel işletmeleri bul "
        "ve satış önceliğine göre sırala."
    )

    flash_message = st.session_state.pop(FLASH_SESSION_KEY, None)
    if flash_message:
        st.success(flash_message)

    settings = get_settings()
    repository = LeadRepository(settings.lead_db_path)
    repository.initialize()

    left, right = st.columns(2)
    with left:
        location_preset = st.selectbox("Bölge", DEFAULT_LOCATIONS, index=0)
        custom_location = ""
        if location_preset == "Özel bölge yaz":
            custom_location = st.text_input(
                "Özel bölge",
                placeholder="Örn. Mudanya Bursa",
            )

    with right:
        sector_preset = st.selectbox("Sektör", SECTOR_PRESETS, index=0)
        custom_sector = ""
        if sector_preset == "Özel sektör yaz":
            custom_sector = st.text_input(
                "Özel sektör",
                placeholder="Örn. veteriner",
            )

    page_size = st.slider(
        "Tek aramada istenecek işletme sayısı",
        min_value=5,
        max_value=20,
        value=settings.google_places_page_size,
        step=5,
    )

    search_requested = st.button(
        "Lead Ara",
        type="primary",
        use_container_width=True,
    )

    if search_requested:
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
            st.session_state.pop(SEARCH_RESULT_SESSION_KEY, None)
            st.session_state.pop(SELECTED_PLACE_SESSION_KEY, None)
            st.warning(
                "Bu sorguda Google Places'ta websitesi listelenmeyen "
                "uygun lead bulunamadı."
            )
            return

        st.session_state[SEARCH_RESULT_SESSION_KEY] = result
        st.session_state[SELECTED_PLACE_SESSION_KEY] = result.leads[0].lead.place.place_id

    result = st.session_state.get(SEARCH_RESULT_SESSION_KEY)
    if not isinstance(result, LeadSearchWithHistoryResult):
        st.info("Başlamak için bölge ve sektör seçip **Lead Ara** butonuna bas.")
        return

    visible_leads = _render_filters(result.leads)
    _render_search_results(result, visible_leads)

    if not visible_leads:
        st.warning("Seçili filtrelere uyan lead bulunamadı.")
        return

    _render_lead_detail(result, visible_leads, repository)


def _render_filters(
    leads: tuple[LeadWithHistory, ...],
) -> tuple[LeadWithHistory, ...]:
    st.markdown("#### Hızlı filtreler")

    website_col, score_col, phone_col, status_col = st.columns(4)
    with website_col:
        website_only = st.checkbox(
            "Sadece websitesiz",
            value=True,
            help="MVP Lead Finder zaten websitesiz işletmelere odaklanır.",
        )
    with score_col:
        min_score = st.slider(
            "Minimum skor",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
        )
    with phone_col:
        phone_only = st.checkbox("Sadece telefonu olanlar", value=False)
    with status_col:
        selected_status_values = st.multiselect(
            "CRM durumu",
            options=[status.value for status in LeadStatus],
            default=[status.value for status in LeadStatus],
        )

    statuses = tuple(LeadStatus(value) for value in selected_status_values)
    return filter_leads(
        leads,
        website_only=website_only,
        min_score=min_score,
        phone_only=phone_only,
        statuses=statuses,
    )


def _render_search_results(
    result: LeadSearchWithHistoryResult,
    visible_leads: tuple[LeadWithHistory, ...],
) -> None:
    st.success(
        f"{len(visible_leads)} / {len(result.leads)} lead gösteriliyor."
    )

    if visible_leads:
        rows = lead_rows(visible_leads)
        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Skor": st.column_config.NumberColumn(
                    "Skor",
                    min_value=0,
                    max_value=100,
                ),
                "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                "Google Maps": st.column_config.LinkColumn(
                    "Google Maps",
                    display_text="Aç",
                ),
                "Place ID": None,
            },
        )

    if result.next_page_token:
        st.caption(
            "Google Places bu sorgu için ek sonuç sayfası olduğunu bildirdi. "
            "Pagination desteği sonraki dashboard geliştirmelerinde UI'a eklenecek."
        )


def _render_lead_detail(
    result: LeadSearchWithHistoryResult,
    visible_leads: tuple[LeadWithHistory, ...],
    repository: LeadRepository,
) -> None:
    st.divider()
    st.subheader("Lead detayı")

    place_ids = [item.lead.place.place_id for item in visible_leads]
    current_place_id = st.session_state.get(SELECTED_PLACE_SESSION_KEY)
    if current_place_id not in place_ids:
        current_place_id = place_ids[0]
        st.session_state[SELECTED_PLACE_SESSION_KEY] = current_place_id

    current_index = place_ids.index(current_place_id)
    selected_place_id = st.selectbox(
        "Detayını görmek istediğin lead",
        options=place_ids,
        index=current_index,
        format_func=lambda place_id: lead_detail_label(
            find_lead_by_place_id(visible_leads, place_id)  # type: ignore[arg-type]
        ),
    )
    st.session_state[SELECTED_PLACE_SESSION_KEY] = selected_place_id

    selected = find_lead_by_place_id(visible_leads, selected_place_id)
    if selected is None:
        st.error("Seçilen lead arama sonucunda bulunamadı.")
        return

    place = selected.lead.place

    score_col, rating_col, reviews_col, status_col = st.columns(4)
    score_col.metric("Lead Score", f"{selected.lead.score}/100")
    rating_col.metric(
        "Google Rating",
        f"{place.rating:.1f}" if place.rating is not None else "—",
    )
    reviews_col.metric("Yorum", place.user_rating_count or 0)
    status_col.metric("CRM", selected.status.value)

    st.markdown(f"### {place.display_name or 'İsimsiz işletme'}")
    detail_left, detail_right = st.columns(2)
    with detail_left:
        st.write(f"**Telefon:** {place.national_phone_number or '—'}")
        st.write(f"**Adres:** {place.formatted_address or '—'}")
        st.write("**Website:** Google Places'ta listelenmiyor")
    with detail_right:
        st.write(
            "**Daha önce görüldü:** "
            + ("Evet" if selected.seen_before else "Hayır")
        )
        st.write(
            "**Daha önce iletişim:** "
            + ("Evet" if selected.was_contacted else "Hayır")
        )
        st.write(f"**İlk görüldü:** {selected.first_seen_at:%Y-%m-%d %H:%M UTC}")

    if place.google_maps_uri:
        st.link_button(
            "Google Maps'te Aç",
            place.google_maps_uri,
            use_container_width=False,
        )

    with st.expander("Skor açıklaması", expanded=True):
        for reason in selected.lead.reasons:
            st.write(f"- {reason.message}")

    st.markdown("#### CRM")
    with st.form(f"crm_form_{selected_place_id}"):
        status_values = [status.value for status in LeadStatus]
        selected_status = st.selectbox(
            "Durum",
            options=status_values,
            index=status_values.index(selected.status.value),
            key=f"crm_status_{selected_place_id}",
        )
        note = st.text_area(
            "Not",
            value=selected.note,
            height=120,
            placeholder="Örn. WhatsApp üzerinden ulaşıldı, cuma tekrar ara.",
            key=f"crm_note_{selected_place_id}",
        )
        submitted = st.form_submit_button(
            "CRM Kaydet",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        tracked = repository.update(
            selected_place_id,
            status=LeadStatus(selected_status),
            note=note,
        )
        updated = apply_tracked_state(selected, tracked)
        st.session_state[SEARCH_RESULT_SESSION_KEY] = replace_result_lead(
            result,
            updated,
        )
        st.session_state[FLASH_SESSION_KEY] = (
            f"{place.display_name or 'Lead'} CRM kaydı güncellendi."
        )
        st.rerun()


def main() -> None:
    run_dashboard()


if __name__ == "__main__":
    main()
