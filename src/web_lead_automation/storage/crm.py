"""SQLite-backed minimal CRM persistence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse


class LeadStatus(StrEnum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    INTERESTED = "INTERESTED"
    WON = "WON"
    LOST = "LOST"


@dataclass(frozen=True, slots=True)
class TrackedLead:
    id: int
    external_place_id: str
    status: LeadStatus
    note: str
    created_at: datetime
    updated_at: datetime
    demo_url: str | None = None


class LeadNotFoundError(LookupError):
    """Raised when a tracked lead cannot be found."""


class LeadRepository:
    """Small SQLite repository for sales-pipeline state."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)

    def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_place_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'NEW'
                        CHECK (status IN ('NEW', 'CONTACTED', 'INTERESTED', 'WON', 'LOST')),
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    demo_url TEXT
                )
                """
            )
            self._ensure_demo_url_column(connection)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)"
            )

    def track(self, external_place_id: str) -> tuple[TrackedLead, bool]:
        place_id = external_place_id.strip()
        if not place_id:
            raise ValueError("external_place_id must not be empty.")

        now = self._now_iso()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO leads (
                    external_place_id, status, note, created_at, updated_at
                ) VALUES (?, 'NEW', '', ?, ?)
                """,
                (place_id, now, now),
            )
            created = cursor.rowcount == 1
            row = connection.execute(
                "SELECT * FROM leads WHERE external_place_id = ?",
                (place_id,),
            ).fetchone()

        assert row is not None
        return self._row_to_lead(row), created

    def exists(self, external_place_id: str) -> bool:
        place_id = external_place_id.strip()
        if not place_id:
            return False
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM leads WHERE external_place_id = ? LIMIT 1",
                (place_id,),
            ).fetchone()
        return row is not None

    def get_by_place_id(self, external_place_id: str) -> TrackedLead | None:
        place_id = external_place_id.strip()
        if not place_id:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM leads WHERE external_place_id = ?",
                (place_id,),
            ).fetchone()
        return self._row_to_lead(row) if row else None

    def list(self, *, status: LeadStatus | None = None) -> tuple[TrackedLead, ...]:
        query = "SELECT * FROM leads"
        params: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            params = (status.value,)
        query += " ORDER BY updated_at DESC, id DESC"

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return tuple(self._row_to_lead(row) for row in rows)

    def update(
        self,
        external_place_id: str,
        *,
        status: LeadStatus | None = None,
        note: str | None = None,
    ) -> TrackedLead:
        """Update one or more CRM fields in a single SQLite transaction."""

        normalized_note = note.strip() if note is not None else None
        return self._update(
            external_place_id,
            status=status,
            note=normalized_note,
        )

    def update_status(self, external_place_id: str, status: LeadStatus) -> TrackedLead:
        return self.update(external_place_id, status=status)

    def update_note(self, external_place_id: str, note: str) -> TrackedLead:
        return self.update(external_place_id, note=note)

    def update_demo_url(self, external_place_id: str, demo_url: str | None) -> TrackedLead:
        """Persist or clear the current public HTTPS demo URL for one lead."""

        place_id = external_place_id.strip()
        if not place_id:
            raise ValueError("external_place_id must not be empty.")
        normalized_url = self._normalize_demo_url(demo_url)

        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE leads SET demo_url = ?, updated_at = ? WHERE external_place_id = ?",
                (normalized_url, self._now_iso(), place_id),
            )
            if cursor.rowcount != 1:
                raise LeadNotFoundError(place_id)
            row = connection.execute(
                "SELECT * FROM leads WHERE external_place_id = ?",
                (place_id,),
            ).fetchone()

        assert row is not None
        return self._row_to_lead(row)

    def _update(
        self,
        external_place_id: str,
        *,
        status: LeadStatus | None = None,
        note: str | None = None,
    ) -> TrackedLead:
        place_id = external_place_id.strip()
        if not place_id:
            raise ValueError("external_place_id must not be empty.")

        assignments: list[str] = []
        values: list[str] = []
        if status is not None:
            assignments.append("status = ?")
            values.append(status.value)
        if note is not None:
            assignments.append("note = ?")
            values.append(note)
        if not assignments:
            lead = self.get_by_place_id(place_id)
            if lead is None:
                raise LeadNotFoundError(place_id)
            return lead

        assignments.append("updated_at = ?")
        values.append(self._now_iso())
        values.append(place_id)

        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE leads SET {', '.join(assignments)} WHERE external_place_id = ?",
                tuple(values),
            )
            if cursor.rowcount != 1:
                raise LeadNotFoundError(place_id)
            row = connection.execute(
                "SELECT * FROM leads WHERE external_place_id = ?",
                (place_id,),
            ).fetchone()

        assert row is not None
        return self._row_to_lead(row)

    @staticmethod
    def _ensure_demo_url_column(connection: sqlite3.Connection) -> None:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(leads)").fetchall()
        }
        if "demo_url" not in columns:
            connection.execute("ALTER TABLE leads ADD COLUMN demo_url TEXT")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _normalize_demo_url(value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        candidate = value.strip()
        parsed = urlparse(candidate)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("demo_url must be an absolute HTTPS URL.")
        return candidate

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _row_to_lead(row: sqlite3.Row) -> TrackedLead:
        demo_url = row["demo_url"] if "demo_url" in row.keys() else None
        return TrackedLead(
            id=int(row["id"]),
            external_place_id=str(row["external_place_id"]),
            status=LeadStatus(str(row["status"])),
            note=str(row["note"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            demo_url=str(demo_url) if demo_url else None,
        )
