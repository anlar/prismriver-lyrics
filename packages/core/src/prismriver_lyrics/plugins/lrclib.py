import re

import httpx

from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics
from prismriver_lyrics.plugins.base import APP_USER_AGENT, LyricsPlugin

_SEARCH_URL = "https://lrclib.net/api/search"

# LRC timestamp tag, e.g. "[01:02.53]"; a line may carry more than one (a
# line repeated at several points in the song).
_TIMESTAMP_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_synced_lyrics(text: str) -> SyncedLyrics | None:
    """Parse lrclib.net's LRC-format `syncedLyrics` into a SyncedLyrics,
    or None if it carries no timestamped lines (e.g. empty, or metadata-only
    tags like `[ar:...]`)."""
    lines: list[SyncedLine] = []

    for raw_line in text.splitlines():
        timestamps = list(_TIMESTAMP_RE.finditer(raw_line))
        if not timestamps:
            continue

        content = raw_line[timestamps[-1].end() :].strip()
        for match in timestamps:
            minutes, seconds = match.groups()
            time_ms = int(minutes) * 60_000 + round(float(seconds) * 1000)
            lines.append(SyncedLine(time_ms=time_ms, text=content))

    if not lines:
        return None

    lines.sort(key=lambda line: line.time_ms)
    return SyncedLyrics(lines=tuple(lines))


class LrcLibPlugin(LyricsPlugin):
    """Fetches lyrics from lrclib.net's public API.

    Searches by artist_name/track_name and, for the first non-instrumental
    result carrying lyrics, returns a plain-text LyricsResult and, if the
    source also has line timestamps, a second LyricsResult whose `lyrics`
    is a SyncedLyrics instead.
    """

    name = "lrclib.net"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        response = await client.get(
            _SEARCH_URL,
            params={"track_name": title, "artist_name": artist},
            headers={"User-Agent": APP_USER_AGENT},
        )
        if response.status_code != 200:
            return []

        for track in response.json():
            if track.get("instrumental"):
                continue

            lyrics = (track.get("plainLyrics") or "").strip()
            synced_raw = (track.get("syncedLyrics") or "").strip()
            synced = parse_synced_lyrics(synced_raw) if synced_raw else None

            if not lyrics and not synced:
                continue

            url = f"https://lrclib.net/api/get/{track['id']}"
            results = []
            if lyrics:
                results.append(
                    LyricsResult(source=self.name, url=url, lyrics=lyrics)
                )
            if synced:
                results.append(
                    LyricsResult(source=self.name, url=url, lyrics=synced)
                )
            return results

        return []
