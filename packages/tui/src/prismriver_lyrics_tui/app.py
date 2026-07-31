import argparse
import asyncio
import importlib.metadata

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.search import search_lyrics
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Markdown, OptionList, Static
from textual.widgets.option_list import Option

from prismriver_lyrics_tui.mpris import (
    MprisWatcher,
    TrackInfo,
    format_duration,
    playback_status_emoji,
)

_MARKDOWN_ESCAPE_CHARS = "\\`*_{}[]()#+-.!>|"


def _md_escape(text: str) -> str:
    """Escape Markdown special characters in MPRIS-supplied text, so titles
    or artist names containing `*`, `_`, `[`, etc. render as literal text
    instead of being interpreted as formatting."""
    escaped = text
    for char in _MARKDOWN_ESCAPE_CHARS:
        escaped = escaped.replace(char, f"\\{char}")
    return escaped


class VimOptionList(OptionList):
    """An OptionList with vim-style j/k/g/G navigation, in addition to the
    default arrow/home/end keys."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "first", "First", show=False),
        Binding("G", "last", "Last", show=False),
    ]


class VimVerticalScroll(VerticalScroll):
    """A VerticalScroll with vim-style j/k/g/G scrolling, in addition to the
    default arrow/home/end keys."""

    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("g", "scroll_home", "Scroll Home", show=False),
        Binding("G", "scroll_end", "Scroll End", show=False),
    ]


class PrismriverTuiApp(App[None]):
    """Shows the currently-playing track (via MPRIS) and its lyrics."""

    CSS_PATH = "app.tcss"
    TITLE = "Prismriver Lyrics"

    BINDINGS = [Binding("q", "quit", "Quit", priority=True)]

    track: reactive[TrackInfo] = reactive(TrackInfo())
    status: reactive[str] = reactive("Waiting for a media player...")

    def __init__(self) -> None:
        super().__init__()
        self._watcher = MprisWatcher()
        self._search_task: asyncio.Task[None] | None = None
        self._last_track_key: tuple[str, str] | None = None
        self._results: list[LyricsResult] = []
        self._players: dict[str, TrackInfo] = {}
        self._selected_bus_name: str | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            with Vertical(id="left-column"):
                with VerticalScroll(id="metadata-container") as metadata:
                    metadata.border_title = "Song"
                    metadata.border_subtitle = "Prismriver Lyrics"
                    metadata.can_focus = False
                    yield Markdown(id="now-playing")
                player_list = VimOptionList(id="player-list")
                player_list.border_title = "Player"
                yield player_list
                results_list = VimOptionList(id="results-list")
                results_list.border_title = "Plugins"
                yield results_list
            with VimVerticalScroll(id="lyrics-container") as lyrics_container:
                lyrics_container.border_title = "Lyrics"
                lyrics_container.border_subtitle = (
                    "<↑↓/j/k> scroll "
                    "· <g/G> top/bottom "
                    "· <PgUp/PgDn> move "
                    "· <Tab> switch panels "
                    "· <q> exit"
                )
                yield Static(id="lyrics", markup=False)

    async def on_mount(self) -> None:
        await self._refresh_now_playing()
        self._refresh_lyrics("")
        self.query_one("#lyrics-container", VerticalScroll).focus()
        self.run_worker(self._watch_mpris(), exclusive=True, group="mpris")

    async def _watch_mpris(self) -> None:
        try:
            async for bus_name, track in self._watcher.watch():
                self._handle_track_event(bus_name, track)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.status = f"D-Bus error: {exc}"

    def _handle_track_event(self, bus_name: str, track: TrackInfo) -> None:
        self._refresh_player_list()

        if self._selected_bus_name is None:
            self._select_player(bus_name)
        elif bus_name == self._selected_bus_name:
            self._handle_track(track)

    def _player_option(self, bus_name: str) -> Option:
        track = self._players[bus_name]
        icon = playback_status_emoji(track.playback_status)
        label = f"{track.player}[dim] / {track.player_short}[/dim]"
        return Option(f"{icon} {label}", id=bus_name)

    def _result_label(self, result: LyricsResult) -> str:
        if result.translation:
            return f"{result.source}[dim] (translation)[/dim]"
        return result.source

    def _refresh_player_list(self) -> None:
        self._players = self._watcher.known_players()
        bus_names = list(self._players)

        player_list = self.query_one("#player-list", OptionList)
        player_list.set_options(
            self._player_option(bus_name) for bus_name in bus_names
        )
        # OptionList's own "auto" height ignores CSS min-height when empty,
        # so the box height is set explicitly here instead: shrink to fit
        # the player count (plus 2 rows for the border), never below 1
        # visible content line.
        player_list.styles.height = max(1, len(bus_names)) + 2

        if self._selected_bus_name in self._players:
            player_list.highlighted = bus_names.index(self._selected_bus_name)
        elif bus_names:
            self._select_player(bus_names[0])
        else:
            self._selected_bus_name = None
            self._handle_track(TrackInfo())

    def _select_player(self, bus_name: str) -> None:
        self._selected_bus_name = bus_name
        player_list = self.query_one("#player-list", OptionList)
        try:
            player_list.highlighted = list(self._players).index(bus_name)
        except ValueError:
            pass
        self._handle_track(self._players.get(bus_name, TrackInfo()))

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
        option_list.set_options(
            Option(self._result_label(result)) for result in results
        )
        if results:
            option_list.highlighted = 0
        else:
            self._refresh_lyrics("")

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        if event.option_list.id == "results-list":
            if 0 <= event.option_index < len(self._results):
                self._refresh_lyrics(self._results[event.option_index].lyrics)
        elif event.option_list.id == "player-list":
            if event.option_id and event.option_id != self._selected_bus_name:
                self._select_player(event.option_id)

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option_list.id == "player-list":
            self.query_one("#results-list", OptionList).focus()
        elif event.option_list.id == "results-list":
            self.query_one("#lyrics-container", VerticalScroll).focus()

    async def watch_track(self) -> None:
        await self._refresh_now_playing()

    async def watch_status(self) -> None:
        await self._refresh_now_playing()

    def _now_playing_markdown(self) -> str:
        t = self.track

        if not t.artist and not t.title:
            return f"*{self.status}*"

        lines = [
            f"**{_md_escape(t.title) or '-'}**",
            "",
            "---",
            "",
            f"- *Artist:* {_md_escape(t.artist) or '-'}",
            f"- *Album:* {_md_escape(t.album) or '-'}",
        ]

        if t.track_number is not None and t.disc_number is not None:
            lines.append(f"- *Track:* {t.track_number} (Disc {t.disc_number})")
        elif t.track_number is not None:
            lines.append(f"- *Track:* {t.track_number}")
        elif t.disc_number is not None:
            lines.append(f"- *Disc:* {t.disc_number}")

        lines += [
            f"- *Genre:* {_md_escape(t.genre) or '-'}",
            f"- *Duration:* {format_duration(t.length_us)}",
            "",
            "---",
            "",
            f"*Lyrics:* {self.status}",
        ]

        return "\n".join(lines)

    async def _refresh_now_playing(self) -> None:
        widget = self.query_one("#now-playing", Markdown)
        await widget.update(self._now_playing_markdown())

    def _refresh_lyrics(self, lyrics: str) -> None:
        widget = self.query_one("#lyrics", Static)
        widget.update(lyrics or "(no lyrics)")
        self.query_one("#lyrics-container", VerticalScroll).scroll_home(
            animate=False
        )


_VERSION_MESSAGE = (
    "Prismriver Lyrics, version {version}\n"
    "License: MIT\n"
    "https://github.com/anlar/prismriver-lyrics"
)


def run() -> None:
    version = importlib.metadata.version("prismriver-lyrics-tui")
    parser = argparse.ArgumentParser(
        prog="prismriver-lyrics-tui",
        description=(
            "Terminal UI showing lyrics for the currently playing track "
            "via MPRIS."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_VERSION_MESSAGE.format(version=version),
    )
    parser.parse_args()

    PrismriverTuiApp().run()


if __name__ == "__main__":
    run()
