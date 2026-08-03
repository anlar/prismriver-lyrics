import asyncio
import sqlite3
import time
from pathlib import Path

from prismriver_lyrics.cache import default_cache_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kv_cache (
    namespace  TEXT NOT NULL,
    key        TEXT NOT NULL,
    value      TEXT NOT NULL,
    expires_at REAL NOT NULL,
    PRIMARY KEY (namespace, key)
);
"""


class KeyValueCache:
    """Persistent on-disk cache for small, short-lived string values (e.g.
    a plugin's own API session token) — not tied to LyricsResult like
    SearchCache, so any plugin can reuse it. Entries are namespaced (e.g.
    by plugin id) so unrelated callers can't collide on the same key, and
    each entry carries its own absolute expiry set at write time, rather
    than one cache-wide TTL — a caller whose value has a known/variable
    lifetime (e.g. a JWT's own `exp` claim) can reflect that directly
    instead of guessing a fixed duration.

    Shares the same SQLite file as SearchCache by default (see
    cache.default_cache_path()), in its own table. A connection is opened
    fresh per call rather than held open, for the same reasons as
    SearchCache: lookups are infrequent, and this sidesteps sharing a
    sqlite3.Connection across asyncio.to_thread calls, which run on
    different threads.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_cache_path()

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

    def get(self, namespace: str, key: str) -> str | None:
        """Return the cached value for (namespace, key), or None on a
        cache miss (never set, expired, or explicitly deleted)."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value FROM kv_cache "
                "WHERE namespace = ? AND key = ? AND expires_at >= ?",
                (namespace, key, time.time()),
            ).fetchone()
        finally:
            conn.close()
        return row[0] if row is not None else None

    def set(self, namespace: str, key: str, value: str, ttl: float) -> None:
        """Cache `value` for (namespace, key) for `ttl` seconds, and prune
        every already-expired entry (in any namespace)."""
        now = time.time()
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO kv_cache "
                    "(namespace, key, value, expires_at) VALUES (?, ?, ?, ?)",
                    (namespace, key, value, now + ttl),
                )
                conn.execute(
                    "DELETE FROM kv_cache WHERE expires_at < ?", (now,)
                )
        finally:
            conn.close()

    def delete(self, namespace: str, key: str) -> None:
        """Drop (namespace, key) early, e.g. because the server rejected
        a cached value as invalid before its recorded expiry."""
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "DELETE FROM kv_cache WHERE namespace = ? AND key = ?",
                    (namespace, key),
                )
        finally:
            conn.close()

    async def aget(self, namespace: str, key: str) -> str | None:
        return await asyncio.to_thread(self.get, namespace, key)

    async def aset(
        self, namespace: str, key: str, value: str, ttl: float
    ) -> None:
        await asyncio.to_thread(self.set, namespace, key, value, ttl)

    async def adelete(self, namespace: str, key: str) -> None:
        await asyncio.to_thread(self.delete, namespace, key)
