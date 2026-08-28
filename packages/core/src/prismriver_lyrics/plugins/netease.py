import re

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import UNKNOWN_LANG, LyricsPlugin

_SEARCH_URL = "https://music.163.com/api/search/get"
_LYRIC_URL = "https://music.163.com/api/song/lyric"

_LRC_TIMESTAMP = re.compile(r"^(\[\d+:\d+(?:\.\d+)?\])+")
_LRC_METADATA = re.compile(r"^\[[a-zA-Z]+:.*\]$")


def _strip_lrc(lrc: str) -> str:
    """Convert LRC-format ([mm:ss.xx]-prefixed) lyrics to plain text."""
    lines = []
    for raw_line in lrc.splitlines():
        if _LRC_METADATA.match(raw_line):
            continue
        lines.append(_LRC_TIMESTAMP.sub("", raw_line).strip())

    return "\n".join(lines).strip()


class NeteasePlugin(LyricsPlugin):
    """Fetches lyrics from music.163.com (NetEase Cloud Music).

    Searches by "{artist} {title}", picks the first available (not
    "uncollected") match, then fetches its LRC-format lyrics and strips
    the [mm:ss.xx] timestamps down to plain text. Songs may also carry a
    community-submitted Chinese translation (the API's "tlyric" field),
    returned as a second, translated result.
    """

    id = "netease"
    name = "NetEase"

    # Community translations on this (Chinese) site are always into
    # Chinese.
    lang = [UNKNOWN_LANG, "zh"]
    translated = 1

    async def search(
        self,
        client: httpx.AsyncClient,
        artist: str,
        title: str,
        duration_ms: int | None = None,
    ) -> list[LyricsResult]:
        data = await self.fetch_json(
            client,
            _SEARCH_URL,
            params={
                "s": f"{artist} {title}",
                "limit": 6,
                "type": 1,
                "offset": 0,
                "total": "true",
            },
        )
        if data is None:
            return []

        songs = data.get("result", {}).get("songs", [])
        song = next((s for s in songs if "uncollected" not in s), None)
        if song is None:
            return []

        song_id = song["id"]
        lyrics_data = await self.fetch_json(
            client,
            _LYRIC_URL,
            params={"id": song_id, "lv": -1, "kv": -1, "tv": -1},
        )
        if lyrics_data is None:
            return []

        lrc = lyrics_data.get("lrc", {}).get("lyric")
        if not lrc:
            return []

        lyrics = _strip_lrc(lrc)
        if not lyrics:
            return []

        url = f"https://music.163.com/#/song?id={song_id}"
        results = [LyricsResult(source=self.name, url=url, lyrics=lyrics)]

        tlrc = lyrics_data.get("tlyric", {}).get("lyric")
        translation = _strip_lrc(tlrc) if tlrc else ""
        if translation:
            results.append(
                LyricsResult(
                    source=self.name,
                    url=url,
                    lyrics=translation,
                    translation=True,
                    lang="zh",
                )
            )

        return results
