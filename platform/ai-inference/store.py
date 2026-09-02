"""SQLite persistence for triage results (E1)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


_LOCK = threading.Lock()


def default_db_path() -> Path:
    raw = os.environ.get("NEXUS_AI_DB_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(os.environ.get("NEXUS_AI_DATA_DIR", "./data")) / "triage.db"


class TriageStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with _LOCK:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS triage_results (
                        source_event_id TEXT PRIMARY KEY,
                        saved_at REAL NOT NULL,
                        score REAL NOT NULL,
                        label TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_triage_saved_at ON triage_results(saved_at DESC)"
                )
                conn.commit()

    def upsert(self, result: dict[str, Any]) -> dict[str, Any]:
        event_id = str(result.get("source_event_id") or result.get("id") or "")
        if not event_id:
            raise ValueError("triage result missing source_event_id")
        saved_at = float(result.get("saved_at") or time.time())
        result = {**result, "saved_at": saved_at, "source_event_id": event_id}
        score = float(result.get("score") or result.get("confidenceScore") or 0.0)
        label = str(result.get("label") or "unknown")
        with _LOCK:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO triage_results (source_event_id, saved_at, score, label, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(source_event_id) DO UPDATE SET
                        saved_at=excluded.saved_at,
                        score=excluded.score,
                        label=excluded.label,
                        payload_json=excluded.payload_json
                    """,
                    (event_id, saved_at, score, label, json.dumps(result)),
                )
                conn.commit()
        return result

    def get(self, source_event_id: str) -> dict[str, Any] | None:
        with _LOCK:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT payload_json FROM triage_results WHERE source_event_id = ?",
                    (str(source_event_id),),
                ).fetchone()
        if not row:
            return None
        return json.loads(row["payload_json"])

    def recent(self, limit: int = 5) -> list[dict[str, Any]]:
        limit = max(1, min(500, int(limit)))
        with _LOCK:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT payload_json FROM triage_results
                    ORDER BY saved_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def count(self) -> int:
        with _LOCK:
            with self._connect() as conn:
                row = conn.execute("SELECT COUNT(*) AS c FROM triage_results").fetchone()
        return int(row["c"] if row else 0)

    def search(self, query_text: str, limit: int = 3) -> list[dict[str, Any]]:
        """Keyword overlap search over persisted reason/action text (pre-embeddings)."""
        import re

        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", query_text.lower())
        words = {w for w in clean.split() if w}
        if not words:
            return []

        # Pull a bounded window and rank in process (fine for lab volumes).
        candidates = self.recent(limit=200)
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in candidates:
            reason = str(item.get("reason") or item.get("reasoningExcerpt") or "").lower()
            action = str(
                item.get("recommended_action") or item.get("recommendedAction") or ""
            ).lower()
            blob = re.sub(r"[^a-zA-Z0-9\s]", " ", f"{reason} {action}")
            overlap = len(words.intersection(set(blob.split())))
            if overlap > 0:
                scored.append((overlap, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[: max(1, min(50, int(limit)))]]
