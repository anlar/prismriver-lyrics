from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics


def test_cache_round_trips_synced_lyrics(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    results = [
        LyricsResult(
            source="lrclib.net",
            url="https://lrclib.net/api/get/1",
            lyrics=SyncedLyrics(
                lines=(
                    SyncedLine(time_ms=1_000, text="First line"),
                    SyncedLine(time_ms=2_000, text="Second line"),
                )
            ),
        )
    ]

    cache.set("Some Artist", "Some Title", results)
    cached = cache.get("Some Artist", "Some Title")

    assert cached == results
    assert isinstance(cached[0].lyrics, SyncedLyrics)


def test_cache_round_trips_plain_lyrics(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    results = [
        LyricsResult(source="lrclib.net", url="u", lyrics="plain text")
    ]

    cache.set("Some Artist", "Some Title", results)
    cached = cache.get("Some Artist", "Some Title")

    assert cached == results
    assert isinstance(cached[0].lyrics, str)


def test_cache_filter_key_is_namespaced_separately_from_plain_entry(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    plain = [LyricsResult(source="Plain", url="u", lyrics="all plugins")]
    filtered = [LyricsResult(source="Filtered", url="u", lyrics="subset")]

    cache.set("Some Artist", "Some Title", plain)
    cache.set("Some Artist", "Some Title", filtered, filter_key="lang=ru")

    assert cache.get("Some Artist", "Some Title") == plain
    assert (
        cache.get("Some Artist", "Some Title", filter_key="lang=ru")
        == filtered
    )
    # A different (or missing) filter key doesn't see another one's entry.
    assert cache.get("Some Artist", "Some Title", filter_key="lang=en") is None


def test_cache_get_filter_key_is_a_miss_before_being_set(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    results = [LyricsResult(source="Plain", url="u", lyrics="all plugins")]
    cache.set("Some Artist", "Some Title", results)

    assert cache.get("Some Artist", "Some Title", filter_key="lang=ru") is None
