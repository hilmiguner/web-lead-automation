import json

import pytest

from web_lead_automation.demo import (
    DemoGenerationError,
    DemoGenerationRequest,
    DemoGenerator,
    ThemeKey,
    demo_slug,
)
from web_lead_automation.services.ai_content import DemoAIContent, GeneratedService


def _content(*, hero_title: str = "Gemlik'te bakım için kolay iletişim") -> DemoAIContent:
    return DemoAIContent(
        tone="Sade ve güven veren",
        hero_title=hero_title,
        hero_text="İşletmeyle hızlıca iletişim kurun ve doğrulanmış bilgileri tek yerde görün.",
        about_text="Bu demo yalnızca doğrulanmış işletme verileri ve kullanıcı tarafından incelenen içerikle hazırlanmıştır.",
        services=(
            GeneratedService(
                title="Hizmetleri Öğrenin",
                description="Sunulan hizmetler hakkında doğrudan işletmeden bilgi alın.",
            ),
            GeneratedService(
                title="Detaylı Bilgi Alın",
                description="İhtiyacınıza uygun seçenekleri işletmeyle görüşerek netleştirin.",
            ),
            GeneratedService(
                title="İletişim ve Konum",
                description="Telefon, WhatsApp ve konum bilgilerine kolayca ulaşın.",
            ),
        ),
        primary_cta_text="WhatsApp'tan Bilgi Al",
        secondary_cta_text="Telefonla Görüş",
        seo_title="Örnek Kuaför | Gemlik",
        seo_description="Örnek Kuaför için hazırlanmış demo web sitesi önizlemesi ve iletişim bilgileri.",
        content_notes=(),
    )


def _request(**overrides) -> DemoGenerationRequest:
    values = {
        "external_place_id": "ChIJ-example-place-id",
        "business_name": "Örnek Kuaför & Bakım",
        "sector": "kuaför berber",
        "content": _content(),
        "phone_number": "0224 123 45 67",
        "whatsapp_number": "0224 123 45 67",
        "address": "Gemlik, Bursa",
        "maps_url": "https://maps.google.com/example",
        "place_types": ("hair_salon",),
    }
    values.update(overrides)
    return DemoGenerationRequest(**values)


def test_demo_slug_is_safe_deterministic_and_does_not_expose_full_place_id() -> None:
    first = demo_slug("Şevval Güzellik & Bakım", "secret-place-id-123")
    second = demo_slug("Şevval Güzellik & Bakım", "secret-place-id-123")

    assert first == second
    assert first.startswith("sevval-guzellik-bakim-")
    assert "secret-place-id-123" not in first
    assert set(first) <= set("abcdefghijklmnopqrstuvwxyz0123456789-")


def test_generate_writes_html_and_manifest_with_reviewed_content(tmp_path) -> None:
    generator = DemoGenerator(tmp_path)

    generated = generator.generate(_request())

    assert generated.regenerated is False
    assert generated.theme_key is ThemeKey.HAIR_BEAUTY
    assert generated.index_path.exists()
    assert generated.manifest_path.exists()

    html = generated.index_path.read_text(encoding="utf-8")
    assert "Gemlik&#x27;te bakım için kolay iletişim" in html
    assert "WhatsApp&#x27;tan Bilgi Al" in html
    assert "Telefonla Görüş" in html
    assert 'data-demo-theme="hair_beauty"' in html

    manifest = json.loads(generated.manifest_path.read_text(encoding="utf-8"))
    assert manifest["external_place_id"] == "ChIJ-example-place-id"
    assert manifest["theme"] == "hair_beauty"
    assert manifest["content"]["hero_title"] == "Gemlik'te bakım için kolay iletişim"


def test_find_index_path_returns_existing_demo(tmp_path) -> None:
    generator = DemoGenerator(tmp_path)
    generated = generator.generate(_request())

    found = generator.find_index_path(
        external_place_id="ChIJ-example-place-id",
        business_name="Örnek Kuaför & Bakım",
    )

    assert found == generated.index_path


def test_remove_demo_deletes_only_target_lead_folder(tmp_path) -> None:
    generator = DemoGenerator(tmp_path)
    target = generator.generate(_request())
    other = generator.generate(
        _request(
            external_place_id="place-other",
            business_name="Başka İşletme",
        )
    )

    removed = generator.remove_demo(
        external_place_id="ChIJ-example-place-id",
        business_name="Örnek Kuaför & Bakım",
    )

    assert removed is True
    assert not target.directory.exists()
    assert other.directory.exists()
    assert generator.remove_demo(
        external_place_id="ChIJ-example-place-id",
        business_name="Örnek Kuaför & Bakım",
    ) is False


def test_regenerate_reuses_same_folder_and_replaces_reviewed_content(tmp_path) -> None:
    generator = DemoGenerator(tmp_path)
    first = generator.generate(_request())
    updated_content = _content(hero_title="Güncellenmiş hero başlığı")

    second = generator.generate(_request(content=updated_content))

    assert second.regenerated is True
    assert second.slug == first.slug
    assert second.directory == first.directory
    assert "Güncellenmiş hero başlığı" in second.index_path.read_text(encoding="utf-8")
    assert "Gemlik&#x27;te bakım için kolay iletişim" not in second.index_path.read_text(
        encoding="utf-8"
    )


def test_load_saved_draft_recovers_last_generated_editable_source(tmp_path) -> None:
    generator = DemoGenerator(tmp_path)
    generator.generate(
        _request(
            theme=ThemeKey.GENERAL,
            brand_mark_text="ÖK",
            content=_content(hero_title="Kullanıcının düzenlediği başlık"),
        )
    )

    saved = generator.load_saved_draft(
        external_place_id="ChIJ-example-place-id",
        business_name="Örnek Kuaför & Bakım",
    )

    assert saved is not None
    assert saved.content.hero_title == "Kullanıcının düzenlediği başlık"
    assert saved.theme_key is ThemeKey.GENERAL
    assert saved.brand_mark_text == "ÖK"
    assert saved.sector == "kuaför berber"


def test_load_saved_draft_returns_none_when_lead_has_no_demo(tmp_path) -> None:
    saved = DemoGenerator(tmp_path).load_saved_draft(
        external_place_id="missing",
        business_name="Yeni İşletme",
    )
    assert saved is None


def test_load_saved_draft_rejects_tampered_manifest(tmp_path) -> None:
    generator = DemoGenerator(tmp_path)
    generated = generator.generate(_request())
    manifest = json.loads(generated.manifest_path.read_text(encoding="utf-8"))
    manifest["external_place_id"] = "another-place"
    generated.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(DemoGenerationError, match="another lead"):
        generator.load_saved_draft(
            external_place_id="ChIJ-example-place-id",
            business_name="Örnek Kuaför & Bakım",
        )


def test_different_place_ids_cannot_collide_on_same_business_name() -> None:
    first = demo_slug("Aynı İşletme", "place-1")
    second = demo_slug("Aynı İşletme", "place-2")
    assert first != second


def test_generate_rejects_blank_identity_fields(tmp_path) -> None:
    with pytest.raises(ValueError, match="external_place_id must not be empty"):
        DemoGenerator(tmp_path).generate(_request(external_place_id="   "))
