"""Explainable lead scoring for local-business website sales.

The first scoring version intentionally stays deterministic. Every point is
traceable to data already returned by Google Places and the conservative
website classification, so users can understand why one lead ranks above
another.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from web_lead_automation.services.places import Place
from web_lead_automation.services.website_filter import (
    WebsiteStatus,
    assess_website,
    places_without_listed_website,
)


# Google Places types that align with the initial sales sectors in ROADMAP.md.
# Generic response types such as ``establishment`` and ``point_of_interest``
# deliberately do not earn business-type points.
HIGH_VALUE_BUSINESS_TYPES = frozenset(
    {
        "barber_shop",
        "beautician",
        "beauty_salon",
        "hair_care",
        "hair_salon",
        "nail_salon",
        "spa",
        "skin_care_clinic",
        "dentist",
        "medical_clinic",
        "car_repair",
        "tire_shop",
        "real_estate_agency",
        "moving_company",
        "event_venue",
        "banquet_hall",
        "general_contractor",
        "roofing_contractor",
        "electrician",
        "plumber",
        "painter",
        "furniture_store",
    }
)

GENERIC_PLACE_TYPES = frozenset(
    {
        "establishment",
        "point_of_interest",
        "premise",
        "place",
    }
)


@dataclass(frozen=True, slots=True)
class ScoreReason:
    """One explainable contribution to a lead score."""

    signal: str
    points: int
    message: str


@dataclass(frozen=True, slots=True)
class LeadScore:
    """Scored Google Place ready for ranking and later dashboard display."""

    place: Place
    score: int
    website_status: WebsiteStatus
    reasons: tuple[ScoreReason, ...]


def score_place(place: Place) -> LeadScore:
    """Calculate a deterministic 0-100 lead score for one business."""

    website = assess_website(place)
    reasons = (
        _website_reason(website.status),
        _phone_reason(place.national_phone_number),
        _reviews_reason(place.user_rating_count),
        _rating_reason(place.rating),
        _business_type_reason(place.types),
    )
    score = sum(reason.points for reason in reasons)

    # The weights above are designed to sum to exactly 100 at maximum. Keep
    # this guard so future edits cannot accidentally break the public contract.
    score = max(0, min(100, score))

    return LeadScore(
        place=place,
        score=score,
        website_status=website.status,
        reasons=reasons,
    )


def score_places(places: Iterable[Place]) -> tuple[LeadScore, ...]:
    """Score places without changing their input order."""

    return tuple(score_place(place) for place in places)


def rank_leads(places: Iterable[Place]) -> tuple[LeadScore, ...]:
    """Score and rank businesses from strongest to weakest sales lead."""

    scored = score_places(places)
    return tuple(
        sorted(
            scored,
            key=lambda item: (
                -item.score,
                -(item.place.user_rating_count or 0),
                item.place.display_name.casefold(),
                item.place.place_id,
            ),
        )
    )


def rank_website_leads(places: Iterable[Place]) -> tuple[LeadScore, ...]:
    """Rank only businesses for which Google Places lists no website.

    ``UNKNOWN`` website values are excluded by ``places_without_listed_website``
    rather than being treated as confirmed website-less opportunities.
    """

    return rank_leads(places_without_listed_website(places))


def _website_reason(status: WebsiteStatus) -> ScoreReason:
    if status is WebsiteStatus.NO_WEBSITE_LISTED:
        return ScoreReason(
            signal="website",
            points=40,
            message="Google Places does not list a website (+40).",
        )
    if status is WebsiteStatus.HAS_WEBSITE:
        return ScoreReason(
            signal="website",
            points=0,
            message="Google Places lists a website (+0).",
        )
    return ScoreReason(
        signal="website",
        points=0,
        message="Website status is uncertain and receives no points (+0).",
    )


def _phone_reason(phone: str | None) -> ScoreReason:
    if phone and phone.strip():
        return ScoreReason(
            signal="phone",
            points=15,
            message="A phone number is available (+15).",
        )
    return ScoreReason(
        signal="phone",
        points=0,
        message="No phone number is available (+0).",
    )


def _reviews_reason(review_count: int | None) -> ScoreReason:
    count = review_count or 0
    if count >= 100:
        points = 20
    elif count >= 50:
        points = 16
    elif count >= 20:
        points = 12
    elif count >= 5:
        points = 6
    elif count > 0:
        points = 3
    else:
        points = 0

    return ScoreReason(
        signal="reviews",
        points=points,
        message=f"Google review count is {count} (+{points}).",
    )


def _rating_reason(rating: float | None) -> ScoreReason:
    value = rating or 0.0
    if value >= 4.5:
        points = 15
    elif value >= 4.2:
        points = 12
    elif value >= 4.0:
        points = 9
    elif value >= 3.5:
        points = 5
    elif value > 0:
        points = 2
    else:
        points = 0

    rating_text = f"{value:.1f}" if rating is not None else "not available"
    return ScoreReason(
        signal="rating",
        points=points,
        message=f"Google rating is {rating_text} (+{points}).",
    )


def _business_type_reason(types: tuple[str, ...]) -> ScoreReason:
    matched = sorted(HIGH_VALUE_BUSINESS_TYPES.intersection(types))
    if matched:
        return ScoreReason(
            signal="business_type",
            points=10,
            message=f"Target sales sector type detected: {matched[0]} (+10).",
        )

    specific_types = sorted(set(types).difference(GENERIC_PLACE_TYPES))
    if specific_types:
        return ScoreReason(
            signal="business_type",
            points=5,
            message=f"Specific business type detected: {specific_types[0]} (+5).",
        )

    return ScoreReason(
        signal="business_type",
        points=0,
        message="No useful business type signal is available (+0).",
    )
