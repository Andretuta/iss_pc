# SPDX-License-Identifier: GPL-2.0-or-later
"""Windows Defender exclusion of the shader cache folder (launcher/defender.py) and its card on the
Graphics page. Nothing here runs PowerShell: the elevated call is replaced by a fake. `paths` points
the launcher config at a throwaway folder."""
import base64
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from paths import ROOT
sys.path.insert(0, str(ROOT / 'launcher'))
import defender  # noqa: E402
import infamous_run  # noqa: E402

try:
    from PySide6.QtCore import QCoreApplication
    from qt.backend import Backend
    from qt.graphics import Graphics
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def decoded(arguments):
    return base64.b64decode(arguments.split('-EncodedCommand ')[1]).decode('utf-16-le')


class CommandTests(unittest.TestCase):
    def test_quotes_cannot_break_out(self):
        folder = r"C:\Users\O'Brien\AppData\Roaming\infamous-pc\cache"
        self.assertEqual(r"'C:\Users\O''Brien\AppData\Roaming\infamous-pc\cache'", defender.ps_quote(folder))
        text = decoded(defender.arguments(folder))
        self.assertIn("Add-MpPreference -ExclusionPath 'C:\\Users\\O''Brien", text)
        self.assertTrue(text.endswith('catch { exit 2 }'))

    def test_unicode_and_dollar_stay_literal(self):
        folder = 'C:\\Usuários\\João $env:TEMP\\cache'
        self.assertIn("'C:\\Usuários\\João $env:TEMP\\cache'", decoded(defender.arguments(folder)))

    def test_hidden_noninteractive(self):
        self.assertTrue(defender.arguments('x').startswith('-NoProfile -NonInteractive -WindowStyle Hidden '))


class ResultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / 'user' / 'cache'

    def test_added(self):
        calls = []
        result = defender.add_exclusion(self.folder, run=lambda exe, args: calls.append((exe, args)) or (0, 0))
        self.assertEqual(defender.OK, result)
        self.assertTrue(self.folder.is_dir())          # made before the first start too
        self.assertIn(str(self.folder), decoded(calls[0][1]))

    def test_no_in_the_prompt(self):
        self.assertEqual(defender.CANCELLED, defender.add_exclusion(self.folder, run=lambda *a: (None, 1223)))

    def test_refused_or_error(self):
        self.assertEqual(defender.FAILED, defender.add_exclusion(self.folder, run=lambda *a: (2, 0)))
        self.assertEqual(defender.FAILED, defender.add_exclusion(self.folder, run=lambda *a: (None, 5)))

        def boom(*_):
            raise OSError('no shell32')
        self.assertEqual(defender.FAILED, defender.add_exclusion(self.folder, run=boom))

    @unittest.skipIf(os.name == 'nt', 'not Windows only')
    def test_other_systems(self):
        self.assertFalse(defender.supported())
        self.assertEqual(defender.UNSUPPORTED, defender.add_exclusion(self.folder))

    def test_marked(self):
        self.assertFalse(defender.is_marked({}, self.folder))
        self.assertTrue(defender.is_marked({'defender_excluded': str(self.folder)}, self.folder))
        self.assertFalse(defender.is_marked({'defender_excluded': 'elsewhere'}, self.folder))

    def test_never_shared_in_presets(self):
        import preset_share
        self.assertNotIn('defender_excluded', preset_share.EXPORT_SETTINGS)
        self.assertEqual('', infamous_run.DEFAULT_SETTINGS['defender_excluded'])


@unittest.skipUnless(HAVE_QT, 'PySide6 not installed')
class CardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patcher = mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.dir / 'cfg'), 'APPDATA': str(self.dir / 'cfg'),
                                               'ISS_USER_DIR': str(self.dir / 'user')})
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ('TLG_USER_DIR', 'ISS_GPU_USER_DIR', 'TLG_GPU_USER_DIR'):
            os.environ.pop(key, None)

    def make(self, result, shown=True):
        probes = {'gpu': lambda: ('GPU', '1'), 'pad': lambda: None, 'problems': lambda: [], 'cache': lambda: 0,
                  'save': lambda: None, 'news': lambda: [], 'version': lambda: 'v1',
                  'saves': {'running': lambda: False, 'scan': lambda: [], 'open': lambda p: None}}
        settings = dict(infamous_run.DEFAULT_SETTINGS, game_dir='/g', ui_language='en_US')
        backend = Backend(settings=settings, probes=probes)
        self.asked = []
        graphics = Graphics(backend, {'vram': lambda: 6144, 'version': lambda: 'v1',
                                      'defender_shown': lambda: shown,
                                      'defender': lambda folder: self.asked.append(folder) or result})
        return graphics

    def wait(self, graphics):
        deadline = time.monotonic() + 5
        while graphics.defenderBusy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertFalse(graphics.defenderBusy)

    def test_added_is_remembered(self):
        graphics = self.make(defender.OK)
        self.assertFalse(graphics.defenderDone)
        graphics.addDefenderExclusion()
        self.assertEqual('Answer the Windows permission prompt…', graphics.defenderMessage)
        self.wait(graphics)
        folder = self.dir / 'user' / 'cache'
        self.assertEqual([folder], self.asked)
        self.assertTrue(graphics.defenderDone)
        self.assertEqual('good', graphics.defenderTone)
        saved = json.loads(infamous_run.config_path().read_text())
        self.assertEqual(str(folder), saved['defender_excluded'])
        self.assertTrue(str(infamous_run.config_path()).startswith(str(self.dir)))

    def test_cancelled_changes_nothing(self):
        graphics = self.make(defender.CANCELLED)
        graphics.addDefenderExclusion()
        self.wait(graphics)
        self.assertFalse(graphics.defenderDone)
        self.assertEqual('Cancelled: nothing changed.', graphics.defenderMessage)
        self.assertFalse(infamous_run.config_path().exists())

    def test_refused(self):
        graphics = self.make(defender.FAILED)
        graphics.addDefenderExclusion()
        self.wait(graphics)
        self.assertEqual('bad', graphics.defenderTone)
        self.assertFalse(graphics.defenderDone)

    def test_hidden_outside_windows(self):
        self.assertFalse(self.make(defender.OK, shown=False).defenderShown)


if __name__ == '__main__':
    unittest.main()
