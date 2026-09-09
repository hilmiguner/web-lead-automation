"""Website presence classification for Google Places results.

Google Places not returning ``websiteUri`` does not prove that a business has no
website anywhere on the internet. The lead finder therefore uses an explicit
status model instead of a bare boolean so uncertain values are not accidentally
sold as confirmed facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable
from urllib.parse import urlparse

from web_lead_automation.services.places import Place


class WebsiteStatus(StrEnum):
    """Website state derived from the Google Places ``websiteUri`` field."""

    HAS_WEBSITE = "HAS_WEBSITE"
    NO_WEBSITE_LISTED = "NO_WEBSITE_LISTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class WebsiteAssessment:
    """Website classification for a single place."""

    place: Place
    status: WebsiteStatus
    website_uri: str | None
    reason: str


def assess_website(place: Place) -> WebsiteAssessment:
    """Classify a place's website information conservatively.

    ``NO_WEBSITE_LISTED`` means Google Places did not provide a usable website
    value. It intentionally does not mean that an independent web search has
    proven the business has no website.
    """

    raw_website = place.website_uri
    if raw_website is None or not raw_website.strip():
        return WebsiteAssessment(
            place=place,
            status=WebsiteStatus.NO_WEBSITE_LISTED,
            website_uri=None,
            reason="Google Places does not list a website for this business.",
        )

    website_uri = raw_website.strip()
    parsed = urlparse(website_uri)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return WebsiteAssessment(
            place=place,
            status=WebsiteStatus.HAS_WEBSITE,
            website_uri=website_uri,
            reason="Google Places lists a valid website URL for this business.",
        )

    return WebsiteAssessment(
        place=place,
        status=WebsiteStatus.UNKNOWN,
        website_uri=website_uri,
        reason="Google Places returned website data that could not be safely classified.",
    )


def assess_websites(places: Iterable[Place]) -> tuple[WebsiteAssessment, ...]:
    """Classify website presence for all places while preserving input order."""

    return tuple(assess_website(place) for place in places)


def filter_by_website_status(
    places: Iterable[Place],
    *statuses: WebsiteStatus,
) -> tuple[Place, ...]:
    """Return places whose website assessment matches one of ``statuses``."""

    if not statuses:
        return tuple(places)

    accepted = set(statuses)
    return tuple(
        assessment.place
        for assessment in assess_websites(places)
        if assessment.status in accepted
    )


def places_without_listed_website(places: Iterable[Place]) -> tuple[Place, ...]:
    """Return only businesses for which Google Places lists no website.

    Ambiguous/malformed website values are excluded rather than treated as
    website-less leads.
    """

    return filter_by_website_status(places, WebsiteStatus.NO_WEBSITE_LISTED)
