"""Game language that follows the system: infamous_run.system_game_language / resolve_game_language,
used by build_env, the Tk launcher and the Qt launcher. No test depends on the machine's locale."""
import os
import sys
import unittest
from unittest import mock

from paths import ROOT
sys.path.insert(0, str(ROOT / 'launcher'))
import infamous_run as run  # noqa: E402


class SystemGameLanguageTests(unittest.TestCase):
    def test_locale_mapping(self):
        cases = {'pt_BR.UTF-8': 'pt_BR', 'pt_PT': 'pt_BR', 'es_MX': 'es_LA', 'es_ES': 'es_LA', 'fr_FR': 'fr_CA',
                 'fr_CA': 'fr_CA', 'tr_TR': 'tr', 'ru_RU': 'ru', 'en_US': 'en', 'de_DE': 'en', 'C': 'en', 'POSIX': 'en',
                 'pt-BR': 'pt_BR', 'ru-RU': 'ru'}
        for value, expected in cases.items():
            self.assertEqual(expected, run.system_game_language({'LANG': value}), value)

    def test_variable_order_and_empty(self):
        self.assertEqual('ru', run.system_game_language({'LC_ALL': 'ru_RU', 'LC_MESSAGES': 'tr_TR', 'LANG': 'fr_FR'}))
        self.assertEqual('tr', run.system_game_language({'LC_MESSAGES': 'tr_TR', 'LANG': 'fr_FR'}))
        with mock.patch('locale.getlocale', return_value=(None, None)):
            self.assertEqual('en', run.system_game_language({}))
            self.assertEqual('en', run.system_game_language({'LANG': ''}))
        with mock.patch('locale.getlocale', return_value=('es_AR', 'UTF-8')):
            self.assertEqual('es_LA', run.system_game_language({}))
        with mock.patch('locale.getlocale', side_effect=ValueError):
            self.assertEqual('en', run.system_game_language({}))

    def test_default_is_auto(self):
        self.assertEqual('auto', run.DEFAULT_SETTINGS['game_language'])

    def test_resolve(self):
        env = {'LANG': 'tr_TR.UTF-8'}
        self.assertEqual('tr', run.resolve_game_language({'game_language': 'auto'}, env))
        self.assertEqual('tr', run.resolve_game_language({}, env))
        self.assertEqual('pt_BR', run.resolve_game_language({'game_language': 'pt_BR'}, env))   # kept
        self.assertEqual('tr', run.resolve_game_language({'game_language': 'klingon'}, env))    # invalid
        self.assertEqual('en', run.resolve_game_language({'game_language': 'auto'}, {'LANG': 'de_DE'}))

    def test_build_env(self):
        with mock.patch.dict(os.environ, {'LC_ALL': 'es_MX.UTF-8'}):
            os.environ.pop('ISS_LANGUAGE', None)
            settings = dict(run.DEFAULT_SETTINGS)
            self.assertEqual('20', run.build_env(settings)['ISS_LANGUAGE'])
            self.assertEqual('17', run.build_env(dict(settings, game_language='pt_BR'))['ISS_LANGUAGE'])
            os.environ['ISS_LANGUAGE'] = '8'                    # the environment wins
            self.assertEqual('8', run.build_env(settings)['ISS_LANGUAGE'])

    def test_tk_and_qt_use_the_same_function(self):
        tk = (ROOT / 'launcher' / 'infamous_launcher.py').read_text(encoding='utf-8')
        qt = (ROOT / 'launcher' / 'qt' / 'backend.py').read_text(encoding='utf-8')
        self.assertIn('tlg_run.resolve_game_language(self.settings)', tk)
        self.assertIn('tlg_run.resolve_game_language(self.settings)', qt)


if __name__ == '__main__':
    unittest.main()
