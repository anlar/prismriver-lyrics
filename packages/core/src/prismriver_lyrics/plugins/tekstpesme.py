import urllib.parse

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.util import slugify

_BASE_URL = "https://tekstpesme.com"

_SELECTOR = "div.lyric-text"

# The site's own URL slugs transliterate Serbian Latin diacritics to their
# plain-ASCII digraph/letter (đ -> dj, š -> s, ...) rather than dropping
# them (e.g. "Đorđe Balašević" -> /tekstovi/djordje-balasevic/...), so
# slugify() alone (which only lowercases and separates) won't reproduce
# an artist's slug unless the input goes through this first.
_TRANSLITERATION = str.maketrans(
    {
        "š": "s", "Š": "S",
        "č": "c", "Č": "C",
        "ć": "c", "Ć": "C",
        "ž": "z", "Ž": "Z",
        "đ": "dj", "Đ": "Dj",
    }
)


class TekstpesmePlugin(LyricsPlugin):
    """Fetches lyrics from tekstpesme.com, a Serbian/ex-Yugoslav lyrics
    site.

    The site's search only matches a song's title, not its artist (a
    query combining both reliably returns zero hits), so this searches
    `GET /?s={title}&post_type=lyrics` by title alone; every hit is an
    `<a href="/tekstovi/{artist-slug}/{song-slug}/">`, and the artist is
    disambiguated from that url's own artist-slug segment (transliterated
    per `_TRANSLITERATION` then slugify()'d) rather than from any
    on-page text, since the song-slug carries an unpredictable numeric
    suffix on title collisions (e.g. `ako-boga-znas-2`) that rules out
    matching it directly.

    A song page's lyrics live in `div.lyric-text` as `<p>`-separated
    verses with `<br>` line breaks - a plain extract_lyrics() shape.
    Note the site also strips diacritics from the lyric text itself
    (not just slugs), so results read e.g. "Osjecam" rather than
    "Osjećam".
    """

    id = "tekstpesme"
    name = "Tekstpesme"

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        song_url = await self._find_song_url(client, artist, title)
        if song_url is None:
            return []

        lyrics = await self.fetch_lyrics(client, song_url, _SELECTOR)
        if not lyrics:
            return []

        return [LyricsResult(source=self.name, url=song_url, lyrics=lyrics)]

    async def _find_song_url(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> str | None:
        soup = await self.fetch_soup(
            client,
            f"{_BASE_URL}/",
            params={"s": title, "post_type": "lyrics"},
        )
        if soup is None:
            return None

        artist_slug = slugify(artist.translate(_TRANSLITERATION))
        if not artist_slug:
            return None

        for link in soup.select("a[href*='/tekstovi/']"):
            href = link.get("href")
            if not href:
                continue
            parts = urllib.parse.urlparse(str(href)).path.strip("/").split(
                "/"
            )
            if len(parts) < 3 or parts[0] != "tekstovi":
                continue
            if parts[1] == artist_slug:
                return urllib.parse.urljoin(_BASE_URL, str(href))

        return None
