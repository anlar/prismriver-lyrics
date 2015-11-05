import re

import dbus


class MprisConnector(object):
    def __init__(self):
        super().__init__()

        self.mpris_re = re.compile('^org\.mpris\.MediaPlayer2\.([^.]+)$')
        self.bus = dbus.SessionBus()
        self.manager = None

    def get_players(self):
        try:
            player_names = [name for name in self.bus.list_names() if self.mpris_re.match(name)]
            players = [self.get_player(name) for name in player_names]
            players.sort(key=lambda x: x.identity.lower())
            return players
        except dbus.exceptions.DBusException:
            return None

    def get_player(self, name):
        try:
            proxy = self.bus.get_object(name, '/org/mpris/MediaPlayer2')
            manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
            identity = manager.Get('org.mpris.MediaPlayer2', 'Identity')
            return MprisPlayer(name, identity)
        except dbus.exceptions.DBusException:
            return None

    def connect(self, player):
        try:
            proxy = self.bus.get_object(player.name, '/org/mpris/MediaPlayer2')
            self.manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
            return True
        except dbus.exceptions.DBusException:
            raise MprisConnectionException()

    def get_meta(self):
        if not self.manager:
            raise MprisConnectionException()

        try:
            meta = self.manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        except dbus.exceptions.DBusException:
            raise MprisConnectionException()

        artist = meta.get('xesam:albumArtist')
        if not artist:
            artist = meta.get('xesam:artist')
        if isinstance(artist, list):
            artist = artist[0]

        title = meta.get('xesam:title')

        return [str(artist) if artist else None, str(title) if title else None]


def get_player_icon_path(player_name):
    player_icons = {'org.mpris.MediaPlayer2.amarok': 'amarok.png',
                    'org.mpris.MediaPlayer2.audacious': 'audacious.png',
                    'org.mpris.MediaPlayer2.deadbeef': 'deadbeef.png',
                    'org.mpris.MediaPlayer2.mpd': 'mpd.png',
                    'org.mpris.MediaPlayer2.rhythmbox': 'rhythmbox.png',
                    'org.mpris.MediaPlayer2.vlc': 'vlc.png'}

    return 'prismriver/pixmaps/player/' + player_icons.get(player_name, 'default.png')


class MprisPlayer(object):
    def __init__(self, name, identity):
        super().__init__()

        self.name = name
        self.identity = identity

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


class MprisConnectionException(Exception):
    pass
