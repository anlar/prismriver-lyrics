import importlib
import inspect
import pkgutil

from prismriver_lyrics import plugins as plugins_package
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
