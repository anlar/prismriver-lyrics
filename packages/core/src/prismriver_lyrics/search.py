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
) -> LyricsResult | None:
    """Query every plugin concurrently and return the first successful hit.

    Plugins that error out or find nothing are ignored in favor of whichever
    other plugin answers next; remaining in-flight requests are cancelled as
    soon as a result is available.
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
        try:
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                except Exception:
                    continue
                if result is not None:
                    return result
            return None
        finally:
            for task in tasks:
                task.cancel()
