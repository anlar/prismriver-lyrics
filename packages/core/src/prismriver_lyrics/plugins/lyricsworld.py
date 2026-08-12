import urllib.parse

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_BASE_URL = "https://lyricsworld.ru"
_SEARCH_URL = f"{_BASE_URL}/search/"

_SELECTOR = "#songLyricsDiv"


class LyricsWorldPlugin(LyricsPlugin):
    """Fetches lyrics from lyricsworld.ru, a Russian/CIS lyrics archive.

    A song's url isn't derivable from its artist/title (paths carry an
    opaque numeric id, e.g. `/Kino/Gruppa-krovi-618714.html`), so this
    searches `GET /search/?q={artist} {title}` first. Each hit is a
    `div.serpresult` whose `h3 a` holds the song title and whose
    `div.serpdesc p:first-child a` holds the artist, matched
    case-insensitively via find_matching_href().

    A song page's lyrics live in `#songLyricsDiv`, a `<p>` with `<br>`
    line breaks - a plain extract_lyrics() shape, no per-site rendering
    needed.
    """

    id = "lyricsworld"
    name = "LyricsWorld"

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

        lyrics = await self.fetch_lyrics(client, song_url, _SELECTOR)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        soup = await self.fetch_soup(
            client, _SEARCH_URL, params={"q": f"{artist} {title}"}
        )
        if soup is None:
            return None

        href = self.find_matching_href(
            soup.select("div.serpresult"),
            "h3 a",
            "div.serpdesc p:first-child a",
            title,
            artist,
        )
        return urllib.parse.urljoin(_BASE_URL, href) if href else None
