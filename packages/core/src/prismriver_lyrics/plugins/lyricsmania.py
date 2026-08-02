import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify


class LyricsManiaPlugin(LyricsPlugin):
    """Fetches lyrics from lyricsmania.com.

    URL shape: https://www.lyricsmania.com/{title}_lyrics_{artist}.html,
    falling back to https://www.lyricsmania.com/{title}_{artist}.html for
    songs published under the older naming pattern. artist/title are
    snake_cased (lowercased, non-alphanumeric runs collapsed to a single
    underscore).
    """

    id = "lyricsmania"
    name = "LyricsMania"

    def build_url(self, artist: str, title: str) -> str:
        return self._build_url(artist, title, with_lyrics=True)

    def _build_url(self, artist: str, title: str, *, with_lyrics: bool) -> str:
        artist_slug = slugify(artist, sep="_")
        title_slug = slugify(title, sep="_")
        middle = "_lyrics_" if with_lyrics else "_"
        return f"https://www.lyricsmania.com/{title_slug}{middle}{artist_slug}.html"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = ""
        lyrics = None
        for with_lyrics in (True, False):
            url = self._build_url(artist, title, with_lyrics=with_lyrics)
            lyrics = await self.fetch_lyrics(client, url, ".lyrics-body")
            if lyrics:
                break
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
