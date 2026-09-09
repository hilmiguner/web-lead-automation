import json

import httpx
import pytest

from web_lead_automation.config import Settings
from web_lead_automation.services.places import (
    DEFAULT_TEXT_SEARCH_FIELD_MASK,
    GooglePlacesClient,
    GooglePlacesConfigurationError,
    GooglePlacesRequestError,
    TEXT_SEARCH_URL,
    create_google_places_client,
)


def test_search_businesses_builds_request_and_parses_response():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "place-1",
                        "displayName": {"text": "Örnek Kuaför"},
                        "formattedAddress": "Gemlik, Bursa",
                        "nationalPhoneNumber": "0224 000 00 00",
                        "rating": 4.8,
                        "userRatingCount": 125,
                        "types": ["hair_salon", "point_of_interest"],
                        "businessStatus": "OPERATIONAL",
                        "googleMapsUri": "https://maps.google.com/example",
                    }
                ],
                "nextPageToken": "next-token",
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = GooglePlacesClient(api_key="secret", http_client=http_client)
        result = client.search_businesses(
            sector="kuaför",
            location="Gemlik Bursa",
            page_size=10,
        )

    assert captured["url"] == TEXT_SEARCH_URL
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["x-goog-api-key"] == "secret"
    assert headers["x-goog-fieldmask"] == DEFAULT_TEXT_SEARCH_FIELD_MASK

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload == {
        "textQuery": "kuaför Gemlik Bursa",
        "pageSize": 10,
        "languageCode": "tr",
        "regionCode": "TR",
        "includePureServiceAreaBusinesses": True,
    }

    assert result.next_page_token == "next-token"
    assert len(result.places) == 1
    place = result.places[0]
    assert place.place_id == "place-1"
    assert place.display_name == "Örnek Kuaför"
    assert place.formatted_address == "Gemlik, Bursa"
    assert place.national_phone_number == "0224 000 00 00"
    assert place.website_uri is None
    assert place.rating == 4.8
    assert place.user_rating_count == 125
    assert place.types == ("hair_salon", "point_of_interest")
    assert place.business_status == "OPERATIONAL"


def test_search_text_uses_default_page_size_and_sends_page_token():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["pageSize"] == 7
        assert payload["pageToken"] == "token-2"
        return httpx.Response(200, json={"places": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = GooglePlacesClient(
            api_key="secret",
            default_page_size=7,
            http_client=http_client,
        )
        result = client.search_text("oto servis Gemlik", page_token="token-2")

    assert result.places == ()
    assert result.next_page_token is None


def test_client_can_be_created_from_environment_settings():
    settings = Settings(
        _env_file=None,
        google_places_api_key="settings-key",
        google_places_timeout_seconds=12,
        google_places_page_size=9,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Goog-Api-Key"] == "settings-key"
        payload = json.loads(request.content)
        assert payload["pageSize"] == 9
        return httpx.Response(200, json={"places": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = create_google_places_client(settings, http_client=http_client)
        result = client.search_text("emlak ofisi Gemlik")

    assert result.places == ()


def test_missing_api_key_is_rejected():
    with pytest.raises(GooglePlacesConfigurationError):
        GooglePlacesClient(api_key="   ")


@pytest.mark.parametrize("page_size", [0, 21])
def test_invalid_page_size_is_rejected(page_size):
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200))
    ) as http_client:
        client = GooglePlacesClient(api_key="secret", http_client=http_client)
        with pytest.raises(ValueError):
            client.search_text("kuaför Gemlik", page_size=page_size)


def test_timeout_is_wrapped():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("boom", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = GooglePlacesClient(api_key="secret", http_client=http_client)
        with pytest.raises(GooglePlacesRequestError, match="timed out"):
            client.search_text("kuaför Gemlik")


def test_api_error_is_wrapped_without_exposing_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"error": {"message": "Places API is not enabled"}},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = GooglePlacesClient(api_key="super-secret", http_client=http_client)
        with pytest.raises(GooglePlacesRequestError) as exc_info:
            client.search_text("kuaför Gemlik")

    message = str(exc_info.value)
    assert "HTTP 403" in message
    assert "Places API is not enabled" in message
    assert "super-secret" not in message
