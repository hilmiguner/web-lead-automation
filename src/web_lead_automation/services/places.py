"""Google Places API (New) integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Minimum fields needed by the lead finder, website filter, scoring and dashboard.
# Contact/rating/website fields place Text Search requests in Google's Enterprise
# SKU, so avoid adding fields casually.
DEFAULT_TEXT_SEARCH_FIELD_MASK = ",".join(
    (
        "places.id",
        "places.displayName.text",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.types",
        "places.businessStatus",
        "places.googleMapsUri",
        "nextPageToken",
    )
)


class GooglePlacesError(RuntimeError):
    """Base error for Google Places integration failures."""


class GooglePlacesConfigurationError(GooglePlacesError):
    """Raised when the Google Places client is misconfigured."""


class GooglePlacesRequestError(GooglePlacesError):
    """Raised when Google Places cannot satisfy a request."""


@dataclass(frozen=True, slots=True)
class Place:
    """Normalized subset of a Google Place used by the application."""

    place_id: str
    display_name: str
    formatted_address: str | None = None
    national_phone_number: str | None = None
    website_uri: str | None = None
    rating: float | None = None
    user_rating_count: int | None = None
    types: tuple[str, ...] = ()
    business_status: str | None = None
    google_maps_uri: str | None = None


@dataclass(frozen=True, slots=True)
class TextSearchResult:
    """Normalized Text Search response."""

    places: tuple[Place, ...]
    next_page_token: str | None = None


class GooglePlacesClient:
    """Small HTTP client for Places API (New) Text Search."""

    def __init__(
        self,
        *,
        api_key: str | None,
        timeout_seconds: float = 10.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        api_key = (api_key or "").strip()
        if not api_key:
            raise GooglePlacesConfigurationError(
                "GOOGLE_PLACES_API_KEY is required to search Google Places."
            )
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")

        self._api_key = api_key
        self._owns_http_client = http_client is None
        self._http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        """Close the internally owned HTTP client."""

        if self._owns_http_client:
            self._http_client.close()

    def __enter__(self) -> "GooglePlacesClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def search_businesses(
        self,
        *,
        sector: str,
        location: str,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> TextSearchResult:
        """Search businesses using a simple sector + location query."""

        sector = sector.strip()
        location = location.strip()
        if not sector:
            raise ValueError("sector must not be empty.")
        if not location:
            raise ValueError("location must not be empty.")

        return self.search_text(
            f"{sector} {location}",
            page_size=page_size,
            page_token=page_token,
        )

    def search_text(
        self,
        text_query: str,
        *,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> TextSearchResult:
        """Run a Places API (New) Text Search request."""

        text_query = text_query.strip()
        if not text_query:
            raise ValueError("text_query must not be empty.")
        if not 1 <= page_size <= 20:
            raise ValueError("page_size must be between 1 and 20.")

        payload: dict[str, Any] = {
            "textQuery": text_query,
            "pageSize": page_size,
            "languageCode": "tr",
            "regionCode": "TR",
            "includePureServiceAreaBusinesses": True,
        }
        if page_token:
            payload["pageToken"] = page_token

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": DEFAULT_TEXT_SEARCH_FIELD_MASK,
        }

        try:
            response = self._http_client.post(
                TEXT_SEARCH_URL,
                headers=headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise GooglePlacesRequestError(
                "Google Places request timed out."
            ) from exc
        except httpx.HTTPError as exc:
            raise GooglePlacesRequestError(
                "Google Places request failed before a response was received."
            ) from exc

        if response.is_error:
            raise GooglePlacesRequestError(self._format_error(response))

        try:
            data = response.json()
        except ValueError as exc:
            raise GooglePlacesRequestError(
                "Google Places returned an invalid JSON response."
            ) from exc

        raw_places = data.get("places", [])
        if not isinstance(raw_places, list):
            raise GooglePlacesRequestError(
                "Google Places returned an unexpected response shape."
            )

        return TextSearchResult(
            places=tuple(self._parse_place(raw) for raw in raw_places),
            next_page_token=self._optional_str(data.get("nextPageToken")),
        )

    @staticmethod
    def _parse_place(raw: dict[str, Any]) -> Place:
        display_name = raw.get("displayName") or {}
        if not isinstance(display_name, dict):
            display_name = {}

        raw_types = raw.get("types")
        types = (
            tuple(item for item in raw_types if isinstance(item, str))
            if isinstance(raw_types, list)
            else ()
        )

        return Place(
            place_id=str(raw.get("id") or ""),
            display_name=str(display_name.get("text") or ""),
            formatted_address=GooglePlacesClient._optional_str(
                raw.get("formattedAddress")
            ),
            national_phone_number=GooglePlacesClient._optional_str(
                raw.get("nationalPhoneNumber")
            ),
            website_uri=GooglePlacesClient._optional_str(raw.get("websiteUri")),
            rating=GooglePlacesClient._optional_float(raw.get("rating")),
            user_rating_count=GooglePlacesClient._optional_int(
                raw.get("userRatingCount")
            ),
            types=types,
            business_status=GooglePlacesClient._optional_str(
                raw.get("businessStatus")
            ),
            google_maps_uri=GooglePlacesClient._optional_str(
                raw.get("googleMapsUri")
            ),
        )

    @staticmethod
    def _format_error(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        error = payload.get("error") if isinstance(payload, dict) else None
        message = error.get("message") if isinstance(error, dict) else None
        suffix = f": {message}" if isinstance(message, str) and message else ""
        return f"Google Places returned HTTP {response.status_code}{suffix}"

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value
