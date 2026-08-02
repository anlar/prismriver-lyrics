import asyncio
import hashlib
import unittest

import httpx
import pytest
from prismriver_lyrics.plugins.absolutelyrics import AbsoluteLyricsPlugin
from prismriver_lyrics.plugins.alphabetlyrics import AlphabetLyricsPlugin
from prismriver_lyrics.plugins.amalgama import AmalgamaPlugin
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.plugins.deezer import DeezerPlugin
from prismriver_lyrics.plugins.elyrics import ElyricsPlugin
from prismriver_lyrics.plugins.genius import GeniusPlugin
from prismriver_lyrics.plugins.kashinavi import KashiNaviPlugin
from prismriver_lyrics.plugins.kugou import KuGouPlugin
from prismriver_lyrics.plugins.letras import LetrasPlugin
from prismriver_lyrics.plugins.lrclib import LrcLibPlugin
from prismriver_lyrics.plugins.lrcmux import LrcmuxPlugin
from prismriver_lyrics.plugins.lyrics_ovh import LyricsOvhPlugin
from prismriver_lyrics.plugins.lyricsfreak import LyricsFreakPlugin
from prismriver_lyrics.plugins.lyricsmania import LyricsManiaPlugin
from prismriver_lyrics.plugins.lyricsmode import LyricsModePlugin
from prismriver_lyrics.plugins.lyrsense import LyrsensePlugin
from prismriver_lyrics.plugins.musixmatch import MusixmatchPlugin
from prismriver_lyrics.plugins.netease import NeteasePlugin
from prismriver_lyrics.plugins.one_music_lyrics import OneMusicLyricsPlugin
from prismriver_lyrics.plugins.paroles import ParolesPlugin
from prismriver_lyrics.plugins.petitlyrics import PetitLyricsPlugin
from prismriver_lyrics.plugins.seekalyric import SeekALyricPlugin
from prismriver_lyrics.plugins.showmelyrics import ShowMeLyricsPlugin
from prismriver_lyrics.plugins.snakeroot import SnakerootPlugin
from prismriver_lyrics.plugins.song_guru import SongGuruPlugin
from prismriver_lyrics.plugins.synclrc import SyncLrcPlugin
from prismriver_lyrics.plugins.utaten import UtaTenPlugin
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
            results = await plugin.search(client, artist, title)

        assert results, (
            f"{plugin.name} found no lyrics for {artist!r} - {title!r}"
        )
        result = results[0]
        digest = hashlib.md5(result.lyrics.encode("utf-8")).hexdigest()
        self.assertEqual(
            digest,
            expected_md5,
            f"{plugin.name} lyrics md5 was {digest}, expected "
            f"{expected_md5}\n\n{result.lyrics}",
        )

    def check_plugin_all(
        self,
        plugin: LyricsPlugin,
        artist: str,
        title: str,
        expected_md5s: list[str],
        expected_langs: list[str | None] | None = None,
    ) -> None:
        asyncio.run(
            self._check_plugin_all(
                plugin, artist, title, expected_md5s, expected_langs
            )
        )

    async def _check_plugin_all(
        self,
        plugin: LyricsPlugin,
        artist: str,
        title: str,
        expected_md5s: list[str],
        expected_langs: list[str | None] | None,
    ) -> None:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=20.0,
            follow_redirects=True,
        ) as client:
            results = await plugin.search(client, artist, title)

        digests = [
            hashlib.md5(result.lyrics.encode("utf-8")).hexdigest()
            for result in results
        ]
        self.assertEqual(
            digests,
            expected_md5s,
            f"{plugin.name} found {len(results)} result(s) with md5s "
            f"{digests}, expected {expected_md5s}",
        )

        if expected_langs is not None:
            langs = [result.lang for result in results]
            self.assertEqual(
                langs,
                expected_langs,
                f"{plugin.name} found {len(results)} result(s) with langs "
                f"{langs}, expected {expected_langs}",
            )


