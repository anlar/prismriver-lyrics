# Prismriver Project [![Build Status](https://travis-ci.org/anlar/prismriver.svg?branch=master)](https://travis-ci.org/anlar/prismriver)

Prismriver is a search engine for song information (generally for it's lyrics). It consists of the following modules:

* Lyrica: core module, contains site search plugins and command line interface for lyrics searching.

* Lunasa: Qt5-based graphical interface, can search lyrics which author/title details where entered manually or received via MPRIS protocol from audio-player.

## Requirements

Package names from Ubuntu 14.04 mentioned within brackets.

### Lyrica

* Python 3.2+ (python3)
* Beautiful Soup 4 (python-beautifulsoup)
* lxml (python3-lxml)

### Lunasa

* *everything from Lyrica*
* PyQt5 (python3-pyqt5)
* D-Bus Python 3 bindings (python3-dbus)

## Usage

    usage: prismriver.py [-h] [--list] [--song] [-a ARTIST] [-t TITLE] [-l LIMIT]
                         [-p PLUGINS] [-f FORMAT] [--async] [-o OUTPUT] [-q] [-v]
                         [--log LOG]

    optional arguments:
      -h, --help            show this help message and exit
      --list                list available search plugins
      --song                search for song information by artist and title
                            (default action)
      -a ARTIST, --artist ARTIST
                            song artist
      -t TITLE, --title TITLE
                            song title
      -l LIMIT, --limit LIMIT
                            maximum results count
      -p PLUGINS, --plugins PLUGINS
                            comma separated listed of enabled plugins (empty list
                            means that everything is enabled - by default)
      -f FORMAT, --format FORMAT
                            lyrics output format (txt (default), json, json_ascii)
      --async               search info from all plugins simultaneously
      -o OUTPUT, --output OUTPUT
                            output template for txt format. Available parameters:
                            %TITLE% - song title, %ARTIST% - song artist, %LYRICS%
                            - song lyrics, %PLUGIN_ID% - plugin id, %PLUGIN_NAME%
                            - plugin name (default value: %ARTIST% -
                            %TITLE%\nSource: %PLUGIN_NAME%\n\n%LYRICS%)
      -q, --quiet           disable logging info (show only errors)
      -v, --verbose         increase output verbosity
      --log LOG             if set will redirect log info to that file

### Examples

Search for song information using all plugins in parallel:

    python3 prismriver.py -a ARTIST_NAME -t SONG_TITLE --async

List all available plugins:

    python3 prismriver.py --list

## Supported lyric databases

* Amalgama             [id: amalgama]
* Anime Lyrics         [id: animelyrics]
* AZLyrics             [id: azlyrics]
* bop.fm               [id: bopfm]
* Chartlyrics          [id: chartlyrics]
* eLyrics              [id: elyrics]
* J-Lyric              [id: jlyric]
* KGet                 [id: kget]
* Leo's Lyrics         [id: leoslyrics]
* Letras               [id: letras]
* LetsSingIt           [id: letssingit]
* Lololyrics           [id: lololyrics]
* Lyrical Nonsense     [id: lyricalnonsense]
* Lyrics N Music       [id: lyricsnmusic]
* LyricsHuddle         [id: lyricshuddle]
* LyricsMania          [id: lyricsmania]
* LyricsReg.com        [id: lyricsreg]
* LyricWiki            [id: lyricwiki]
* Lyrster              [id: lyrster]
* Megalyrics           [id: megalyrics]
* MetroLyrics          [id: metrolyrics]
* NitroLyrics          [id: nitrolyrics]
* SongLyrics.com       [id: songlyrics]
* TouhouWiki           [id: touhouwiki]
* Vagalume             [id: vagalume]


## TODO

### General features

#### Lyrica

* Options for pre-processing artist and title: trim, remove redundant details (feat, remix, version etc), romanize...

* Sort search results by site rating.

* Support Python2.

#### Lunasa

* Create application icon.

* Add more player icons.

* Make dbus optional dependency.

* Implement proper dbus-listener.


### Lyric databases

* http://www.darklyrics.com/
* http://www.lyricfind.com/ (available only via their mobile app)
* https://bandcamp.com/
* http://www.lyricsmode.com/
* http://www.lyricsfreak.com/
* http://www.lyrics.com/
* http://www.lyrics.net/
* http://www.urbanlyrics.com/
* http://www.plyrics.com/
* http://www.metal-archives.com/
* http://www.allyrics.net/
* http://www.songs-lyrics.net/
* http://www.seekalyric.com/
* http://www.1songlyrics.com/
* http://www.stlyrics.com/
* http://showmelyrics.com/
* http://www.lyricsmansion.com/
* http://animeasialyrics.free.fr/
* http://lyrics.jetmute.com/
* http://lyrics.astraweb.com/ (search engine is dead)
* http://www.alivelyrics.com/
* http://alphabetlyrics.com/
* http://www.stlyrics.com/
* http://www.lyred.com/
* http://metal-lyrics.narod.ru/
* http://www.directlyrics.com/
* http://www.songlyrics.com/
* http://www.nautiljon.com/paroles/
* http://ostanimepluslyrics.blogspot.ru/search/label/Lyrics%20Music
* http://lyrics.snakeroot.ru/lyrics.html
* https://www.musixmatch.com/
* http://www.lyricsplugin.com/
* https://www.jamendo.com/
* http://www.lyriki.com/
* http://www.lyricsbay.com/
* http://www.directlyrics.com/
* http://teksty.org/
* http://www.sing365.com/
* http://www.clickgratis.com.br/
* http://www.absolutelyrics.com/
* http://www.allmusicals.com/
* http://www.hitslyrics.com/
* http://www.cowboylyrics.com/
* http://www.popular-lyrics.com/
* http://www.lyricsby.com/
* http://www.thebroadwaymusicals.com/
* http://songmeanings.com/
* http://www.kasi-time.com/
* http://www.evesta.jp/
* http://www.utamap.com/
* http://www.uta-net.com/

See also:

* https://en.wikipedia.org/wiki/Category:Online_music_and_lyrics_databases
* http://www.kiwi-musume.com/profiles/links.htm

## Similar projects

* https://github.com/boyska/lyricseek;
Python;
multiple sites

* https://github.com/sahib/glyr;
C;
multiple sites

* https://github.com/javichito/Lyricfy;
Ruby;
Wikia, MetroLyrics

* https://github.com/timrogers/genius;
Ruby;
Genius

* https://github.com/geecko86/QuickLyric;
Java;
multiple sites

* https://github.com/dmo60/lLyrics
Python;
multiple sites

* https://git.gnome.org/browse/rhythmbox/tree/plugins/lyrics
Python;
multiple sites

* http://kde-apps.org/content/show.php/Ultimate+Lyrics?content=108967
Javascript;
multiple sites

* https://github.com/BansheeMediaPlayer/banshee-community-extensions/tree/master/src/Lyrics
C#;
multiple sites

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