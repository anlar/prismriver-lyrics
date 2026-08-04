import pytest
from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics
from prismriver_lyrics_tui.app import PrismriverTuiApp
from prismriver_lyrics_tui.mpris import MprisWatcher, TrackInfo
from textual.widgets import OptionList, TabbedContent


async def _empty_watch(self):
    return
    yield  # pragma: no cover


@pytest.fixture(autouse=True)
def _no_mpris(monkeypatch):
    monkeypatch.setattr(MprisWatcher, "watch", _empty_watch)


class _FakeSearch:
    """Stand-in for search_lyrics() that records every call it receives."""

    def __init__(self, results: list[LyricsResult] | None = None) -> None:
        self.results = results if results is not None else []
        self.calls: list[tuple[str, str]] = []

    async def __call__(
        self,
        artist: str,
        title: str,
        duration_ms: int | None = None,
        **kwargs: object,
    ):
        self.calls.append((artist, title))
        return self.results


async def _open_dialog_and_submit(pilot, title: str, artist: str) -> None:
    await pilot.press("s")
    await pilot.press(*title)
    await pilot.press("tab")
    await pilot.press(*artist)
    await pilot.press("enter")
    await pilot.pause()


@pytest.mark.asyncio
async def test_manual_search_disables_auto_sync(monkeypatch):
    fake = _FakeSearch([LyricsResult(source="Test", url="u", lyrics="la la")])
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await _open_dialog_and_submit(pilot, "Song Title", "Some Artist")

        assert app.auto_sync is False
        assert app.track.artist == "Some Artist"
        assert app.track.title == "Song Title"
        assert fake.calls == [("Some Artist", "Song Title")]

        assert app._players == {}
        player_list = app.query_one("#player-list", OptionList)
        assert player_list.option_count == 1
        assert player_list.get_option_at_index(0).prompt == "Auto-sync disabled"


@pytest.mark.asyncio
async def test_search_dialog_cancel_is_a_noop(monkeypatch):
    fake = _FakeSearch()
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await pilot.press("s")
        await pilot.press("escape")
        await pilot.pause()

        assert app.auto_sync is True
        assert len(app.screen_stack) == 1
        assert fake.calls == []


@pytest.mark.asyncio
async def test_resync_forces_refresh_even_with_matching_key(monkeypatch):
    fake = _FakeSearch([LyricsResult(source="Test", url="u", lyrics="la la")])
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await _open_dialog_and_submit(pilot, "Song Title", "Some Artist")
        assert app.auto_sync is False
        assert len(fake.calls) == 1

        mpris_track = TrackInfo(artist="Some Artist", title="Song Title")
        app._watcher._states = {"org.mpris.MediaPlayer2.test": mpris_track}

        await pilot.press("a")
        await pilot.pause()

        assert app.auto_sync is True
        assert app.track == mpris_track
        assert len(fake.calls) == 2
        assert "org.mpris.MediaPlayer2.test" in app._players


def _synced_result(source: str = "lrclib.net") -> LyricsResult:
    return LyricsResult(
        source=source,
        url="u",
        lyrics=SyncedLyrics(
            lines=(
                SyncedLine(time_ms=0, text="Line one"),
                SyncedLine(time_ms=1_000, text="Line two"),
            )
        ),
    )


def test_result_label_plain():
    app = PrismriverTuiApp()
    result = LyricsResult(source="Test", url="u", lyrics="text")
    assert app._result_label(result, has_synced=False) == "Test"


def test_result_label_lang_only():
    app = PrismriverTuiApp()
    result = LyricsResult(source="Test", url="u", lyrics="text", lang="en")
    assert (
        app._result_label(result, has_synced=False)
        == "Test[dim] \\[EN][/dim]"
    )


def test_result_label_translated_no_original_lang():
    app = PrismriverTuiApp()
    result = LyricsResult(
        source="Test", url="u", lyrics="text", translation=True, lang="en"
    )
    assert (
        app._result_label(result, has_synced=False)
        == "Test[dim] \\[?? -> EN][/dim]"
    )


def test_result_label_translated_with_original_lang():
    app = PrismriverTuiApp()
    result = LyricsResult(
        source="Test",
        url="u",
        lyrics="text",
        translation=True,
        lang="en",
        original_lang="ja",
    )
    assert (
        app._result_label(result, has_synced=False)
        == "Test[dim] \\[JA -> EN][/dim]"
    )


def test_result_label_synced_only():
    app = PrismriverTuiApp()
    assert (
        app._result_label(_synced_result(), has_synced=True)
        == "[palegreen bold dim]\\[S] [/]lrclib.net"
    )


def test_result_label_plain_alongside_synced_is_indented():
    app = PrismriverTuiApp()
    result = LyricsResult(source="Test", url="u", lyrics="text")
    assert app._result_label(result, has_synced=True) == "    Test"


