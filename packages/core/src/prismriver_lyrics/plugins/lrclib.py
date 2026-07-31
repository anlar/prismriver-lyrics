import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import APP_USER_AGENT, LyricsPlugin

_SEARCH_URL = "https://lrclib.net/api/search"


class LrcLibPlugin(LyricsPlugin):
    """Fetches lyrics from lrclib.net's public API.

    Searches by artist_name/track_name and returns the first non-instrumental
    result that has plain lyrics.
    """

    name = "lrclib.net"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
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
            if not lyrics:
                continue
            url = f"https://lrclib.net/api/get/{track['id']}"
            return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

        return []
