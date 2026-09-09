"""Safe renderer for the reusable single-page website demo template."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from importlib.resources import files
from string import Template
from urllib.parse import urlparse


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


def render_demo_html(context: DemoTemplateContext) -> str:
    """Render a self-contained, escaped HTML demo page.

    User/AI-provided text is HTML-escaped before insertion. Only http/https map
    links are accepted. Phone links are generated from digits rather than raw
    user input so the template cannot inject arbitrary URI schemes.
    """

    business_name = _required(context.business_name, "business_name")
    sector = _required(context.sector, "sector")
    hero_title = _required(context.hero_title, "hero_title")
    hero_text = _required(context.hero_text, "hero_text")
    about_text = _required(context.about_text, "about_text")

    services = tuple(context.services)
    if not services:
        raise ValueError("services must contain at least one item.")

    template_text = (
        files("web_lead_automation.demo.templates")
        .joinpath("default.html")
        .read_text(encoding="utf-8")
    )
    # Keep the reusable template readable while rendering a compact monogram
    # inside the fixed-size brand mark for long business names.
    template_text = template_text.replace(
        '<span class="brand-mark">$business_name</span>',
        '<span class="brand-mark">$brand_initial</span>',
        1,
    )

    phone_display = (context.phone_number or "").strip()
    phone_digits = _phone_digits(phone_display)
    phone_href = f"tel:+{phone_digits}" if phone_digits else "#contact"

    whatsapp_display = (context.whatsapp_number or phone_display).strip()
    whatsapp_digits = _phone_digits(whatsapp_display)
    whatsapp_href = (
        f"https://wa.me/{whatsapp_digits}" if whatsapp_digits else "#contact"
    )

    safe_maps_url = _safe_http_url(context.maps_url)
    map_href = safe_maps_url or "#contact"

    seo_title = (context.seo_title or f"{business_name} | {sector}").strip()
    seo_description = (
        context.seo_description
        or f"{business_name} için hazırlanmış web sitesi demo önizlemesi."
    ).strip()

    mapping = {
        "seo_title": escape(seo_title),
        "seo_description": escape(seo_description, quote=True),
        "business_name": escape(business_name),
        "brand_initial": escape(_brand_initial(business_name)),
        "sector": escape(sector),
        "hero_title": escape(hero_title),
        "hero_text": escape(hero_text),
        "about_text": escape(about_text),
        "service_cards": _render_service_cards(services),
        "phone_display": escape(phone_display or "Telefon bilgisi eklenecek"),
        "phone_href": escape(phone_href, quote=True),
        "whatsapp_href": escape(whatsapp_href, quote=True),
        "address": escape((context.address or "Adres bilgisi eklenecek").strip()),
        "maps_href": escape(map_href, quote=True),
    }
    return Template(template_text).substitute(mapping)


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


def _brand_initial(business_name: str) -> str:
    return business_name[0].upper()


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
