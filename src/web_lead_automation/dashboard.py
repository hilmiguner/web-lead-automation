"""Streamlit dashboard for the MVP lead-search workflow."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

import streamlit as st

from web_lead_automation.config import Settings, get_settings
from web_lead_automation.services.ai_content import (
    AIContentError,
    BusinessContentBrief,
    DemoAIContent,
    GeneratedService,
    OpenAIContentClient,
)
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
SEARCH_SECTOR_SESSION_KEY = "lead_search_sector"
SELECTED_PLACE_SESSION_KEY = "selected_place_id"
FLASH_SESSION_KEY = "crm_flash_message"
AI_CONTENT_SESSION_PREFIX = "ai_content:"

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


def parse_known_services(raw_value: str) -> tuple[str, ...]:
    """Parse user-confirmed services while preserving order and removing duplicates."""

    normalized = raw_value.replace("\n", ",").replace(";", ",")
    services: list[str] = []
    seen: set[str] = set()
    for value in normalized.split(","):
        service = value.strip()
        key = service.casefold()
        if not service or key in seen:
            continue
        seen.add(key)
        services.append(service)
    return tuple(services)


def ai_content_session_key(place_id: str) -> str:
    """Return a stable per-lead session key for editable AI content."""

    return f"{AI_CONTENT_SESSION_PREFIX}{place_id}"


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
            st.session_state.pop(SEARCH_SECTOR_SESSION_KEY, None)
            st.session_state.pop(SELECTED_PLACE_SESSION_KEY, None)
            st.warning(
                "Bu sorguda Google Places'ta websitesi listelenmeyen "
                "uygun lead bulunamadı."
            )
            return

        st.session_state[SEARCH_RESULT_SESSION_KEY] = result
        st.session_state[SEARCH_SECTOR_SESSION_KEY] = sector
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

    _render_lead_detail(result, visible_leads, repository, settings)


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
    st.success(f"{len(visible_leads)} / {len(result.leads)} lead gösteriliyor.")

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
    settings: Settings,
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

    _render_ai_content_draft(selected, settings)

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


def _render_ai_content_draft(selected: LeadWithHistory, settings: Settings) -> None:
    """Generate and edit AI copy without creating/deploying the website yet."""

    place = selected.lead.place
    place_id = place.place_id
    content_key = ai_content_session_key(place_id)

    st.divider()
    st.subheader("AI demo içeriği")
    st.caption(
        "Bu aşama yalnızca düzenlenebilir içerik taslağı üretir. Site dosyası ve "
        "preview oluşturma M4.4–M4.5 aşamalarında bağlanacak."
    )

    fallback_sector = (
        place.types[0].replace("_", " ") if place.types else "yerel işletme"
    )
    sector = st.text_input(
        "İçerik sektörü",
        value=str(st.session_state.get(SEARCH_SECTOR_SESSION_KEY) or fallback_sector),
        key=f"ai_sector_{place_id}",
    )
    known_services_raw = st.text_area(
        "Doğrulanmış hizmetler (opsiyonel)",
        placeholder="Örn. Saç kesimi, sakal tıraşı. Bilmiyorsan boş bırak.",
        help=(
            "Buraya yalnızca doğruladığın hizmetleri yaz. Boş bırakırsan AI belirli "
            "bir hizmeti işletme sunuyormuş gibi iddia etmeyecek."
        ),
        key=f"ai_known_services_{place_id}",
    )

    if not settings.openai_api_key:
        st.info(
            "AI içerik üretmek için `.env` dosyasına `OPENAI_API_KEY=...` ekle. "
            "Model `OPENAI_MODEL` ile değiştirilebilir."
        )

    generate_requested = st.button(
        "AI İçerik Taslağı Üret",
        key=f"generate_ai_content_{place_id}",
        disabled=not bool(settings.openai_api_key),
        use_container_width=True,
    )

    if generate_requested:
        try:
            with st.spinner("AI içerik taslağı hazırlanıyor..."):
                with OpenAIContentClient(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    timeout_seconds=settings.openai_timeout_seconds,
                ) as client:
                    content = client.generate(
                        BusinessContentBrief(
                            business_name=place.display_name or place.place_id,
                            sector=sector,
                            address=place.formatted_address,
                            known_services=parse_known_services(known_services_raw),
                        )
                    )
            st.session_state[content_key] = content
            st.success("AI içerik taslağı üretildi. Paylaşmadan önce kontrol et.")
        except (AIContentError, ValueError) as exc:
            st.error(str(exc))

    content = st.session_state.get(content_key)
    if not isinstance(content, DemoAIContent):
        return

    if content.content_notes:
        with st.expander("AI kontrol notları", expanded=True):
            for note in content.content_notes:
                st.write(f"- {note}")

    with st.form(f"ai_content_form_{place_id}"):
        tone = st.text_input("Ton", value=content.tone)
        hero_title = st.text_input("Hero başlığı", value=content.hero_title)
        hero_text = st.text_area("Hero açıklaması", value=content.hero_text, height=100)
        about_text = st.text_area("Hakkında", value=content.about_text, height=140)

        st.markdown("**Hizmet / bilgi kartları**")
        edited_services: list[GeneratedService] = []
        service_values: list[tuple[str, str]] = []
        for index, service in enumerate(content.services, start=1):
            title = st.text_input(
                f"Kart {index} başlığı",
                value=service.title,
                key=f"ai_service_title_{place_id}_{index}",
            )
            description = st.text_area(
                f"Kart {index} açıklaması",
                value=service.description,
                height=90,
                key=f"ai_service_desc_{place_id}_{index}",
            )
            service_values.append((title, description))

        cta_left, cta_right = st.columns(2)
        with cta_left:
            primary_cta_text = st.text_input(
                "Birincil CTA",
                value=content.primary_cta_text,
            )
        with cta_right:
            secondary_cta_text = st.text_input(
                "İkincil CTA",
                value=content.secondary_cta_text,
            )

        seo_title = st.text_input("SEO title", value=content.seo_title)
        seo_description = st.text_area(
            "SEO description",
            value=content.seo_description,
            height=90,
        )
        save_content = st.form_submit_button(
            "İçerik Düzenlemelerini Kaydet",
            use_container_width=True,
        )

    if save_content:
        try:
            edited_services = [
                GeneratedService(title=title, description=description)
                for title, description in service_values
            ]
            edited = DemoAIContent(
                tone=tone,
                hero_title=hero_title,
                hero_text=hero_text,
                about_text=about_text,
                services=tuple(edited_services),
                primary_cta_text=primary_cta_text,
                secondary_cta_text=secondary_cta_text,
                seo_title=seo_title,
                seo_description=seo_description,
                content_notes=content.content_notes,
            )
        except ValueError:
            st.error(
                "İçerik alanlarından biri boş veya izin verilen uzunluk sınırının dışında."
            )
        else:
            st.session_state[content_key] = edited
            st.success("İçerik düzenlemeleri oturumda kaydedildi.")


def main() -> None:
    run_dashboard()


if __name__ == "__main__":
    main()
