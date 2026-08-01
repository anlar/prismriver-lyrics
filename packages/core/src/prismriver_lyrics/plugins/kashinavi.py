import urllib.parse

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://kashinavi.com/search.php"
_BASE_URL = "https://kashinavi.com"


def _quote(value: str) -> str:
    # kashinavi.com's search form submits Shift_JIS (cp932) encoded query
    # parameters rather than the usual UTF-8; a UTF-8 encoded query is
    # silently misinterpreted and matches unrelated songs.
    return urllib.parse.quote(value, encoding="cp932")


class KashiNaviPlugin(LyricsPlugin):
    """Fetches lyrics from kashinavi.com.

    Search: https://kashinavi.com/search.php?kyoku={title}&kashu={artist}.
    Each result row is a `div[style*='overflow:hidden']` holding the title
    link (`a[href^='/lyrics/']`) and artist link (`a[href^='/artist/']`)
    side by side. A song page's lyrics sit in the plain text + `<br>` div
    that immediately follows the div containing the page's `<h2>` title
    header.
    """

    name = "kashinavi.com"

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
        response.encoding = "cp932"

        soup = BeautifulSoup(response.text, "html.parser")
        h2 = soup.find("h2")
        header_div = h2.find_parent("div") if h2 else None
        container = header_div.find_next_sibling("div") if header_div else None
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        url = f"{_SEARCH_URL}?kyoku={_quote(title)}&kashu={_quote(artist)}"
        response = await client.get(url)
        if response.status_code != 200:
            return None
        response.encoding = "cp932"

        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("table tr div[style*='overflow:hidden']"):
            title_link = row.select_one("a[href^='/lyrics/']")
            artist_link = row.select_one("a[href^='/artist/']")
            if title_link is None or artist_link is None:
                continue
            if (
                title_link.get_text(strip=True).lower() == title.lower()
                and artist_link.get_text(strip=True).lower() == artist.lower()
            ):
                href = title_link.get("href")
                if href:
                    return _BASE_URL + href
        return None
