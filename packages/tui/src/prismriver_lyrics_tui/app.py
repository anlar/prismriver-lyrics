import argparse
import asyncio
import importlib.metadata
import logging
import sys

from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import LyricsResult, SyncedLyrics
from prismriver_lyrics.registry import (
    default_plugins,
    filter_results,
    parse_ids,
    print_plugins,
)
from prismriver_lyrics.search import search_lyrics
from prismriver_lyrics.util import DEFAULT_CACHE_TTL, parse_duration
from rich.markup import escape
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.logging import TextualHandler
from textual.reactive import reactive
from textual.widgets import (
    Label,
    OptionList,
    ProgressBar,
    Static,
    TabbedContent,
    TabPane,
)
from textual.widgets.option_list import Option, OptionDoesNotExist

from prismriver_lyrics_tui.mpris import (
    MprisWatcher,
    TrackInfo,
    format_duration,
    playback_status_emoji,
)
from prismriver_lyrics_tui.search_dialog import SearchDialog
from prismriver_lyrics_tui.synced_lyrics import SyncedLyricsView
from prismriver_lyrics_tui.widgets import (
    StillProgressBar,
    VimOptionList,
    VimVerticalScroll,
)

# How often the currently-selected player's position is polled to advance
# the synced-lyrics highlight and the song progress bar. MPRIS doesn't push
# position updates on its own (see the note by
# mpris._PLAYER_PROPERTY_GETTERS), so this trades a little precision for not
# hammering D-Bus.
_POSITION_POLL_INTERVAL = 0.5


