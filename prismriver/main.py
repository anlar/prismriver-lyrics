import logging
import time

from prismriver import util
from prismriver.plugin.chartlyrics import ChartlyricsPlugin
from prismriver.plugin.leoslyrics import LeosLyricsPlugin
from prismriver.plugin.lyricsmania import LyricsManiaPlugin
from prismriver.plugin.lyricwiki import LyricWikiPlugin
from prismriver.plugin.megalyrics import MegalyricsPlugin
from prismriver.plugin.metrolyrics import MetroLyricsPlugin
from prismriver.plugin.touhouwiki import TouhouWikiPlugin


def is_enabled(plugin, enabled_plugins):
    if enabled_plugins:
        for enabled_plugin in enabled_plugins:
            if plugin.plugin_id == enabled_plugin:
                return True

        return False
    else:
        return True


def search(artist, title, limit=None, enabled_plugins=None):
    plugins = [
        TouhouWikiPlugin(),
        LyricWikiPlugin(),
        MegalyricsPlugin(),
        LyricsManiaPlugin(),
        ChartlyricsPlugin(),
        MetroLyricsPlugin(),
        LeosLyricsPlugin()
    ]

    result = []
    for plugin in plugins:

        if is_enabled(plugin, enabled_plugins):
            if plugin.is_valid_request(artist, title):
                logging.info('Search lyrics on "{}" [{}]...'.format(plugin.plugin_name, plugin.plugin_id))
                try:
                    start_time = time.time()
                    song = plugin.search(artist, title)
                    total_time = time.time() - start_time

                    if song:
                        logging.info('Found song info on "{}" [{}], {}'.format(plugin.plugin_name, plugin.plugin_id,
                                                                               util.format_time_ms(total_time)))
                        result.append(song)
                    else:
                        logging.info('Found nothing on "{}" [{}], {}'.format(plugin.plugin_name, plugin.plugin_id,
                                                                             util.format_time_ms(total_time)))
                except Exception:
                    logging.exception('Failed to get info from "{}" [{}]'.format(plugin.plugin_name, plugin.plugin_id))
                    pass

                if limit and len(result) >= limit:
                    break
            else:
                logging.info(
                    'Skip search on "{}" [{}] - request not valid'.format(plugin.plugin_name, plugin.plugin_id))

    if limit:
        return result[:limit]
    else:
        return result
