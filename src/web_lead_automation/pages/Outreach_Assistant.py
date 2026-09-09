"""Streamlit page for copy-ready sales outreach and contact tracking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

from web_lead_automation.config import get_settings
from web_lead_automation.dashboard import (
    SEARCH_RESULT_SESSION_KEY,
    SEARCH_SECTOR_SESSION_KEY,
    SELECTED_PLACE_SESSION_KEY,
    apply_tracked_state,
    find_lead_by_place_id,
    lead_detail_label,
    replace_result_lead,
)
from web_lead_automation.services.lead_history import LeadSearchWithHistoryResult
from web_lead_automation.services.outreach import generate_outreach_bundle
from web_lead_automation.storage.crm import LeadRepository, TrackedLead


OUTREACH_FLASH_SESSION_KEY = "outreach_flash_message"
FOLLOW_UP_OPTIONS = {
    "Takip planlama": None,
    "Yarın": 1,
    "3 gün sonra": 3,
    "7 gün sonra": 7,
}


def follow_up_datetime(option: str, *, now: datetime | None = None) -> datetime | None:
    """Resolve a simple follow-up preset into a timezone-aware UTC datetime."""

    if option not in FOLLOW_UP_OPTIONS:
        raise ValueError("Unknown follow-up option.")
    days = FOLLOW_UP_OPTIONS[option]
    if days is None:
        return None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware.")
    return current.astimezone(timezone.utc) + timedelta(days=days)


def follow_up_rows(leads: tuple[TrackedLead, ...]) -> list[dict[str, object]]:
    """Convert due CRM follow-ups into a compact Streamlit table."""

    return [
        {
            "İşletme": lead.display_name or lead.external_place_id,
            "CRM": lead.status.value,
            "Son iletişim": (
                lead.last_contact_at.strftime("%Y-%m-%d %H:%M UTC")
                if lead.last_contact_at
                else "—"
            ),
            "Takip zamanı": (
                lead.follow_up_at.strftime("%Y-%m-%d %H:%M UTC")
                if lead.follow_up_at
                else "—"
            ),
            "Görüşme notu": lead.contact_note or "—",
            "Place ID": lead.external_place_id,
        }
        for lead in leads
    ]


def main() -> None:
    st.set_page_config(page_title="Outreach Assistant", page_icon="💬", layout="wide")
    st.title("Outreach Assistant")
    st.caption(
        "Seçili lead için güvenli satış metinleri hazırla, iletişimi kaydet ve takip zamanı "
        "gelen lead'leri gör. Mesajlar otomatik gönderilmez."
    )

    flash_message = st.session_state.pop(OUTREACH_FLASH_SESSION_KEY, None)
    if flash_message:
        st.success(flash_message)

    settings = get_settings()
    repository = LeadRepository(settings.lead_db_path)
    repository.initialize()
    _render_due_follow_ups(repository)

    result = st.session_state.get(SEARCH_RESULT_SESSION_KEY)
    if not isinstance(result, LeadSearchWithHistoryResult) or not result.leads:
        st.info(
            "Yeni bir lead ile çalışmak için ana Lead Finder sayfasında bölge/sektör araması yap. "
            "Yukarıdaki takip listesi CRM verisinden bağımsız olarak kullanılabilir."
        )
        return

    place_ids = [item.lead.place.place_id for item in result.leads]
    selected_place_id = st.session_state.get(SELECTED_PLACE_SESSION_KEY)
    if selected_place_id not in place_ids:
        selected_place_id = place_ids[0]

    current_index = place_ids.index(str(selected_place_id))
    selected_place_id = st.selectbox(
        "Lead",
        options=place_ids,
        index=current_index,
        format_func=lambda place_id: lead_detail_label(
            find_lead_by_place_id(result.leads, place_id)  # type: ignore[arg-type]
        ),
    )
    st.session_state[SELECTED_PLACE_SESSION_KEY] = selected_place_id

    selected = find_lead_by_place_id(result.leads, selected_place_id)
    if selected is None:
        st.error("Seçilen lead mevcut arama sonucunda bulunamadı.")
        return

    place = selected.lead.place
    tracked = repository.get_by_place_id(place.place_id)
    demo_url = tracked.demo_url if tracked else None

    info_left, info_right = st.columns(2)
    with info_left:
        st.write(f"**İşletme:** {place.display_name or place.place_id}")
        st.write(f"**Telefon:** {place.national_phone_number or '—'}")
        st.write(f"**CRM:** {selected.status.value}")
    with info_right:
        st.write(
            "**Son iletişim:** "
            + (
                tracked.last_contact_at.strftime("%Y-%m-%d %H:%M UTC")
                if tracked and tracked.last_contact_at
                else "Henüz kaydedilmedi"
            )
        )
        st.write(
            "**Planlı takip:** "
            + (
                tracked.follow_up_at.strftime("%Y-%m-%d %H:%M UTC")
                if tracked and tracked.follow_up_at
                else "Yok"
            )
        )
        if demo_url:
            st.link_button("Paylaşılabilir Demoyu Aç", demo_url)
        else:
            st.write("**Demo linki:** Henüz yayınlanmadı")

    _render_contact_form(selected, result, repository, tracked)

    include_demo_link = st.checkbox(
        "Paylaşılabilir demo linkini WhatsApp mesajına ekle",
        value=bool(demo_url),
        disabled=not bool(demo_url),
        help="Demo linki önce Lead Finder sayfasında Netlify'a yayınlanıp CRM'e kaydedilmelidir.",
    )

    sector = str(st.session_state.get(SEARCH_SECTOR_SESSION_KEY) or "").strip() or None
    try:
        bundle = generate_outreach_bundle(
            business_name=place.display_name or place.place_id,
            sector=sector,
            demo_url=demo_url,
            include_demo_link=include_demo_link,
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    st.divider()
    st.subheader("WhatsApp mesajları")
    st.caption(
        "İstediğin varyasyonu seç. Her kod kutusunun sağ üstündeki kopyalama düğmesi mesajı "
        "tek tıkla panoya alır. Göndermeden önce son kez kontrol et."
    )

    tabs = st.tabs([message.label for message in bundle.whatsapp_messages])
    for tab, message in zip(tabs, bundle.whatsapp_messages, strict=True):
        with tab:
            st.code(message.text, language=None, wrap_lines=True)

    st.divider()
    st.subheader("Telefon görüşmesi açılışı")
    st.caption("Kısa bir ilk temas metni; işletmenin resmi sitesi var/yok konusunda kesin iddia içermez.")
    st.code(bundle.phone_opener, language=None, wrap_lines=True)

    st.info(
        "Outreach Assistant yalnızca metin ve CRM takibi sağlar. WhatsApp mesajını veya aramayı "
        "otomatik olarak başlatmaz; gönderim ve iletişim kararı kullanıcıdadır."
    )


def _render_due_follow_ups(repository: LeadRepository) -> None:
    st.subheader("Takip zamanı gelen lead'ler")
    due = repository.list_follow_ups_due()
    if not due:
        st.caption("Şu anda takip zamanı gelmiş açık lead bulunmuyor.")
        return

    st.warning(f"{len(due)} lead için planlı takip zamanı geldi.")
    st.dataframe(
        follow_up_rows(due),
        hide_index=True,
        use_container_width=True,
        column_config={"Place ID": None},
    )


def _render_contact_form(
    selected,
    result: LeadSearchWithHistoryResult,
    repository: LeadRepository,
    tracked: TrackedLead | None,
) -> None:
    place = selected.lead.place
    st.divider()
    st.subheader("İletişim takibi")
    st.caption(
        "Mesajı gönderdikten veya aramayı yaptıktan sonra burada kaydet. NEW durumundaki lead "
        "CONTACTED olur; daha ileri CRM durumları geriye alınmaz."
    )

    with st.form(f"contact_form_{place.place_id}"):
        contact_note = st.text_area(
            "Kısa görüşme notu",
            value=tracked.contact_note if tracked else "",
            height=100,
            placeholder="Örn. WhatsApp gönderildi, cuma yeniden dönüş yap.",
        )
        follow_up_option = st.selectbox(
            "Tekrar takip",
            options=list(FOLLOW_UP_OPTIONS),
            index=0,
        )
        submitted = st.form_submit_button(
            "CONTACTED + İletişimi Kaydet",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    now = datetime.now(timezone.utc)
    updated = repository.record_contact(
        place.place_id,
        contact_note=contact_note,
        contacted_at=now,
        follow_up_at=follow_up_datetime(follow_up_option, now=now),
    )
    st.session_state[SEARCH_RESULT_SESSION_KEY] = replace_result_lead(
        result,
        apply_tracked_state(selected, updated),
    )
    st.session_state[OUTREACH_FLASH_SESSION_KEY] = (
        f"{place.display_name or 'Lead'} iletişimi kaydedildi."
    )
    st.rerun()


if __name__ == "__main__":
    main()