class PrismriverTuiApp(App[None]):
    """Shows the currently-playing track (via MPRIS) and its lyrics."""

    CSS_PATH = "app.tcss"
    TITLE = "Prismriver Lyrics"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        # Overrides App's default ctrl+q -> quit binding with a no-op, so
        # "q" is the only way to quit.
        Binding("ctrl+q", "no_op", "", show=False),
        Binding("s", "search", "Search lyrics", show=False),
        Binding("a", "resync", "Resume auto-sync", show=False),
        Binding("t", "change_theme", "Change theme", show=False),
    ]

    track: reactive[TrackInfo] = reactive(TrackInfo())
    status: reactive[str] = reactive("Waiting for a media player")
    auto_sync: reactive[bool] = reactive(True)

    def __init__(
        self,
        plugin_ids: frozenset[str] | None = None,
        langs: frozenset[str] | None = None,
        translated: bool | None = None,
        synced: bool | None = None,
        limit: int | None = None,
        cache_ttl: float = parse_duration(DEFAULT_CACHE_TTL),
    ) -> None:
        super().__init__()
        self._watcher = MprisWatcher()
        self._search_task: asyncio.Task[None] | None = None
        self._last_track_key: tuple[str, str] | None = None
        self._results: list[LyricsResult] = []
        self._players: dict[str, TrackInfo] = {}
        self._selected_bus_name: str | None = None
        self._plugin_ids = plugin_ids
        self._langs = langs
        self._translated = translated
        self._synced = synced
        self._limit = limit
        self._cache = SearchCache(ttl=cache_ttl)

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            with Vertical(id="left-column"):
                with VerticalScroll(id="metadata-container") as metadata:
                    metadata.border_title = "Song"
                    metadata.can_focus = False
                    yield Static(id="song-title", markup=False)
                    with Grid(id="song-fields"):
                        yield Label("Artist", classes="song-field-label")
                        yield Static(id="song-artist", markup=False)
                        yield Label("Album", classes="song-field-label")
                        yield Static(id="song-album", markup=False)
                        yield Label("Genre", classes="song-field-label")
                        yield Static(id="song-genre", markup=False)
                        yield Label("Length", classes="song-field-label")
                        yield Static(id="song-length", markup=False)
                    with Horizontal(id="song-progress-row"):
                        yield StillProgressBar(
                            id="song-progress", show_eta=False
                        )
                        yield Label(id="song-position")
                player_list = VimOptionList(id="player-list")
                player_list.border_title = "Player"
                yield player_list
                results_list = VimOptionList(id="results-list")
                results_list.border_title = "Results"
                yield results_list
            with Vertical(id="lyrics-container") as lyrics_container:
                lyrics_container.border_title = "Lyrics"
                with TabbedContent(id="lyrics-tabs", initial="lyrics-plain"):
                    with TabPane("Plain", id="lyrics-plain"):
                        with VimVerticalScroll(id="lyrics-plain-scroll"):
                            yield Static(id="lyrics", markup=False)
                    with TabPane("Synced", id="lyrics-synced"):
                        yield SyncedLyricsView(id="lyrics-sync-view")
        with Horizontal(id="status-bar"):
            tui_version = importlib.metadata.version("prismriver-lyrics-tui")
            yield Static(
                f"[dim](≧ᴗ≦)ﾉ♬[/]  Prismriver Lyrics v{tui_version}",
                id="status-bar-app",
            )
            yield Static(
                "<↑↓/j/k> [dim]scroll[/] "
                "[dim]·[/] <g/G> [dim]top/bottom[/] "
                "[dim]·[/] <PgUp/PgDn> [dim]move[/] "
                "[dim]·[/] <Tab> [dim]switch panels[/] "
                "[dim]·[/] <s> [dim]search[/] "
                "[dim]·[/] <t> [dim]theme[/] "
                "[dim]·[/] <q> [dim]exit[/]",
                id="status-bar-hotkeys",
            )

    async def on_mount(self) -> None:
        self._refresh_player_list()
        self._refresh_song_panel()
        self._refresh_lyrics(None)
        self.query_one("#lyrics-plain-scroll", VerticalScroll).focus()
        self.run_worker(self._watch_mpris(), exclusive=True, group="mpris")
        self.set_interval(_POSITION_POLL_INTERVAL, self._tick_position)

    async def _watch_mpris(self) -> None:
        try:
            async for bus_name, track in self._watcher.watch():
                self._handle_track_event(bus_name, track)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.status = f"D-Bus error: {exc}"

    def _handle_track_event(self, bus_name: str, track: TrackInfo) -> None:
        if not self.auto_sync:
            return

        self._refresh_player_list()

        if self._selected_bus_name is None:
            self._select_player(bus_name)
        elif bus_name == self._selected_bus_name:
            self._handle_track(track)

    def _player_option(self, bus_name: str) -> Option:
        track = self._players[bus_name]
        icon = escape(playback_status_emoji(track.playback_status))
        label = f"{track.player}[dim] / {track.player_short}[/dim]"
        return Option(f"{icon} {label}", id=bus_name)

    def _result_label(self, result: LyricsResult, has_synced: bool) -> str:
        if has_synced:
            prefix = (
                "[palegreen bold dim]\\[S] [/]"
                if isinstance(result.lyrics, SyncedLyrics)
                else "    "
            )
        else:
            prefix = ""
        label = prefix + result.source
        if result.lang:
            target = result.lang.upper()
            if result.translation:
                source_lang = (
                    result.original_lang.upper()
                    if result.original_lang
                    else "??"
                )
                suffix = f"{source_lang} -> {target}"
            else:
                suffix = target
            label += f"[dim] \\[{suffix}][/dim]"
        return label

    def _clear_player_list(self, message: str) -> None:
        self._selected_bus_name = None
        self._players = {}
        player_list = self.query_one("#player-list", OptionList)
        player_list.set_options([Option(message, disabled=True)])
        player_list.styles.height = 3

    def _refresh_player_list(self) -> None:
        previous_statuses = {
            bus_name: track.playback_status
            for bus_name, track in self._players.items()
        }
        self._players = self._watcher.known_players()
        bus_names = sorted(
            self._players,
            key=lambda bus_name: self._players[bus_name].player.lower(),
        )

        player_list = self.query_one("#player-list", OptionList)
        if bus_names:
            player_list.set_options(
                self._player_option(bus_name) for bus_name in bus_names
            )
        else:
            player_list.set_options(
                [Option("No player available", disabled=True)]
            )
        # OptionList's own "auto" height ignores CSS min-height when empty,
        # so the box height is set explicitly here instead: shrink to fit
        # the player count (plus 2 rows for the border), never below 1
        # visible content line.
        player_list.styles.height = max(1, len(bus_names)) + 2

        # If the selected player isn't playing, prefer switching to a
        # player that just started playing (whether it's brand new or an
        # existing one that just resumed) over keeping the current
        # selection. Pick the first one alphabetically if several started
        # playing at once.
        selected_status = self._players.get(
            self._selected_bus_name, TrackInfo()
        ).playback_status
        if selected_status != "Playing":
            newly_playing = next(
                (
                    bus_name
                    for bus_name in bus_names
                    if self._players[bus_name].playback_status == "Playing"
                    and previous_statuses.get(bus_name) != "Playing"
                ),
                None,
            )
            if newly_playing is not None:
                self._select_player(newly_playing)
                return

        if self._selected_bus_name in self._players:
            player_list.highlighted = bus_names.index(self._selected_bus_name)
        elif bus_names:
            self._select_player(bus_names[0])
        else:
            self._selected_bus_name = None
            self._handle_track(TrackInfo())

    def _select_player(self, bus_name: str) -> None:
        if not self.auto_sync:
            return

        self._selected_bus_name = bus_name
        player_list = self.query_one("#player-list", OptionList)
        try:
            player_list.highlighted = player_list.get_option_index(bus_name)
        except OptionDoesNotExist:
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
            self.status = "No track playing"
            self._set_results([], placeholder=self.status)
            return

        duration_ms = (
            track.length_us // 1000 if track.length_us is not None else None
        )
        self._search_task = asyncio.create_task(
            self._search_lyrics(track.artist, track.title, duration_ms)
        )

    async def _search_lyrics(
        self, artist: str, title: str, duration_ms: int | None = None
    ) -> None:
        self._set_results([], placeholder="Searching...")

        try:
            results = await search_lyrics(
                artist,
                title,
                duration_ms,
                cache=self._cache,
                langs=self._langs,
                translated=self._translated,
                synced=self._synced,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._set_results([], placeholder=f"Error: {exc}")
            return

        results = filter_results(
            results,
            self._plugin_ids,
            self._langs,
            self._translated,
            self._synced,
        )
        self._set_results(results, placeholder="No lyrics found")
        if results:
            self._refresh_lyrics(results[0])

    def action_no_op(self) -> None:
        """Placeholder used to disable an inherited default keybinding."""

    @work
    async def action_search(self) -> None:
        result = await self.push_screen_wait(SearchDialog())
        if result is not None:
            artist, title = result
            self._handle_manual_search(artist, title)

    def action_resync(self) -> None:
        self.auto_sync = True
        self._last_track_key = None
        self._refresh_player_list()
        if self._selected_bus_name is not None:
            self._handle_track(
                self._players.get(self._selected_bus_name, TrackInfo())
            )

    def _handle_manual_search(self, artist: str, title: str) -> None:
        self.auto_sync = False
        self._last_track_key = None
        self._clear_player_list("Auto-sync disabled")
        self.track = TrackInfo(artist=artist, title=title)

        if self._search_task is not None and not self._search_task.done():
            self._search_task.cancel()
        self._search_task = asyncio.create_task(
            self._search_lyrics(artist, title)
        )

    def _set_results(
        self, results: list[LyricsResult], *, placeholder: str = ""
    ) -> None:
        results = sorted(results, key=lambda result: result.source.lower())
        results, duplicates_hidden = self._dedup_results(results)
        if self._limit is not None:
            results = results[: self._limit]
        self._results = results
        has_synced = any(
            isinstance(result.lyrics, SyncedLyrics) for result in self._results
        )
        option_list = self.query_one("#results-list", OptionList)
        option_list.set_class(not self._results, "placeholder")

        if self._results:
            option_list.set_options(
                Option(self._result_label(result, has_synced))
                for result in self._results
            )
            # Prefer a synced-lyrics result over the alphabetically-first
            # one, since a highlighted current line is a nicer default view
            # than plain text when both are available.
            sync_index = next(
                (
                    i
                    for i, result in enumerate(self._results)
                    if isinstance(result.lyrics, SyncedLyrics)
                ),
                0,
            )
            option_list.highlighted = sync_index
            option_list.border_title = self._results_border_title(
                len(self._results), duplicates_hidden
            )
        else:
            option_list.set_options([Option(placeholder, disabled=True)])
            option_list.border_title = "Results"
            self._refresh_lyrics(None)

    @staticmethod
    def _dedup_results(
        results: list[LyricsResult],
    ) -> tuple[list[LyricsResult], int]:
        """Drop later results whose lyrics exactly match an earlier one
        (e.g. the same source's plain-text result found via two plugin
        aliases, or two sources hosting identical text), keeping the
        first of each group. Returns the deduped list and how many were
        dropped."""
        seen: set[str | SyncedLyrics] = set()
        deduped: list[LyricsResult] = []
        for result in results:
            if result.lyrics in seen:
                continue
            seen.add(result.lyrics)
            deduped.append(result)
        return deduped, len(results) - len(deduped)

    @staticmethod
    def _results_border_title(count: int, duplicates_hidden: int) -> str:
        if not duplicates_hidden:
            return f"Results ({count})"
        suffix = "duplicate" if duplicates_hidden == 1 else "duplicates"
        return f"Results ({count}, {duplicates_hidden} {suffix} hidden)"

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        if event.option_list.id == "results-list":
            if 0 <= event.option_index < len(self._results):
                self._refresh_lyrics(self._results[event.option_index])
        elif event.option_list.id == "player-list":
            if event.option_id and event.option_id != self._selected_bus_name:
                self._select_player(event.option_id)

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option_list.id == "player-list":
            self.query_one("#results-list", OptionList).focus()
        elif event.option_list.id == "results-list":
            self._focus_lyrics()

    def watch_track(self) -> None:
        self._refresh_song_panel()

    def watch_status(self) -> None:
        self._refresh_song_panel()

    def watch_auto_sync(self, auto_sync: bool) -> None:
        player_list = self.query_one("#player-list", OptionList)
        player_list.border_subtitle = (
            None if auto_sync else "<a> [dim]resume auto-sync[/]"
        )

    def _refresh_song_panel(self) -> None:
        t = self.track
        has_track = bool(t.artist or t.title)

        title_widget = self.query_one("#song-title", Static)
        fields = self.query_one("#song-fields", Grid)
        progress_row = self.query_one("#song-progress-row", Horizontal)

        if not has_track:
            title_widget.update(self.status)
            title_widget.set_class(True, "placeholder")
            fields.display = False
            progress_row.display = False
            return

        title_widget.set_class(False, "placeholder")
        title_widget.update(t.title or "-")
        self.query_one("#song-artist", Static).update(t.artist or "-")
        self.query_one("#song-album", Static).update(t.album or "-")
        self.query_one("#song-genre", Static).update(t.genre or "-")
        self.query_one("#song-length", Static).update(
            format_duration(t.length_us)
        )
        fields.display = True
        progress_row.display = True

        total_seconds = t.length_us / 1_000_000 if t.length_us else None
        self.query_one("#song-progress", ProgressBar).update(
            total=total_seconds, progress=0
        )
        self.query_one("#song-position", Label).update(format_duration(0))

    def _refresh_lyrics(self, result: LyricsResult | None) -> None:
        synced = (
            result.lyrics
            if result and isinstance(result.lyrics, SyncedLyrics)
            else None
        )
        lyrics = (
            result.lyrics if result and isinstance(result.lyrics, str) else ""
        )

        plain_scroll = self.query_one("#lyrics-plain-scroll", VerticalScroll)
        sync_view = self.query_one("#lyrics-sync-view", SyncedLyricsView)
        # Switching tabs below hides whichever pane is losing focus, which
        # blurs it without moving focus anywhere else. Track whether lyrics
        # currently hold focus so it can follow onto the pane that becomes
        # active, instead of vanishing.
        had_lyrics_focus = self.focused in (plain_scroll, sync_view)

        plain_widget = self.query_one("#lyrics", Static)
        plain_widget.set_class(not lyrics, "placeholder")
        plain_widget.update(lyrics or "(no lyrics)")
        plain_scroll.scroll_home(animate=False)

        sync_view.set_lines(synced.lines if synced else ())

        tabs = self.query_one("#lyrics-tabs", TabbedContent)
        tabs.active = "lyrics-synced" if synced else "lyrics-plain"

        if had_lyrics_focus:
            self._focus_lyrics()

    def _focus_lyrics(self) -> None:
        tabs = self.query_one("#lyrics-tabs", TabbedContent)
        if tabs.active == "lyrics-synced":
            self.query_one("#lyrics-sync-view", SyncedLyricsView).focus()
        else:
            self.query_one("#lyrics-plain-scroll", VerticalScroll).focus()

    async def _tick_position(self) -> None:
        if self._selected_bus_name is None:
            return

        position_us = await self._watcher.get_position(self._selected_bus_name)
        if position_us is None:
            return

        progress_row = self.query_one("#song-progress-row", Horizontal)
        if progress_row.display:
            self.query_one("#song-progress", ProgressBar).update(
                progress=position_us / 1_000_000
            )
            self.query_one("#song-position", Label).update(
                format_duration(position_us)
            )

        tabs = self.query_one("#lyrics-tabs", TabbedContent)
        if tabs.active == "lyrics-synced":
            self.query_one("#lyrics-sync-view", SyncedLyricsView).highlight(
                position_us // 1000
            )


_VERSION_MESSAGE = (
    "Prismriver Lyrics, version {version}\n"
    "License: MIT\n"
    "https://github.com/anlar/prismriver-lyrics"
)


def run() -> None:
    logging.basicConfig(level=logging.WARNING, handlers=[TextualHandler()])
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
    parser.add_argument(
        "--theme",
        metavar="NAME",
        help="Color theme to use (see --themes for the available names).",
    )
    parser.add_argument(
        "--themes",
        action="store_true",
        help="Print the available color themes and exit.",
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Print the available plugins (id<TAB>name) and exit.",
    )
    parser.add_argument(
        "--filter-plugins",
        metavar="ID[,ID...]",
        help="Only show results from these plugin ids (see --plugins). "
        "Default: all.",
    )
    parser.add_argument(
        "--filter-lang",
        metavar="CODE[,CODE...]",
        help="Only show results tagged with one of these language codes; "
        "use ? to include results with an unknown/untagged language, or "
        "* to include results tagged with any (known) language. "
        "Default: all.",
    )
    parser.add_argument(
        "--filter-translated",
        choices=("0", "1"),
        metavar="{0,1}",
        help="Only show translated (1) or original (0) results. "
        "Default: both.",
    )
    parser.add_argument(
        "--filter-sync",
        choices=("0", "1"),
        metavar="{0,1}",
        help="Only show time-synced (1) or plain-text (0) results. "
        "Default: both.",
    )
    parser.add_argument(
        "--cache-ttl",
        type=parse_duration,
        default=DEFAULT_CACHE_TTL,
        metavar="DURATION",
        help="How long cached results stay valid, e.g. 1w, 1d5h, 90m. "
        "Default: %(default)s.",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        metavar="N",
        help="Limit the number of results shown. Default: unlimited.",
    )
    args = parser.parse_args()

    if args.plugins:
        print_plugins()
        return

    plugin_ids = parse_ids(args.filter_plugins)
    langs = parse_ids(args.filter_lang)
    translated = (
        None if args.filter_translated is None
        else args.filter_translated == "1"
    )
    synced = None if args.filter_sync is None else args.filter_sync == "1"

    if plugin_ids is not None:
        unknown = plugin_ids - {p.id for p in default_plugins()}
        if unknown:
            parser.error(f"unknown plugin id(s): {', '.join(sorted(unknown))}")

    app = PrismriverTuiApp(
        plugin_ids=plugin_ids,
        langs=langs,
        translated=translated,
        synced=synced,
        limit=args.limit,
        cache_ttl=args.cache_ttl,
    )

    if args.themes:
        for name in sorted(app.available_themes):
            print(name)
        return

    if args.theme is not None:
        if args.theme not in app.available_themes:
            print(f"Unknown theme: {args.theme}", file=sys.stderr)
            raise SystemExit(1)
        app.theme = args.theme

    app.run()


if __name__ == "__main__":
    run()
