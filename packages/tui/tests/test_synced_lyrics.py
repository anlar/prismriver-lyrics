import pytest
from prismriver_lyrics.models import SyncedLine
from prismriver_lyrics_tui.synced_lyrics import SyncedLyricsView
from textual.app import App, ComposeResult


class _Harness(App[None]):
    def compose(self) -> ComposeResult:
        yield SyncedLyricsView(id="view")


@pytest.mark.asyncio
async def test_set_lines_mounts_one_widget_per_line():
    app = _Harness()
    async with app.run_test() as pilot:
        view = app.query_one("#view", SyncedLyricsView)
        view.set_lines(
            (
                SyncedLine(time_ms=0, text="A"),
                SyncedLine(time_ms=1_000, text="B"),
            )
        )
        await pilot.pause()

        assert len(view.children) == 2


@pytest.mark.asyncio
async def test_highlight_marks_current_line_and_advances():
    app = _Harness()
    async with app.run_test() as pilot:
        view = app.query_one("#view", SyncedLyricsView)
        view.set_lines(
            (
                SyncedLine(time_ms=0, text="A"),
                SyncedLine(time_ms=1_000, text="B"),
                SyncedLine(time_ms=2_000, text="C"),
            )
        )
        await pilot.pause()

        view.highlight(1_500)
        assert view._current_index == 1
        assert [w.has_class("current-line") for w in view.children] == [
            False,
            True,
            False,
        ]

        view.highlight(1_600)
        assert view._current_index == 1

        view.highlight(2_500)
        assert view._current_index == 2
        assert [w.has_class("current-line") for w in view.children] == [
            False,
            False,
            True,
        ]


@pytest.mark.asyncio
async def test_highlight_before_first_line_selects_first_line():
    app = _Harness()
    async with app.run_test() as pilot:
        view = app.query_one("#view", SyncedLyricsView)
        view.set_lines((SyncedLine(time_ms=1_000, text="A"),))
        await pilot.pause()

        view.highlight(0)
        assert view._current_index == 0


@pytest.mark.asyncio
async def test_highlight_is_noop_without_lines():
    app = _Harness()
    async with app.run_test():
        view = app.query_one("#view", SyncedLyricsView)
        view.highlight(1_000)
        assert view._current_index is None
