import re

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")


class SeekALyricPlugin(LyricsPlugin):
    """Fetches lyrics from seekalyric.com.

    URL shape: https://www.seekalyric.com/song/{Artist}/{Title}, where
    artist/title are split into words and each word is title-cased
    (capitalized, not lowercased), joined by underscores.
    """

    name = "seekalyric.com"

    def _slug(self, value: str) -> str:
        words = [w for w in _NON_ALNUM.split(value.strip()) if w]
        return "_".join(w.capitalize() for w in words)

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        return f"https://www.seekalyric.com/song/{artist_slug}/{title_slug}"

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

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one("#contentt")
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
