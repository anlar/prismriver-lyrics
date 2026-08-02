import re

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

# song.guru keeps non-Latin scripts (e.g. Cyrillic) verbatim in its URL
# path rather than transliterating, so slugging needs a Unicode-aware
# "word character" notion instead of the shared ASCII-only slug.slugify.
_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)


def _slugify(value: str) -> str:
    return _NON_WORD.sub("-", value.strip().lower()).strip("-")


class SongGuruPlugin(LyricsPlugin):
    """Fetches lyrics from m.song.guru (formerly song5.ru).

    URL shape: https://m.song.guru/text/{artist}-{title}, a single
    hyphen-joined slug covering both artist and title.
    """

    id = "songguru"
    name = "Гуру Песен"

    def build_url(self, artist: str, title: str) -> str:
        artist_slug = _slugify(artist)
        title_slug = _slugify(title)
        return f"https://m.song.guru/text/{artist_slug}-{title_slug}"

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

        container = soup.select_one("div.songtext")
        if container is None:
            return []

        # Yandex ad slots are injected mid-lyrics as a <script> plus an
        # empty ad <div>; both are already dropped as content by
        # extract_lyrics, but removing them here avoids each leaving its
        # own stray line break behind.
        for tag in container.select("script, div[id^='yandex_rtb']"):
            tag.decompose()

        lyrics = self.extract_lyrics(container)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
