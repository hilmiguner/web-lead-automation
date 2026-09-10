import pytest

from web_lead_automation.demo import (
    DemoService,
    DemoTemplateContext,
    ThemeKey,
    render_demo_html,
)


def _context(**overrides) -> DemoTemplateContext:
    values = {
        "business_name": "Örnek Kuaför",
        "sector": "Kuaför / Berber",
        "hero_title": "Tarzınızı öne çıkaran modern bakım deneyimi.",
        "hero_text": "Randevu ve bilgi için işletmeyle kolayca iletişime geçin.",
        "about_text": "İşletmenin doğrulanmış bilgileri bu alanda sunulacaktır.",
        "services": (
            DemoService("Saç Kesimi", "Hizmet açıklaması."),
            DemoService("Bakım", "Hizmet açıklaması."),
            DemoService("Randevu", "Hizmet açıklaması."),
        ),
        "phone_number": "0224 123 45 67",
        "whatsapp_number": "0224 123 45 67",
        "address": "Gemlik, Bursa",
        "maps_url": "https://maps.google.com/example",
    }
    values.update(overrides)
    return DemoTemplateContext(**values)


def test_render_contains_all_m4_1_sections_and_demo_notice() -> None:
    html = render_demo_html(_context())

    assert '<meta name="viewport"' in html
    assert 'id="services"' in html
    assert 'id="about"' in html
    assert 'id="contact"' in html
    assert "Demo Önizleme" in html
    assert "resmi web sitesi olduğu anlamına gelmez" in html
    assert "mobile-contact" in html
    assert "@media (max-width: 640px)" in html


def test_internal_hash_navigation_stays_inside_embedded_preview() -> None:
    html = render_demo_html(_context())

    assert 'href="#services"' in html
    assert 'href="#about"' in html
    assert 'href="#contact"' in html
    assert "data-demo-internal-navigation" in html
    assert "event.preventDefault();" in html
    assert "target.scrollIntoView" in html
    assert "document.getElementById(hash.slice(1))" in html


def test_render_builds_phone_whatsapp_and_maps_actions_when_explicitly_available() -> None:
    html = render_demo_html(_context())

    assert 'href="tel:+902241234567"' in html
    assert 'href="https://wa.me/902241234567"' in html
    assert 'href="https://maps.google.com/example"' in html


def test_render_does_not_infer_whatsapp_from_phone_number() -> None:
    html = render_demo_html(_context(whatsapp_number=None))

    assert "wa.me" not in html
    assert ">WhatsApp</a>" not in html
    assert "WhatsApp'tan Yazın" not in html
    assert 'href="tel:+902241234567"' in html


def test_ai_cta_labels_are_bound_to_contact_and_maps_targets() -> None:
    html = render_demo_html(
        _context(
            whatsapp_number=None,
            primary_cta_text="İletişime Geçin",
            secondary_cta_text="Konumu Görün",
        )
    )

    assert (
        '<a class="button button-primary" href="tel:+902241234567">'
        "İletişime Geçin</a>"
    ) in html
    assert (
        '<a class="button button-secondary" href="https://maps.google.com/example" '
        'rel="noopener">Konumu Görün</a>'
    ) in html
    assert 'href="tel:+902241234567">Konumu Görün</a>' not in html


def test_unavailable_whatsapp_label_falls_back_to_generic_contact_copy() -> None:
    html = render_demo_html(
        _context(
            whatsapp_number=None,
            primary_cta_text="WhatsApp'tan Bilgi Al",
            secondary_cta_text="Konumu Görün",
        )
    )

    assert "WhatsApp&#x27;tan Bilgi Al" not in html
    assert 'href="tel:+902241234567">İletişime Geçin</a>' in html
    assert 'href="https://maps.google.com/example" rel="noopener">Konumu Görün</a>' in html


def test_render_normalizes_google_address_unicode_casing_and_business_prefix() -> None:
    html = render_demo_html(
        _context(
            business_name="Kuaför Engin VAROL",
            address=(
                "Kuaför Engin VAROL, osmaniye, Taksim sk. bilgen apt, "
                "16600 Gemli\u0307k / bursa"
            ),
        )
    )

    assert "Osmaniye, Taksim Sk. Bilgen Apt., 16600 Gemlik/Bursa" in html
    assert "Gemli\u0307k" not in html
    assert "bilgen apt" not in html


def test_render_escapes_business_and_service_content() -> None:
    html = render_demo_html(
        _context(
            business_name='<script>alert("x")</script>',
            services=(DemoService("<b>Kesim</b>", "<img src=x onerror=alert(1)>") ,),
        )
    )

    assert '<script>alert("x")</script>' not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;Kesim&lt;/b&gt;" in html
    assert "onerror=alert(1)&gt;" in html


def test_render_rejects_unsafe_maps_scheme() -> None:
    html = render_demo_html(_context(maps_url="javascript:alert(1)"))

    assert "javascript:alert(1)" not in html
    assert 'href="https://maps.google.com/example"' not in html


def test_render_handles_missing_contact_information() -> None:
    html = render_demo_html(
        _context(phone_number=None, whatsapp_number=None, maps_url=None, address=None)
    )

    assert "Adres bilgisi eklenecek" in html
    assert "wa.me" not in html
    assert 'href="#contact"' in html


def test_render_requires_at_least_one_service() -> None:
    with pytest.raises(ValueError, match="services must contain at least one item"):
        render_demo_html(_context(services=()))


def test_render_rejects_blank_required_content() -> None:
    with pytest.raises(ValueError, match="hero_title must not be empty"):
        render_demo_html(_context(hero_title="   "))


def test_render_automatically_applies_sector_theme() -> None:
    html = render_demo_html(_context())

    assert 'data-demo-theme="hair_beauty"' in html
    assert "--accent: #a855f7" in html
    assert "Bakım, stil ve randevu odaklı deneyim" in html


def test_render_allows_explicit_trusted_theme_override() -> None:
    html = render_demo_html(_context(theme=ThemeKey.AUTOMOTIVE))

    assert 'data-demo-theme="automotive"' in html
    assert "--accent: #2563eb" in html


def test_render_supports_short_text_brand_mark() -> None:
    html = render_demo_html(_context(brand_mark_text="ÖK"))
    assert '<span class="brand-mark">ÖK</span>' in html


def test_render_rejects_long_brand_mark() -> None:
    with pytest.raises(ValueError, match="at most 3 characters"):
        render_demo_html(_context(brand_mark_text="UZUN"))
