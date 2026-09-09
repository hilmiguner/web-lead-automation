"""Enrich scored search results with persistent CRM history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from web_lead_automation.services.lead_finder import LeadSearchResult
from web_lead_automation.services.scoring import LeadScore
from web_lead_automation.storage.crm import LeadRepository, LeadStatus


CONTACTED_STATUSES = frozenset(
    {
        LeadStatus.CONTACTED,
        LeadStatus.INTERESTED,
        LeadStatus.WON,
        LeadStatus.LOST,
    }
)
CLOSED_STATUSES = frozenset({LeadStatus.WON, LeadStatus.LOST})


@dataclass(frozen=True, slots=True)
class LeadWithHistory:
    """A scored lead annotated with the local sales history."""

    lead: LeadScore
    seen_before: bool
    status: LeadStatus
    note: str
    first_seen_at: datetime
    updated_at: datetime
    was_contacted: bool
    is_closed: bool


@dataclass(frozen=True, slots=True)
class LeadSearchWithHistoryResult:
    """Lead-search result after CRM history has been attached."""

    leads: tuple[LeadWithHistory, ...]
    next_page_token: str | None = None


class LeadHistoryService:
    """Record discovered leads and expose their existing CRM state."""

    def __init__(self, repository: LeadRepository) -> None:
        self._repository = repository

    def record_leads(
        self,
        leads: Iterable[LeadScore],
    ) -> tuple[LeadWithHistory, ...]:
        """Track leads idempotently and return their persistent history.

        ``seen_before`` is false only when the lead is inserted into the CRM by
        this call. Existing status and notes are never overwritten by a repeated
        search result.
        """

        enriched: list[LeadWithHistory] = []
        for lead in leads:
            place_id = lead.place.place_id.strip()
            if not place_id:
                raise ValueError("lead place_id must not be empty.")

            tracked, created = self._repository.track(place_id)
            enriched.append(
                LeadWithHistory(
                    lead=lead,
                    seen_before=not created,
                    status=tracked.status,
                    note=tracked.note,
                    first_seen_at=tracked.created_at,
                    updated_at=tracked.updated_at,
                    was_contacted=tracked.status in CONTACTED_STATUSES,
                    is_closed=tracked.status in CLOSED_STATUSES,
                )
            )

        return tuple(enriched)

    def record_search_result(
        self,
        result: LeadSearchResult,
    ) -> LeadSearchWithHistoryResult:
        """Attach CRM history while preserving search order and pagination."""

        return LeadSearchWithHistoryResult(
            leads=self.record_leads(result.leads),
            next_page_token=result.next_page_token,
        )
