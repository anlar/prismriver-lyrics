import re
import unicodedata

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# The site occasionally has a stray extra <br> in a verse block (e.g. 3 in a
# row instead of the usual 2), which extract_lyrics() faithfully renders as
# multiple blank lines; collapse any such run down to a single blank line.
_MULTI_BLANK_LINE = re.compile(r"\n{3,}")


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
        soup = await self.fetch_soup(client, url, follow_redirects=False)
        if soup is None:
            return []

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

        lyrics = _MULTI_BLANK_LINE.sub("\n\n", "\n\n".join(parts))
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
