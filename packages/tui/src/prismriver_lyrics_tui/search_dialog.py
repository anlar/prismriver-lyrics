from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label


class SearchDialog(ModalScreen[tuple[str, str] | None]):
    """Modal for manually searching lyrics by title and artist.

    Dismisses with `(artist, title)` on submit, or `None` on cancel.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog") as dialog:
            dialog.border_title = "Search"
            dialog.border_subtitle = "<Enter> search · <Esc> cancel"
            yield Label("Title")
            yield Input(placeholder="Song title", id="search-title")
            yield Label("Artist")
            yield Input(placeholder="Artist name", id="search-artist")

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
