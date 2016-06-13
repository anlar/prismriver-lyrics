# Prismriver Lyrics

[![Build Status](https://travis-ci.org/anlar/prismriver-lyrics.svg?branch=master)](https://travis-ci.org/anlar/prismriver-lyrics)
[![Release](https://img.shields.io/github/release/anlar/prismriver-lyrics.svg)](https://github.com/anlar/prismriver-lyrics/releases/latest)
[![License](https://img.shields.io/github/license/anlar/prismriver-lyrics.svg)](https://github.com/anlar/prismriver-lyrics/blob/master/LICENSE)

Prismriver Lyrics is a plugin-based search engine for song lyrics with command-line and Qt graphic interfaces.

![screenshot-linux](https://github.com/anlar/prismriver-lyrics/raw/master/docs/images/screenshot-linux.png)

## Requirements

Package names from Ubuntu 14.04 mentioned within brackets.

### Core

* Python 3.3+ (python3)
* Beautiful Soup 4 (python-beautifulsoup)
* lxml (python3-lxml)

### GUI

* *everything from Core*
* PyQt5 (python3-pyqt5)
* D-Bus Python 3 bindings (python3-dbus)


## Usage

    prismriver-cli.py [ACTION] [OPTIONS]

    Where ACTION must be one of:
        --song                search for song information by artist and title (default action)
        --list                list available search plugins
        --cleanup             remove outdated files from cache
        -h, --help            show help message and exit

    OPTIONS:
        -a ARTIST, --artist ARTIST
                              song artist
        -t TITLE, --title TITLE
                              song title
        -l LIMIT, --limit LIMIT
                              maximum results count
        -p PLUGINS, --plugins PLUGINS
                              comma separated listed of enabled plugins (empty list means that
                              everything is enabled - by default)
        --web_timeout WEB_TIMEOUT
                              timeout for web-page downloading in seconds (default: 10 sec)
        --sync                search info from all plugins consecutively
        --cache_dir CACHE_DIR
                              cache directory for downloaded web pages (default: ~/.cache/prismriver)
        --cache_ttl CACHE_TTL
                              cache ttl for downloaded web pages in seconds (default: one week)
        --skip_cleanup        do not remove outdated files from cache after search completion
        -f FORMAT, --format FORMAT
                              lyrics output format (txt (default), json, json_ascii)
        -o OUTPUT, --output OUTPUT
                              output template for txt format. Available parameters:
                              %TITLE% - song title, %ARTIST% - song artist, %LYRICS% - song lyrics,
                              %PLUGIN_ID% - plugin id, %PLUGIN_NAME% - plugin name
                              (default value: %ARTIST% - %TITLE%\nSource: %PLUGIN_NAME%\n\n%LYRICS%)
        --log LOG             if set will redirect log info to that file
        -q, --quiet           disable logging info (show only errors)
        -v, --verbose         increase output verbosity


### Examples

Search for song information using all plugins:

    prismriver-cli.py -a ARTIST_NAME -t SONG_TITLE

List all available plugins:

    prismriver-cli.py --list


## Supported lyric databases

* 1 Music Lyrics       [id: 1musiclyrics]
* 1 Song Lyrics        [id: 1songlyrics]
* AbsoluteLyrics       [id: absolutelyrics]
* AliveLyrics          [id: alivelyrics]
* AlLyrics.net         [id: allyrics]
* Alphabet Lyrics      [id: alphabetlyrics]
* Amalgama             [id: amalgama]
* Anime Lyrics         [id: animelyrics]
* AZLyrics             [id: azlyrics]
* Bandcamp             [id: bandcamp]
* Chartlyrics          [id: chartlyrics]
* Dark Lyrics          [id: darklyrics]
* Directlyrics         [id: directlyrics]
* eLyrics              [id: elyrics]
* Encyclopaedia Metallum [id: metallum]
* Evesta               [id: evesta]
* Genius               [id: genius]
* J-Lyric              [id: jlyric]
* J-Lyrics.ru          [id: jlyricsru]
* JetLyrics            [id: jetlyrics]
* Kasi-Time            [id: kasitime]
* KGet                 [id: kget]
* Letras               [id: letras]
* LetsSingIt           [id: letssingit]
* Lololyrics           [id: lololyrics]
* Lyrical Nonsense     [id: lyricalnonsense]
* Lyrics Action        [id: lyricsaction]
* Lyrics Bay           [id: lyricsbay]
* Lyrics Depot         [id: lyricsdepot]
* Lyrics N Music       [id: lyricsnmusic]
* Lyrics Place         [id: lyricsplace]
* Lyrics.com           [id: lyricscom]
* Lyrics.net           [id: lyricsnet]
* LyricsFreak          [id: lyricsfreak]
* LyricsHuddle         [id: lyricshuddle]
* LyricsMania          [id: lyricsmania]
* LyricsMode           [id: lyricsmode]
* LyricsReg.com        [id: lyricsreg]
* LyricWiki            [id: lyricwiki]
* Lyrsense             [id: lyrsense]
* Lyrster              [id: lyrster]
* Megalyrics           [id: megalyrics]
* MetroLyrics          [id: metrolyrics]
* Mp3Lyrics            [id: mp3lyrics]
* Musixmatch           [id: musixmatch]
* Nautiljon            [id: nautiljon]
* NitroLyrics          [id: nitrolyrics]
* SeekaLyric           [id: seekalyric]
* ShowMeLyrics         [id: showmelyrics]
* Sing365              [id: sing365]
* Snakie's Obsession   [id: snakie]
* Song5                [id: song5]
* SongLyrics.com       [id: songlyrics]
* Songs Lyrics         [id: songslyrics]
* SonicHits            [id: sonichits]
* TouhouWiki           [id: touhouwiki]
* Uta-Net              [id: utanet]
* UtaMap               [id: utamap]
* UtaTen               [id: utaten]
* Vagalume             [id: vagalume]


## Changes

[See docs/changes.md](docs/changes.md)


## TODO

[See docs/todo.md](docs/todo.md)


## Similar projects

[See docs/similar.md](docs/similar.md)


## Copyright

Source code released under Expat license (aka MIT License), see [LICENSE](LICENSE) for details.

Also it contains additional icons from the following projects:

* *player/amarok.png*: [Amarok](https://quickgit.kde.org/?p=amarok.git&a=blob&f=images/amarok_icon.svg)

* *player/audacious.png*: [Audacious](https://github.com/audacious-media-player/audacious/blob/master/images/audacious.svg)

* *player/deadbeef.png*: [DeaDBeeF Player](https://github.com/Alexey-Yakovenko/deadbeef/blob/master/icons/256x256/deadbeef.png)

* *player/default.png*: [MATE Desktop Environment icon theme](https://github.com/mate-desktop/mate-icon-theme/blob/master/mate/256x256/mimetypes/audio-x-generic.png)

* *player/mpd.png*: [MPD](http://git.musicpd.org/cgit/master/mpd.git/plain/mpd.svg)

* *player/rhythmbox.png*: [Rhythmbox](https://git.gnome.org/browse/rhythmbox/plain/data/icons/hicolor/256x256/apps/rhythmbox.png)

* *player/vlc.png*: [VLC media player](https://github.com/videolan/vlc/blob/master/share/icons/256x256/vlc.png)