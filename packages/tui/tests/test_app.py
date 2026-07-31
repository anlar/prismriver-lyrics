import pytest
from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics_tui.app import PrismriverTuiApp
from prismriver_lyrics_tui.mpris import MprisWatcher, TrackInfo
from textual.widgets import OptionList


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

    async def __call__(self, artist: str, title: str, **kwargs: object):
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
