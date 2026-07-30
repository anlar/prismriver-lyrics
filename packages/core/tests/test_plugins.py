import asyncio
import hashlib
import unittest

import httpx
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.plugins.elyrics import ElyricsPlugin
from prismriver_lyrics.plugins.letras import LetrasPlugin
from prismriver_lyrics.plugins.lyrics_ovh import LyricsOvhPlugin
from prismriver_lyrics.search import USER_AGENT


class PluginTestCase(unittest.TestCase):
    """Base class for live plugin tests.

    Load lyrics from sites and tests them against md5 of the extracted lyrics,
    without need to embed the entire lyrics in the test file.
    """

    def check_plugin(
        self, plugin: LyricsPlugin, artist: str, title: str, expected_md5: str
    ) -> None:
        asyncio.run(self._check_plugin(plugin, artist, title, expected_md5))

    async def _check_plugin(
        self, plugin: LyricsPlugin, artist: str, title: str, expected_md5: str
    ) -> None:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            result = await plugin.search(client, artist, title)

        assert result is not None, (
            f"{plugin.name} found no lyrics for {artist!r} - {title!r}"
        )
        digest = hashlib.md5(result.lyrics.encode("utf-8")).hexdigest()
        self.assertEqual(
            digest,
            expected_md5,
            f"{plugin.name} lyrics md5 was {digest}, expected "
            f"{expected_md5}\n\n{result.lyrics}",
        )


class TestPlugins(PluginTestCase):
    def test_elyrics_01(self):
        self.check_plugin(
            ElyricsPlugin(),
            "Chuck Strangers",
            "Backwood Falls",
            "5ab762a2f7c9f07ebb5d10ffcbb73305",
        )

    def test_letras_01(self):
        self.check_plugin(
            LetrasPlugin(),
            "Shakira",
            "Dai Dai (feat. Burna Boy)",
            "185a1268927a80a4e3f92498f1915967",
        )

    def test_lyrics_ovh_01(self):
        self.check_plugin(
            LyricsOvhPlugin(),
            "Metallica",
            "Sad But True",
            "a1a484a129f48294fb08985c7d85de58",
        )
