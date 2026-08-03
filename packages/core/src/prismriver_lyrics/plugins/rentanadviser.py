import re

import httpx
from bs4 import BeautifulSoup

from prismriver_lyrics.models import LyricsResult, SyncedLine, SyncedLyrics
from prismriver_lyrics.plugins.base import LyricsPlugin

_API_URL = "https://www.rentanadviser.com/subtitles/subtitle-api.ashx"

# rentanadviser.com serves subtitle-api.ashx only to requests that look
# like same-site AJAX calls (a plain GET 403s); no other headers or a
# prior page visit are needed.
_HEADERS = {"X-Requested-With": "XMLHttpRequest"}

# Both "lrc" and "srt" carry site branding baked into the content itself
# rather than as separate metadata: "lrc" is prefixed with an <h2>Artist -
# Title (lang) Lyrics</h2> heading, and both "lrc" and "srt" repeat this
# attribution line as if it were a lyric line (in "srt", as bogus first
# and last entries timed to 0 and to the track's end).
_ATTRIBUTION = "by rentanadviser.com"

# A search result's "Title" field, e.g. "Metallica - Nothing Else Matters
# (07:09-429-0-en)": artist, title, and a trailing 2-letter language code
# distinguishing same-song entries available in different languages.
_RESULT_TITLE_RE = re.compile(
    r"^(?P<artist>.+?) - (?P<title>.+?) \([\d:]+-\d+-\d+-(?P<lang>[a-z]{2})\)$"
)


class RentAnAdviserPlugin(LyricsPlugin):
    """Fetches plain-text and line-synced lyrics from rentanadviser.com's
    subtitle-api.ashx JSON endpoint.

    The site's own public download page (getsubtitles.aspx) gates its
    .lrc/.srt/.vtt download buttons behind an image CAPTCHA. But that
    page's "Preview/Test" feature, and its separate local-media-file
    matching tool, both read lyrics via a plain JSON API instead, with no
    CAPTCHA involved:

    1. `subtitle-api.ashx?q={artist} {title}` returns
       `{"Results": [{"Title": ..., "URL": "subtitle-api.ashx?id=N"}]}`,
       one entry per available language for a matching song (`duration`
       is accepted too but doesn't actually filter results, just
       informational).
    2. `subtitle-api.ashx?id=N` (the id from a chosen result's URL)
       returns `{"lrc": "<lyrics as HTML>", "srt": [{"start", "end",
       "text"}, ...]}` directly. Despite the field name, "lrc" isn't
       LRC-tagged; it's an `<h2>` heading plus the lyrics as HTML
       (`<br />` line breaks mixed with literal newlines), and both
       "lrc" and "srt" repeat a "by RentAnAdviser.com" attribution line
       as if it were lyric content (see `_ATTRIBUTION`). "srt"'s
       start/end are fractional seconds, not milliseconds, despite the
       field names looking SRT-native.

    Search results across languages share the same "Artist - Title"
    text, so language is picked by preferring "en" among the entries
    whose artist/title exactly match the query, falling back to
    whichever comes first if no English entry is present.
    """

    id = "rentanadviser"
    name = "RentAnAdviser"

    sync = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        result_id = await self._find_result_id(
            client, artist, title, duration_ms
        )
        if result_id is None:
            return []

        response = await client.get(
            _API_URL, params={"id": result_id}, headers=_HEADERS
        )
        if response.status_code != 200:
            return []

        data = response.json()
        lyrics = self._clean_plain(data.get("lrc") or "")
        lines = [
            SyncedLine(time_ms=round(entry["start"] * 1000), text=text)
            for entry in data.get("srt") or []
            if (text := (entry.get("text") or "").strip())
            and text.lower() != _ATTRIBUTION
        ]
        if not lyrics and not lines:
            return []

        url = (
            "https://www.rentanadviser.com/subtitles/getsubtitles.aspx"
            f"?id={result_id}"
        )
        results = []
        if lyrics:
            results.append(
                LyricsResult(source=self.name, url=url, lyrics=lyrics)
            )
        if lines:
            results.append(
                LyricsResult(
                    source=self.name,
                    url=url,
                    lyrics=SyncedLyrics(lines=tuple(lines)),
                )
            )
        return results

    @classmethod
    def _clean_plain(cls, raw: str) -> str:
        soup = BeautifulSoup(raw, "html.parser")
        for heading in soup.find_all("h2"):
            heading.decompose()

        lines = [
            line
            for line in cls.extract_lyrics(soup).splitlines()
            if line.strip().lower() != _ATTRIBUTION
        ]
        return "\n".join(lines).strip()

    async def _find_result_id(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None,
    ) -> str | None:
        params = {"q": f"{artist} {title}"}
        if duration_ms is not None:
            params["duration"] = str(duration_ms)

        response = await client.get(_API_URL, params=params, headers=_HEADERS)
        if response.status_code != 200:
            return None

        fallback_id = None
        for result in response.json().get("Results") or []:
            match = _RESULT_TITLE_RE.match(result.get("Title") or "")
            if match is None:
                continue
            if (
                match.group("artist").lower() != artist.lower()
                or match.group("title").lower() != title.lower()
            ):
                continue

            result_id = (result.get("URL") or "").rpartition("id=")[2]
            if not result_id:
                continue

            if match.group("lang") == "en":
                return result_id
            if fallback_id is None:
                fallback_id = result_id

        return fallback_id
