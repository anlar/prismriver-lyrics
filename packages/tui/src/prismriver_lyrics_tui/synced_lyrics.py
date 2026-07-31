from prismriver_lyrics.models import SyncedLine
from textual.widgets import Static

from prismriver_lyrics_tui.widgets import VimVerticalScroll


class SyncedLyricsView(VimVerticalScroll):
    """Shows synchronized lyrics one line per widget, highlighting whichever
    line is current for a given playback position and keeping it centered
    in view."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._lines: tuple[SyncedLine, ...] = ()
        self._current_index: int | None = None

    def set_lines(self, lines: tuple[SyncedLine, ...]) -> None:
        """Replace the displayed lines and reset the highlight."""
        self._lines = lines
        self._current_index = None
        self.remove_children()
        if lines:
            self.mount_all(
                Static(line.text or " ", markup=False) for line in lines
            )
        self.scroll_home(animate=False)

    def highlight(self, position_ms: int) -> None:
        """Mark the line current at `position_ms` and scroll it to the
        center of the view. A no-op if that's already the current line."""
        if not self._lines:
            return

        index = 0
        for i, line in enumerate(self._lines):
            if line.time_ms > position_ms:
                break
            index = i

        if index == self._current_index:
            return

        children = self.children
        if self._current_index is not None:
            children[self._current_index].remove_class("current-line")

        self._current_index = index
        current_widget = children[index]
        current_widget.add_class("current-line")
        self.scroll_to_widget(current_widget, animate=True, center=True)
