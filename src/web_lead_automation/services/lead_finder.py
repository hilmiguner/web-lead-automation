"""End-to-end lead discovery orchestration for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from web_lead_automation.services.places import TextSearchResult
from web_lead_automation.services.scoring import LeadScore, rank_website_leads


class BusinessSearchClient(Protocol):
    """Minimal Places-client contract required by the lead finder."""

    def search_businesses(
        self,
        *,
        sector: str,
        location: str,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> TextSearchResult: ...


@dataclass(frozen=True, slots=True)
class LeadSearchResult:
    """Website-less, scored leads returned by one Places search page."""

    leads: tuple[LeadScore, ...]
    next_page_token: str | None = None


class LeadFinder:
    """Compose business search, website filtering and lead scoring."""

    def __init__(self, places_client: BusinessSearchClient) -> None:
        self._places_client = places_client

    def search(
        self,
        *,
        sector: str,
        location: str,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> LeadSearchResult:
        """Find and rank businesses for which Google Places lists no website."""

        places_result = self._places_client.search_businesses(
            sector=sector,
            location=location,
            page_size=page_size,
            page_token=page_token,
        )
        return LeadSearchResult(
            leads=rank_website_leads(places_result.places),
            next_page_token=places_result.next_page_token,
        )
