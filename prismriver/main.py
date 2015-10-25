import logging
from threading import Thread
import time
from multiprocessing import Queue

from prismriver import util
from prismriver.plugin.absolutelyrics import AbsoluteLyricsPlugin
from prismriver.plugin.alivelyrics import AliveLyricsPlugin
from prismriver.plugin.allyrics import AlLyricsPlugin
from prismriver.plugin.alphabetlyrics import AlphabetLyricsPlugin
from prismriver.plugin.amalgama import AmalgamaPlugin
from prismriver.plugin.animelyrics import AnimeLyricsPlugin
from prismriver.plugin.azlyrics import AZLyricsPlugin
from prismriver.plugin.bopfmp import BopFmPlugin
from prismriver.plugin.chartlyrics import ChartlyricsPlugin
from prismriver.plugin.directlyrics import DirectLyricsPlugin
from prismriver.plugin.elyrics import ELyricsPlugin
from prismriver.plugin.evesta import EvestaPlugin
from prismriver.plugin.genius import GeniusPlugin
from prismriver.plugin.jlyric import JLyricPlugin
from prismriver.plugin.jlyricsru import JLyricsRuPlugin
from prismriver.plugin.kget import KGetPlugin
from prismriver.plugin.leoslyrics import LeosLyricsPlugin
from prismriver.plugin.letras import LetrasPlugin
from prismriver.plugin.letssingit import LetsSingItPlugin
from prismriver.plugin.lololyrics import LololyricsPlugin
from prismriver.plugin.lyricalnonsense import LyricalNonsensePlugin
from prismriver.plugin.lyricsaction import LyricsActionPlugin
from prismriver.plugin.lyricscom import LyricsComPlugin
from prismriver.plugin.lyricsdepot import LyricsDepotPlugin
from prismriver.plugin.lyricshuddle import LyricsHuddlePlugin
from prismriver.plugin.lyricsmania import LyricsManiaPlugin
from prismriver.plugin.lyricsmode import LyricsModePlugin
from prismriver.plugin.lyricsnmusic import LyricsNMusicPlugin
from prismriver.plugin.lyricsreg import LyricsRegPlugin
from prismriver.plugin.lyricwiki import LyricWikiPlugin
from prismriver.plugin.lyrster import LyrsterPlugin
from prismriver.plugin.megalyrics import MegalyricsPlugin
from prismriver.plugin.metrolyrics import MetroLyricsPlugin
from prismriver.plugin.mp3lyrics import Mp3LyricsPlugin
from prismriver.plugin.musixmatch import MusixmatchPlugin
from prismriver.plugin.nautiljon import NautiljonPlugin
from prismriver.plugin.nitrolyrics import NitroLyricsPlugin
from prismriver.plugin.onesonglyrics import OneSongLyricsPlugin
from prismriver.plugin.seekalyric import SeekaLyricPlugin
from prismriver.plugin.showmelyrics import ShowMeLyricsPlugin
from prismriver.plugin.song5 import SongFivePlugin
from prismriver.plugin.songlyrics import SongLyricsPlugin
from prismriver.plugin.sonichits import SonicHitsPlugin
from prismriver.plugin.touhouwiki import TouhouWikiPlugin
from prismriver.plugin.vagalume import VagalumePlugin


# plugin list

def get_plugins(config=None):
    all_plugins = sorted([
        AZLyricsPlugin,
        TouhouWikiPlugin,
        LyricWikiPlugin,
        MegalyricsPlugin,
        LyricsManiaPlugin,
        ChartlyricsPlugin,
        MetroLyricsPlugin,
        LeosLyricsPlugin,
        LyrsterPlugin,
        LyricsHuddlePlugin,
        ELyricsPlugin,
        NitroLyricsPlugin,
        JLyricPlugin,
        KGetPlugin,
        LololyricsPlugin,
        AmalgamaPlugin,
        AnimeLyricsPlugin,
        LyricalNonsensePlugin,
        VagalumePlugin,
        LyricsNMusicPlugin,
        LetrasPlugin,
        BopFmPlugin,
        LetsSingItPlugin,
        LyricsRegPlugin,
        SongLyricsPlugin,
        GeniusPlugin,
        Mp3LyricsPlugin,
        SonicHitsPlugin,
        LyricsComPlugin,
        SeekaLyricPlugin,
        AbsoluteLyricsPlugin,
        AliveLyricsPlugin,
        AlLyricsPlugin,
        LyricsActionPlugin,
        SongFivePlugin,
        EvestaPlugin,
        LyricsModePlugin,
        ShowMeLyricsPlugin,
        AlphabetLyricsPlugin,
        DirectLyricsPlugin,
        JLyricsRuPlugin,
        LyricsDepotPlugin,
        OneSongLyricsPlugin,
        NautiljonPlugin,
        MusixmatchPlugin
    ], key=lambda x: x.RANK, reverse=True)

    plugins = []
    for plugin in all_plugins:
        if not config or is_enabled(plugin, config.enabled_plugins):
            plugins.append(plugin(config))

    return plugins


def is_enabled(plugin, enabled_plugins):
    if enabled_plugins:
        for enabled_plugin in enabled_plugins:
            if plugin.ID == enabled_plugin:
                return True

        return False
    else:
        return True


# lyrics search

def search(artist, title, config):
    if (not artist) or (not title):
        logging.warning('Skip search - song artist and title can\'t be empty string')
        return []

    if config.sync:
        return search_sync(artist, title, config)
    else:
        return search_async(artist, title, config)


def search_sync(artist, title, config):
    result = []
    for plugin in get_plugins(config):
        song = do_search(plugin, artist, title)
        if song:
            result.append(song)

        if config.result_limit and len(result) >= config.result_limit:
            break

    return result


def search_async(artist, title, config):
    queue = Queue()
    threads = []
    for plugin in get_plugins(config):
        thread = Thread(target=do_search_async, args=(artist, title, plugin, queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    result = []
    for items in range(0, queue.qsize()):
        result.append(queue.get())

    result.sort(key=lambda x: x.plugin_rank, reverse=True)

    if config.result_limit:
        return result[:config.result_limit]
    else:
        return result


def do_search_async(artist, title, plugin, queue):
    song = do_search(plugin, artist, title)
    if song:
        queue.put(song)


def do_search(plugin, artist, title):
    logging.info('Search lyrics on "{}" [{}]...'.format(plugin.plugin_name, plugin.ID))
    try:
        start_time = time.time()
        song = plugin.search_song(artist, title)
        total_time = time.time() - start_time

        if song:
            song.plugin_id = plugin.ID
            song.plugin_rank = plugin.RANK
            song.plugin_name = plugin.plugin_name

            logging.info('Found song info on "{}" [{}], {}'.format(plugin.plugin_name, plugin.ID,
                                                                   util.format_time_ms(total_time)))
            return song
        else:
            logging.info('Nothing was found on "{}" [{}], {}'.format(plugin.plugin_name, plugin.ID,
                                                                     util.format_time_ms(total_time)))
    except Exception:
        logging.exception('Failed to get info from "{}" [{}]'.format(plugin.plugin_name, plugin.ID))
        pass
