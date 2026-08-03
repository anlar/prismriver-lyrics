import urllib.parse

import httpx
from bs4 import BeautifulSoup, Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify

_BASE_URL = "http://www.darklyrics.com"


class DarkLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from darklyrics.com, a metal-focused lyrics archive.

    The site is HTTP-only, and has no query-based search, so this uses a
    two-step index-then-page lookup:

    1. An artist's index page, `/{first_letter}/{artist_slug}.html`
       (e.g. `/m/metallica.html` for Metallica), lists every one of that
       artist's albums as a `div.album`: an `<h2>` album heading followed
       by one `<a href="../lyrics/{artist}/{album}.html#{N}">{Track
       Title}</a>` per track. The link text is matched case-insensitively
       against the requested title to get the album page URL and that
       track's anchor number.
    2. The album page has every track's lyrics concatenated in one
       `div.lyrics`, each track headed by `<h3><a name="{N}">{N}. {Track
       Title}</a></h3>` followed by an `<i>[Writer / Credits]</i>` line
       and then the lyrics themselves, `<br />`-separated. The target
       track's slice is isolated by cutting the container down to just
       the nodes between its `<h3>` and the next one (or the end),
       dropping the heading itself; the `<i>` credits line is discarded
       for free by the shared `extract_lyrics()`, which treats unknown
       inline tags as content to skip but not a line break to keep.
    """

    id = "darklyrics"
    name = "DarkLyrics"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        track = await self._find_track(client, artist, title)
        if track is None:
            return []
        page_url, track_num = track

        soup = await self.fetch_soup(client, page_url)
        if soup is None:
            return []

        lyrics = self._extract_track(soup, track_num)
        if not lyrics:
            return []

        return [
            LyricsResult(
                source=self.name, url=f"{page_url}#{track_num}", lyrics=lyrics
            )
        ]

    async def _find_track(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> tuple[str, str] | None:
        artist_slug = slugify(artist, sep="")
        if not artist_slug:
            return None

        index_url = f"{_BASE_URL}/{artist_slug[0]}/{artist_slug}.html"
        soup = await self.fetch_soup(client, index_url)
        if soup is None:
            return None

        for link in soup.select("div.album a[href]"):
            if link.get_text(strip=True).lower() != title.lower():
                continue
            page_path, _, track_num = link["href"].partition("#")
            if not track_num:
                continue
            return urllib.parse.urljoin(index_url, page_path), track_num

        return None

    @staticmethod
    def _extract_track(soup: BeautifulSoup, track_num: str) -> str | None:
        container = soup.find("div", class_="lyrics")
        if container is None:
            return None

        contents = list(container.contents)
        start = end = None
        for i, node in enumerate(contents):
            if not (isinstance(node, Tag) and node.name == "h3"):
                continue
            anchor = node.find("a")
            if start is None:
                if anchor is not None and anchor.get("name") == track_num:
                    start = i
                continue
            end = i
            break

        if start is None:
            return None
        if end is None:
            end = len(contents)

        for node in contents[:start] + contents[end:]:
            node.extract()
        contents[start].decompose()

        return DarkLyricsPlugin.extract_lyrics(container) or None
