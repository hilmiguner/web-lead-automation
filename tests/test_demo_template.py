import pytest

from web_lead_automation.demo import (
    DemoService,
    DemoTemplateContext,
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


def test_render_builds_phone_whatsapp_and_maps_actions() -> None:
    html = render_demo_html(_context())

    assert 'href="tel:+902241234567"' in html
    assert 'href="https://wa.me/902241234567"' in html
    assert 'href="https://maps.google.com/example"' in html


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
    assert 'href="#contact"' in html


def test_render_handles_missing_contact_information() -> None:
    html = render_demo_html(
        _context(phone_number=None, whatsapp_number=None, maps_url=None, address=None)
    )

    assert "Telefon bilgisi eklenecek" in html
    assert "Adres bilgisi eklenecek" in html
    assert 'href="#contact"' in html


def test_render_requires_at_least_one_service() -> None:
    with pytest.raises(ValueError, match="services must contain at least one item"):
        render_demo_html(_context(services=()))


def test_render_rejects_blank_required_content() -> None:
    with pytest.raises(ValueError, match="hero_title must not be empty"):
        render_demo_html(_context(hero_title="   "))
