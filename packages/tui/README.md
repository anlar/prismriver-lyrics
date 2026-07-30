# prismriver-lyrics-tui

Textual terminal UI that watches the active MPRIS media player over D-Bus
and displays the player, artist, title, and matching lyrics fetched via
`prismriver-lyrics`.

## Usage

```sh
prismriver-lyrics-tui
```

Requires a running D-Bus session bus and an MPRIS-compliant media player
(e.g. VLC, mpv with the mpris plugin, rhythmbox, etc).
