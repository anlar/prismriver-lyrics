from prismriver_lyrics.models import (
    LyricsResult,
    SyncedLine,
    SyncedLyrics,
)
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.registry import (
    filter_cache_key,
    filter_plugins,
    filter_results,
    parse_ids,
)


class _FakePlugin(LyricsPlugin):
    id = "fake"
    name = "Fake"

    async def search(self, client, artist, title, duration_ms=None):
        return []


def _plugin(
    plugin_id: str,
    lang: list[str] | None = None,
    translated: int = 0,
    sync: int = 0,
) -> LyricsPlugin:
    cls = type(
        plugin_id,
        (_FakePlugin,),
        {
            "id": plugin_id,
            "name": plugin_id,
            "lang": lang if lang is not None else ["?"],
            "translated": translated,
            "sync": sync,
        },
    )
    return cls()


def _result(source: str, lang: str | None = None, translation: bool = False):
    return LyricsResult(
        source=source,
        url="u",
        lyrics="text",
        lang=lang,
        translation=translation,
    )


def _synced_result(source: str):
    return LyricsResult(
        source=source,
        url="u",
        lyrics=SyncedLyrics(lines=(SyncedLine(time_ms=0, text="text"),)),
    )


def test_parse_ids_returns_none_for_none():
    assert parse_ids(None) is None


def test_parse_ids_splits_and_strips_csv():
    assert parse_ids("lrclib, genius ,,musixmatch") == frozenset(
        {"lrclib", "genius", "musixmatch"}
    )


def test_filter_results_no_constraints_is_noop():
    results = [_result("LRCLIB"), _result("Genius", lang="en")]
    assert filter_results(results) == results


def test_filter_results_by_plugin_id():
    results = [_result("LRCLIB"), _result("Genius")]
    assert filter_results(results, plugin_ids=frozenset({"lrclib"})) == [
        results[0]
    ]


def test_filter_results_by_lang():
    results = [
        _result("Genius", lang="en"),
        _result("Genius", lang="ru"),
        _result("LRCLIB", lang=None),
    ]
    assert filter_results(results, langs=frozenset({"en"})) == [results[0]]


def test_filter_results_by_lang_unknown_token_matches_untagged():
    tagged = _result("Genius", lang="en")
    untagged = _result("LRCLIB", lang=None)
    results = [tagged, untagged]

    assert filter_results(results, langs=frozenset({"?"})) == [untagged]
    assert filter_results(results, langs=frozenset({"en", "?"})) == results


def test_filter_results_by_lang_any_token_matches_any_tagged_result():
    tagged_en = _result("Genius", lang="en")
    tagged_ru = _result("Amalgama-Lab", lang="ru")
    untagged = _result("LRCLIB", lang=None)
    results = [tagged_en, tagged_ru, untagged]

    assert filter_results(results, langs=frozenset({"*"})) == [
        tagged_en,
        tagged_ru,
    ]
    assert filter_results(results, langs=frozenset({"*", "?"})) == results


def test_filter_results_by_translated():
    original = _result("Amalgama-Lab", translation=False)
    translated = _result("Amalgama-Lab", lang="ru", translation=True)
    results = [original, translated]

    assert filter_results(results, translated=True) == [translated]
    assert filter_results(results, translated=False) == [original]


def test_filter_results_by_sync():
    plain = _result("LRCLIB")
    synced = _synced_result("LRCLIB")
    results = [plain, synced]

    assert filter_results(results, synced=True) == [synced]
    assert filter_results(results, synced=False) == [plain]


def test_filter_results_combines_constraints():
    results = [
        _result("Amalgama-Lab", lang="ru", translation=True),
        _result("Amalgama-Lab", translation=False),
        _result("Genius", lang="ru", translation=True),
    ]
    assert filter_results(
        results,
        plugin_ids=frozenset({"amalgama"}),
        langs=frozenset({"ru"}),
        translated=True,
    ) == [results[0]]


def test_filter_cache_key_is_none_without_any_constraint():
    assert filter_cache_key() is None


def test_filter_cache_key_is_stable_regardless_of_lang_order():
    assert filter_cache_key(langs=frozenset({"ru", "en"})) == filter_cache_key(
        langs=frozenset({"en", "ru"})
    )


def test_filter_cache_key_differs_by_constraint():
    keys = {
        filter_cache_key(langs=frozenset({"ru"})),
        filter_cache_key(translated=True),
        filter_cache_key(synced=True),
        filter_cache_key(langs=frozenset({"en"})),
    }
    assert len(keys) == 4
    assert None not in keys


def test_filter_plugins_no_constraints_is_noop():
    plugins = [_plugin("untagged"), _plugin("wildcard", lang=["*"])]
    assert filter_plugins(plugins) == plugins


def test_filter_plugins_by_lang_drops_plugins_that_cant_tag_it():
    untagged = _plugin("untagged")
    ru_only = _plugin("ru_only", lang=["?", "ru"])
    wildcard = _plugin("wildcard", lang=["*"])
    plugins = [untagged, ru_only, wildcard]

    assert filter_plugins(plugins, langs=frozenset({"en"})) == [wildcard]
    assert filter_plugins(plugins, langs=frozenset({"ru"})) == [
        ru_only,
        wildcard,
    ]


def test_filter_plugins_by_lang_unknown_token_matches_untagged_and_wildcard():
    untagged = _plugin("untagged")
    ru_only = _plugin("ru_only", lang=["?", "ru"])
    wildcard = _plugin("wildcard", lang=["*"])
    plugins = [untagged, ru_only, wildcard]

    assert filter_plugins(plugins, langs=frozenset({"?"})) == plugins


def test_filter_plugins_by_lang_any_token_keeps_plugins_that_can_tag():
    untagged_only = _plugin("untagged_only")
    ru_only = _plugin("ru_only", lang=["?", "ru"])
    wildcard = _plugin("wildcard", lang=["*"])
    plugins = [untagged_only, ru_only, wildcard]

    assert filter_plugins(plugins, langs=frozenset({"*"})) == [
        ru_only,
        wildcard,
    ]


def test_filter_plugins_by_translated_only_excludes_when_true():
    original_only = _plugin("original_only")
    with_translation = _plugin("with_translation", translated=1)
    plugins = [original_only, with_translation]

    assert filter_plugins(plugins, translated=True) == [with_translation]
    assert filter_plugins(plugins, translated=False) == plugins


def test_filter_plugins_by_sync_only_excludes_when_true():
    unsynced_only = _plugin("unsynced_only")
    with_sync = _plugin("with_sync", sync=1)
    plugins = [unsynced_only, with_sync]

    assert filter_plugins(plugins, synced=True) == [with_sync]
    assert filter_plugins(plugins, synced=False) == plugins


def test_filter_plugins_combines_constraints():
    plugins = [
        _plugin("amalgama_like", lang=["?", "ru"], translated=1),
        _plugin("untagged_only"),
        _plugin("wildcard", lang=["*"], translated=1),
    ]

    assert filter_plugins(
        plugins, langs=frozenset({"ru"}), translated=True
    ) == [plugins[0], plugins[2]]
