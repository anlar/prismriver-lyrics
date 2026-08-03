import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path

from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics

logger = logging.getLogger(__name__)


def _decode_result(item: dict) -> LyricsResult:
    # asdict() flattens a SyncedLyrics `lyrics` value to a plain dict;
    # dataclasses aren't reconstructed from that automatically, so it's
    # rebuilt by hand here.
    lyrics = item["lyrics"]
    if isinstance(lyrics, dict):
        item = {
            **item,
            "lyrics": SyncedLyrics(
                lines=tuple(SyncedLine(**line) for line in lyrics["lines"])
            ),
        }
    return LyricsResult(**item)


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


def _cache_key(artist: str, title: str, filter_key: str | None = None) -> str:
    key = f"{artist.strip().lower()}\0{title.strip().lower()}"
    if filter_key is not None:
        key = f"{key}\0{filter_key}"
    return key


class SearchCache:
    """Persistent on-disk cache of search_lyrics() results, keyed by
    normalized (artist, title) — or, when a `filter_key` is given, by
    (artist, title, filter_key), namespacing a filtered search's (partial
    plugin coverage) results separately from the plain, every-plugin
    entry for the same (artist, title) so one can't shadow the other.
    Backed by a single SQLite file so the CLI and TUI can share entries,
    and concurrent readers/writers (e.g. both running at once) don't
    corrupt each other.

    A connection is opened fresh per call rather than held open, since
    lookups are infrequent (one per search) and this sidesteps sharing a
    sqlite3.Connection across asyncio.to_thread calls, which run on
    different threads.
    """

    def __init__(self, ttl: float, path: Path | None = None) -> None:
        self._path = path or default_cache_path()
        self._ttl = ttl

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path)
        # WAL lets a reader and a writer (e.g. the CLI and TUI at once) work
        # concurrently; busy_timeout makes a blocked writer wait instead of
        # immediately raising "database is locked".
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.executescript(_SCHEMA)
        return conn

    def get(
        self, artist: str, title: str, filter_key: str | None = None
    ) -> list[LyricsResult] | None:
        """Return the cached results for (artist, title[, filter_key]),
        or None on a cache miss (never searched, or the entry expired)."""
        cutoff = time.time() - self._ttl
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT results FROM search_cache "
                "WHERE key = ? AND created_at >= ?",
                (_cache_key(artist, title, filter_key), cutoff),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None
        try:
            return [_decode_result(item) for item in json.loads(row[0])]
        except Exception:
            logger.warning(
                "failed to decode cache entry for %r/%r, treating as a "
                "cache miss",
                artist,
                title,
                exc_info=True,
            )
            return None

    def set(
        self,
        artist: str,
        title: str,
        results: list[LyricsResult],
        filter_key: str | None = None,
    ) -> None:
        """Cache results for (artist, title[, filter_key]), and prune
        expired entries."""
        now = time.time()
        cutoff = now - self._ttl
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO search_cache "
                    "(key, created_at, results) VALUES (?, ?, ?)",
                    (
                        _cache_key(artist, title, filter_key),
                        now,
                        json.dumps([asdict(result) for result in results]),
                    ),
                )
                conn.execute(
                    "DELETE FROM search_cache WHERE created_at < ?", (cutoff,)
                )
        finally:
            conn.close()

    async def aget(
        self, artist: str, title: str, filter_key: str | None = None
    ) -> list[LyricsResult] | None:
        return await asyncio.to_thread(self.get, artist, title, filter_key)

    async def aset(
        self,
        artist: str,
        title: str,
        results: list[LyricsResult],
        filter_key: str | None = None,
    ) -> None:
        await asyncio.to_thread(self.set, artist, title, results, filter_key)
