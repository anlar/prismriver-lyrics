import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify


class ElyricsPlugin(LyricsPlugin):
    """Fetches lyrics from elyrics.net.

    URL shape: https://www.elyrics.net/read/{letter}/{artist}-lyrics/{title}-lyrics.html
    """

    id = "elyrics"
    name = "eLyrics"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        letter = artist_slug[0] if artist_slug else "a"
        return (
            f"https://www.elyrics.net/read/{letter}/"
            f"{artist_slug}-lyrics/{title_slug}-lyrics.html"
        )

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        lyrics = await self.fetch_lyrics(
            client, url, "div#lyr.ly div#inlyr.translate"
        )
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
