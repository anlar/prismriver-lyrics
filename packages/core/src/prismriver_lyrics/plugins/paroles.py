import re
import unicodedata

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class ParolesPlugin(LyricsPlugin):
    """Fetches lyrics from paroles.net.

    URL shape: https://www.paroles.net/{artist}/paroles-{title}, where
    artist/title are independently deburred (accents stripped) and
    kebab-cased. The lyrics live in <article class="lyrics">, split across
    several unmarked (no class/id) <div> verse blocks separated by empty
    spacer divs; other children (heading, trailing ad widget) carry a
    class and are skipped.
    """

    id = "paroles"
    name = "Paroles.net"

    def _slug(self, value: str) -> str:
        deburred = "".join(
            c
            for c in unicodedata.normalize("NFKD", value)
            if not unicodedata.combining(c)
        )
        return _NON_ALNUM.sub("-", deburred.lower()).strip("-")

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        return f"https://www.paroles.net/{artist_slug}/paroles-{title_slug}"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        # A missing song redirects elsewhere rather than 404ing.
        response = await client.get(url, follow_redirects=False)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.select_one("article.lyrics")
        if container is None:
            return []

        parts = []
        for div in container.find_all("div", recursive=False):
            if div.get("class"):
                continue
            text = self.extract_lyrics(div)
            if text:
                parts.append(text)

        lyrics = "\n\n".join(parts)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
