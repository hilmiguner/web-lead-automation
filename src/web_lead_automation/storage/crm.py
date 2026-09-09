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
    display_name: str | None = None
    last_contact_at: datetime | None = None
    contact_note: str = ""
    follow_up_at: datetime | None = None


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
                    demo_url TEXT,
                    display_name TEXT,
                    last_contact_at TEXT,
                    contact_note TEXT NOT NULL DEFAULT '',
                    follow_up_at TEXT
                )
                """
            )
            self._ensure_columns(connection)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_leads_follow_up_at ON leads(follow_up_at)"
            )

    def track(
        self,
        external_place_id: str,
        *,
        display_name: str | None = None,
    ) -> tuple[TrackedLead, bool]:
        place_id = external_place_id.strip()
        if not place_id:
            raise ValueError("external_place_id must not be empty.")
        normalized_name = self._normalize_optional_text(display_name)

        now = self._now_iso()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO leads (
                    external_place_id, status, note, created_at, updated_at, display_name
                ) VALUES (?, 'NEW', '', ?, ?, ?)
                """,
                (place_id, now, now, normalized_name),
            )
            created = cursor.rowcount == 1
            if not created and normalized_name:
                connection.execute(
                    "UPDATE leads SET display_name = ? WHERE external_place_id = ?",
                    (normalized_name, place_id),
                )
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

    def list_follow_ups_due(
        self,
        *,
        as_of: datetime | None = None,
    ) -> tuple[TrackedLead, ...]:
        """Return open leads whose explicitly scheduled follow-up is due."""

        cutoff = self._normalize_datetime(as_of or datetime.now(timezone.utc), "as_of")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM leads
                WHERE follow_up_at IS NOT NULL
                  AND follow_up_at <= ?
                  AND status NOT IN ('WON', 'LOST')
                ORDER BY follow_up_at ASC, id ASC
                """,
                (cutoff.isoformat(),),
            ).fetchall()
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

    def record_contact(
        self,
        external_place_id: str,
        *,
        contact_note: str = "",
        contacted_at: datetime | None = None,
        follow_up_at: datetime | None = None,
    ) -> TrackedLead:
        """Record a contact attempt and move NEW leads to CONTACTED.

        Existing INTERESTED/WON/LOST states are preserved so a contact-log action
        cannot accidentally downgrade the sales pipeline.
        """

        place_id = external_place_id.strip()
        if not place_id:
            raise ValueError("external_place_id must not be empty.")

        contacted = self._normalize_datetime(
            contacted_at or datetime.now(timezone.utc),
            "contacted_at",
        )
        follow_up = (
            self._normalize_datetime(follow_up_at, "follow_up_at")
            if follow_up_at is not None
            else None
        )
        if follow_up is not None and follow_up <= contacted:
            raise ValueError("follow_up_at must be later than contacted_at.")
        normalized_contact_note = contact_note.strip()

        with self._connect() as connection:
            current = connection.execute(
                "SELECT status FROM leads WHERE external_place_id = ?",
                (place_id,),
            ).fetchone()
            if current is None:
                raise LeadNotFoundError(place_id)

            current_status = LeadStatus(str(current["status"]))
            new_status = (
                LeadStatus.CONTACTED
                if current_status is LeadStatus.NEW
                else current_status
            )
            cursor = connection.execute(
                """
                UPDATE leads
                SET status = ?, last_contact_at = ?, contact_note = ?, follow_up_at = ?, updated_at = ?
                WHERE external_place_id = ?
                """,
                (
                    new_status.value,
                    contacted.isoformat(),
                    normalized_contact_note,
                    follow_up.isoformat() if follow_up else None,
                    self._now_iso(),
                    place_id,
                ),
            )
            if cursor.rowcount != 1:
                raise LeadNotFoundError(place_id)
            row = connection.execute(
                "SELECT * FROM leads WHERE external_place_id = ?",
                (place_id,),
            ).fetchone()

        assert row is not None
        return self._row_to_lead(row)

    def clear_follow_up(self, external_place_id: str) -> TrackedLead:
        """Clear a scheduled follow-up after it is handled or no longer needed."""

        place_id = external_place_id.strip()
        if not place_id:
            raise ValueError("external_place_id must not be empty.")
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE leads SET follow_up_at = NULL, updated_at = ? WHERE external_place_id = ?",
                (self._now_iso(), place_id),
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
    def _ensure_columns(connection: sqlite3.Connection) -> None:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(leads)").fetchall()
        }
        migrations = {
            "demo_url": "ALTER TABLE leads ADD COLUMN demo_url TEXT",
            "display_name": "ALTER TABLE leads ADD COLUMN display_name TEXT",
            "last_contact_at": "ALTER TABLE leads ADD COLUMN last_contact_at TEXT",
            "contact_note": (
                "ALTER TABLE leads ADD COLUMN contact_note TEXT NOT NULL DEFAULT ''"
            ),
            "follow_up_at": "ALTER TABLE leads ADD COLUMN follow_up_at TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(statement)

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
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @staticmethod
    def _normalize_datetime(value: datetime, field_name: str) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware.")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _row_to_lead(row: sqlite3.Row) -> TrackedLead:
        keys = set(row.keys())
        demo_url = row["demo_url"] if "demo_url" in keys else None
        display_name = row["display_name"] if "display_name" in keys else None
        last_contact_at = row["last_contact_at"] if "last_contact_at" in keys else None
        contact_note = row["contact_note"] if "contact_note" in keys else ""
        follow_up_at = row["follow_up_at"] if "follow_up_at" in keys else None
        return TrackedLead(
            id=int(row["id"]),
            external_place_id=str(row["external_place_id"]),
            status=LeadStatus(str(row["status"])),
            note=str(row["note"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            demo_url=str(demo_url) if demo_url else None,
            display_name=str(display_name) if display_name else None,
            last_contact_at=(
                datetime.fromisoformat(str(last_contact_at)) if last_contact_at else None
            ),
            contact_note=str(contact_note or ""),
            follow_up_at=(
                datetime.fromisoformat(str(follow_up_at)) if follow_up_at else None
            ),
        )
