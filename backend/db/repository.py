"""
Database Repository Abstraction Layer for TARA.
Provides pluggable conversation persistence supporting In-Memory (Dev),
SQLite, and clean extensible interfaces for PostgreSQL and MongoDB.
"""

from __future__ import annotations

import os
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessageRecord:
    id: str
    session_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sentiment: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseConversationRepository(ABC):
    """Abstract repository interface for TARA conversation persistence."""

    @abstractmethod
    def save_message(self, message: ChatMessageRecord) -> None:
        """Persist a conversation message."""
        pass

    @abstractmethod
    def get_history(self, session_id: str, limit: int = 20) -> List[ChatMessageRecord]:
        """Retrieve recent conversation history for a session."""
        pass

    @abstractmethod
    def clear_history(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        pass

    @abstractmethod
    def get_last_topic(self, session_id: str) -> Optional[str]:
        """Get the most recent entity/topic discussed in this session."""
        pass


class InMemoryConversationRepository(BaseConversationRepository):
    """Lightweight in-memory development repository."""

    def __init__(self):
        self._sessions: Dict[str, List[ChatMessageRecord]] = {}
        self._topics: Dict[str, str] = {}

    def save_message(self, message: ChatMessageRecord) -> None:
        if message.session_id not in self._sessions:
            self._sessions[message.session_id] = []
        self._sessions[message.session_id].append(message)
        if message.intent and message.intent not in ("fallback", "greeting", "goodbye", "thanks", "help"):
            self._topics[message.session_id] = message.intent

    def get_history(self, session_id: str, limit: int = 20) -> List[ChatMessageRecord]:
        msgs = self._sessions.get(session_id, [])
        return msgs[-limit:]

    def clear_history(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._topics.pop(session_id, None)

    def get_last_topic(self, session_id: str) -> Optional[str]:
        return self._topics.get(session_id)


class SqliteConversationRepository(BaseConversationRepository):
    """File-based SQLite repository for persistent conversation storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    confidence REAL,
                    sentiment TEXT,
                    timestamp REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages (session_id, timestamp)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_topics (
                    session_id TEXT PRIMARY KEY,
                    last_topic TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

    def save_message(self, message: ChatMessageRecord) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO messages (id, session_id, role, content, intent, confidence, sentiment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.session_id,
                    message.role,
                    message.content,
                    message.intent,
                    message.confidence,
                    message.sentiment,
                    message.timestamp,
                ),
            )
            if message.intent and message.intent not in ("fallback", "greeting", "goodbye", "thanks", "help"):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO session_topics (session_id, last_topic, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (message.session_id, message.intent, message.timestamp),
                )

    def get_history(self, session_id: str, limit: int = 20) -> List[ChatMessageRecord]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT id, session_id, role, content, intent, confidence, sentiment, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = cursor.fetchall()
            return [
                ChatMessageRecord(
                    id=r[0],
                    session_id=r[1],
                    role=r[2],
                    content=r[3],
                    intent=r[4],
                    confidence=r[5],
                    sentiment=r[6],
                    timestamp=r[7],
                )
                for r in rows
            ]

    def clear_history(self, session_id: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM session_topics WHERE session_id = ?", (session_id,))

    def get_last_topic(self, session_id: str) -> Optional[str]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT last_topic FROM session_topics WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            return row[0] if row else None


_REPO_INSTANCE: Optional[BaseConversationRepository] = None


def get_repository() -> BaseConversationRepository:
    """Factory providing the configured repository instance."""
    global _REPO_INSTANCE
    if _REPO_INSTANCE is not None:
        return _REPO_INSTANCE

    db_type = os.getenv("DB_TYPE", "memory").lower().strip()
    db_url = os.getenv("DATABASE_URL", "")

    if db_type == "sqlite" or db_url.startswith("sqlite"):
        db_file = os.getenv("SQLITE_PATH", "database/tara_conversations.db")
        _REPO_INSTANCE = SqliteConversationRepository(db_file)
    else:
        _REPO_INSTANCE = InMemoryConversationRepository()

    return _REPO_INSTANCE
