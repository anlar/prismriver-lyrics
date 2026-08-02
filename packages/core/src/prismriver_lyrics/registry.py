import importlib
import inspect
import pkgutil

from prismriver_lyrics import plugins as plugins_package
from prismriver_lyrics.models import LyricsResult, SyncedLyrics
from prismriver_lyrics.plugins.base import LyricsPlugin


def _discover_plugin_classes() -> list[type[LyricsPlugin]]:
    """Import every module in the `plugins` package and collect the
    concrete LyricsPlugin subclasses each one defines (not re-exported
    ones, so importing e.g. LyricsPlugin itself into a plugin module
    doesn't register it)."""
    classes: list[type[LyricsPlugin]] = []
    for module_info in pkgutil.iter_modules(plugins_package.__path__):
        if module_info.name == "base":
            continue
        module = importlib.import_module(
            f"{plugins_package.__name__}.{module_info.name}"
        )
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                obj.__module__ == module.__name__
                and issubclass(obj, LyricsPlugin)
                and not inspect.isabstract(obj)
            ):
                classes.append(obj)
    return classes


def default_plugins() -> list[LyricsPlugin]:
    """Plugins queried by default, one instance per lyrics source.

    Auto-discovered from the `plugins` package, so adding a new plugin
    module is enough to register it here; sorted by id for a result order
    that's stable across runs.
    """
    plugins = [cls() for cls in _discover_plugin_classes()]
    return sorted(plugins, key=lambda plugin: plugin.id)


def print_plugins() -> None:
    """Print the available plugins as id/name columns, one per line,
    the id column padded to align with the longest id."""
    plugins = default_plugins()
    width = max(len(plugin.id) for plugin in plugins)
    for plugin in plugins:
        print(f"{plugin.id:<{width}}  {plugin.name}")


def parse_ids(value: str | None) -> frozenset[str] | None:
    """Split a comma-separated CLI value into a frozenset, or None if
    value is None (no filter given)."""
    if value is None:
        return None
    return frozenset(v.strip() for v in value.split(",") if v.strip())


# langs filter token standing in for LyricsResult.lang=None (language not
# tagged/unknown), since the real value isn't a valid lang code to type.
UNKNOWN_LANG = "?"


def filter_results(
    results: list[LyricsResult],
    plugin_ids: frozenset[str] | None = None,
    langs: frozenset[str] | None = None,
    translated: bool | None = None,
    synced: bool | None = None,
) -> list[LyricsResult]:
    """Keep only results matching every given constraint; None means "no
    constraint" for that axis. plugin_ids is matched by resolving ids to
    their plugin's `name` and comparing against LyricsResult.source,
    since results don't carry the id directly. langs matches against
    LyricsResult.lang, with UNKNOWN_LANG ("?") standing in for lang=None
    so untagged results can be included/excluded explicitly. synced
    matches whether LyricsResult.lyrics is time-synced (a SyncedLyrics)
    rather than plain text."""
    names = (
        None
        if plugin_ids is None
        else {p.name for p in default_plugins() if p.id in plugin_ids}
    )
    return [
        r
        for r in results
        if (names is None or r.source in names)
        and (langs is None or (r.lang or UNKNOWN_LANG) in langs)
        and (translated is None or r.translation == translated)
        and (
            synced is None
            or isinstance(r.lyrics, SyncedLyrics) == synced
        )
    ]
