import asyncio
import logging

import httpx

from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.registry import (
    default_plugins,
    filter_cache_key,
    filter_plugins,
    filter_results,
)
from prismriver_lyrics.util import (
    DEFAULT_CACHE_TTL,
    parse_duration,
    strip_title_postfix,
)

logger = logging.getLogger(__name__)


class SearchFailedError(Exception):
    """Raised when every queried plugin errored out (e.g. no network),
    as opposed to plugins successfully running and simply finding
    nothing."""


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)

_default_cache = SearchCache(ttl=parse_duration(DEFAULT_CACHE_TTL))


async def search_lyrics(
    artist: str,
    title: str,
    duration_ms: int | None = None,
    plugins: list[LyricsPlugin] | None = None,
    timeout: float = 10.0,
    use_cache: bool = True,
    cache: SearchCache | None = None,
    langs: frozenset[str] | None = None,
    translated: bool | None = None,
    synced: bool | None = None,
) -> list[LyricsResult]:
    """Query every plugin concurrently and return every successful hit.

    Waits for all plugins to finish rather than racing them. Plugins that
    error out or find nothing are silently excluded. Results are returned
    in the same order as `plugins` (or `default_plugins()`), not
    completion order, so the ranking is stable across runs.

    `duration_ms` (the track's known length, if any) is passed through to
    plugins that can use it to disambiguate same-titled results (e.g. a
    remix returned alongside the original); most plugins ignore it.

    `langs`/`translated`/`synced` (see registry.filter_plugins() and
    filter_results()) are optional; when any is given, the search only
    queries the subset of `plugins` whose lang/translated/sync hints
    could satisfy them, and the result cache lookup/write uses a
    filter-specific key (registry.filter_cache_key()) instead of the
    plain one, so a search that skipped plugins on hints never shadows
    or gets shadowed by the plain, every-plugin entry for the same
    (artist, title). Cache order for a filtered search: try the
    filter-specific entry; then the plain entry, filtered in memory (no
    request needed); only on a full miss is a live search made, of just
    the hint-narrowed plugins, cached under the filter-specific key.

    Results are cached on disk keyed by (artist, title) (see above for
    the filtered case); pass `use_cache=False` to force a fresh search.

    `title` has any known noise postfix (e.g. "(Official Music Video)")
    stripped via `util.strip_title_postfix()` before it's used for the
    cache key or plugin queries.
    """
    title = strip_title_postfix(title)

    if cache is None:
        cache = _default_cache

    filter_key = filter_cache_key(langs, translated, synced)

    if use_cache:
        cached = await cache.aget(artist, title, filter_key=filter_key)
        if cached is not None:
            return cached
        if filter_key is not None:
            full_cached = await cache.aget(artist, title)
            if full_cached is not None:
                return filter_results(
                    full_cached,
                    langs=langs,
                    translated=translated,
                    synced=synced,
                )

    if plugins is None:
        plugins = default_plugins()
    if filter_key is not None:
        plugins = filter_plugins(plugins, langs, translated, synced)

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

    if plugins and all(isinstance(r, BaseException) for r in gathered):
        raise SearchFailedError(f"all {len(plugins)} plugin(s) failed")

    results = [
        result
        for plugin_results in gathered
        if isinstance(plugin_results, list)
        for result in plugin_results
    ]

    if filter_key is not None:
        results = filter_results(
            results, langs=langs, translated=translated, synced=synced
        )

    if use_cache:
        await cache.aset(artist, title, results, filter_key=filter_key)

    return results
