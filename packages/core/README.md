# prismriver-lyrics

Core library and CLI for searching song lyrics across multiple sources.

## Usage

```sh
prismriver-lyrics --artist "Metallica" --title "Master of Puppets"
```

## Plugins

Lyrics sources live under `prismriver_lyrics.plugins` and implement the
`LyricsPlugin` interface (`prismriver_lyrics.plugins.base`). All registered
plugins are queried in parallel and the first successful hit wins.