def test_result_label_synced_and_translation():
    app = PrismriverTuiApp()
    result = LyricsResult(
        source="lrclib.net",
        url="u",
        lyrics=SyncedLyrics(lines=(SyncedLine(time_ms=0, text="A"),)),
        translation=True,
        lang="en",
        original_lang="ja",
    )
    assert (
        app._result_label(result, has_synced=True)
        == "[palegreen bold dim]\\[S] [/]lrclib.net"
        "[dim] \\[JA -> EN][/dim]"
    )


@pytest.mark.asyncio
async def test_sync_result_shows_symbol_in_results_list(monkeypatch):
    plain = LyricsResult(source="Plain Source", url="u", lyrics="plain text")
    fake = _FakeSearch([_synced_result(), plain])
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await _open_dialog_and_submit(pilot, "Song Title", "Some Artist")

        results_list = app.query_one("#results-list", OptionList)
        labels = [
            results_list.get_option_at_index(i).prompt
            for i in range(results_list.option_count)
        ]
        assert any(
            "\\[S]" in label and "lrclib.net" in label for label in labels
        )
        assert any("    Plain Source" in label for label in labels)


@pytest.mark.asyncio
async def test_synced_result_selected_by_default_over_alphabetical_order(
    monkeypatch,
):
    # "Aaa Plain" sorts before "lrclib.net", so this only passes if the
    # synced result is preferred over the alphabetically-first one.
    plain = LyricsResult(source="Aaa Plain", url="u", lyrics="plain text")
    fake = _FakeSearch([plain, _synced_result()])
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await _open_dialog_and_submit(pilot, "Song Title", "Some Artist")

        assert app._results[0].source == "Aaa Plain"
        results_list = app.query_one("#results-list", OptionList)
        selected = app._results[results_list.highlighted]
        assert isinstance(selected.lyrics, SyncedLyrics)

        tabs = app.query_one("#lyrics-tabs", TabbedContent)
        assert tabs.active == "lyrics-synced"


@pytest.mark.asyncio
async def test_selecting_sync_result_switches_to_synced_tab(monkeypatch):
    plain = LyricsResult(source="Plain Source", url="u", lyrics="plain text")
    fake = _FakeSearch([_synced_result(), plain])
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await _open_dialog_and_submit(pilot, "Song Title", "Some Artist")

        results_list = app.query_one("#results-list", OptionList)
        tabs = app.query_one("#lyrics-tabs", TabbedContent)

        sync_index = next(
            i
            for i, r in enumerate(app._results)
            if isinstance(r.lyrics, SyncedLyrics)
        )
        results_list.highlighted = sync_index
        await pilot.pause()
        assert tabs.active == "lyrics-synced"

        plain_index = next(
            i
            for i, r in enumerate(app._results)
            if not isinstance(r.lyrics, SyncedLyrics)
        )
        results_list.highlighted = plain_index
        await pilot.pause()
        assert tabs.active == "lyrics-plain"


def test_dedup_results_drops_later_exact_lyrics_matches():
    app = PrismriverTuiApp()
    first = LyricsResult(source="Aaa", url="u1", lyrics="same text")
    dup = LyricsResult(source="Bbb", url="u2", lyrics="same text")
    unique = LyricsResult(source="Ccc", url="u3", lyrics="other text")

    deduped, hidden = app._dedup_results([first, dup, unique])

    assert deduped == [first, unique]
    assert hidden == 1


def test_dedup_results_keeps_synced_and_plain_lyrics_distinct():
    app = PrismriverTuiApp()
    plain = LyricsResult(source="Aaa", url="u1", lyrics="Line one")
    synced = _synced_result(source="Bbb")

    deduped, hidden = app._dedup_results([plain, synced])

    assert deduped == [plain, synced]
    assert hidden == 0


def test_results_border_title_without_duplicates():
    app = PrismriverTuiApp()
    assert app._results_border_title(20, 0) == "Results (20)"


def test_results_border_title_with_duplicates():
    app = PrismriverTuiApp()
    assert (
        app._results_border_title(20, 5)
        == "Results (20, 5 duplicates hidden)"
    )


def test_results_border_title_singular_duplicate():
    app = PrismriverTuiApp()
    assert (
        app._results_border_title(20, 1) == "Results (20, 1 duplicate hidden)"
    )


@pytest.mark.asyncio
async def test_search_results_hide_exact_duplicate_lyrics(monkeypatch):
    first = LyricsResult(source="Aaa", url="u1", lyrics="same text")
    dup = LyricsResult(source="Bbb", url="u2", lyrics="same text")
    fake = _FakeSearch([first, dup])
    monkeypatch.setattr("prismriver_lyrics_tui.app.search_lyrics", fake)

    app = PrismriverTuiApp()
    async with app.run_test() as pilot:
        await _open_dialog_and_submit(pilot, "Song Title", "Some Artist")

        assert [r.source for r in app._results] == ["Aaa"]
        results_list = app.query_one("#results-list", OptionList)
        assert (
            results_list.border_title == "Results (1, 1 duplicate hidden)"
        )
