import asyncio
import logging

import httpx

from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.registry import default_plugins

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

_default_cache = SearchCache()


async def search_lyrics(
    artist: str,
    title: str,
    duration_ms: int | None = None,
    plugins: list[LyricsPlugin] | None = None,
    timeout: float = 10.0,
    use_cache: bool = True,
    cache: SearchCache | None = None,
) -> list[LyricsResult]:
    """Query every plugin concurrently and return every successful hit.

    Waits for all plugins to finish rather than racing them. Plugins that
    error out or find nothing are silently excluded. Results are returned
    in the same order as `plugins` (or `default_plugins()`), not
    completion order, so the ranking is stable across runs.

    `duration_ms` (the track's known length, if any) is passed through to
    plugins that can use it to disambiguate same-titled results (e.g. a
    remix returned alongside the original); most plugins ignore it.

    Results are cached on disk keyed by (artist, title); pass
    `use_cache=False` to force a fresh search.
    """
    if cache is None:
        cache = _default_cache

    if use_cache:
        cached = await cache.aget(artist, title)
        if cached is not None:
            return cached

    if plugins is None:
        plugins = default_plugins()

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        tasks = [
            asyncio.create_task(
                plugin.search(client, artist, title, duration_ms)
            )
            for plugin in plugins
        ]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

    for plugin, plugin_results in zip(plugins, gathered, strict=True):
        if isinstance(plugin_results, BaseException):
            logger.warning(
                "%s search failed: %r", plugin.id, plugin_results
            )

    results = [
        result
        for plugin_results in gathered
        if isinstance(plugin_results, list)
        for result in plugin_results
    ]

    if use_cache:
        await cache.aset(artist, title, results)

    return results
