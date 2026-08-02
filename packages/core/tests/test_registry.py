from prismriver_lyrics.models import (
    LyricsResult,
    SyncedLine,
    SyncedLyrics,
)
from prismriver_lyrics.registry import filter_results, parse_ids


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
