import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://j-lyric.net/search.php"
_BASE_URL = "https://j-lyric.net"


class JLyricPlugin(LyricsPlugin):
    """Fetches lyrics from j-lyric.net.

    Search: https://j-lyric.net/search.php?kt={title}&ka={artist}&...
    (see `_find_song_url` for the full param set). Each result is a
    `div.bdy` that's a *direct* child of `div#mnb`; other direct children
    of `div#mnb` include the search forms (`div#ebox`, `div#sbox`), which
    also nest a `div.bdy` one level deeper for their own layout, so a
    plain descendant selector would wrongly match those instead of (or
    ahead of) the actual result. A song page's lyrics sit in
    `div#bas div#cnt div#mnb div.lbdy p#Lyric`.

    `kt` (the title field) is server-side broken: any space in its value
    makes the site return zero results, no matter the match mode, even
    for an exact full-title query (verified live, e.g. "ring your bell"
    against Kalafina). `ka` (artist) doesn't have this problem. So a
    multi-word title is queried by its single longest word instead of the
    full title, which is still guaranteed to appear verbatim in the
    title, and combined with the (unmodified) artist to narrow the match.
    """

    id = "jlyric"
    name = "J-Lyric.net"

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

        lyrics = await self.fetch_lyrics(
            client, song_url, "div#bas div#cnt div#mnb div.lbdy p#Lyric"
        )
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        title_words = title.split()
        kt = max(title_words, key=len) if title_words else title

        soup = await self.fetch_soup(
            client,
            _SEARCH_URL,
            params={
                "ex": "on",
                "ct": "2",
                "ca": "2",
                "cl": "2",
                "kt": kt,
                "ka": artist,
                "search": "検索",
            },
        )
        if soup is None:
            return None

        entry = soup.select_one("div#mnb > div.bdy")
        if entry is None:
            return None

        link = entry.select_one("p.mid a")
        if link is None:
            return None

        href = link.get("href")
        if not href:
            return None
        return _BASE_URL + str(href)
