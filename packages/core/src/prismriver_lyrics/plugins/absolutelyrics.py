import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify


class AbsoluteLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from absolutelyrics.com.

    URL shape: http://www.absolutelyrics.com/lyrics/view/{artist}/{title},
    where artist/title are snake_cased (lowercased, non-alphanumeric runs
    collapsed to a single underscore).
    """

    id = "absolutelyrics"
    name = "AbsoluteLyrics"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist, sep="_")
        title_slug = slugify(title, sep="_")
        return f"http://www.absolutelyrics.com/lyrics/view/{artist_slug}/{title_slug}"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        lyrics = await self.fetch_lyrics(client, url, "p#view_lyrics")
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
