import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://www.tekstowo.pl/js/completeSongSearch"
_SONG_URL = "https://www.tekstowo.pl/piosenka,{song_id}.html"


class TekstowoPlugin(LyricsPlugin):
    """Fetches lyrics from tekstowo.pl.

    Search is a POST to an autocomplete endpoint that returns "Artist - Title"
    candidates keyed by a slug id (e.g. "metallica,enter-sandman"); this picks
    the id whose artist/title match, then scrapes that song's page.
    """

    id = "tekstowo"
    name = "Tekstowo"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        song_id = await self._find_song_id(client, artist, title)
        if song_id is None:
            return []

        url = _SONG_URL.format(song_id=song_id)
        lyrics = await self.fetch_lyrics(
            client, url, "div.song-text .inner-text"
        )
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

    async def _find_song_id(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        response = await client.post(
            _SEARCH_URL, data={"search-query": f"{artist} {title}"}
        )
        if response.status_code != 200:
            return None

        for candidate in response.json():
            candidate_artist, _, candidate_title = candidate.get(
                "text", ""
            ).partition(" - ")
            if (
                candidate_artist.strip().lower() == artist.lower()
                and candidate_title.strip().lower() == title.lower()
            ):
                return candidate.get("id")
        return None
