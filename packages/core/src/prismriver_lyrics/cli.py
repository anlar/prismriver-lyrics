import asyncio

import click

from prismriver_lyrics.search import search_lyrics

_VERSION_MESSAGE = (
    "Prismriver Lyrics, version %(version)s\n"
    "License: MIT\n"
    "https://github.com/anlar/prismriver-lyrics"
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--artist", "-a", required=True, help="Song artist.")
@click.option("--title", "-t", required=True, help="Song title.")
@click.version_option(
    package_name="prismriver-lyrics", message=_VERSION_MESSAGE
)
def main(artist: str, title: str) -> None:
    """Search for song lyrics across multiple sources and print the first
    match."""
    results = asyncio.run(search_lyrics(artist, title))

    if not results:
        click.echo("No lyrics found.", err=True)
        raise SystemExit(1)

    result = results[0]
    click.echo(f"# {artist} - {title}")
    click.echo(f"# source: {result.source} ({result.url})")
    click.echo()
    click.echo(result.lyrics)


if __name__ == "__main__":
    main()
