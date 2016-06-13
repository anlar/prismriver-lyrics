#! /usr/bin/env bash

# Encoded artist name.
ARTIST="$1"

# Encoded song title.
TITLE="$2"

#Encoded album name.
ALBUM="$3"

unquote () {
  decoded_url=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.unquote(sys.argv[1]))' "$1")
  echo $decoded_url
}

UNQ_ARTIST=$(unquote "$ARTIST")
UNQ_TITLE=$(unquote "$TITLE")

prismriver-cli.py -t "$UNQ_TITLE" -a "$UNQ_ARTIST" --output $'%LYRICS%\n\nSource: %PLUGIN_NAME%'
