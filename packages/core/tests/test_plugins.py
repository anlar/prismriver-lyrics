import asyncio
import hashlib
import unittest

import httpx
from prismriver_lyrics.plugins.absolutelyrics import AbsoluteLyricsPlugin
from prismriver_lyrics.plugins.alphabetlyrics import AlphabetLyricsPlugin
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.plugins.elyrics import ElyricsPlugin
from prismriver_lyrics.plugins.letras import LetrasPlugin
from prismriver_lyrics.plugins.lyrics_ovh import LyricsOvhPlugin
from prismriver_lyrics.plugins.lyricsmania import LyricsManiaPlugin
from prismriver_lyrics.plugins.one_music_lyrics import OneMusicLyricsPlugin
from prismriver_lyrics.plugins.paroles import ParolesPlugin
from prismriver_lyrics.plugins.seekalyric import SeekALyricPlugin
from prismriver_lyrics.plugins.snakeroot import SnakerootPlugin
from prismriver_lyrics.plugins.vagalume import VagalumePlugin
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
            timeout=20.0,
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
    def test_absolutelyrics_01(self):
        self.check_plugin(
            AbsoluteLyricsPlugin(),
            "Sienna Spiro",
            "This Is My House",
            "2aab7b2ae643d5f37ded075b4fbf4531",
        )

    def test_alphabetlyrics_01(self):
        self.check_plugin(
            AlphabetLyricsPlugin(),
            "Metallica",
            "Enter Sandman",
            "cd4bca18b2565ac47d9f188e5033a1a3",
        )

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

    def test_lyricsmania_01(self):
        self.check_plugin(
            LyricsManiaPlugin(),
            "Metallica",
            "Sad But True",
            "a1a484a129f48294fb08985c7d85de58",
        )

    def test_one_music_lyrics_01(self):
        self.check_plugin(
            OneMusicLyricsPlugin(),
            "Metallica",
            "Eye Of The Beholder",
            "75c4b5f411649046668596fb8b0bfeaa",
        )

    def test_paroles_01(self):
        self.check_plugin(
            ParolesPlugin(),
            "Stromae",
            "Alors on danse",
            "5989a684b9f9fd414bcdefd8580aa65e",
        )

    def test_seekalyric_01(self):
        self.check_plugin(
            SeekALyricPlugin(),
            "Metallica",
            "Invisible Kid",
            "ae36cad9850a767e5827129708c1657c",
        )

    def test_snakeroot_01(self):
        self.check_plugin(
            SnakerootPlugin(),
            "Hayashibara Megumi",
            "Successful Mission",
            "b0ee20935d2dd4b31efa9d47c64889aa",
        )

    def test_vagalume_01(self):
        self.check_plugin(
            VagalumePlugin(),
            "Metallica",
            "...And Justice For All",
            "eef7dbd45da708054e09aca95c983b28",
        )
