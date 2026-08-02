import argparse
import asyncio
import importlib.metadata
import sys

from prismriver_lyrics.cache import SearchCache
from prismriver_lyrics.models import SyncedLyrics
from prismriver_lyrics.registry import (
    default_plugins,
    filter_plugins,
    filter_results,
    parse_ids,
    print_plugins,
)
from prismriver_lyrics.search import search_lyrics
from prismriver_lyrics.util import DEFAULT_CACHE_TTL, parse_duration

_VERSION_MESSAGE = (
    "Prismriver Lyrics, version {version}\n"
    "License: MIT\n"
    "https://github.com/anlar/prismriver-lyrics"
)


def _lang_info(result) -> str | None:
    if not result.lang:
        return None
    target = result.lang.upper()
    if result.translation:
        source_lang = (
            result.original_lang.upper() if result.original_lang else "??"
        )
        return f"{source_lang} -> {target}"
    return target


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
        "--cache-ttl",
        type=parse_duration,
        default=DEFAULT_CACHE_TTL,
        metavar="DURATION",
        help="How long cached results stay valid, e.g. 1w, 1d5h, 90m. "
        "Default: %(default)s.",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        metavar="N",
        help="Limit the number of results printed. Default: unlimited.",
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
        "use ? to include results with an unknown/untagged language, or "
        "* to include results tagged with any (known) language. "
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

    # A lang/translated/sync filter lets some plugins be skipped up front
    # (see filter_plugins()), but that means the search may no longer
    # cover every plugin a plain, unfiltered search would have — so the
    # shared (artist, title) cache is bypassed rather than read from or
    # polluted with a partial result set in that case.
    hint_filtered = (
        langs is not None or translated is not None or synced is not None
    )
    plugins = (
        filter_plugins(default_plugins(), langs, translated, synced)
        if hint_filtered
        else None
    )
    use_cache = not args.no_cache and not hint_filtered

    results = asyncio.run(
        search_lyrics(
            args.artist,
            args.title,
            plugins=plugins,
            use_cache=use_cache,
            cache=SearchCache(ttl=args.cache_ttl),
        )
    )
    results = filter_results(results, plugin_ids, langs, translated, synced)

    if not results:
        print("No lyrics found.", file=sys.stderr)
        raise SystemExit(1)

    results = sorted(results, key=lambda result: result.source.lower())
    if args.limit is not None:
        results = results[: args.limit]

    blocks = []
    for result in results:
        lines = [f"source: {result.source}", f"url: {result.url}"]
        lang = _lang_info(result)
        if lang:
            lines.append(f"lang: {lang}")
        if not isinstance(result.lyrics, SyncedLyrics):
            lines.append("")
            lines.append(result.lyrics)
        blocks.append("\n".join(lines))

    print(f"# {args.artist} - {args.title}")
    print()
    print("\n\n---\n\n".join(blocks))


if __name__ == "__main__":
    main()
