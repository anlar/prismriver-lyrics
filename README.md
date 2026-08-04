<div align="center">
  <h1>Prismriver Lyrics</h1>

  <p>A CLI and terminal UI for searching song lyrics across multiple sources via a plugin system.</p>

  [![test](https://github.com/anlar/prismriver-lyrics/actions/workflows/test.yml/badge.svg)](https://github.com/anlar/prismriver-lyrics/actions/workflows/test.yml)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
  [![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
</div>

## About

![Prismriver Lyrics Screenshot](https://raw.githubusercontent.com/anlar/prismriver-lyrics/refs/heads/master/docs/screenshot.png)

Prismriver Lyrics is a uv workspace with two packages built on a shared lyrics
search engine (`prismriver_lyrics`):

- `prismriver-lyrics` — a CLI that takes an artist/title, queries the
  registered plugins, and prints results.
- `prismriver-lyrics-tui` — a Textual terminal UI that reads the active MPRIS
  player's state over D-Bus, searches for lyrics on each track change, and
  renders the result, highlighting the current line for time-synced (LRC)
  lyrics.

Features:

- 30+ lyrics source plugins (`prismriver_lyrics.plugins`, auto-discovered
  `LyricsPlugin` subclasses)
- On-disk SQLite cache of results, with a configurable TTL (`--cache-ttl`) and
  a bypass flag (`--no-cache`)
- Filtering by plugin id, language, translated/original, or synced/plain-text,
  and a result cap (`--limit`/`-l`)
- Time-synced (LRC) lyrics, with the current line highlighted in the TUI as the
  track plays
- TUI manual search dialog (for when no MPRIS player is active or the
  auto-detected metadata is wrong), theme switching, and vim-style keybindings

### Built With

* [Python 3](https://www.python.org/)
* [Textual](https://textual.textualize.io/)
* [httpx](https://www.python-httpx.org/)
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
* [dbus-next](https://github.com/altdesktop/python-dbus-next)

## Getting Started

### Prerequisites

Prismriver Lyrics requires Python 3.12+.

### Installation

Both packages are published on PyPI. Install either or both with `pipx`, `pip`,
or `uv`:

```sh
$ pipx install prismriver-lyrics
$ pipx install prismriver-lyrics-tui
```

```sh
$ pip install prismriver-lyrics
$ pip install prismriver-lyrics-tui
```

```sh
$ uv tool install prismriver-lyrics
$ uv tool install prismriver-lyrics-tui
```

Alternatively, install from source using [`uv`](https://docs.astral.sh/uv/)
and `pipx`:

```sh
git clone https://github.com/anlar/prismriver-lyrics.git
cd prismriver-lyrics
make install-pipx
```

This builds both packages and installs each as its own isolated pipx app,
exposing both the `prismriver-lyrics` and `prismriver-lyrics-tui` commands.

## Usage

Search for lyrics from the CLI:

```sh
$ prismriver-lyrics --artist "The Clash" --title "Police and Thieves"
```

Or launch the terminal UI, which follows whatever's playing on an
MPRIS-compatible media player:

```sh
$ prismriver-lyrics-tui
```

Check other command line options using the help command:

```
$ prismriver-lyrics --help
$ prismriver-lyrics-tui --help
```

View the available hotkeys for the Prismriver Lyrics TUI in the status bar.

## Roadmap

See the [open issues](https://github.com/anlar/prismriver-lyrics/issues) for a
full list of proposed features (and known issues).

## Contributing

Feel free to open bug reports and send pull requests.

## License

Distributed under the MIT license. See `LICENSE.txt` for more information.
