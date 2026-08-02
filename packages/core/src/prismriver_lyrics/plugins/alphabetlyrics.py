import re

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class AlphabetLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from alphabetlyrics.com.

    URL shape: http://alphabetlyrics.com/lyrics/{artist}/{title}.html,
    where artist/title are snake_cased (lowercased, non-alphanumeric runs
    collapsed to a single underscore).

    The page has several div.lyrics elements (nav/heading noise plus the
    real one); the real one is identified by having <br> line breaks. Its
    actual text is spread across many small per-word/phrase <div>s rather
    than flat text, so (like genius.com) this uses get_text()-based
    extraction instead of the shared LyricsPlugin.extract_lyrics, which
    would otherwise drop all of that nested div content. <script> tags are
    stripped first since get_text() would otherwise leak their JS content.
    """

    id = "alphabetlyrics"
    name = "AlphabetLyrics"

    def _slug(self, value: str) -> str:
        return _NON_ALNUM.sub("_", value.lower()).strip("_")

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        return f"http://alphabetlyrics.com/lyrics/{artist_slug}/{title_slug}.html"

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
        container = self._find_lyrics_container(soup)
        if container is None:
            return []

        lyrics = self._extract(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

    @staticmethod
    def _find_lyrics_container(soup: BeautifulSoup) -> Tag | None:
        container = None
        best_br_count = 0
        for div in soup.select("div.lyrics"):
            br_count = len(div.find_all("br"))
            if br_count > best_br_count:
                best_br_count = br_count
                container = div
        return container

    @staticmethod
    def _extract(container: Tag) -> str:
        for script in container.find_all("script"):
            script.decompose()
        for br in container.find_all("br"):
            br.replace_with("\n")

        lines = [line.strip() for line in container.get_text().splitlines()]
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
        return "\n".join(lines)
