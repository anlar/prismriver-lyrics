import urllib.parse

import httpx

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

    id = "kashinavi"
    name = "KashiNavi"

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

        soup = await self.fetch_soup(client, song_url, encoding="cp932")
        if soup is None:
            return []

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
        soup = await self.fetch_soup(client, url, encoding="cp932")
        if soup is None:
            return None

        href = self.find_matching_href(
            soup.select("table tr div[style*='overflow:hidden']"),
            "a[href^='/lyrics/']",
            "a[href^='/artist/']",
            title,
            artist,
        )
        return _BASE_URL + href if href else None
