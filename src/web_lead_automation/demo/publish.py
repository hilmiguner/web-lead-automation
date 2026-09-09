"""Publish generated demo HTML files to a single Netlify site."""

from __future__ import annotations

import io
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import httpx


NETLIFY_API_BASE = "https://api.netlify.com/api/v1"


class DemoPublishError(RuntimeError):
    """Raised when demo publication cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class PublishedDemoSite:
    """One completed production deployment."""

    deploy_id: str
    base_url: str
    state: str


class NetlifyPublisher:
    """Deploy all locally generated demo HTML pages as one static Netlify site.

    Only each demo's ``index.html`` is published. Local ``demo.json`` manifests
    remain private on disk and are deliberately excluded from the upload.
    """

    def __init__(
        self,
        *,
        auth_token: str,
        site_id: str,
        timeout_seconds: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        poll_interval_seconds: float = 0.5,
        max_poll_attempts: int = 30,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        token = auth_token.strip()
        site = site_id.strip()
        if not token:
            raise ValueError("Netlify auth token must not be empty.")
        if not site:
            raise ValueError("Netlify site ID must not be empty.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")
        if max_poll_attempts < 1:
            raise ValueError("max_poll_attempts must be at least 1.")

        self._site_id = site
        self._poll_interval_seconds = max(0.0, poll_interval_seconds)
        self._max_poll_attempts = max_poll_attempts
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=NETLIFY_API_BASE,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout_seconds,
            transport=transport,
        )

    def __enter__(self) -> "NetlifyPublisher":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def publish(self, output_root: str | Path) -> PublishedDemoSite:
        """Publish every current local demo as one production deployment."""

        archive = build_publish_archive(output_root)
        try:
            response = self._client.post(
                f"/sites/{self._site_id}/deploys",
                headers={"Content-Type": "application/zip"},
                content=archive,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DemoPublishError("Netlify deployment request failed.") from exc

        deploy_id = str(payload.get("id") or "").strip()
        if not deploy_id:
            raise DemoPublishError("Netlify response did not include a deploy ID.")

        final_payload = self._wait_until_ready(deploy_id, payload)
        base_url = _deployment_base_url(final_payload)
        return PublishedDemoSite(
            deploy_id=deploy_id,
            base_url=base_url,
            state=str(final_payload.get("state") or "ready"),
        )

    def _wait_until_ready(self, deploy_id: str, payload: dict[str, object]) -> dict[str, object]:
        current = payload
        for attempt in range(self._max_poll_attempts):
            state = str(current.get("state") or "").casefold()
            if state == "ready":
                return current
            if state == "error":
                message = str(current.get("error_message") or "Netlify deployment failed.")
                raise DemoPublishError(message)
            if attempt == self._max_poll_attempts - 1:
                break
            if self._poll_interval_seconds:
                self._sleep(self._poll_interval_seconds)
            try:
                response = self._client.get(f"/deploys/{deploy_id}")
                response.raise_for_status()
                current = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise DemoPublishError("Could not read Netlify deployment status.") from exc

        raise DemoPublishError("Netlify deployment did not become ready in time.")


def build_publish_archive(output_root: str | Path) -> bytes:
    """Build a ZIP containing public HTML only; manifests stay local."""

    root = Path(output_root)
    if not root.exists() or not root.is_dir():
        raise DemoPublishError("No generated demo directory was found to publish.")

    pages: list[tuple[str, Path]] = []
    for directory in sorted(root.iterdir(), key=lambda item: item.name):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        index_path = directory / "index.html"
        if index_path.is_file():
            pages.append((directory.name, index_path))

    if not pages:
        raise DemoPublishError("No generated demo HTML file was found to publish.")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("robots.txt", "User-agent: *\nDisallow: /\n")
        for slug, index_path in pages:
            archive.writestr(f"{slug}/index.html", index_path.read_bytes())
    return buffer.getvalue()


def public_demo_url(base_url: str, slug: str) -> str:
    """Return the stable public URL for one lead folder on the shared site."""

    base = base_url.strip().rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("base_url must be an absolute HTTPS URL.")
    normalized_slug = slug.strip().strip("/")
    if not normalized_slug or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in normalized_slug):
        raise ValueError("slug is not safe for a public demo URL.")
    return f"{base}/{normalized_slug}/"


def _deployment_base_url(payload: dict[str, object]) -> str:
    candidate = str(payload.get("ssl_url") or payload.get("url") or "").strip().rstrip("/")
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or not parsed.netloc:
        raise DemoPublishError("Netlify response did not include a valid HTTPS site URL.")
    return candidate
