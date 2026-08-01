import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import APP_USER_AGENT, LyricsPlugin
from prismriver_lyrics.plugins.lrclib import parse_synced_lyrics

_API_URL = "https://api.synclrc.dev/lyrics"
_HOMEPAGE_URL = "https://synclrc.dev"


class SyncLrcPlugin(LyricsPlugin):
    """Fetches lyrics from synclrc.dev's public API.

    Requests lyrics by artist/track and returns a plain-text LyricsResult,
    plus a second LyricsResult whose `lyrics` is a SyncedLyrics when the
    source also has line timestamps. The word-level `karaoke` field isn't
    used, since SyncedLyrics only tracks one timestamp per line and its
    `synced` field already provides that at line granularity.
    """

    name = "synclrc.dev"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        response = await client.get(
            _API_URL,
            params={"track": title, "artist": artist},
            headers={"User-Agent": APP_USER_AGENT},
        )
        if response.status_code != 200:
            return []

        data = response.json()
        if data.get("instrumental"):
            return []

        lyrics = (data.get("plain") or "").strip()
        synced_raw = (data.get("synced") or "").strip()
        synced = parse_synced_lyrics(synced_raw) if synced_raw else None

        if not lyrics and not synced:
            return []

        results = []
        if lyrics:
            results.append(
                LyricsResult(source=self.name, url=_HOMEPAGE_URL, lyrics=lyrics)
            )
        if synced:
            results.append(
                LyricsResult(source=self.name, url=_HOMEPAGE_URL, lyrics=synced)
            )
        return results
