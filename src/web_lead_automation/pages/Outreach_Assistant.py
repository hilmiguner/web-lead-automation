"""Streamlit page for copy-ready sales outreach."""

from __future__ import annotations

import streamlit as st

from web_lead_automation.config import get_settings
from web_lead_automation.dashboard import (
    SEARCH_RESULT_SESSION_KEY,
    SEARCH_SECTOR_SESSION_KEY,
    SELECTED_PLACE_SESSION_KEY,
    find_lead_by_place_id,
    lead_detail_label,
)
from web_lead_automation.services.lead_history import LeadSearchWithHistoryResult
from web_lead_automation.services.outreach import generate_outreach_bundle
from web_lead_automation.storage.crm import LeadRepository


def main() -> None:
    st.set_page_config(page_title="Outreach Assistant", page_icon="💬", layout="wide")
    st.title("Outreach Assistant")
    st.caption(
        "Seçili lead için güvenli WhatsApp mesajları ve kısa telefon görüşmesi açılışı hazırla. "
        "Mesajlar otomatik gönderilmez."
    )

    result = st.session_state.get(SEARCH_RESULT_SESSION_KEY)
    if not isinstance(result, LeadSearchWithHistoryResult) or not result.leads:
        st.info(
            "Önce ana Lead Finder sayfasında bir bölge/sektör araması yap ve iletişime geçmek "
            "istediğin lead'i seç."
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
    settings = get_settings()
    repository = LeadRepository(settings.lead_db_path)
    repository.initialize()
    tracked = repository.get_by_place_id(place.place_id)
    demo_url = tracked.demo_url if tracked else None

    info_left, info_right = st.columns(2)
    with info_left:
        st.write(f"**İşletme:** {place.display_name or place.place_id}")
        st.write(f"**Telefon:** {place.national_phone_number or '—'}")
    with info_right:
        st.write(f"**CRM:** {selected.status.value}")
        if demo_url:
            st.link_button("Paylaşılabilir Demoyu Aç", demo_url)
        else:
            st.write("**Demo linki:** Henüz yayınlanmadı")

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
        "Outreach Assistant yalnızca metin hazırlar. WhatsApp mesajını veya aramayı otomatik olarak "
        "başlatmaz; gönderim ve iletişim kararı kullanıcıdadır."
    )


if __name__ == "__main__":
    main()
