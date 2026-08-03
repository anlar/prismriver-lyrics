import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify


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

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist, sep="_")
        title_slug = slugify(title, sep="_")
        return f"http://alphabetlyrics.com/lyrics/{artist_slug}/{title_slug}.html"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        soup = await self.fetch_soup(client, url)
        if soup is None:
            return []

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
        return "\n".join(lines).strip()
