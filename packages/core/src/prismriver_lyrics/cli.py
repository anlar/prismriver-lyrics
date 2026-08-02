import argparse
import asyncio
import importlib.metadata
import sys

from prismriver_lyrics.models import SyncedLyrics
from prismriver_lyrics.registry import (
    default_plugins,
    filter_results,
    parse_ids,
    print_plugins,
)
from prismriver_lyrics.search import search_lyrics

_VERSION_MESSAGE = (
    "Prismriver Lyrics, version {version}\n"
    "License: MIT\n"
    "https://github.com/anlar/prismriver-lyrics"
)


def main() -> None:
    version = importlib.metadata.version("prismriver-lyrics")
    parser = argparse.ArgumentParser(
        prog="prismriver-lyrics",
        description=(
            "Search for song lyrics across multiple sources and print the "
            "first match."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--artist", "-a", help="Song artist.")
    parser.add_argument("--title", "-t", help="Song title.")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the on-disk results cache and force a fresh search.",
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Print the available plugins (id<TAB>name) and exit.",
    )
    parser.add_argument(
        "--filter-plugins",
        metavar="ID[,ID...]",
        help="Only show results from these plugin ids (see --plugins). "
        "Default: all.",
    )
    parser.add_argument(
        "--filter-lang",
        metavar="CODE[,CODE...]",
        help="Only show results tagged with one of these language codes; "
        "use ? to include results with an unknown/untagged language. "
        "Default: all.",
    )
    parser.add_argument(
        "--filter-translated",
        choices=("0", "1"),
        metavar="{0,1}",
        help="Only show translated (1) or original (0) results. "
        "Default: both.",
    )
    parser.add_argument(
        "--filter-sync",
        choices=("0", "1"),
        metavar="{0,1}",
        help="Only show time-synced (1) or plain-text (0) results. "
        "Default: both.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_VERSION_MESSAGE.format(version=version),
    )
    args = parser.parse_args()

    if args.plugins:
        print_plugins()
        return

    if not args.artist or not args.title:
        parser.error(
            "the following arguments are required: --artist/-a, --title/-t"
        )

    plugin_ids = parse_ids(args.filter_plugins)
    langs = parse_ids(args.filter_lang)
    translated = (
        None if args.filter_translated is None
        else args.filter_translated == "1"
    )
    synced = None if args.filter_sync is None else args.filter_sync == "1"

    if plugin_ids is not None:
        unknown = plugin_ids - {p.id for p in default_plugins()}
        if unknown:
            parser.error(
                f"unknown plugin id(s): {', '.join(sorted(unknown))}"
            )

    results = asyncio.run(
        search_lyrics(args.artist, args.title, use_cache=not args.no_cache)
    )
    results = filter_results(results, plugin_ids, langs, translated, synced)

    if not results:
        print("No lyrics found.", file=sys.stderr)
        raise SystemExit(1)

    result = results[0]
    print(f"# {args.artist} - {args.title}")
    print(f"# source: {result.source} ({result.url})")
    print()
    if isinstance(result.lyrics, SyncedLyrics):
        print("\n".join(line.text for line in result.lyrics.lines))
    else:
        print(result.lyrics)


if __name__ == "__main__":
    main()
