import io
import zipfile

import httpx
import pytest

from web_lead_automation.demo.publish import (
    DemoPublishError,
    NetlifyPublisher,
    build_publish_archive,
    public_demo_url,
)


def _demo_tree(tmp_path):
    first = tmp_path / "demo-one"
    second = tmp_path / "demo-two"
    first.mkdir()
    second.mkdir()
    (first / "index.html").write_text("<h1>One</h1>", encoding="utf-8")
    (first / "demo.json").write_text('{"secret":"local"}', encoding="utf-8")
    (second / "index.html").write_text("<h1>Two</h1>", encoding="utf-8")
    return tmp_path


def test_publish_archive_contains_only_public_html_and_hub_files(tmp_path) -> None:
    archive_bytes = build_publish_archive(_demo_tree(tmp_path))

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
        assert names == {
            "index.html",
            "robots.txt",
            "demo-one/index.html",
            "demo-two/index.html",
        }
        assert "demo-one/demo.json" not in names
        assert "Disallow: /" in archive.read("robots.txt").decode("utf-8")
        assert "Demo Önizlemeleri" in archive.read("index.html").decode("utf-8")


def test_publish_archive_can_sync_empty_demo_hub_after_cleanup(tmp_path) -> None:
    archive_bytes = build_publish_archive(tmp_path)

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        assert set(archive.namelist()) == {"index.html", "robots.txt"}


def test_publish_archive_requires_output_directory(tmp_path) -> None:
    with pytest.raises(DemoPublishError, match="No demo output directory"):
        build_publish_archive(tmp_path / "missing")


def test_netlify_publish_returns_ready_https_site(tmp_path) -> None:
    root = _demo_tree(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/sites/site-123/deploys"
        assert request.headers["authorization"] == "Bearer token-123"
        assert request.headers["content-type"] == "application/zip"
        return httpx.Response(
            200,
            json={
                "id": "deploy-1",
                "state": "ready",
                "ssl_url": "https://demo-hub.netlify.app",
            },
        )

    with NetlifyPublisher(
        auth_token="token-123",
        site_id="site-123",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    ) as publisher:
        published = publisher.publish(root)

    assert published.deploy_id == "deploy-1"
    assert published.state == "ready"
    assert published.base_url == "https://demo-hub.netlify.app"


def test_netlify_publish_polls_until_ready(tmp_path) -> None:
    root = _demo_tree(tmp_path)
    states = iter(["processing", "ready"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "id": "deploy-1",
                    "state": "processing",
                    "ssl_url": "https://demo-hub.netlify.app",
                },
            )
        return httpx.Response(
            200,
            json={
                "id": "deploy-1",
                "state": next(states),
                "ssl_url": "https://demo-hub.netlify.app",
            },
        )

    with NetlifyPublisher(
        auth_token="token-123",
        site_id="site-123",
        transport=httpx.MockTransport(handler),
        poll_interval_seconds=0,
        max_poll_attempts=4,
    ) as publisher:
        published = publisher.publish(root)

    assert published.state == "ready"


def test_netlify_publish_hides_provider_http_details(tmp_path) -> None:
    root = _demo_tree(tmp_path)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "bad token"})

    with NetlifyPublisher(
        auth_token="top-secret-token",
        site_id="site-123",
        transport=httpx.MockTransport(handler),
    ) as publisher:
        with pytest.raises(DemoPublishError, match="deployment request failed") as exc_info:
            publisher.publish(root)

    assert "top-secret-token" not in str(exc_info.value)


def test_public_demo_url_uses_stable_slug() -> None:
    assert public_demo_url(
        "https://demo-hub.netlify.app/",
        "ornek-kuafor-abc123",
    ) == "https://demo-hub.netlify.app/ornek-kuafor-abc123/"


def test_public_demo_url_requires_https_and_safe_slug() -> None:
    with pytest.raises(ValueError):
        public_demo_url("http://example.test", "safe-slug")
    with pytest.raises(ValueError):
        public_demo_url("https://example.test", "../unsafe")
