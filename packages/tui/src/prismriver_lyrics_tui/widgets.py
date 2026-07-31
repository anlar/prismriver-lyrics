from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import OptionList


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
