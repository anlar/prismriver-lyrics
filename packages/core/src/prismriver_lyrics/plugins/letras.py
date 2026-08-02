import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify


class LetrasPlugin(LyricsPlugin):
    """Fetches lyrics from letras.mus.br.

    URL shape: https://www.letras.mus.br/{artist}/{title}/
    """

    id = "letras"
    name = "Letras"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist)
        title_slug = slugify(title)
        return f"https://www.letras.mus.br/{artist_slug}/{title_slug}/"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        lyrics = await self.fetch_lyrics(client, url, "div.lyric-original")
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
