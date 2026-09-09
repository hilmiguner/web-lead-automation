import pytest

from web_lead_automation.services.places import Place
from web_lead_automation.services.scoring import (
    rank_leads,
    rank_website_leads,
    score_place,
)
from web_lead_automation.services.website_filter import WebsiteStatus


def make_place(**overrides):
    values = {
        "place_id": "place-1",
        "display_name": "Example Business",
        "formatted_address": "Gemlik, Bursa",
        "national_phone_number": None,
        "website_uri": None,
        "rating": None,
        "user_rating_count": None,
        "types": (),
        "business_status": "OPERATIONAL",
        "google_maps_uri": "https://maps.google.com/example",
    }
    values.update(overrides)
    return Place(**values)


def reason_points(result, signal):
    return next(reason.points for reason in result.reasons if reason.signal == signal)


def test_high_quality_website_less_target_business_scores_100():
    place = make_place(
        national_phone_number="+90 224 000 00 00",
        rating=4.8,
        user_rating_count=180,
        types=("beauty_salon", "point_of_interest", "establishment"),
    )

    result = score_place(place)

    assert result.score == 100
    assert result.website_status is WebsiteStatus.NO_WEBSITE_LISTED
    assert [reason.points for reason in result.reasons] == [40, 15, 20, 15, 10]


def test_existing_website_receives_no_website_points():
    place = make_place(
        website_uri="https://example.com",
        national_phone_number="+90 224 000 00 00",
        rating=4.8,
        user_rating_count=180,
        types=("car_repair",),
    )

    result = score_place(place)

    assert result.website_status is WebsiteStatus.HAS_WEBSITE
    assert reason_points(result, "website") == 0
    assert result.score == 60


def test_unknown_website_is_not_treated_as_website_less_lead():
    place = make_place(
        website_uri="example.com",
        national_phone_number="+90 224 000 00 00",
        rating=4.8,
        user_rating_count=180,
        types=("barber_shop",),
    )

    scored = score_place(place)
    ranked = rank_website_leads((place,))

    assert scored.website_status is WebsiteStatus.UNKNOWN
    assert reason_points(scored, "website") == 0
    assert ranked == ()


@pytest.mark.parametrize(
    ("review_count", "expected_points"),
    [
        (None, 0),
        (1, 3),
        (5, 6),
        (20, 12),
        (50, 16),
        (100, 20),
        (500, 20),
    ],
)
def test_review_count_tiers(review_count, expected_points):
    result = score_place(make_place(user_rating_count=review_count))

    assert reason_points(result, "reviews") == expected_points


@pytest.mark.parametrize(
    ("rating", "expected_points"),
    [
        (None, 0),
        (3.0, 2),
        (3.5, 5),
        (4.0, 9),
        (4.2, 12),
        (4.5, 15),
        (5.0, 15),
    ],
)
def test_rating_tiers(rating, expected_points):
    result = score_place(make_place(rating=rating))

    assert reason_points(result, "rating") == expected_points


def test_business_type_points_distinguish_target_specific_and_generic_types():
    target = score_place(make_place(types=("real_estate_agency", "establishment")))
    specific = score_place(make_place(types=("restaurant", "establishment")))
    generic = score_place(make_place(types=("point_of_interest", "establishment")))

    assert reason_points(target, "business_type") == 10
    assert reason_points(specific, "business_type") == 5
    assert reason_points(generic, "business_type") == 0


def test_rank_leads_orders_by_score_then_review_count_then_name():
    stronger = make_place(
        place_id="stronger",
        display_name="Zeta",
        national_phone_number="1",
        rating=4.8,
        user_rating_count=100,
        types=("beauty_salon",),
    )
    tie_more_reviews = make_place(
        place_id="more-reviews",
        display_name="Beta",
        national_phone_number="1",
        rating=4.0,
        user_rating_count=70,
        types=("restaurant",),
    )
    tie_fewer_reviews = make_place(
        place_id="fewer-reviews",
        display_name="Alpha",
        national_phone_number="1",
        rating=4.2,
        user_rating_count=20,
        types=("restaurant",),
    )

    ranked = rank_leads((tie_fewer_reviews, stronger, tie_more_reviews))

    assert [item.place.place_id for item in ranked] == [
        "stronger",
        "more-reviews",
        "fewer-reviews",
    ]


def test_rank_website_leads_filters_existing_and_unknown_websites():
    no_website = make_place(
        place_id="no-site",
        national_phone_number="1",
        rating=4.6,
        user_rating_count=120,
        types=("barber_shop",),
    )
    has_website = make_place(
        place_id="has-site",
        website_uri="https://example.com",
        national_phone_number="1",
        rating=5.0,
        user_rating_count=500,
        types=("barber_shop",),
    )
    unknown = make_place(
        place_id="unknown-site",
        website_uri="example.com",
        national_phone_number="1",
        rating=5.0,
        user_rating_count=500,
        types=("barber_shop",),
    )

    ranked = rank_website_leads((has_website, unknown, no_website))

    assert [item.place.place_id for item in ranked] == ["no-site"]
