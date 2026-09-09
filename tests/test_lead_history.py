import pytest

from web_lead_automation.services.lead_finder import LeadSearchResult
from web_lead_automation.services.lead_history import LeadHistoryService
from web_lead_automation.services.places import Place
from web_lead_automation.services.scoring import LeadScore
from web_lead_automation.services.website_filter import WebsiteStatus
from web_lead_automation.storage.crm import LeadRepository, LeadStatus


def _lead(place_id: str, name: str = "Example Business") -> LeadScore:
    return LeadScore(
        place=Place(place_id=place_id, display_name=name),
        score=75,
        website_status=WebsiteStatus.NO_WEBSITE_LISTED,
        reasons=(),
    )


def _service(tmp_path) -> tuple[LeadRepository, LeadHistoryService]:
    repository = LeadRepository(tmp_path / "leads.sqlite3")
    repository.initialize()
    return repository, LeadHistoryService(repository)


def test_first_search_records_lead_and_second_search_marks_seen_before(tmp_path):
    repository, service = _service(tmp_path)
    lead = _lead("place-1")

    first = service.record_leads([lead])[0]
    second = service.record_leads([lead])[0]

    assert first.seen_before is False
    assert first.status is LeadStatus.NEW
    assert first.was_contacted is False
    assert first.is_closed is False

    assert second.seen_before is True
    assert second.first_seen_at == first.first_seen_at
    assert repository.list() == (repository.get_by_place_id("place-1"),)


def test_existing_contacted_lead_keeps_status_and_note(tmp_path):
    repository, service = _service(tmp_path)
    repository.track("place-1")
    repository.update_status("place-1", LeadStatus.CONTACTED)
    repository.update_note("place-1", "Demo hazırlanacak")

    result = service.record_leads([_lead("place-1")])[0]

    assert result.seen_before is True
    assert result.status is LeadStatus.CONTACTED
    assert result.note == "Demo hazırlanacak"
    assert result.was_contacted is True
    assert result.is_closed is False


@pytest.mark.parametrize(
    ("status", "was_contacted", "is_closed"),
    [
        (LeadStatus.NEW, False, False),
        (LeadStatus.INTERESTED, True, False),
        (LeadStatus.WON, True, True),
        (LeadStatus.LOST, True, True),
    ],
)
def test_history_flags_reflect_pipeline_status(
    tmp_path,
    status,
    was_contacted,
    is_closed,
):
    repository, service = _service(tmp_path)
    repository.track("place-1")
    repository.update_status("place-1", status)

    result = service.record_leads([_lead("place-1")])[0]

    assert result.status is status
    assert result.was_contacted is was_contacted
    assert result.is_closed is is_closed


def test_record_search_result_preserves_ranking_and_page_token(tmp_path):
    _, service = _service(tmp_path)
    search_result = LeadSearchResult(
        leads=(
            _lead("place-high", "High Score"),
            _lead("place-low", "Low Score"),
        ),
        next_page_token="next-page",
    )

    result = service.record_search_result(search_result)

    assert [item.lead.place.place_id for item in result.leads] == [
        "place-high",
        "place-low",
    ]
    assert result.next_page_token == "next-page"


def test_lead_without_place_id_cannot_be_recorded(tmp_path):
    _, service = _service(tmp_path)

    with pytest.raises(ValueError, match="place_id"):
        service.record_leads([_lead("   ")])
