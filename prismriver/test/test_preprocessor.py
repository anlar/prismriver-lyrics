from prismriver import preprocessor

test_cases = [('Artist', 'Title', 'Artist', 'Title'),
              ('  Artist', '  Title', 'Artist', 'Title'),
              ('Artist ', 'Title ', 'Artist', 'Title'),
              (' Artist ', ' Title ', 'Artist', 'Title')]


def test():
    for params in test_cases:
        yield check_em, params[0], params[1], params[2], params[3]


def check_em(artist: str, title: str, clean_artist: str, clean_title: str):
    (processed_artist, processed_title) = preprocessor.apply(artist, title, ['trim'])
    assert processed_artist == clean_artist
    assert processed_title == clean_title
