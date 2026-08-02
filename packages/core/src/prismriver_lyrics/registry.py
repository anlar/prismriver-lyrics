import importlib
import inspect
import logging
import pkgutil

from prismriver_lyrics import plugins as plugins_package
from prismriver_lyrics.models import LyricsResult, SyncedLyrics
from prismriver_lyrics.plugins.base import ANY_LANG, UNKNOWN_LANG, LyricsPlugin

logger = logging.getLogger(__name__)


def _discover_plugin_classes() -> list[type[LyricsPlugin]]:
    """Import every module in the `plugins` package and collect the
    concrete LyricsPlugin subclasses each one defines (not re-exported
    ones, so importing e.g. LyricsPlugin itself into a plugin module
    doesn't register it). A module that fails to import is logged and
    skipped rather than taking down discovery for every other plugin."""
    classes: list[type[LyricsPlugin]] = []
    for module_info in pkgutil.iter_modules(plugins_package.__path__):
        if module_info.name == "base":
            continue
        try:
            module = importlib.import_module(
                f"{plugins_package.__name__}.{module_info.name}"
            )
        except Exception:
            logger.warning(
                "failed to import plugin module %r", module_info.name,
                exc_info=True,
            )
            continue
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
    if not plugins:
        return
    width = max(len(plugin.id) for plugin in plugins)
    for plugin in plugins:
        print(f"{plugin.id:<{width}}  {plugin.name}")


def parse_ids(value: str | None) -> frozenset[str] | None:
    """Split a comma-separated CLI value into a frozenset, or None if
    value is None (no filter given)."""
    if value is None:
        return None
    return frozenset(v.strip() for v in value.split(",") if v.strip())


def filter_cache_key(
    langs: frozenset[str] | None = None,
    translated: bool | None = None,
    synced: bool | None = None,
) -> str | None:
    """A stable string identifying this lang/translated/synced filter
    combination, for SearchCache's `filter_key` — so a filtered search
    (which may only cover a hint-narrowed subset of plugins) is cached
    separately from the plain, every-plugin (artist, title) entry rather
    than shadowing or being shadowed by it. Returns None when every axis
    is unconstrained, so callers can use that directly to mean "no
    filter, use the plain cache entry".
    """
    if langs is None and translated is None and synced is None:
        return None
    lang_part = ",".join(sorted(langs)) if langs is not None else ""
    return f"lang={lang_part}|translated={translated}|synced={synced}"


def _lang_hint_matches(plugin_langs: set[str], langs: frozenset[str]) -> bool:
    """Whether a plugin whose results may carry any of `plugin_langs`
    (see LyricsPlugin.lang) could produce something the `langs` filter
    would keep. Three ways to match: the plugin's hint says it varies
    (ANY_LANG, e.g. musixmatch) and so could tag anything, including a
    code the caller asked for; a hint code is directly requested (this
    also covers UNKNOWN_LANG, i.e. explicitly requesting untagged
    results); or the caller asked for ANY_LANG ("any defined language")
    and the plugin can tag at least one real code (not just
    UNKNOWN_LANG)."""
    return (
        ANY_LANG in plugin_langs
        or bool(plugin_langs & langs)
        or (
            ANY_LANG in langs
            and bool(plugin_langs - {UNKNOWN_LANG})
        )
    )


def filter_plugins(
    plugins: list[LyricsPlugin],
    langs: frozenset[str] | None = None,
    translated: bool | None = None,
    synced: bool | None = None,
) -> list[LyricsPlugin]:
    """Narrow plugins down to those whose lang/translated/sync hints
    (LyricsPlugin class attributes) don't already rule out ever
    satisfying the given constraints, so a plugin that provably can't
    match doesn't have to be queried over the network at all. None means
    "no constraint" for that axis, same as filter_results().

    Hints are advisory, not authoritative: a plugin kept by this filter
    may still end up contributing nothing (or nothing matching) once its
    actual results are checked by filter_results() afterward. This
    function should never discard a plugin that filter_results() could
    still have kept results from.
    """
    return [
        plugin
        for plugin in plugins
        if (
            langs is None
            or _lang_hint_matches(set(plugin.lang), langs)
        )
        and (translated is not True or plugin.translated)
        and (synced is not True or plugin.sync)
    ]


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
    LyricsResult.lang: UNKNOWN_LANG ("?") stands in for lang=None so
    untagged results can be included/excluded explicitly, and ANY_LANG
    ("*") matches any *tagged* (non-None) lang regardless of the actual
    code, alongside whatever specific codes are also in `langs`. synced
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
        and (
            langs is None
            or (r.lang or UNKNOWN_LANG) in langs
            or (ANY_LANG in langs and r.lang is not None)
        )
        and (translated is None or r.translation == translated)
        and (
            synced is None
            or isinstance(r.lyrics, SyncedLyrics) == synced
        )
    ]
