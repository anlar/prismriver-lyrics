import pytest
from prismriver_lyrics.kv_cache import KeyValueCache


def test_kv_cache_round_trips_a_value(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.set("deezer", "jwt", "some-token", ttl=3600)

    assert cache.get("deezer", "jwt") == "some-token"


def test_kv_cache_miss_before_being_set(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    assert cache.get("deezer", "jwt") is None


def test_kv_cache_namespaces_dont_collide(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.set("deezer", "jwt", "deezer-token", ttl=3600)
    cache.set("other", "jwt", "other-token", ttl=3600)

    assert cache.get("deezer", "jwt") == "deezer-token"
    assert cache.get("other", "jwt") == "other-token"


def test_kv_cache_expired_entry_is_a_miss(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.set("deezer", "jwt", "some-token", ttl=-1)

    assert cache.get("deezer", "jwt") is None


def test_kv_cache_set_overwrites_previous_value(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.set("deezer", "jwt", "old-token", ttl=3600)
    cache.set("deezer", "jwt", "new-token", ttl=3600)

    assert cache.get("deezer", "jwt") == "new-token"


def test_kv_cache_delete_removes_entry_before_expiry(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.set("deezer", "jwt", "some-token", ttl=3600)
    cache.delete("deezer", "jwt")

    assert cache.get("deezer", "jwt") is None


def test_kv_cache_delete_is_a_noop_for_missing_key(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.delete("deezer", "jwt")

    assert cache.get("deezer", "jwt") is None


def test_kv_cache_set_prunes_other_expired_entries(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    cache.set("deezer", "stale", "old-token", ttl=-1)
    cache.set("deezer", "jwt", "new-token", ttl=3600)

    conn = cache._connect()
    try:
        rows = conn.execute("SELECT key FROM kv_cache").fetchall()
    finally:
        conn.close()
    assert [row[0] for row in rows] == ["jwt"]


@pytest.mark.asyncio
async def test_kv_cache_async_round_trip(tmp_path):
    cache = KeyValueCache(path=tmp_path / "cache.sqlite3")

    await cache.aset("deezer", "jwt", "some-token", ttl=3600)

    assert await cache.aget("deezer", "jwt") == "some-token"
    await cache.adelete("deezer", "jwt")
    assert await cache.aget("deezer", "jwt") is None
