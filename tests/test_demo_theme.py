import pytest

from web_lead_automation.demo.theme import (
    THEMES,
    ThemeKey,
    recommend_theme,
    render_theme_css,
    resolve_theme,
)


@pytest.mark.parametrize(
    ("sector", "expected"),
    [
        ("Kuaför / Berber", ThemeKey.HAIR_BEAUTY),
        ("Güzellik Merkezi", ThemeKey.HAIR_BEAUTY),
        ("Oto Servis", ThemeKey.AUTOMOTIVE),
        ("Emlak Ofisi", ThemeKey.PROPERTY),
        ("Nakliyat Firması", ThemeKey.LOGISTICS),
        ("Düğün Salonu / Organizasyon", ThemeKey.EVENT),
        ("Yapı / Tadilat", ThemeKey.CONSTRUCTION),
    ],
)
def test_recommend_theme_from_sector(sector: str, expected: ThemeKey) -> None:
    assert recommend_theme(sector).key is expected


def test_recommend_theme_can_use_google_place_type() -> None:
    theme = recommend_theme("yerel işletme", place_types=("car_repair",))
    assert theme.key is ThemeKey.AUTOMOTIVE


def test_unknown_sector_falls_back_to_general() -> None:
    assert recommend_theme("veteriner").key is ThemeKey.GENERAL


def test_explicit_theme_overrides_sector_recommendation() -> None:
    theme = resolve_theme(ThemeKey.EVENT, sector="Oto Servis")
    assert theme.key is ThemeKey.EVENT


def test_unknown_explicit_theme_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown demo theme"):
        resolve_theme("javascript:alert(1)", sector="Kuaför")


def test_render_theme_css_only_uses_trusted_preset_values() -> None:
    theme = THEMES[ThemeKey.PROPERTY]
    css = render_theme_css(theme)

    assert theme.accent in css
    assert theme.background in css
    assert theme.surface_strong in css
    assert "url(" not in css
    assert "javascript:" not in css
