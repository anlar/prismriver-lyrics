import asyncio

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.search import search_lyrics
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from prismriver_lyrics_tui.mpris import MprisWatcher, TrackInfo, format_duration


class PrismriverTuiApp(App[None]):
    """Shows the currently-playing track (via MPRIS) and its lyrics."""

    CSS_PATH = "app.tcss"
    TITLE = "Prismriver Lyrics"

    track: reactive[TrackInfo] = reactive(TrackInfo())
    status: reactive[str] = reactive("Waiting for a media player...")

    def __init__(self) -> None:
        super().__init__()
        self._watcher = MprisWatcher()
        self._search_task: asyncio.Task[None] | None = None
        self._last_track_key: tuple[str, str] | None = None
        self._results: list[LyricsResult] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="left-column"):
                with VerticalScroll(id="metadata-container"):
                    yield Static(id="now-playing")
                yield OptionList(id="results-list")
            with VerticalScroll(id="lyrics-container"):
                yield Static(id="lyrics")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_now_playing()
        self._refresh_lyrics("")
        self.query_one("#lyrics-container", VerticalScroll).focus()
        self.run_worker(self._watch_mpris(), exclusive=True, group="mpris")

    async def _watch_mpris(self) -> None:
        try:
            async for track in self._watcher.watch():
                self._handle_track(track)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.status = f"D-Bus error: {exc}"

    def _handle_track(self, track: TrackInfo) -> None:
        self.track = track

        # MprisWatcher emits an update for *any* change (playback state,
        # ...), not just a new song, so only kick off a fresh lyrics search
        # when the artist/title actually changed.
        key = (track.artist, track.title)
        if key == self._last_track_key:
            return
        self._last_track_key = key

        if self._search_task is not None and not self._search_task.done():
            self._search_task.cancel()

        if not track.artist or not track.title:
            self.status = "No track playing."
            self._refresh_lyrics("")
            return

        self._search_task = asyncio.create_task(
            self._search_lyrics(track.artist, track.title)
        )

    async def _search_lyrics(self, artist: str, title: str) -> None:
        self.status = "Searching..."
        self._set_results([])

        try:
            results = await search_lyrics(artist, title)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.status = f"Error: {exc}"
            return

        self._set_results(results)
        if not results:
            self.status = "No lyrics found."
        else:
            sources = "source" if len(results) == 1 else "sources"
            self.status = f"Found {len(results)} {sources}"
            self._refresh_lyrics(results[0].lyrics)

    def _set_results(self, results: list[LyricsResult]) -> None:
        self._results = results
        option_list = self.query_one("#results-list", OptionList)
        option_list.set_options(Option(result.source) for result in results)
        if results:
            option_list.highlighted = 0
        else:
            self._refresh_lyrics("")

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        if event.option_list.id != "results-list":
            return
        if 0 <= event.option_index < len(self._results):
            self._refresh_lyrics(self._results[event.option_index].lyrics)

    def watch_track(self) -> None:
        self._refresh_now_playing()

    def watch_status(self) -> None:
        self._refresh_now_playing()

    def _refresh_now_playing(self) -> None:
        t = self.track
        lines = [
            f"Player: {t.player or '-'}",
            f"Status: {t.playback_status or '-'}",
            "",
            f"Artist: {t.artist or '-'}",
            f"Title:  {t.title or '-'}",
            f"Album:  {t.album or '-'}",
        ]

        if t.album_artist and t.album_artist != t.artist:
            lines.append(f"Album Artist: {t.album_artist}")

        lines.append(f"Genre:  {t.genre or '-'}")

        track_disc = []
        if t.track_number is not None:
            track_disc.append(f"Track {t.track_number}")
        if t.disc_number is not None:
            track_disc.append(f"Disc {t.disc_number}")
        if track_disc:
            lines.append(", ".join(track_disc))

        lines.append(f"Duration: {format_duration(t.length_us)}")

        if t.art_url:
            lines.append(f"Art: {t.art_url}")

        lines.append("")
        lines.append(f"Lyrics: {self.status}")

        widget = self.query_one("#now-playing", Static)
        widget.update("\n".join(lines))

    def _refresh_lyrics(self, lyrics: str) -> None:
        widget = self.query_one("#lyrics", Static)
        widget.update(lyrics or "(no lyrics)")


def run() -> None:
    PrismriverTuiApp().run()


if __name__ == "__main__":
    run()
