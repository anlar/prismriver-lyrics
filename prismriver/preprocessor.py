import logging


def apply(artist: str, title: str, options: '[str]') -> '[str]':
    if 'trim' in options:
        [artist, title] = trim(artist, title)

    return [artist, title]


def trim(artist: str, title: str) -> '[str]':
    new_artist = artist.strip()
    new_title = title.strip()

    log_change('trim', artist, title, new_artist, new_title)

    return [new_artist, new_title]


def log_change(operation: str, artist: str, title: str, new_artist: str, new_title: str) -> None:
    logging.debug('Perform "{}": "{}", "{}" -> "{}", "{}"'.format(operation, artist, title, new_artist, new_title))
