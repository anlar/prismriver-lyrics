from rich.style import Style
from textual.app import ComposeResult, RenderResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import OptionList, ProgressBar
from textual.widgets._progress_bar import Bar, ETAStatus, PercentageStatus


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


class _StillBar(Bar):
    """A Bar that never animates, including while indeterminate: it renders
    as a fixed, fully-highlighted bar instead of sweeping back and forth."""

    def watch_percentage(self, percentage: float | None) -> None:
        self.auto_refresh = None

    def render_indeterminate(self) -> RenderResult:
        bar_style = self.get_component_rich_style("bar--indeterminate")
        return self.bar_renderable(
            highlight_range=(0, self.size.width),
            highlight_style=Style.from_color(bar_style.color),
            background_style=Style.from_color(bar_style.bgcolor),
        )


class StillProgressBar(ProgressBar):
    """A ProgressBar whose indeterminate state renders as a static bar
    instead of the default sweeping animation."""

    def compose(self) -> ComposeResult:
        if self.show_bar:
            yield (
                _StillBar(
                    id="bar",
                    clock=self._clock,
                    bar_renderable=self.BAR_RENDERABLE,
                )
                .data_bind(ProgressBar.percentage)
                .data_bind(ProgressBar.gradient)
            )
        if self.show_percentage:
            yield PercentageStatus(id="percentage").data_bind(
                ProgressBar.percentage
            )
        if self.show_eta:
            yield ETAStatus(id="eta").data_bind(eta=ProgressBar._display_eta)
