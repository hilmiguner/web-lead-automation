"""Safe renderer for the reusable single-page website demo template."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from html import escape
from importlib.resources import files
from string import Template
from urllib.parse import urlparse

from web_lead_automation.demo.theme import ThemeKey, render_theme_css, resolve_theme


@dataclass(frozen=True, slots=True)
class DemoService:
    """One service card rendered in the demo website."""

    title: str
    description: str


@dataclass(frozen=True, slots=True)
class DemoTemplateContext:
    """Known and reviewable content used to render a customer demo."""

    business_name: str
    sector: str
    hero_title: str
    hero_text: str
    about_text: str
    services: tuple[DemoService, ...]
    phone_number: str | None = None
    whatsapp_number: str | None = None
    address: str | None = None
    maps_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    primary_cta_text: str = "WhatsApp'tan Yazın"
    secondary_cta_text: str = "Telefonla Ulaşın"
    theme: ThemeKey | str | None = None
    place_types: tuple[str, ...] = ()
    brand_mark_text: str | None = None


def render_demo_html(context: DemoTemplateContext) -> str:
    """Render a self-contained, escaped HTML demo page.

    User/AI-provided text is HTML-escaped before insertion. Visual styling is
    restricted to application-owned theme presets. Only http/https map links
    are accepted. Phone links are generated from digits rather than raw user
    input so the template cannot inject arbitrary URI schemes.

    WhatsApp actions are rendered only when an explicit WhatsApp number was
    supplied. AI CTA labels are bound deterministically to safe actions instead
    of being substituted into unrelated static buttons.
    """

    business_name = _required(context.business_name, "business_name")
    sector = _required(context.sector, "sector")
    hero_title = _required(context.hero_title, "hero_title")
    hero_text = _required(context.hero_text, "hero_text")
    about_text = _required(context.about_text, "about_text")
    primary_cta_text = _required(context.primary_cta_text, "primary_cta_text")
    secondary_cta_text = _required(context.secondary_cta_text, "secondary_cta_text")

    services = tuple(context.services)
    if not services:
        raise ValueError("services must contain at least one item.")

    theme = resolve_theme(
        context.theme,
        sector=sector,
        place_types=tuple(context.place_types),
    )

    template_text = (
        files("web_lead_automation.demo.templates")
        .joinpath("default.html")
        .read_text(encoding="utf-8")
    )
    template_text = template_text.replace(
        '<span class="brand-mark">$business_name</span>',
        '<span class="brand-mark">$brand_initial</span>',
        1,
    )

    # Replace static action blocks with renderer-owned slots. This prevents AI
    # CTA copy from accidentally changing the label of an unrelated tel/maps
    # anchor, which was possible with broad string replacement.
    template_text = template_text.replace(
        """          <div class="hero-actions">
            <a class="button button-primary" href="$whatsapp_href" rel="noopener">WhatsApp'tan Yazın</a>
            <a class="button button-secondary" href="$phone_href">$phone_display</a>
          </div>""",
        "          $hero_actions",
        1,
    )
    template_text = template_text.replace(
        """          <div class="hero-actions">
            <a class="button button-primary" href="$phone_href">Telefonla Ulaşın</a>
            <a class="button button-secondary" href="$maps_href" rel="noopener">Konumu Görün</a>
          </div>""",
        "          $about_actions",
        1,
    )
    template_text = template_text.replace(
        """          <div class="contact-actions">
            <a class="button button-primary" href="$whatsapp_href" rel="noopener">WhatsApp</a>
            <a class="button button-secondary" href="$phone_href">$phone_display</a>
          </div>""",
        "          $contact_actions",
        1,
    )
    template_text = template_text.replace(
        """  <div class="mobile-contact" aria-label="Mobil hızlı iletişim">
    <a href="$phone_href">Ara</a>
    <a href="$whatsapp_href" rel="noopener">WhatsApp</a>
  </div>""",
        "$mobile_contact",
        1,
    )

    theme_style = (
        f'<style data-demo-theme="{escape(theme.key.value, quote=True)}">\n'
        f"{render_theme_css(theme)}\n"
        "</style>"
    )
    template_text = template_text.replace("</head>", f"{theme_style}\n</head>", 1)
    template_text = template_text.replace(
        "İşletmenize hızlıca ulaşın, hizmetleri inceleyin ve konum bilgisine tek ekrandan erişin.",
        "$visual_label",
        1,
    )

    phone_display = (context.phone_number or "").strip()
    phone_digits = _phone_digits(phone_display)
    phone_href = f"tel:+{phone_digits}" if phone_digits else None

    # Never infer WhatsApp availability from the ordinary phone number. Google
    # Places may expose a phone number without proving that it is on WhatsApp.
    whatsapp_display = (context.whatsapp_number or "").strip()
    whatsapp_digits = _phone_digits(whatsapp_display)
    whatsapp_href = f"https://wa.me/{whatsapp_digits}" if whatsapp_digits else None

    maps_href = _safe_http_url(context.maps_url)
    normalized_address = normalize_address(context.address, business_name=business_name)

    primary_href = whatsapp_href or phone_href or maps_href or "#contact"
    secondary_href = _first_distinct_href(
        primary_href,
        maps_href,
        phone_href,
        whatsapp_href,
    )

    hero_actions = _render_cta_actions(
        primary_text=primary_cta_text,
        primary_href=primary_href,
        secondary_text=secondary_cta_text,
        secondary_href=secondary_href,
        container_class="hero-actions",
    )
    about_actions = _render_cta_actions(
        primary_text=primary_cta_text,
        primary_href=primary_href,
        secondary_text=secondary_cta_text,
        secondary_href=secondary_href,
        container_class="hero-actions",
    )
    contact_actions = _render_contact_actions(
        phone_display=phone_display,
        phone_href=phone_href,
        whatsapp_href=whatsapp_href,
    )
    mobile_contact = _render_mobile_contact(
        phone_href=phone_href,
        whatsapp_href=whatsapp_href,
    )

    if not whatsapp_href:
        template_text = template_text.replace(
            "Telefon, WhatsApp ve konum bağlantıları mobil kullanıcılar için tek dokunuşla erişilebilir.",
            "Telefon ve konum bağlantıları mobil kullanıcılar için tek dokunuşla erişilebilir.",
        )
        template_text = template_text.replace(
            "Telefon ve WhatsApp butonları doğrudan iletişime yönlendirir.",
            "Telefon bağlantısı doğrudan iletişime yönlendirir.",
        )
        template_text = template_text.replace(
            "Telefon veya WhatsApp üzerinden işletmeye ulaşabilir, konum bilgisini açabilirsiniz.",
            "Telefon üzerinden işletmeye ulaşabilir, konum bilgisini açabilirsiniz.",
        )

    seo_title = (context.seo_title or f"{business_name} | {sector}").strip()
    seo_description = (
        context.seo_description
        or f"{business_name} için hazırlanmış web sitesi demo önizlemesi."
    ).strip()

    mapping = {
        "seo_title": escape(seo_title),
        "seo_description": escape(seo_description, quote=True),
        "business_name": escape(business_name),
        "brand_initial": escape(_brand_mark(context.brand_mark_text, business_name)),
        "sector": escape(sector),
        "hero_title": escape(hero_title),
        "hero_text": escape(hero_text),
        "about_text": escape(about_text),
        "visual_label": escape(theme.visual_label),
        "service_cards": _render_service_cards(services),
        "phone_display": escape(phone_display or "Telefon bilgisi eklenecek"),
        "phone_href": escape(phone_href or "#contact", quote=True),
        "whatsapp_href": escape(whatsapp_href or "#contact", quote=True),
        "address": escape(normalized_address or "Adres bilgisi eklenecek"),
        "maps_href": escape(maps_href or "#contact", quote=True),
        "hero_actions": hero_actions,
        "about_actions": about_actions,
        "contact_actions": contact_actions,
        "mobile_contact": mobile_contact,
    }
    return Template(template_text).substitute(mapping)


def normalize_address(value: str | None, *, business_name: str | None = None) -> str | None:
    """Normalize Google-style address text for human-facing demo output.

    The function keeps the factual address content intact while fixing common
    Unicode artifacts, whitespace/punctuation, Turkish address abbreviation
    casing, and obvious lowercase address tokens. A duplicated business-name
    prefix is removed because the site already displays the business name.
    """

    if value is None or not value.strip():
        return None

    text = _normalize_unicode(value.strip())
    normalized_business_name = _normalize_unicode((business_name or "").strip())
    if normalized_business_name and text.casefold().startswith(
        normalized_business_name.casefold()
    ):
        remainder = text[len(normalized_business_name) :]
        if remainder.lstrip().startswith(","):
            text = remainder.lstrip()[1:].strip()

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*/\s*", "/", text)

    abbreviations = {
        r"\bmah\.?\b": "Mah.",
        r"\bsk\.?\b": "Sk.",
        r"\bsok\.?\b": "Sok.",
        r"\bcad\.?\b": "Cad.",
        r"\bcd\.?\b": "Cd.",
        r"\bapt\.?\b": "Apt.",
    }
    for pattern, replacement in abbreviations.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"[^\W\d_]+", _capitalize_address_word, text, flags=re.UNICODE)
    return text.strip(" ,") or None


def _render_cta_actions(
    *,
    primary_text: str,
    primary_href: str,
    secondary_text: str,
    secondary_href: str | None,
    container_class: str,
) -> str:
    links = [
        _render_action_link(
            css_class="button button-primary",
            href=primary_href,
            label=primary_text,
        )
    ]
    if secondary_href:
        links.append(
            _render_action_link(
                css_class="button button-secondary",
                href=secondary_href,
                label=secondary_text,
            )
        )
    return f'<div class="{container_class}">' + "".join(links) + "</div>"


def _render_contact_actions(
    *,
    phone_display: str,
    phone_href: str | None,
    whatsapp_href: str | None,
) -> str:
    links: list[str] = []
    if whatsapp_href:
        links.append(
            _render_action_link(
                css_class="button button-primary",
                href=whatsapp_href,
                label="WhatsApp",
            )
        )
    if phone_href:
        links.append(
            _render_action_link(
                css_class=(
                    "button button-secondary" if whatsapp_href else "button button-primary"
                ),
                href=phone_href,
                label=phone_display,
            )
        )
    if not links:
        return ""
    return '<div class="contact-actions">' + "".join(links) + "</div>"


def _render_mobile_contact(
    *,
    phone_href: str | None,
    whatsapp_href: str | None,
) -> str:
    links: list[str] = []
    if phone_href:
        links.append(_render_plain_link(phone_href, "Ara"))
    if whatsapp_href:
        links.append(_render_plain_link(whatsapp_href, "WhatsApp"))
    if not links:
        return ""
    columns = len(links)
    return (
        '<div class="mobile-contact" aria-label="Mobil hızlı iletişim" '
        f'style="grid-template-columns: repeat({columns}, 1fr)">'
        + "".join(links)
        + "</div>"
    )


def _render_action_link(*, css_class: str, href: str, label: str) -> str:
    rel = ' rel="noopener"' if href.startswith(("http://", "https://")) else ""
    return (
        f'<a class="{escape(css_class, quote=True)}" '
        f'href="{escape(href, quote=True)}"{rel}>{escape(label)}</a>'
    )


def _render_plain_link(href: str, label: str) -> str:
    rel = ' rel="noopener"' if href.startswith(("http://", "https://")) else ""
    return f'<a href="{escape(href, quote=True)}"{rel}>{escape(label)}</a>'


def _first_distinct_href(primary_href: str, *candidates: str | None) -> str | None:
    return next(
        (candidate for candidate in candidates if candidate and candidate != primary_href),
        None,
    )


def _render_service_cards(services: tuple[DemoService, ...]) -> str:
    cards: list[str] = []
    for index, service in enumerate(services, start=1):
        title = _required(service.title, f"services[{index}].title")
        description = _required(
            service.description,
            f"services[{index}].description",
        )
        cards.append(
            "<article class=\"service-card\">"
            f"<span class=\"service-index\">{index:02d}</span>"
            f"<h3>{escape(title)}</h3>"
            f"<p>{escape(description)}</p>"
            "</article>"
        )
    return "\n".join(cards)


def _required(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    return normalized


def _brand_mark(value: str | None, business_name: str) -> str:
    mark = (value or "").strip() or business_name[0].upper()
    if len(mark) > 3:
        raise ValueError("brand_mark_text must contain at most 3 characters.")
    return mark


def _phone_digits(value: str) -> str:
    digits = "".join(character for character in value if character.isdigit())
    if digits.startswith("0") and len(digits) == 11:
        digits = "90" + digits[1:]
    return digits


def _safe_http_url(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return candidate


def _normalize_unicode(value: str) -> str:
    # Google data can occasionally contain a decomposed dotted-i sequence such
    # as ``Gemli\u0307k``. NFC does not collapse that sequence, so normalize it
    # explicitly after canonical composition.
    return (
        unicodedata.normalize("NFC", value)
        .replace("i\u0307", "i")
        .replace("I\u0307", "İ")
    )


def _capitalize_address_word(match: re.Match[str]) -> str:
    word = match.group(0)
    if word.casefold() in {"ve", "ile"}:
        return word.casefold()
    if not word.islower():
        return word
    first = {
        "i": "İ",
        "ı": "I",
        "ç": "Ç",
        "ğ": "Ğ",
        "ö": "Ö",
        "ş": "Ş",
        "ü": "Ü",
    }.get(word[0], word[0].upper())
    return first + word[1:]
