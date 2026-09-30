import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EventStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or os.getenv("MPESA_DB_PATH", "mpesa_events.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mpesa_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    event_key TEXT,
                    payload TEXT NOT NULL,
                    received_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mpesa_events_key ON mpesa_events(event_key)")

    def add(self, kind: str, payload: Dict[str, Any], event_key: Optional[str] = None) -> int:
        received_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute("INSERT INTO mpesa_events(kind, event_key, payload, received_at) VALUES (?, ?, ?, ?)", (kind, event_key, json.dumps(payload, separators=(",", ":")), received_at))
            return int(cursor.lastrowid)

    def list(self, limit: int = 20, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            if kind:
                rows = conn.execute("SELECT * FROM mpesa_events WHERE kind = ? ORDER BY id DESC LIMIT ?", (kind, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM mpesa_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": row["id"], "kind": row["kind"], "event_key": row["event_key"], "payload": json.loads(row["payload"]), "received_at": row["received_at"]} for row in rows]
