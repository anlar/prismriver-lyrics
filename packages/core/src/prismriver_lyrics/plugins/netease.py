import re

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

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

    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return "\n".join(lines)


class NeteasePlugin(LyricsPlugin):
    """Fetches lyrics from music.163.com (NetEase Cloud Music).

    Searches by "{artist} {title}", picks the first available (not
    "uncollected") match, then fetches its LRC-format lyrics and strips
    the [mm:ss.xx] timestamps down to plain text.
    """

    name = "music.163.com"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> list[LyricsResult]:
        response = await client.get(
            _SEARCH_URL,
            params={
                "s": f"{artist} {title}",
                "limit": 6,
                "type": 1,
                "offset": 0,
                "total": "true",
            },
        )
        if response.status_code != 200:
            return []

        songs = response.json().get("result", {}).get("songs", [])
        song = next((s for s in songs if "uncollected" not in s), None)
        if song is None:
            return []

        song_id = song["id"]
        lyrics_response = await client.get(
            _LYRIC_URL, params={"id": song_id, "lv": -1, "kv": -1, "tv": -1}
        )
        if lyrics_response.status_code != 200:
            return []

        lrc = lyrics_response.json().get("lrc", {}).get("lyric")
        if not lrc:
            return []

        lyrics = _strip_lrc(lrc)
        if not lyrics:
            return []

        url = f"https://music.163.com/#/song?id={song_id}"
        return [LyricsResult(source=self.name, url=url, lyrics=lyrics)]
