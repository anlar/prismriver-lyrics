from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label


class SearchDialog(ModalScreen[tuple[str, str] | None]):
    """Modal for manually searching lyrics by title and artist.

    `artist`/`title` pre-fill the inputs with the track the app is already
    showing, so the common case (retrying the current song with a tweak) is
    an edit rather than a retype. Both inputs select their contents on
    focus, so typing still replaces the pre-filled value outright.

    Dismisses with `(artist, title)` on submit, or `None` on cancel.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, artist: str = "", title: str = "") -> None:
        super().__init__()
        self._artist = artist
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog") as dialog:
            dialog.border_title = "Search"
            dialog.border_subtitle = "<Enter> search · <Esc> cancel"
            yield Label("Title")
            yield Input(
                value=self._title,
                placeholder="Song title",
                id="search-title",
            )
            yield Label("Artist")
            yield Input(
                value=self._artist,
                placeholder="Artist name",
                id="search-artist",
            )

    def on_mount(self) -> None:
        self.query_one("#search-title", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        title = self.query_one("#search-title", Input).value.strip()
        artist = self.query_one("#search-artist", Input).value.strip()
        if title and artist:
            self.dismiss((artist, title))
        elif not title:
            self.query_one("#search-title", Input).focus()
        else:
            self.query_one("#search-artist", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)
