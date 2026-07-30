import base64
import xml.etree.ElementTree as ET

import httpx

from prismriver_lyrics.models import LyricsResult
from prismriver_lyrics.plugins.base import LyricsPlugin

_SEARCH_URL = "https://on.petitlyrics.com/api/GetPetitLyricsData.php"
_CLIENT_APP_ID = "p1110417"


class PetitLyricsPlugin(LyricsPlugin):
    """Fetches lyrics from petitlyrics.com.

    POSTs to their internal (undocumented) API used by the official
    mobile apps, authenticated with a client app id. Lyrics come back
    base64-encoded inside the first matching <song> of the XML response.
    """

    name = "petitlyrics.com"

    async def search(
        self, client: httpx.AsyncClient, artist: str, title: str
    ) -> LyricsResult | None:
        response = await client.post(
            _SEARCH_URL,
            data={
                "key_title": title,
                "key_artist": artist,
                "lyricsType": 1,
                "terminalType": 10,
                "clientAppId": _CLIENT_APP_ID,
            },
        )
        if response.status_code != 200:
            return None

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            return None

        song = root.find("./songs/song")
        if song is None:
            return None

        lyrics_data = song.findtext("lyricsData")
        lyrics_id = song.findtext("lyricsId")
        if not lyrics_data or not lyrics_id:
            return None

        try:
            lyrics = base64.b64decode(lyrics_data).decode("utf-8").strip()
        except (ValueError, UnicodeDecodeError):
            return None
        if not lyrics:
            return None

        url = f"https://petitlyrics.com/lyrics/{lyrics_id}"
        return LyricsResult(source=self.name, url=url, lyrics=lyrics)
