import logging
import random
from time import sleep
import unittest
import hashlib
import os
from unittest.case import SkipTest

from prismriver.main import search
from prismriver.struct import SearchConfig


class TestPlugins(unittest.TestCase):
    def check_plugin(self, plugin_id, artist, title, lyric_hashes):
        logging.basicConfig(format='%(asctime)s %(levelname)s [%(module)s] %(message)s', level=logging.DEBUG)

        self.is_skipped(plugin_id)

        retry_delay = int(os.getenv('PRISMRIVER_TEST_RETRY_DELAY', '120'))
        retry_count = int(os.getenv('PRISMRIVER_TEST_RETRY_COUNT', '0'))

        config = self.get_search_config(plugin_id)

        step = 0
        result = search(artist, title, config)
        while not result and step < retry_count:
            config.cache_web_ttl_sec = 0  # force test to re-download pages instead of getting them from cache
            delay = retry_delay * (step + 1)
            logging.debug('Empty search result, wait for {} sec. before retry'.format(delay))
            sleep(delay)
            result = search(artist, title, config)
            step += 1

        self.assertEqual(1, len(result), 'Wrong songs count')
        self.assertEqual(len(lyric_hashes), len(result[0].lyrics), 'Wrong lyrics count')

        index = 0
        for lyric_hash in lyric_hashes:
            logging.debug('Lyric #{}:\n'.format(index) + result[0].lyrics[index])
            self.assertEqual(lyric_hash, self.get_md5(result[0].lyrics[index]),
                             'Different text in #{} lyrics'.format(index))
            index += 1

    def is_skipped(self, plugin_id):
        disabled_plugins = os.getenv('PRISMRIVER_TEST_DISABLED_PLUGINS', '').split(',')
        if plugin_id in disabled_plugins:
            raise SkipTest('plugin test disabled')

    def setUp(self):
        max_delay = int(os.getenv('PRISMRIVER_TEST_MAX_DELAY', '0'))
        delay = random.randint(0, max_delay)
        logging.debug('Wait {}sec. before executing test...'.format(delay))
        sleep(delay)

    def get_md5(self, value):
        return hashlib.md5(value.encode('utf-8')).hexdigest()

    def get_search_config(self, plugin_id):
        config = SearchConfig(enabled_plugins=[plugin_id], web_timeout_sec=60, sync=True)
        config.debug_log_page = bool(os.getenv('PRISMRIVER_TEST_LOG_PAGE', False))
        return config

    def test_absolutelyrics_01(self):
        self.check_plugin('absolutelyrics',
                          'Ace Of Base', "Cruel Summer (C'est Fini)",
                          ['ffc15aa756b305cbae8c3a7e0533f636'])

    def test_alivelyrics_01(self):
        self.check_plugin('alivelyrics',
                          'Ace Of Base', "Never Gonna Say I'm Sorry",
                          ['95c85dedd498ecfe8591fb09c98d47bb'])

    def test_allyrics_01(self):
        self.check_plugin('allyrics',
                          'Megumi Hayashibara', 'Omokage (English)',
                          ['caded604d9ec062a2e7236ab30728350'])

    def test_alphabetlyrics_01(self):
        self.check_plugin('alphabetlyrics',
                          'Ace of Base', "C'est La Vie (Always 21)",
                          ['b31dc2a31407badc08efbfb782fd2f81'])

    def test_amalgama_01(self):
        self.check_plugin('amalgama',
                          'Modern Talking', "You're My Heart, You're My Soul",
                          ['7236c048b8f71ba1e7485136efba5abf',
                           '1aa073ad09ad5b3d10cc67e4d4060ab7',
                           '7b2a083cfbf7d20ad7e1b3749b229564'])

    def test_amalgama_02(self):
        self.check_plugin('amalgama',
                          'Modern Talking', 'China in Her Eyes (Rap Version)',
                          ['23b184a36effe86c42ec29e65fcbc512',
                           '9bc36b6bd9160f86f7378964d6267928',
                           'bbeccf0b9e0670bdcb4049aa38ae5f29'])

    def test_animelyrics_01(self):
        self.check_plugin('animelyrics',
                          'Yui Horie', 'ALL MY LOVE',
                          ['38f0889fce3c422d894d1e766e14f492',
                           'f474cf8ef4017fd9a2adda76c88bde2c',
                           '5636bb331d8d91da75c4477a78e0ae56'])

    def test_animelyrics_02(self):
        self.check_plugin('animelyrics',
                          'supercell', 'Kokuhaku',
                          ['12933b6f2b339d01b9b1bbb7228525c4',
                           'fa2bdfc06457002b0640ac4f6d782ced'])

    def test_animelyrics_03(self):
        self.check_plugin('animelyrics',
                          'Konomi Suzuki', 'Yume no Tsuzuki',
                          ['ddc2639d5ce46acfba260d38cc21a74a',
                           'c05345db62f58cff9ca2c9facf038d1e'])

    def test_animelyrics_04(self):
        self.check_plugin('animelyrics',
                          'Luca Yumi', 'Truth',
                          ['b67b5b76497a3bf3dfde36c58f489279',
                           '68a292d2337da33f80bf80c8e01bc81f',
                           '680a12a7055ca78f51e9a3e80a9af8fd'])

    def test_animelyrics_05(self):
        self.check_plugin('animelyrics',
                          'Kalafina', 'Door',
                          ['2ff25479cf3f32794a757b803dd87827',
                           '3f9c95a21fc726c5836af0dc8673360e'])

    def test_azlyrics_01(self):
        self.check_plugin('azlyrics',
                          'Modern Talking', "You're My Heart, You're My Soul",
                          ['c02cee74bc3d8bc20ed95e8ff5b39c13'])

    def test_azlyrics_02(self):
        self.check_plugin('azlyrics',
                          'Modern Talking', "Atlantis Is Calling (S.O.S. For Love)",
                          ['4b826df521c5a9ca057796daa760b5b7'])

    def test_bandcamp_01(self):
        self.check_plugin('bandcamp',
                          'Odyssey & the DNA Team', 'Chained Lady [Extended]',
                          ['19c3f184d060a768d249faba9b91a53d'])

    def test_chartlyrics_01(self):
        self.check_plugin('chartlyrics',
                          'James Brown', 'Prisoner of Love',
                          ['a4cc13ee79455148090068388b74b8cf'])

    def test_darklyrics_01(self):
        self.check_plugin('darklyrics',
                          'DragonForce', 'Revolution Deathsquad',
                          ['37aab959e8f7a4bb8a8edff75f4e039e'])

    def test_directlyrics_01(self):
        self.check_plugin('directlyrics',
                          'Daft Punk', "Doin' It Right",
                          ['780eeea5024d3c8208e4f98a3e1ad1f6'])

    def test_elyrics_01(self):
        self.check_plugin('elyrics',
                          'C.C. Catch', "V.i.p. (they're Calling Me Tonight)",
                          ['f841980a7040ff3733e41cf75f075b04'])

    def test_elyrics_02(self):
        self.check_plugin('elyrics',
                          'Dschinghis Khan', 'Pistolero',
                          ['4be7cef73596ded5201904c31b4ced91'])

    def test_evesta_01(self):
        self.check_plugin('evesta',
                          '林原 めぐみ', 'BRAVE SOULS ～give a reason',
                          ['aa3322837c81e5dd4cd4be3e00e7868a'])

    def test_genius_01(self):
        self.check_plugin('genius',
                          'The Bee Gees', "I Can't Help It (with Olivia Newton-John)",
                          ['98cf0624d48892db275b16b865d8cc97'])

    def test_jetlyrics_01(self):
        self.check_plugin('jetlyrics',
                          'Kalafina', 'to the beginning',
                          ['8f6757f252792fc316e4367db91aae88',
                           '505e2ace457caaacd3a0125478d14c60'])

    def test_jlyric_01(self):
        self.check_plugin('jlyric',
                          '宇多田ヒカル', 'Beautiful World',
                          ['0f8a63e0369675653f2c734a534555fe'])

    def test_jlyric_02(self):
        self.check_plugin('jlyric',
                          '浜崎あゆみ', 'Bold & Delicious',
                          ['87cdd3d59e867ece975a49c2129d3aa6'])

    def test_jlyricsru_01(self):
        # entry has only original lyrics
        self.check_plugin('jlyricsru',
                          'Nakabayashi May', "Welcome To My FanClub's Night!",
                          ['80651e5c7478268ac3788244fa861b50'])

    def test_jlyricsru_02(self):
        # entry has original, en and ru translated lyrics
        self.check_plugin('jlyricsru',
                          'Access', 'Doubt & Trust',
                          ['c76c0549bc0edc06c919f305d0dd506e',
                           '2f6f3ccea179f44caa1ea2e969d1a36e',
                           '40e0026f93add2f867971ac270726474'])

    def test_jlyricsru_03(self):
        # entry has original, en and 2 ru translated lyrics
        # and there are 3 artist fields
        self.check_plugin('jlyricsru',
                          'Asumi Kana', 'Koi wa Konton no Reiya',
                          ['ce2c22a9ba932d56446cb4bc7fddb4e7',
                           '270916af302cb1483d61a55e5635cc06',
                           '889aae7c3e241e26c8e57dc0753be969',
                           'adbd8436ceecba9ed48eb78f93a2fb0b'])

    def test_kashinavi_01(self):
        self.check_plugin('kashinavi',
                          'Kalafina', 'moonfesta〜ムーンフェスタ〜',
                          ['38e459cefc05b564f762846cb1b9c221'])

    def test_kasitime_01(self):
        self.check_plugin('kasitime',
                          'いとうかなこ', 'Hacking to the Gate',
                          ['2917f7e96bcd394d6292696f83a47e52'])

    def test_kget_01(self):
        self.check_plugin('kget',
                          'YUI', 'CHE.R.RY ～Bossa Live Version～',
                          ['7f96f730bf8b3181d203d2ca50bf2112'])

    def test_kget_02(self):
        self.check_plugin('kget',
                          'Groove Coverage', '7 years & 50 days (Cascada vs. Plazmatek Remix)',
                          ['7efbe88d207031795a16f85f5c2f2460'])

    def test_kget_03(self):
        self.check_plugin('kget',
                          '浜崎あゆみ', 'A Song for ××',
                          ['e06cfe45fa4e261ff92c30fd444ce39e'])

    def test_letras_01(self):
        # simple case - lyrics: div.p.text
        self.check_plugin('letras',
                          'Ayumi Hamasaki', 'Is This Love?',
                          ['8a8ffe4e08b0d438bc145eaff0a1eec5'])

    def test_letras_02(self):
        # lyrics with additional paragraph level - lyrics: div.p.p.text
        self.check_plugin('letras',
                          'Mirai Nikki', 'Dead End',
                          ['a7358c18d3b45f7de86e368dcc2e4755'])

    def test_letssingit_01(self):
        self.check_plugin('letssingit',
                          "Blackmore's Night", 'Shadow Of The Moon',
                          ['d41eb27d17ea1adcd1f1eabc7e27ce37'])

    def test_lololyrics_01(self):
        self.check_plugin('lololyrics',
                          'Daft Punk', 'Harder, Better, Faster, Stronger',
                          ['b97a0f09485238d5fb09780c44d54c51'])

    def test_lololyrics_02(self):
        self.check_plugin('lololyrics',
                          'Groove Coverage', 'Holy Virgin (Radio Edit)',
                          ['5348e8a8cb887b00ae918dffe518ed51'])

    def test_lyricsaction_01(self):
        self.check_plugin('lyricsaction',
                          'Megumi Hayashibara', 'Northern Lights (Midnight Wedding Mix)',
                          ['022039d57cc9138b0aa4827fd9d81f43'])

    def test_lyricalnonsense_01(self):
        self.check_plugin('lyricalnonsense',
                          'supercell', 'ワールドイズマイン',
                          ['5ade846c09fb4ce827482fbc179b0c34',
                           '3b4b84e5bda3df6443e3b6cfc309c5dc',
                           'd04c60b41653cf8dfef9fc76af9d8e8a'])

    def test_lyricalnonsense_02(self):
        self.check_plugin('lyricalnonsense',
                          'CHiCO with HoneyWorks', 'Pride Kakumei',
                          ['8012b45bb22c66fc29ae1e9b187a007a',
                           '4e4e4d50316b66c3d777bc1fc835fedd',
                           '74173c292dbe4e186a1fc19833ce69e0',
                           'd3bba39ec6acaea1d331102ad95bacc9',
                           '9036ad7dd21e63b6f8e7349a590bdf49',
                           'e5fdf7fd58d25afb98acfeecf31adcb7'])

    def test_lyricscom_01(self):
        self.check_plugin('lyricscom',
                          'Yuki Kajiura', 'Open Your Heart',
                          ['ea318b768fa5a169a0b28362f1c1635f'])

    def test_lyricshuddle_01(self):
        self.check_plugin('lyricshuddle',
                          'Daft Punk', "One More Time (romanthony's Unplugged Version)",
                          ['9931445a1c03a8cc78745ffcba611691'])

    def test_lyricshuddle_02(self):
        self.check_plugin('lyricshuddle',
                          'Daft Punk', "Harder, Better, Faster, Stronger (neptunes Remix)",
                          ['995db98bba775ccf4e8cbc97efd37e98'])

    def test_lyricsdepot_01(self):
        self.check_plugin('lyricsdepot',
                          'Daft Punk', 'Harder, Better, Faster, Stronger',
                          ['58032c5a972b3ea6b4ac7e597f75fb98'])

    def test_lyricsfreak_01(self):
        self.check_plugin('lyricsfreak',
                          'Megumi Hayashibara', 'Give A Reason (From Slayers Next)',
                          ['4adfbc3482fc3e8fc340d98855a122ac'])

    def test_lyricsmania_01(self):
        self.check_plugin('lyricsmania',
                          'Ayumi Hamasaki', '(Miss)understood',
                          ['42029923f3f4a69d2c6b0b3525e387c1'])

    def test_lyricsmania_02(self):
        self.check_plugin('lyricsmania',
                          'Joe Esposito', 'You\'re The Best',
                          ['a9fc94979c4ec8e245ce80740cc63fc1'])

    def test_lyricsmode_01(self):
        # lyric with great quantity of comments
        self.check_plugin('lyricsmode',
                          'MandoPony', 'Just Gold',
                          ['46e6b0d4b5928704503abb75ca9a45ea'])

    def test_lyricsmode_02(self):
        # lyric without comments
        self.check_plugin('lyricsmode',
                          'Megumi Hayashibara', 'Touch Yourself',
                          ['c418607c95c0d341d90a373ae78a1723'])

    def test_lyricsnet_01(self):
        self.check_plugin('lyricsnet',
                          'Oingo Boingo', 'No One Lives Forever',
                          ['83060a72896096b3ace676945d4b7317'])

    def test_lyricsnmusic_01(self):
        self.check_plugin('lyricsnmusic',
                          'Joe Dassin', 'Le Moustique',
                          ['492a37b433c45767a589eefbec8060a3'])

    def test_lyricsplace_01(self):
        self.check_plugin('lyricsplace',
                          'Ace of Base', 'Never Gonna Say I\'m Sorry',
                          ['adda1df81c49b9e8d55af164ceef35d5'])

    def test_lyricsreg_01(self):
        self.check_plugin('lyricsreg',
                          'Groove Coverage', '7 Years & 50 Days',
                          ['de1d69411a7e4eada406fdd48d32281e'])

    def test_lyricwiki_01(self):
        self.check_plugin('lyricwiki',
                          'Sound Holic', 'Grip & Break Down !!',
                          ['ea12362512264723fee26192a3ea53b5'])

    def test_lyricwiki_02(self):
        # original lyric on main page, one translation on separate page
        self.check_plugin('lyricwiki',
                          'Kalafina', 'Red Moon',
                          ['a2cf1a1d1b54145d262418d22cac9381',
                           '3a8a2b0b4ec438a9cef665b861ef0f43'])

    def test_lyricwiki_03(self):
        self.check_plugin('lyricwiki',
                          'Jeff Williams & Casey Lee Williams', 'Red Like Roses (Red Trailer)',
                          ['e27047e110f688d3b0a8ba8ea381f245'])

    def test_lyricwiki_04(self):
        self.check_plugin('lyricwiki',
                          "Blackmore's Night", 'Beyond The Sunset',
                          ['c68011d57b164ae6c719fcf116a31541'])

    def test_lyricwiki_05(self):
        self.check_plugin('lyricwiki',
                          "Kotoko & Hiromi Sato", 'Second Flight',
                          ['611161c9feeb34ed117ccccfd6277722',
                           '6fdc1b2c608a847f9f89c635eba09be9',
                           'd0ce0dd39f3bb0d645480093d84b254e'])

    def test_lyrsense_01(self):
        self.check_plugin('lyrsense',
                          'AC/DC', 'Highway to hell',
                          ['02891effb5c7733b463cf74456cfafc5',
                           '2ff5eddc4b37c5596d4178ac1403ece5'])

    def test_lyrster_01(self):
        self.check_plugin('lyrster',
                          'Groove Coverage', 'Damn!',
                          ['b7efbc6c5899c123e0459324c66732ac'])

    def test_lyrster_02(self):
        self.check_plugin('lyrster',
                          'Pink Floyd', 'The Wall (complete)',
                          ['5011d7e7a1a26480601237820e65ef4d'])

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

    def test_metallum_01(self):
        self.check_plugin('metallum',
                          'DragonForce', 'Operation Ground and Pound',
                          ['04a8019d2569aa8cdbe5d31160dbad61'])

    def test_metrolyrics_01(self):
        self.check_plugin('metrolyrics',
                          'Ace of Base', "Never Gonna Say I'm Sorry",
                          ['f3e7fbdfd3c1bc85a21dad24188b75b4'])

    def test_metrolyrics_02(self):
        self.check_plugin('metrolyrics',
                          'Joe Dassin', "Et Si Tu N'existais Pas",
                          ['788563902df68de8c27b2f04f20a7568'])

    def test_mp3lyrics_01(self):
        self.check_plugin('mp3lyrics',
                          'Ace of Base', "Never Gonna Say I'm Sorry",
                          ['4b368840c5b409d6107bf8fdca935b1b'])

    def test_nitrolyrics_01(self):
        self.check_plugin('nitrolyrics',
                          'C. C. Catch', "Can't Catch Me",
                          ['231af8f3447878ac33625e9e36c36047'])

    def test_1musiclyrics_01(self):
        self.check_plugin('1musiclyrics',
                          'Megumi Hayashibara', 'Give A Reason (From Slayers Next)',
                          ['3197946854a8a14c188018f32764476c'])

    def test_musixmatch_01(self):
        self.check_plugin('musixmatch',
                          '林原めぐみ', 'Over Soul',
                          ['feb98569635577eeb9c4d16e63eed9dd'])

    def test_musixmatch_02(self):
        self.check_plugin('musixmatch',
                          'Кино', 'Невесёлая песня',
                          ['b9ed3e78498f564e37d708306ac08dc3'])

    def test_nautiljon_01(self):
        # only original lyrics
        self.check_plugin('nautiljon',
                          'Perfume', 'Pick Me Up',
                          ['7867f09d5c27d2c46600f2cc8397924b'])

    def test_nautiljon_02(self):
        # original and translated lyrics
        self.check_plugin('nautiljon',
                          'Perfume', 'Cling Cling',
                          ['85e912b195d6aaa816842f64828efaa2',
                           '0503a47e1046b7f52128a652e81a1b06'])

    def test_nitrolyrics_02(self):
        self.check_plugin('nitrolyrics',
                          'Bad Boys Blue', 'A World Without You (michelle)',
                          ['ad1240f4f772fc36e5286c4a4f29f187'])

    def test_onesonglyrics_01(self):
        self.check_plugin('1songlyrics',
                          'Megumi Hayashibara', 'Exit->Running',
                          ['5ccc738d3df217f31682b25be6156a0f'])

    def test_seekalyric_01(self):
        self.check_plugin('seekalyric',
                          'Megumi Hayashibara', 'Give A Reason (From Slayers Next)',
                          ['d9a7905a87a11de3c99bd3176e1e905f'])

    def test_showmelyrics_01(self):
        self.check_plugin('showmelyrics',
                          'Joe Dassin', 'Don’t Sit Under the Apple Tree [Live]',
                          ['4bfa677bc254640c6285483c7bb2f210'])

    def test_sing365_01(self):
        self.check_plugin('sing365',
                          'Utada Hikaru', "Easy Breezy",
                          ['a2d01052c8e1c508eab40d54303eab1b'])

    def test_snakie_01(self):
        # lyrics located in the last paragraph
        self.check_plugin('snakie',
                          'Aoi Eir', 'Addicted...',
                          ['5dfbff839820acafb8f63c32f3bcb70f'])

    def test_snakie_02(self):
        # lyrics located in next to the last paragraph
        self.check_plugin('snakie',
                          'Kalafina', 'believe',
                          ['bc3acdffab7e4591df061b99366735ae'])

    def test_song5_01(self):
        # entry has only original lyrics
        self.check_plugin('song5',
                          'Megumi Hayashibara', 'Kujikenai Kara! (OST Рубаки)',
                          ['931f9fae6741a8b689ebf7dfc964c55d'])

    def test_songlyrics_01(self):
        self.check_plugin('songlyrics',
                          'Modern Talking', "You're My Heart, You're My Soul",
                          ['cf59e45d8ce8070a0db077ddfb88343c'])

    def test_songlyrics_02(self):
        self.check_plugin('songlyrics',
                          'Modern Talking', "Geronimo's Cadillac (New Version)",
                          ['5ce4ce7e3be27a0ba4c4fe86b55fb767'])

    def test_songslyrics_01(self):
        self.check_plugin('songslyrics',
                          'Oingo Boingo', "Dead Man's Party",
                          ['9afeef8198423784d8ac26dce178d139'])

    def test_sonichits_01(self):
        self.check_plugin('sonichits',
                          'Bee Gees', "Stayin' Alive",
                          ['42539cecba26bb367286b017b727ee52'])

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
                          ['bf8cc305e81594b38d5b282b58e53d68',
                           'a7de7b5e4460d573c87feded75709bce',
                           '3b5ae103d34b8a1e5d782f8439b400ad'])

    def test_utamap_01(self):
        self.check_plugin('utamap',
                          '宇多田ヒカル', "Keep Tryin'",
                          ['8372d40e5149f86b40260052812572f7'])

    def test_utanet_01(self):
        self.check_plugin('utanet',
                          'いとうかなこ', 'Brave the Sky',
                          ['f13a38b1fca24935a949abdb4c3f4534'])

    def test_utaten_01(self):
        self.check_plugin('utaten',
                          'いとうかなこ', 'Brave the Sky',
                          ['09273a9bc31ac68987a1da44757bfb36'])

    def test_vagalume_01(self):
        self.check_plugin('vagalume',
                          'Ito Kanako', 'Hacking To The Gate',
                          ['34a5b44635a7aeaac6242fdac86198f5'])
