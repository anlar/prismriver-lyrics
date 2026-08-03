import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_AUTOCOMPLETE_URL = "https://songmeanings.com/actions/autocomplete.php"


class SongMeaningsPlugin(LyricsPlugin):
    """Fetches lyrics from songmeanings.com.

    Search: POST to actions/autocomplete.php with `query`/`tab=songs`/`limit`,
    returning `{"status": "success", "results": [{"title", "subtitle", "url"},
    ...]}` where `title` is the song title and `subtitle` the artist. The first
    result whose title/subtitle exactly match the query is used.

    A song page keeps its lyrics in a `<textarea name="editLyricsBody">` — part
    of the page's inline lyrics-editing UI, but also the only copy of the
    lyrics text present in the page at all (nothing else renders them
    separately). Being a `<textarea>`, its content is plain text with real
    newlines, not HTML, so no `<br>` handling is needed.
    """

    id = "songmeanings"
    name = "SongMeanings"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = await self._find_song_url(client, artist, title)
        if url is None:
            return []

        soup = await self.fetch_soup(client, url)
        if soup is None:
            return []

        textarea = soup.find("textarea", attrs={"name": "editLyricsBody"})
        if textarea is None:
            return []

        lines = [line.strip() for line in textarea.get_text().splitlines()]
        while lines and not lines[-1]:
            lines.pop()
        lyrics = "\n".join(lines).strip()
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        response = await client.post(
            _AUTOCOMPLETE_URL,
            data={"query": f"{artist} {title}", "tab": "songs", "limit": "5"},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        if data.get("status") != "success":
            return None

        for result in data.get("results") or []:
            if (
                (result.get("title") or "").lower() == title.lower()
                and (result.get("subtitle") or "").lower() == artist.lower()
            ):
                return result.get("url")

        return None
