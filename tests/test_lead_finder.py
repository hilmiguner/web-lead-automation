from web_lead_automation.services.lead_finder import LeadFinder
from web_lead_automation.services.places import Place, TextSearchResult


class StubPlacesClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def search_businesses(
        self,
        *,
        sector,
        location,
        page_size=20,
        page_token=None,
    ):
        self.calls.append(
            {
                "sector": sector,
                "location": location,
                "page_size": page_size,
                "page_token": page_token,
            }
        )
        return self.result


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


def test_lead_finder_composes_search_filter_scoring_and_pagination():
    strong_no_site = make_place(
        place_id="strong",
        display_name="Strong Barber",
        national_phone_number="+90 224 000 00 00",
        rating=4.8,
        user_rating_count=150,
        types=("barber_shop",),
    )
    weak_no_site = make_place(
        place_id="weak",
        display_name="Weak Shop",
        user_rating_count=3,
        types=("store",),
    )
    has_site = make_place(
        place_id="has-site",
        display_name="Existing Website",
        website_uri="https://example.com",
        national_phone_number="+90 224 000 00 01",
        rating=5.0,
        user_rating_count=500,
        types=("barber_shop",),
    )
    unknown_site = make_place(
        place_id="unknown-site",
        display_name="Unknown Website",
        website_uri="example.com",
        national_phone_number="+90 224 000 00 02",
        rating=5.0,
        user_rating_count=500,
        types=("barber_shop",),
    )

    client = StubPlacesClient(
        TextSearchResult(
            places=(weak_no_site, has_site, strong_no_site, unknown_site),
            next_page_token="next-token",
        )
    )
    finder = LeadFinder(client)

    result = finder.search(
        sector="berber",
        location="Gemlik Bursa",
        page_size=10,
        page_token="page-token",
    )

    assert [lead.place.place_id for lead in result.leads] == ["strong", "weak"]
    assert result.leads[0].score == 100
    assert result.next_page_token == "next-token"
    assert client.calls == [
        {
            "sector": "berber",
            "location": "Gemlik Bursa",
            "page_size": 10,
            "page_token": "page-token",
        }
    ]
