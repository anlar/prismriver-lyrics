from urllib.parse import quote

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin


class LyricsOvhPlugin(LyricsPlugin):
    """Fetches lyrics from the lyrics.ovh API.

    URL shape: https://api.lyrics.ovh/v1/{artist}/{title}, a small JSON API
    ({"lyrics": "..."}).
    """

    id = "lyricsovh"
    name = "Lyrics.ovh"

    def build_url(self, artist: str, title: str) -> str:
        return f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return []

        lyrics = response.json().get("lyrics", "").strip()
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
