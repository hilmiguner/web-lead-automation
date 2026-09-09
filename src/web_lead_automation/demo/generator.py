"""Filesystem pipeline for generating repeatable per-lead website demos."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from web_lead_automation.demo.template import (
    DemoService,
    DemoTemplateContext,
    render_demo_html,
)
from web_lead_automation.demo.theme import ThemeKey, resolve_theme
from web_lead_automation.services.ai_content import DemoAIContent


MANIFEST_VERSION = 1
TURKISH_ASCII_TRANSLATION = str.maketrans(
    {
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ş": "s",
        "Ş": "S",
        "ü": "u",
        "Ü": "U",
    }
)


class DemoGenerationError(RuntimeError):
    """Raised when an existing or newly generated demo cannot be used safely."""


@dataclass(frozen=True, slots=True)
class DemoGenerationRequest:
    """Reviewed inputs required to materialize one lead demo."""

    external_place_id: str
    business_name: str
    sector: str
    content: DemoAIContent
    phone_number: str | None = None
    whatsapp_number: str | None = None
    address: str | None = None
    maps_url: str | None = None
    place_types: tuple[str, ...] = ()
    theme: ThemeKey | str | None = None
    brand_mark_text: str | None = None


@dataclass(frozen=True, slots=True)
class GeneratedDemo:
    """Paths and metadata for a generated static demo."""

    slug: str
    directory: Path
    index_path: Path
    manifest_path: Path
    theme_key: ThemeKey
    regenerated: bool


@dataclass(frozen=True, slots=True)
class SavedDemoDraft:
    """Editable source data recovered from a previous generated demo."""

    slug: str
    sector: str
    content: DemoAIContent
    theme_key: ThemeKey
    brand_mark_text: str | None


class DemoGenerator:
    """Render and persist self-contained demos under a deterministic lead folder."""

    def __init__(self, output_root: str | Path) -> None:
        self._output_root = Path(output_root)

    def generate(self, request: DemoGenerationRequest) -> GeneratedDemo:
        """Render and atomically replace the generated files for one lead."""

        place_id = _required(request.external_place_id, "external_place_id")
        business_name = _required(request.business_name, "business_name")
        sector = _required(request.sector, "sector")
        slug = demo_slug(business_name, place_id)
        directory = self._output_root / slug
        index_path = directory / "index.html"
        manifest_path = directory / "demo.json"
        regenerated = index_path.exists() or manifest_path.exists()

        theme = resolve_theme(
            request.theme,
            sector=sector,
            place_types=tuple(request.place_types),
        )
        html = render_demo_html(
            DemoTemplateContext(
                business_name=business_name,
                sector=sector,
                hero_title=request.content.hero_title,
                hero_text=request.content.hero_text,
                about_text=request.content.about_text,
                services=tuple(
                    DemoService(service.title, service.description)
                    for service in request.content.services
                ),
                phone_number=request.phone_number,
                whatsapp_number=request.whatsapp_number,
                address=request.address,
                maps_url=request.maps_url,
                seo_title=request.content.seo_title,
                seo_description=request.content.seo_description,
                primary_cta_text=request.content.primary_cta_text,
                secondary_cta_text=request.content.secondary_cta_text,
                theme=theme.key,
                place_types=tuple(request.place_types),
                brand_mark_text=request.brand_mark_text,
            )
        )
        manifest = _manifest_json(
            request,
            place_id=place_id,
            business_name=business_name,
            sector=sector,
            slug=slug,
            theme_key=theme.key,
        )

        try:
            directory.mkdir(parents=True, exist_ok=True)
            _atomic_write_text(index_path, html)
            _atomic_write_text(manifest_path, manifest)
        except OSError as exc:
            raise DemoGenerationError(
                f"Demo files could not be written under {directory}."
            ) from exc

        return GeneratedDemo(
            slug=slug,
            directory=directory,
            index_path=index_path,
            manifest_path=manifest_path,
            theme_key=theme.key,
            regenerated=regenerated,
        )

    def find_index_path(
        self,
        *,
        external_place_id: str,
        business_name: str,
    ) -> Path | None:
        """Return an existing local demo index path for one lead."""

        place_id = _required(external_place_id, "external_place_id")
        name = _required(business_name, "business_name")
        index_path = self._output_root / demo_slug(name, place_id) / "index.html"
        return index_path if index_path.is_file() else None

    def remove_demo(
        self,
        *,
        external_place_id: str,
        business_name: str,
    ) -> bool:
        """Delete one deterministic local demo directory, if it exists."""

        place_id = _required(external_place_id, "external_place_id")
        name = _required(business_name, "business_name")
        directory = self._output_root / demo_slug(name, place_id)
        if not directory.exists():
            return False
        try:
            shutil.rmtree(directory)
        except OSError as exc:
            raise DemoGenerationError(f"Demo directory could not be removed: {directory}.") from exc
        return True

    def load_saved_draft(
        self,
        *,
        external_place_id: str,
        business_name: str,
    ) -> SavedDemoDraft | None:
        """Recover the last generated editable source for a lead, if available."""

        place_id = _required(external_place_id, "external_place_id")
        name = _required(business_name, "business_name")
        slug = demo_slug(name, place_id)
        manifest_path = self._output_root / slug / "demo.json"
        if not manifest_path.exists():
            return None

        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            if payload.get("version") != MANIFEST_VERSION:
                raise DemoGenerationError("Saved demo manifest version is not supported.")
            if payload.get("external_place_id") != place_id:
                raise DemoGenerationError("Saved demo manifest belongs to another lead.")
            content = DemoAIContent.model_validate(payload["content"])
            theme_key = ThemeKey(payload["theme"])
            sector = _required(str(payload["sector"]), "sector")
            brand_mark = payload.get("brand_mark_text")
            if brand_mark is not None and not isinstance(brand_mark, str):
                raise DemoGenerationError("Saved demo brand mark is invalid.")
        except DemoGenerationError:
            raise
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise DemoGenerationError("Saved demo manifest is invalid or unreadable.") from exc

        return SavedDemoDraft(
            slug=slug,
            sector=sector,
            content=content,
            theme_key=theme_key,
            brand_mark_text=brand_mark,
        )


def demo_slug(business_name: str, external_place_id: str) -> str:
    """Build a filesystem-safe deterministic slug without exposing the full Place ID."""

    name = _required(business_name, "business_name")
    place_id = _required(external_place_id, "external_place_id")
    ascii_name = (
        unicodedata.normalize("NFKD", name.translate(TURKISH_ASCII_TRANSLATION))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    base = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-") or "demo"
    base = base[:60].rstrip("-") or "demo"
    suffix = hashlib.sha256(place_id.encode("utf-8")).hexdigest()[:10]
    return f"{base}-{suffix}"


def _manifest_json(
    request: DemoGenerationRequest,
    *,
    place_id: str,
    business_name: str,
    sector: str,
    slug: str,
    theme_key: ThemeKey,
) -> str:
    payload: dict[str, Any] = {
        "version": MANIFEST_VERSION,
        "slug": slug,
        "external_place_id": place_id,
        "business_name": business_name,
        "sector": sector,
        "theme": theme_key.value,
        "brand_mark_text": request.brand_mark_text,
        "content": request.content.model_dump(mode="json"),
        "contact": {
            "phone_number": request.phone_number,
            "whatsapp_number": request.whatsapp_number,
            "address": request.address,
            "maps_url": request.maps_url,
        },
        "place_types": list(request.place_types),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _atomic_write_text(path: Path, content: str) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        temp_path.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _required(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    return normalized
