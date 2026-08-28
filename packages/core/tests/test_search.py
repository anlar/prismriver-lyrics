import pytest
from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.registry import filter_cache_key
from prismriver_lyrics.search import SearchFailedError, search_lyrics


class _FakePlugin(LyricsPlugin):
    def __init__(
        self,
        plugin_id: str,
        result: LyricsResult | None = None,
        lang: list[str] | None = None,
        translated: int = 0,
        sync: int = 0,
    ) -> None:
        self.id = plugin_id
        self.name = plugin_id
        self.lang = lang if lang is not None else ["?"]
        self.translated = translated
        self.sync = sync
        self.result = result
        self.called = False

    async def search(self, client, artist, title, duration_ms=None):
        self.called = True
        return [self.result] if self.result is not None else []


class _FailingPlugin(LyricsPlugin):
    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id
        self.name = plugin_id
        self.lang = ["?"]
        self.translated = 0
        self.sync = 0

    async def search(self, client, artist, title, duration_ms=None):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_search_lyrics_without_filter_uses_plain_cache(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    result = LyricsResult(source="P1", url="u", lyrics="a")
    plugin = _FakePlugin("p1", result=result)

    results = await search_lyrics(
        "Artist", "Title", plugins=[plugin], cache=cache
    )

    assert results == [result]
    assert plugin.called
    assert cache.get("Artist", "Title") == [result]


@pytest.mark.asyncio
async def test_search_lyrics_strips_title_postfix(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    result = LyricsResult(source="P1", url="u", lyrics="a")
    plugin = _FakePlugin("p1", result=result)

    results = await search_lyrics(
        "Artist",
        "Title (Official Music Video)",
        plugins=[plugin],
        cache=cache,
    )

    assert results == [result]
    assert cache.get("Artist", "Title") == [result]


@pytest.mark.asyncio
async def test_search_lyrics_uses_filter_specific_cache_entry_first(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    cached_result = LyricsResult(
        source="Cached", url="u", lyrics="x", lang="ru"
    )
    filter_key = filter_cache_key(langs=frozenset({"ru"}))
    cache.set("Artist", "Title", [cached_result], filter_key=filter_key)

    plugin = _FakePlugin(
        "never_called", result=LyricsResult(source="Never", url="u", lyrics="y")
    )

    results = await search_lyrics(
        "Artist",
        "Title",
        plugins=[plugin],
        cache=cache,
        langs=frozenset({"ru"}),
    )

    assert results == [cached_result]
    assert not plugin.called


@pytest.mark.asyncio
async def test_search_lyrics_falls_back_to_plain_cache_filtered_in_memory(
    tmp_path,
):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    ru_result = LyricsResult(source="A", url="u", lyrics="x", lang="ru")
    en_result = LyricsResult(source="B", url="u", lyrics="y", lang="en")
    cache.set("Artist", "Title", [ru_result, en_result])

    plugin = _FakePlugin(
        "never_called", result=LyricsResult(source="Never", url="u", lyrics="z")
    )

    results = await search_lyrics(
        "Artist",
        "Title",
        plugins=[plugin],
        cache=cache,
        langs=frozenset({"ru"}),
    )

    assert results == [ru_result]
    assert not plugin.called
    # The plain-cache fallback doesn't backfill a filter-specific entry.
    filter_key = filter_cache_key(langs=frozenset({"ru"}))
    assert cache.get("Artist", "Title", filter_key=filter_key) is None


@pytest.mark.asyncio
async def test_search_lyrics_live_search_narrows_plugins_and_caches_by_filter(
    tmp_path,
):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")

    matching_result = LyricsResult(
        source="RU", url="u", lyrics="x", lang="ru"
    )
    matching = _FakePlugin(
        "ru_plugin", result=matching_result, lang=["?", "ru"]
    )
    skipped = _FakePlugin(
        "untagged_plugin",
        result=LyricsResult(source="Untagged", url="u", lyrics="y"),
    )

    results = await search_lyrics(
        "Artist",
        "Title",
        plugins=[matching, skipped],
        cache=cache,
        langs=frozenset({"ru"}),
    )

    assert results == [matching_result]
    assert matching.called
    assert not skipped.called

    filter_key = filter_cache_key(langs=frozenset({"ru"}))
    assert cache.get("Artist", "Title", filter_key=filter_key) == [
        matching_result
    ]
    # The plain (artist, title) entry is left untouched by a filtered search.
    assert cache.get("Artist", "Title") is None


@pytest.mark.asyncio
async def test_search_lyrics_raises_when_every_plugin_fails(tmp_path):
    cache = SearchCache(ttl=3600, path=tmp_path / "cache.sqlite3")
    plugins = [_FailingPlugin("p1"), _FailingPlugin("p2")]

    with pytest.raises(SearchFailedError):
        await search_lyrics(
            "Artist", "Title", plugins=plugins, cache=cache
        )

    # A total failure isn't cached as an empty ("no results") entry.
    assert cache.get("Artist", "Title") is None
