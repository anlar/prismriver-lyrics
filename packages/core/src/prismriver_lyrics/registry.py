from prismriver_lyrics.plugins.absolutelyrics import AbsoluteLyricsPlugin
from prismriver_lyrics.plugins.alphabetlyrics import AlphabetLyricsPlugin
from prismriver_lyrics.plugins.amalgama import AmalgamaPlugin
from prismriver_lyrics.plugins.base import LyricsPlugin
from prismriver_lyrics.plugins.deezer import DeezerPlugin
from prismriver_lyrics.plugins.elyrics import ElyricsPlugin
from prismriver_lyrics.plugins.genius import GeniusPlugin
from prismriver_lyrics.plugins.kashinavi import KashiNaviPlugin
from prismriver_lyrics.plugins.letras import LetrasPlugin
from prismriver_lyrics.plugins.lrclib import LrcLibPlugin
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
from prismriver_lyrics.plugins.utaten import UtaTenPlugin
from prismriver_lyrics.plugins.vagalume import VagalumePlugin


def default_plugins() -> list[LyricsPlugin]:
    """Plugins queried by default, one instance per lyrics source."""
    return [
        AbsoluteLyricsPlugin(),
        AlphabetLyricsPlugin(),
        AmalgamaPlugin(),
        DeezerPlugin(),
        ElyricsPlugin(),
        GeniusPlugin(),
        KashiNaviPlugin(),
        LetrasPlugin(),
        LrcLibPlugin(),
        LyricsFreakPlugin(),
        LyricsManiaPlugin(),
        LyricsModePlugin(),
        LyricsOvhPlugin(),
        LyrsensePlugin(),
        MusixmatchPlugin(),
        NeteasePlugin(),
        OneMusicLyricsPlugin(),
        ParolesPlugin(),
        PetitLyricsPlugin(),
        SeekALyricPlugin(),
        ShowMeLyricsPlugin(),
        SnakerootPlugin(),
        SongGuruPlugin(),
        UtaTenPlugin(),
        VagalumePlugin(),
    ]
