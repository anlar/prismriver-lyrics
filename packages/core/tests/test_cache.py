from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics


def test_cache_round_trips_synced_lyrics(tmp_path):
    cache = SearchCache(path=tmp_path / "cache.sqlite3")
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
    cache = SearchCache(path=tmp_path / "cache.sqlite3")
    results = [
        LyricsResult(source="lrclib.net", url="u", lyrics="plain text")
    ]

    cache.set("Some Artist", "Some Title", results)
    cached = cache.get("Some Artist", "Some Title")

    assert cached == results
    assert isinstance(cached[0].lyrics, str)
