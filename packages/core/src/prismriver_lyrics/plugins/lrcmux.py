import httpx

from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics
from prismriver_lyrics.plugins.base import APP_USER_AGENT, LyricsPlugin

_API_URL = "https://api.lrcmux.dev/get"
_HOMEPAGE_URL = "https://lrcmux.dev"


class LrcmuxPlugin(LyricsPlugin):
    """Fetches lyrics from lrcmux.dev, an aggregator that queries multiple
    providers (Genius, KuGou, Musixmatch, NetEase, YouTube Music) and
    returns the best available result.

    Requests the structured `json` format and returns a plain-text
    LyricsResult, plus a second LyricsResult carrying SyncedLyrics when the
    best available result is line- or word-level synced (word-level timing
    is discarded down to one timestamp per line, since that's all
    SyncedLyrics represents).
    """

    id = "lrcmux"
    name = "LRCMux"

    sync = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        response = await client.get(
            _API_URL,
            params={"artist": artist, "title": title, "format": "json"},
            headers={"User-Agent": APP_USER_AGENT},
        )
        if response.status_code != 200:
            return []

        data = response.json()
        meta = data.get("meta") or {}
        if meta.get("instrumental"):
            return []

        lines = data.get("lines") or []
        lyrics = "\n".join(line["text"] for line in lines).strip()
        if not lyrics:
            return []

        url = (meta.get("source") or {}).get("url") or _HOMEPAGE_URL
        results = [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

        if meta.get("level") in ("word", "line"):
            # Undocumented unit for JSONLine.start/end; word-level timing
            # implies sub-second precision, so milliseconds (the
            # convention used elsewhere by this app) is assumed.
            synced = SyncedLyrics(
                lines=tuple(
                    SyncedLine(time_ms=line["start"], text=line["text"])
                    for line in lines
                )
            )
            results.append(
                LyricsResult(source=self.name, url=url, lyrics=synced)
            )

        return results
