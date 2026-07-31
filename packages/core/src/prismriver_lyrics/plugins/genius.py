import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://api.genius.com/search"
_TOKEN = "V_3MoK-nWNF2VKm_zG6qoH8mLnQsr4BU79c4sSNypbLXoXVQZXQI9Dl2Gg9tWed8"


class GeniusPlugin(LyricsPlugin):
    """Fetches lyrics from genius.com.

    Genius's API (https://docs.genius.com/) only returns song metadata and a
    link to the song's page, not lyrics text itself, so this plugin calls
    the Search endpoint to find the matching song's URL, then scrapes the
    lyrics out of that page's `data-lyrics-container` blocks.
    """

    name = "genius.com"

    # Genius wraps most lyric lines in <a> (referent/annotation) tags and
    # some styled spans in <span>; both wrap real lyric text, not chrome.
    _INLINE_TAGS = frozenset({"a", "span"})

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        response = await client.get(
            _SEARCH_URL,
            params={"q": f"{artist} {title}"},
            headers={"Authorization": f"Bearer {_TOKEN}"},
        )
        if response.status_code != 200:
            return []

        hits = response.json().get("response", {}).get("hits", [])
        song = next(
            (
                hit["result"]
                for hit in hits
                if hit.get("type") == "song"
                and hit.get("result", {}).get("url")
            ),
            None,
        )
        if song is None:
            return []

        url = song["url"]
        page_response = await client.get(url)
        if page_response.status_code != 200:
            return []

        soup = BeautifulSoup(page_response.text, "html.parser")
        containers = soup.select("div[data-lyrics-container='true']")
        if not containers:
            return []

        lyrics = "\n\n".join(
            self.extract_lyrics(container) for container in containers
        ).strip()
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
