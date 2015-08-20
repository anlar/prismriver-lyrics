import re

import dbus


class MprisConnector(object):
    def __init__(self):
        super().__init__()

        self.mpris_re = re.compile('^org\.mpris\.MediaPlayer2\.([^.]+)$')
        self.bus = dbus.SessionBus()
        self.manager = None

    def get_active_players(self):
        active_players = [name for name in self.bus.list_names() if self.mpris_re.match(name)]
        return active_players

    def connect(self, player_name):
        proxy = self.bus.get_object(player_name, '/org/mpris/MediaPlayer2')
        self.manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
        return True

    def get_meta(self):
        if not self.manager:
            return None

        meta = self.manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')

        artist = meta.get('xesam:albumArtist')
        if not artist:
            artist = meta.get('xesam:artist')

        title = meta.get('xesam:title')

        if isinstance(artist, list):
            return [str(artist[0]), str(title)]
        else:
            return [str(artist), str(title)]
