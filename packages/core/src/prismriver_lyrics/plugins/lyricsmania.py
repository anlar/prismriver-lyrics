import re

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class LyricsManiaPlugin(LyricsPlugin):
    """Fetches lyrics from lyricsmania.com.

    URL shape: https://www.lyricsmania.com/{title}_lyrics_{artist}.html,
    falling back to https://www.lyricsmania.com/{title}_{artist}.html for
    songs published under the older naming pattern. artist/title are
    snake_cased (lowercased, non-alphanumeric runs collapsed to a single
    underscore).
    """

    id = "lyricsmania"
    name = "LyricsMania"

    def _slug(self, value: str) -> str:
        return _NON_ALNUM.sub("_", value.lower()).strip("_")

    def build_url(self, artist: str, title: str) -> str:
        return self._build_url(artist, title, with_lyrics=True)

    def _build_url(self, artist: str, title: str, *, with_lyrics: bool) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        middle = "_lyrics_" if with_lyrics else "_"
        return f"https://www.lyricsmania.com/{title_slug}{middle}{artist_slug}.html"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        response = None
        url = ""
        for with_lyrics in (True, False):
            url = self._build_url(artist, title, with_lyrics=with_lyrics)
            response = await client.get(url)
            if response.status_code == 200:
                break
        if response is None or response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one(".lyrics-body")
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
