import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import UNKNOWN_LANG, LyricsPlugin

_SEARCH_URL = "https://lyrsense.com/search"
_BASE_URL = "https://lyrsense.com"


class LyrsensePlugin(LyricsPlugin):
    """Fetches lyrics and a Russian translation from lyrsense.com.

    The site doesn't expose a deterministic artist/title -> URL slug (song
    paths sometimes carry an extra disambiguating suffix, e.g.
    /bee_gees/stayin_alive_bg), so this searches by title first and picks
    the result whose artist matches, then scrapes that song's page. Each
    lyric line is laid out as a `div.songTextLine` holding a
    `span.songTextLine__original` and a matching
    `span.songTextLine__translation`; blank `div.songTextLine--empty`
    entries mark stanza breaks.
    """

    id = "lyrsense"
    name = "Lyrsense"

    # Original results are untagged; translations are always into Russian.
    lang = [UNKNOWN_LANG, "ru"]
    translated = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        song_url = await self._find_song_url(client, artist, title)
        if song_url is None:
            return []

        response = await client.get(song_url)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        lines = soup.select("#songFlexLines > div")
        if not lines:
            return []

        original = self._extract_column(lines, "songTextLine__original")
        translation = self._extract_column(lines, "songTextLine__translation")

        results: list[LyricsResult] = []
        if original:
            results.append(
                LyricsResult(source=self.name, url=song_url, lyrics=original)
            )
        if translation:
            results.append(
                LyricsResult(
                    source=self.name,
                    url=song_url,
                    lyrics=translation,
                    translation=True,
                    lang="ru",
                )
            )
        return results

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        response = await client.get(_SEARCH_URL, params={"s": title})
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select("ul[id^='song_'][id$='List'] li.element"):
            link = item.find("a")
            artist_span = item.find("span")
            if link is None or artist_span is None:
                continue
            if (
                link.get_text(strip=True).lower() == title.lower()
                and artist_span.get_text(strip=True).lower() == artist.lower()
            ):
                href = link.get("href")
                if href:
                    return _BASE_URL + href
        return None

    @staticmethod
    def _extract_column(lines: list[Tag], css_class: str) -> str:
        text_lines = []
        for line in lines:
            span = line.select_one(f".{css_class}")
            if span is None:
                text_lines.append("")
                continue
            # <sup> holds a footnote reference number (e.g. a translator's
            # note marker), not lyric text.
            for sup in span.find_all("sup"):
                sup.decompose()
            text_lines.append(span.get_text(strip=True))
        return "\n".join(text_lines).strip()
