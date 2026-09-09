import json

import httpx
import pytest

from web_lead_automation.services.ai_content import (
    AIContentConfigurationError,
    AIContentRequestError,
    AIContentResponseError,
    BusinessContentBrief,
    OpenAIContentClient,
)


VALID_CONTENT = {
    "tone": "modern ve güven veren",
    "hero_title": "İşletmenizle kolayca iletişime geçin",
    "hero_text": "İletişim ve konum bilgilerine hızlıca ulaşabileceğiniz sade ve kullanışlı bir dijital vitrin.",
    "about_text": "Bu demo alanı, işletmenin doğrulanmış temel bilgilerini ziyaretçilere açık ve erişilebilir biçimde sunmak için hazırlanmıştır.",
    "services": [
        {
            "title": "Hizmetleri Öğrenin",
            "description": "Sunulan hizmetlerin güncel detaylarını öğrenmek için işletmeyle doğrudan iletişime geçin.",
        },
        {
            "title": "Detaylı Bilgi Alın",
            "description": "İhtiyacınıza uygun seçenekler ve güncel bilgiler için işletmeden doğrudan bilgi alın.",
        },
        {
            "title": "İletişim ve Konum",
            "description": "Telefon ve konum bilgilerini kullanarak işletmeye hızlı ve kolay biçimde ulaşın.",
        },
    ],
    "primary_cta_text": "WhatsApp'tan Yazın",
    "secondary_cta_text": "Telefonla Ulaşın",
    "seo_title": "Örnek İşletme | Kuaför",
    "seo_description": "Örnek İşletme için iletişim ve konum bilgilerini öne çıkaran web sitesi demo önizlemesi.",
    "content_notes": ["Hizmet listesi doğrulanmadığı için özel hizmet iddiası kullanılmadı."],
}


def _responses_payload(content=VALID_CONTENT):
    return {
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(content, ensure_ascii=False),
                    }
                ],
            }
        ]
    }


def test_missing_api_key_is_rejected() -> None:
    with pytest.raises(AIContentConfigurationError):
        OpenAIContentClient(api_key=None)


def test_generate_uses_responses_api_and_strict_schema() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json=_responses_payload())

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenAIContentClient(
        api_key="secret-test-key",
        model="gpt-5.6-luna",
        http_client=http_client,
    )

    content = client.generate(
        BusinessContentBrief(
            business_name=" Örnek İşletme ",
            sector=" kuaför ",
            address=" Gemlik, Bursa ",
        )
    )

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["authorization"] == "Bearer secret-test-key"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "gpt-5.6-luna"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    input_payload = json.loads(payload["input"])
    assert input_payload["business_name"] == "Örnek İşletme"
    assert input_payload["sector"] == "kuaför"
    assert input_payload["known_services"] == []
    assert content.hero_title == VALID_CONTENT["hero_title"]
    assert len(content.services) == 3


def test_known_services_are_normalized_and_sent_as_verified_data() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json=_responses_payload())

    client = OpenAIContentClient(
        api_key="key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    client.generate(
        BusinessContentBrief(
            business_name="Test",
            sector="oto servis",
            known_services=(" Yağ değişimi ", "", "Fren kontrolü"),
        )
    )

    payload = captured["payload"]
    assert isinstance(payload, dict)
    input_payload = json.loads(payload["input"])
    assert input_payload["known_services"] == ["Yağ değişimi", "Fren kontrolü"]


def test_invalid_structured_content_is_rejected() -> None:
    invalid = dict(VALID_CONTENT)
    invalid["services"] = []

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_responses_payload(invalid))

    client = OpenAIContentClient(
        api_key="key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AIContentResponseError, match="required schema"):
        client.generate(BusinessContentBrief("Test", "kuaför"))


def test_refusal_is_reported_without_raw_provider_payload() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "refusal", "refusal": "No"}],
                    }
                ]
            },
        )

    client = OpenAIContentClient(
        api_key="key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AIContentResponseError, match="declined"):
        client.generate(BusinessContentBrief("Test", "kuaför"))


def test_http_error_does_not_echo_api_key() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    client = OpenAIContentClient(
        api_key="super-secret-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AIContentRequestError) as exc_info:
        client.generate(BusinessContentBrief("Test", "kuaför"))

    assert "429" in str(exc_info.value)
    assert "super-secret-key" not in str(exc_info.value)


def test_timeout_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    client = OpenAIContentClient(
        api_key="key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AIContentRequestError, match="timed out"):
        client.generate(BusinessContentBrief("Test", "kuaför"))
