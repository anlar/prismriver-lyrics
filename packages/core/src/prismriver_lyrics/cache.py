import asyncio
import json
import os
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path

from prismriver_lyrics.models import LyricsResult

# Week-long TTL
DEFAULT_TTL = 7 * 24 * 60 * 60.0

_SCHEMA = """
CREATE TABLE IF NOT EXISTS search_cache (
    key        TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    results    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_search_cache_created_at
    ON search_cache (created_at);
"""


def default_cache_path() -> Path:
    """Default on-disk cache location, following the XDG base dir spec."""
    cache_home = os.environ.get("XDG_CACHE_HOME")
    base = Path(cache_home) if cache_home else Path.home() / ".cache"
    return base / "prismriver-lyrics" / "cache.sqlite3"


def _cache_key(artist: str, title: str) -> str:
    return f"{artist.strip().lower()}\0{title.strip().lower()}"


class SearchCache:
    """Persistent on-disk cache of search_lyrics() results, keyed by
    normalized (artist, title). Backed by a single SQLite file so the CLI
    and TUI can share entries, and concurrent readers/writers (e.g. both
    running at once) don't corrupt each other.

    A connection is opened fresh per call rather than held open, since
    lookups are infrequent (one per search) and this sidesteps sharing a
    sqlite3.Connection across asyncio.to_thread calls, which run on
    different threads.
    """

    def __init__(
        self, path: Path | None = None, ttl: float = DEFAULT_TTL
    ) -> None:
        self._path = path or default_cache_path()
        self._ttl = ttl

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path)
        conn.executescript(_SCHEMA)
        return conn

    def get(self, artist: str, title: str) -> list[LyricsResult] | None:
        """Return the cached results for (artist, title), or None on a
        cache miss (never searched, or the entry expired)."""
        cutoff = time.time() - self._ttl
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT results FROM search_cache "
                "WHERE key = ? AND created_at >= ?",
                (_cache_key(artist, title), cutoff),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None
        return [LyricsResult(**item) for item in json.loads(row[0])]

    def set(self, artist: str, title: str, results: list[LyricsResult]) -> None:
        """Cache results for (artist, title), and prune expired entries."""
        now = time.time()
        cutoff = now - self._ttl
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO search_cache "
                    "(key, created_at, results) VALUES (?, ?, ?)",
                    (
                        _cache_key(artist, title),
                        now,
                        json.dumps([asdict(result) for result in results]),
                    ),
                )
                conn.execute(
                    "DELETE FROM search_cache WHERE created_at < ?", (cutoff,)
                )
        finally:
            conn.close()

    async def aget(self, artist: str, title: str) -> list[LyricsResult] | None:
        return await asyncio.to_thread(self.get, artist, title)

    async def aset(
        self, artist: str, title: str, results: list[LyricsResult]
    ) -> None:
        await asyncio.to_thread(self.set, artist, title, results)
