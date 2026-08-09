from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label


class ConfirmDialog(ModalScreen[bool]):
    """Modal that asks a yes/no question.

    Dismisses with True on confirm, False on cancel.
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog") as dialog:
            dialog.border_title = "Confirm"
            dialog.border_subtitle = "<y> [dim]yes[/] · <n>/<Esc> [dim]no[/]"
            yield Label(self._message, id="confirm-message")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
