import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from models import Vacancy


class VacancyDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_vacancies (
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    sent_at TEXT,
                    PRIMARY KEY (source, external_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def is_seen(self, source: str, external_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_vacancies WHERE source = ? AND external_id = ?",
                (source, external_id),
            ).fetchone()
            return row is not None

    def mark_seen(self, vacancy: Vacancy, *, sent: bool = False) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO seen_vacancies
                (source, external_id, title, url, first_seen_at, sent_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    vacancy.source,
                    vacancy.external_id,
                    vacancy.title,
                    vacancy.url,
                    now,
                    now if sent else None,
                ),
            )
            if sent:
                conn.execute(
                    """
                    UPDATE seen_vacancies
                    SET sent_at = ?
                    WHERE source = ? AND external_id = ?
                    """,
                    (now, vacancy.source, vacancy.external_id),
                )
            conn.commit()

    def count_seen(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM seen_vacancies").fetchone()
            return int(row["cnt"])

    def get_state(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM bot_state WHERE key = ?",
                (key,),
            ).fetchone()
            return row["value"] if row else None

    def set_state(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO bot_state (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            conn.commit()
