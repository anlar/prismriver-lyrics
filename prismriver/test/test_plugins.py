import logging
import unittest
import hashlib

from prismriver.main import search


class TestPlugins(unittest.TestCase):
    def check_plugin(self, plugin_id, artist, title, lyric_hashes):
        logging.basicConfig(format='%(asctime)s %(levelname)s [%(module)s] %(message)s', level=logging.DEBUG)

        result = search(artist, title, limit=None, enabled_plugins=[plugin_id])

        self.assertEqual(1, len(result), 'Wrong songs count')
        self.assertEqual(len(lyric_hashes), len(result[0].lyrics), 'Wrong lyrics count')

        index = 0
        for lyric_hash in lyric_hashes:
            self.assertEqual(lyric_hash, self.get_md5(result[0].lyrics[index]),
                             'Different text in #{} lyrics'.format(index))
            index += 1

    def get_md5(self, value):
        return hashlib.md5(value.encode('utf-8')).hexdigest()

    def test_chartlyrics_01(self):
        self.check_plugin('chartlyrics',
                          'James Brown', 'Prisoner of Love',
                          ['a4cc13ee79455148090068388b74b8cf'])

    def test_lyricsmania_01(self):
        self.check_plugin('lyricsmania',
                          'Ayumi Hamasaki', '(Miss)understood',
                          ['f3fac3f5e50ca009457e5167e06fa728'])

    def test_lyricsmania_02(self):
        self.check_plugin('lyricsmania',
                          'Joe Esposito', 'You\'re The Best',
                          ['754cfd853d3f924bc243404b9306a222'])

    def test_lyricwiki_01(self):
        self.check_plugin('lyricwiki',
                          'Sound Holic', 'Grip & Break Down !!',
                          ['ea12362512264723fee26192a3ea53b5'])

    def test_megalyrics_01(self):
        self.check_plugin('megalyrics',
                          'Joe Dassin', 'Salut',
                          ['6882d41054640c1c4e9749af1f08966f',
                           'f6a941fd3d5297f25062d3912bea3752'])

    def test_megalyrics_02(self):
        self.check_plugin('megalyrics',
                          'Rammstein', 'Du hast',
                          ['9776ed55e1c7ca636a2fb69721127dc5',
                           '91f572732889601128280fb06eac2a95'])

    def test_touhouwiki_01(self):
        self.check_plugin('touhouwiki',
                          'FELT', 'World Around Us',
                          ['49c8b1f1d35cc7627b9f163d2301ef58'])

    def test_touhouwiki_02(self):
        self.check_plugin('touhouwiki',
                          'ShibayanRecords', 'Fall In The Dark',
                          ['29f3f203077b522be3d5da484732d0f0',
                           '0d6849e8150afc2c529fa790b5531968',
                           'c0d7a18839b1da9c2236a63559c6d8a5'])

    def test_touhouwiki_03(self):
        self.check_plugin('touhouwiki',
                          'Shinra-bansho', '受け入れられない真実',
                          ['1d6b57d693eee13ffb5eed10a31d6605',
                           '895cdd1950bdf462b2ed4d2f53d910a2',
                           '53ba62a6cb0b8d1a2311796b81aff106'])
