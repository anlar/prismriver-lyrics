import httpx
from bs4 import Comment
from bs4.element import Tag

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify

_BASE_URL = "https://www.azlyrics.com"

# Text of the HTML comment azlyrics.com places right before the lyrics
# text on every song page, used to locate the lyrics container (see
# `_find_lyrics_container`).
_LYRICS_COMMENT_MARKER = "Usage of azlyrics.com content"


class AZLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from azlyrics.com.

    No search: azlyrics.com URLs are a predictable
    /lyrics/{artist}/{title}.html, both path segments lowercased with all
    non-alphanumeric characters stripped (no separator) and a leading
    "the " dropped from the artist, e.g. "The Beatles"/"Let It Be" ->
    /lyrics/beatles/letitbe.html.

    The lyrics themselves sit as bare text nodes (interspersed with
    `<br>`) in an unmarked `<div>` — no class or id — that azlyrics.com
    relies on obfuscating from scrapers rather than any CSS hook. It's
    found instead via the licensing-warning HTML comment ("Usage of
    azlyrics.com content by any third-party lyrics provider is
    prohibited...") that immediately precedes the lyrics text and shares
    its parent div, which is stable across songs.
    """

    id = "azlyrics"
    name = "AZLyrics"

    def build_url(self, artist: str, title: str) -> str:
        artist = artist.strip()
        if artist.lower().startswith("the "):
            artist = artist[4:]
        artist_slug = slugify(artist, sep="")
        title_slug = slugify(title, sep="")
        return f"{_BASE_URL}/lyrics/{artist_slug}/{title_slug}.html"

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

        container = self._find_lyrics_container(soup)
        if container is None:
            return []

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

    @staticmethod
    def _find_lyrics_container(soup: Tag) -> Tag | None:
        comment = soup.find(
            string=lambda s: isinstance(s, Comment)
            and _LYRICS_COMMENT_MARKER in s
        )
        if comment is None:
            return None
        parent = comment.parent
        return parent if isinstance(parent, Tag) else None
