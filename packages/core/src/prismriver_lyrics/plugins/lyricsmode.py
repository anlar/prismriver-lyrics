import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify


class LyricsModePlugin(LyricsPlugin):
    """Fetches lyrics from lyricsmode.com.

    URL shape: https://www.lyricsmode.com/lyrics/{letter}/{artist}/{title}.html
    """

    id = "lyricsmode"
    name = "LyricsMode"

    # Individual lines are wrapped in <span> for the site's annotation
    # feature; it wraps real lyric text, not chrome, so it's recursed into.
    _INLINE_TAGS = frozenset({"span"})

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = slugify(artist, sep="_")
        title_slug = slugify(title, sep="_")
        letter = artist_slug[0] if artist_slug else "a"
        return (
            f"https://www.lyricsmode.com/lyrics/{letter}/"
            f"{artist_slug}/{title_slug}.html"
        )

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        soup = await self.fetch_soup(client, url)
        if soup is None:
            return []

        container = soup.select_one("#lyrics_text")
        if container is None:
            return []

        # A stray literal "..." text node sits between the lyrics and the
        # annotation-button chrome; drop it so it doesn't leak into the
        # extracted text as a trailing line.
        for node in container.find_all(string=lambda s: s.strip() == "..."):
            node.extract()

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