@pytest.mark.xfail(
    reason="live plugin tests hit real sites and may fail or be blocked",
    strict=False,
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

    def test_amalgama_01(self):
        self.check_plugin_all(
            AmalgamaPlugin(),
            "Modern Talking",
            "Cheri Cheri Lady",
            [
                "81bef7029732fe421ec33191da0831f0",
                "949f4524e93f0c6497c1ac84f6113f67",
                "2db90098decbd965cb2eb53dd54fb099",
            ],
            [None, "ru", "ru"],
        )

    def test_deezer_01(self):
        self.check_plugin(
            DeezerPlugin(),
            "Metallica",
            "Sad But True",
            "76eca4e5d8c2d454435783df08fdb2fc",
        )

    def test_elyrics_01(self):
        self.check_plugin(
            ElyricsPlugin(),
            "Chuck Strangers",
            "Backwood Falls",
            "5ab762a2f7c9f07ebb5d10ffcbb73305",
        )

    def test_genius_01(self):
        self.check_plugin_all(
            GeniusPlugin(),
            "Metallica",
            "Sad But True",
            [
                "b48d45c541b8f96df659c9b53b634b7b",
                "aab6049a27cc42303ae0c8f44b85937f",
                "c05214206511d40466458257cac68098",
                "ac6cb1d33404326f3374eca01ed5c818",
                "bf64c5d170682949dbfc296545782f8f",
            ],
            ["en", "ru", "de", "pt", "nl"],
        )

    def test_kashinavi_01(self):
        self.check_plugin(
            KashiNaviPlugin(),
            "Kalafina",
            "monochrome",
            "c4882ce77d83c81ca189eddeb2580640",
        )

    def test_kugou_01(self):
        self.check_plugin(
            KuGouPlugin(),
            "Кино",
            "Звезда по имени Солнце",
            "010f51e62c60f75f75b0c148fc0ecbff",
        )

    def test_letras_01(self):
        self.check_plugin(
            LetrasPlugin(),
            "Shakira",
            "Dai Dai (feat. Burna Boy)",
            "185a1268927a80a4e3f92498f1915967",
        )

    def test_lrclib_01(self):
        self.check_plugin(
            LrcLibPlugin(),
            "Metallica",
            "Sad But True",
            "ccd5690dbd7f4c7aaa20e95beffd8beb",
        )

    def test_lrcmux_01(self):
        self.check_plugin(
            LrcmuxPlugin(),
            "Кино",
            "Звезда по имени Солнце",
            "4ac522fa29ec1d4a3075a1cacdbd56b1",
        )

    def test_lyrics_ovh_01(self):
        self.check_plugin(
            LyricsOvhPlugin(),
            "Metallica",
            "Sad But True",
            "a1a484a129f48294fb08985c7d85de58",
        )

    def test_lyricsfreak_01(self):
        self.check_plugin(
            LyricsFreakPlugin(),
            "System of a Down",
            "Shame",
            "d343f1479c619ad34a6450f57a2237d9",
        )

    def test_lyricsmania_01(self):
        self.check_plugin(
            LyricsManiaPlugin(),
            "Metallica",
            "Sad But True",
            "a1a484a129f48294fb08985c7d85de58",
        )

    def test_lyricsmode_01(self):
        self.check_plugin(
            LyricsModePlugin(),
            "Metallica",
            "Nothing Else Matters",
            "89cfe45a4f42ff099ce689c80c18ca97",
        )

    def test_lyrsense_01(self):
        self.check_plugin_all(
            LyrsensePlugin(),
            "System of a Down",
            "Suite-Pee",
            [
                "b5f53c28fcaca70767590ea8d0ef16c0",
                "db691a5ab8bae6dc801aebd7339b66bf",
            ],
            [None, "ru"],
        )

    def test_musixmatch_01(self):
        self.check_plugin_all(
            MusixmatchPlugin(),
            "Metallica",
            "Sad But True",
            [
                "356aee6fd75543851b57b8468ac9439c",
                "8ee3338c52f50854184b4be1961361bd",
                "021854a80cd06b19824885d0e0d915bb",
                "bb461f656986bf598b59abe7eee046da",
                "040dd0533e3a7db39ddfebcb4c71658c",
                "6df3431cb1671feec2b9b6f7e254881b",
                "3856af94881ffc48ccb3e8cb37390ab5",
                "94fc815e9dc2071bd80ac3c993a47046",
                "25ebd432e3b4c45f0851e805dd4ca21f",
                "b6f4225412436cdf9a4d6af57e8d39ec",
                "ccc312a3f5813589abf6539f44cbd014",
                "c76f15d93fa371274423041792138181",
            ],
            [
                "en",
                "pl",
                "es",
                "ru",
                "it",
                "uk",
                "de",
                "fr",
                "tr",
                "pt",
                "cs",
                "nl",
            ],
        )

    def test_netease_01(self):
        self.check_plugin(
            NeteasePlugin(),
            "The Clash",
            "London Calling",
            "6cbe3b629c81aebf680eaee8f60e29e6",
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

    def test_petitlyrics_01(self):
        self.check_plugin(
            PetitLyricsPlugin(),
            "Metallica",
            "Sad But True",
            "d2514da2afbd7ba49d2c78b0cc5abf86",
        )

    def test_seekalyric_01(self):
        self.check_plugin(
            SeekALyricPlugin(),
            "Metallica",
            "Invisible Kid",
            "ae36cad9850a767e5827129708c1657c",
        )

    def test_showmelyrics_01(self):
        self.check_plugin(
            ShowMeLyricsPlugin(),
            "Eminem",
            "Just Lose It",
            "48b836c348e5f4d4de251ed858ea8c75",
        )

    def test_snakeroot_01(self):
        self.check_plugin(
            SnakerootPlugin(),
            "Hayashibara Megumi",
            "Successful Mission",
            "b0ee20935d2dd4b31efa9d47c64889aa",
        )

    def test_song_guru_01(self):
        self.check_plugin(
            SongGuruPlugin(),
            "Сектор Газа",
            "Колхозный панк",
            "ea86197ca454df706fa1221f2125cc0c",
        )

    def test_synclrc_01(self):
        self.check_plugin(
            SyncLrcPlugin(),
            "Наутилус Помпилиус",
            "Три царя",
            "e3dadd7f156cb76fdab971a18fe4637a",
        )

    def test_utaten_01(self):
        self.check_plugin_all(
            UtaTenPlugin(),
            "Kalafina",
            "adore",
            [
                "9e7408d6a148d54288af18cf29f050ae",
                "e492440dbf1fee18976a3c45de7a0160",
                "9ed5d8dfb6bc194bf85cd52392938235",
            ],
            ["ja", "ja-Hira", "ja-Latn"],
        )

    def test_utaten_02(self):
        # No furigana on this one (non-Japanese lyrics), so only a single,
        # unlabeled result is expected instead of three.
        self.check_plugin_all(
            UtaTenPlugin(),
            "The Clash",
            "Should I Stay or Should I Go",
            ["ea73fc2c07846a2418fc1243bde7b795"],
            [None],
        )

    def test_vagalume_01(self):
        self.check_plugin(
            VagalumePlugin(),
            "Metallica",
            "...And Justice For All",
            "eef7dbd45da708054e09aca95c983b28",
        )
