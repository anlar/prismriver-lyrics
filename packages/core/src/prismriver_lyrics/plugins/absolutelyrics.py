import re

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class AbsoluteLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from absolutelyrics.com.

    URL shape: http://www.absolutelyrics.com/lyrics/view/{artist}/{title},
    where artist/title are snake_cased (lowercased, non-alphanumeric runs
    collapsed to a single underscore).
    """

    name = "absolutelyrics.com"

    def _slug(self, value: str) -> str:
        return _NON_ALNUM.sub("_", value.lower()).strip("_")

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        return f"http://www.absolutelyrics.com/lyrics/view/{artist_slug}/{title_slug}"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> LyricsResult | None:
        url = self.build_url(artist, title)
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one("p#view_lyrics")
        if container is None:
            return None

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return None

        return LyricsResult(source=self.name, url=url, lyrics=lyrics)
