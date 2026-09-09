"""Safe, deterministic sales outreach copy for selected website leads."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class OutreachMessage:
    """One copy-ready WhatsApp message variant."""

    key: str
    label: str
    text: str


@dataclass(frozen=True, slots=True)
class OutreachBundle:
    """Copy-ready outreach assets for one lead."""

    whatsapp_messages: tuple[OutreachMessage, ...]
    phone_opener: str
    demo_url: str | None


def generate_outreach_bundle(
    *,
    business_name: str,
    sector: str | None = None,
    demo_url: str | None = None,
    include_demo_link: bool = True,
) -> OutreachBundle:
    """Build short Turkish outreach copy without making unverified claims.

    The copy deliberately says that Google Business does not list a website link
    rather than claiming the business has no website anywhere. The generated
    demo is also described as an unofficial example preview.
    """

    name = _single_line_required(business_name, "business_name")
    normalized_sector = _single_line_optional(sector)
    normalized_demo_url = _https_url_or_none(demo_url)
    shared_url = normalized_demo_url if include_demo_link else None

    sector_phrase = f" {normalized_sector} işletmeniz" if normalized_sector else " işletmeniz"
    link_block = f"\n\nDemo: {shared_url}" if shared_url else ""

    standard = OutreachMessage(
        key="standard",
        label="Dengeli",
        text=(
            f"Merhaba, {name} için iletişime geçiyorum. Google'daki işletme profilinizde "
            "bir web sitesi bağlantısına rastlamadım. İşletmenizin internette nasıl "
            "görünebileceğini göstermek amacıyla kısa bir demo hazırladım. Bu çalışma "
            f"yalnızca örnek bir önizlemedir; işletmeniz adına yayınlanmış resmi bir site değildir.{link_block}\n\n"
            "Uygun olursanız kısaca görüşüp detayları paylaşabilirim."
        ),
    )
    short = OutreachMessage(
        key="short",
        label="Kısa",
        text=(
            f"Merhaba, {name} için örnek bir web sitesi demosu hazırladım. Google'daki "
            "işletme profilinizde web sitesi bağlantısı göremediğim için nasıl "
            f"görünebileceğini göstermek istedim. Demo resmi siteniz değildir.{link_block}\n\n"
            "İncelemek isterseniz detayları paylaşabilirim."
        ),
    )
    direct = OutreachMessage(
        key="direct",
        label="Doğrudan",
        text=(
            f"Merhaba, {name}{sector_phrase} için mobil uyumlu tek sayfalık bir demo "
            "hazırladım. Bu, yalnızca satış öncesi örnek önizlemedir ve işletmeniz adına "
            f"yayınlanmış resmi bir web sitesi değildir.{link_block}\n\n"
            "Uygun görürseniz siteyi size özel hale getirip yayına alabiliriz."
        ),
    )

    phone_opener = (
        f"Merhaba, {name} yetkilisiyle mi görüşüyorum? Google'daki işletme profilinizde "
        "web sitesi bağlantısı göremediğim için, işletmenizin internette nasıl "
        "görünebileceğini göstermek amacıyla kısa bir demo hazırladım. Bu yalnızca örnek "
        "bir önizleme. Uygunsanız 30 saniyede ne hazırladığımı anlatıp linki paylaşabilirim."
    )

    return OutreachBundle(
        whatsapp_messages=(standard, short, direct),
        phone_opener=phone_opener,
        demo_url=normalized_demo_url,
    )


def _https_url_or_none(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().rstrip("/") + "/"
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("demo_url must be an absolute HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("demo_url must not contain credentials.")
    return normalized


def _single_line_required(value: str, field_name: str) -> str:
    normalized = _single_line_optional(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    return normalized


def _single_line_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None
