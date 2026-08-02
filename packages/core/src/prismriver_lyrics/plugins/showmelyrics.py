import re

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")

# showmelyrics.com's server blocks requests whose User-Agent reports an
# outdated Chrome version (the shared client's "Chrome/124.0" among
# them) with a 403, but accepts a recent one; override the shared
# client's User-Agent with a newer version just for this source.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


class ShowMeLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from showmelyrics.com.

    URL shape: https://showmelyrics.com/lyrics/{Artist}-{Title}, where
    artist/title are split into words and each word is title-cased
    (capitalized, not lowercased), joined by hyphens. The site sometimes
    redirects this guessed slug to a disambiguated one (e.g. suffixed
    with "-2"); httpx's client follows that automatically.
    """

    id = "showmelyrics"
    name = "ShowMeLyrics"

    def _slug(self, value: str) -> str:
        words = [w for w in _NON_ALNUM.split(value.strip()) if w]
        return "-".join(w.capitalize() for w in words)

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = self._slug(artist)
        title_slug = self._slug(title)
        return f"https://showmelyrics.com/lyrics/{artist_slug}-{title_slug}"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        url = self.build_url(artist, title)
        lyrics = await self.fetch_lyrics(
            client,
            url,
            ".editable-content[itemprop='text']",
            headers={"User-Agent": _USER_AGENT},
        )
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
