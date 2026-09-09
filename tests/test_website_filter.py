from web_lead_automation.services.places import Place
from web_lead_automation.services.website_filter import (
    WebsiteStatus,
    assess_website,
    assess_websites,
    filter_by_website_status,
    places_without_listed_website,
)


def make_place(*, place_id: str, website_uri: str | None) -> Place:
    return Place(
        place_id=place_id,
        display_name=f"Business {place_id}",
        website_uri=website_uri,
    )


def test_assess_website_detects_valid_https_url():
    place = make_place(place_id="1", website_uri="https://example.com")

    assessment = assess_website(place)

    assert assessment.status is WebsiteStatus.HAS_WEBSITE
    assert assessment.website_uri == "https://example.com"


def test_assess_website_detects_valid_http_url_and_trims_whitespace():
    place = make_place(place_id="2", website_uri="  http://example.com/path  ")

    assessment = assess_website(place)

    assert assessment.status is WebsiteStatus.HAS_WEBSITE
    assert assessment.website_uri == "http://example.com/path"


def test_assess_website_marks_missing_value_as_not_listed():
    place = make_place(place_id="3", website_uri=None)

    assessment = assess_website(place)

    assert assessment.status is WebsiteStatus.NO_WEBSITE_LISTED
    assert assessment.website_uri is None


def test_assess_website_marks_blank_value_as_not_listed():
    place = make_place(place_id="4", website_uri="   ")

    assessment = assess_website(place)

    assert assessment.status is WebsiteStatus.NO_WEBSITE_LISTED
    assert assessment.website_uri is None


def test_assess_website_marks_malformed_value_as_unknown():
    place = make_place(place_id="5", website_uri="example.com")

    assessment = assess_website(place)

    assert assessment.status is WebsiteStatus.UNKNOWN
    assert assessment.website_uri == "example.com"


def test_places_without_listed_website_excludes_existing_and_unknown_websites():
    missing = make_place(place_id="missing", website_uri=None)
    existing = make_place(place_id="existing", website_uri="https://example.com")
    unknown = make_place(place_id="unknown", website_uri="example.com")

    result = places_without_listed_website((existing, missing, unknown))

    assert result == (missing,)


def test_filter_by_website_status_supports_multiple_statuses():
    existing = make_place(place_id="existing", website_uri="https://example.com")
    missing = make_place(place_id="missing", website_uri=None)
    unknown = make_place(place_id="unknown", website_uri="ftp://example.com")

    result = filter_by_website_status(
        (existing, missing, unknown),
        WebsiteStatus.HAS_WEBSITE,
        WebsiteStatus.UNKNOWN,
    )

    assert result == (existing, unknown)


def test_assess_websites_preserves_input_order():
    first = make_place(place_id="first", website_uri=None)
    second = make_place(place_id="second", website_uri="https://example.com")

    assessments = assess_websites((first, second))

    assert tuple(item.place for item in assessments) == (first, second)
