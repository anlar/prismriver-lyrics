import asyncio

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.registry import default_plugins

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


async def search_lyrics(
    artist: str,
    title: str,
    plugins: list[LyricsPlugin] | None = None,
    timeout: float = 10.0,
) -> list[LyricsResult]:
    """Query every plugin concurrently and return every successful hit.

    Waits for all plugins to finish rather than racing them. Plugins that
    error out or find nothing are silently excluded. Results are returned
    in the same order as `plugins` (or `default_plugins()`), not
    completion order, so the ranking is stable across runs.
    """
    if plugins is None:
        plugins = default_plugins()

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        tasks = [
            asyncio.create_task(plugin.search(client, artist, title))
            for plugin in plugins
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    return [
        result
        for plugin_results in results
        if isinstance(plugin_results, list)
        for result in plugin_results
    ]
