# SPDX-License-Identifier: GPL-2.0-or-later
"""Developer tool: renders every screen offscreen to PNG files with demo data (no game, no GPU,
no real settings touched).   QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \\
    python3 -m qt.screenshots <out-dir>   (run from port/launcher)"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
sandbox = Path(tempfile.mkdtemp(prefix='iss-qt-shots-'))
os.environ['XDG_CONFIG_HOME'] = str(sandbox)   # the settings file of the demo, not the player's
os.environ['ISS_QT_REDUCED_MOTION'] = '1'      # the play button's pulse stays still

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import infamous_run as tlg_run  # noqa: E402
from qt import logic  # noqa: E402
from qt.app import App  # noqa: E402
from qt.backend import Backend  # noqa: E402


def demo_backend(with_art=False):
    settings = dict(tlg_run.DEFAULT_SETTINGS, ui_language='pt_BR', game_dir=str(sandbox / 'game'))
    if with_art:
        from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
        art = sandbox / 'game' / 'sce_sys'
        art.mkdir(parents=True, exist_ok=True)
        img = QImage(1920, 1080, QImage.Format.Format_RGB32)
        p = QPainter(img)
        g = QLinearGradient(0, 0, 1920, 1080)
        g.setColorAt(0, QColor('#22304a'))
        g.setColorAt(1, QColor('#6a2a3a'))
        p.fillRect(0, 0, 1920, 1080, g)
        p.end()
        img.save(str(art / 'pic1.png'))   # a synthetic stand-in, not game art
    states = {i.id: None for i in logic.backports_table.ITEMS}
    probes = {'gpu': lambda: ('NVIDIA GeForce RTX 2060', '1.4'), 'pad': lambda: 'DualSense',
              'problems': lambda: [], 'cache': lambda: 218 * 1024 * 1024,
              'save': lambda: 'Welcome to Seattle — 8%', 'version': lambda: 'v2026.10.15',
              'save_fixes': lambda s, st: None}
    backend = Backend(settings=settings, probes=probes)
    backend._gpu = probes['gpu']()
    backend.fix_states = states
    backend.fixes.rebuild()
    backend.refresh()
    return backend


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    backend = demo_backend(with_art='--art' in sys.argv)
    app = App(backend=backend)
    names = ['inicio', 'graficos', 'controles', 'correcoes', 'suporte', 'atualizacoes']
    app.window.setProperty('animate', False)
    prefix = 'art-' if '--art' in sys.argv else ''
    for index, name in enumerate(names):
        if prefix and index:
            break
        app.go(index)
        app.grab(out / f'{prefix}{name}.png')
    if not prefix:
        backend.setFix('BP06', '1')           # one change: profile becomes custom
        app.go(3)
        app.grab(out / 'correcoes-personalizado.png')
        backend.scrollRequested.emit(2400)
        app.grab(out / 'correcoes-fim.png')
        backend.setFix('BP06', '0')
        backend.setLang('en_US')
        for index, name in ((0, 'home-en'), (3, 'fixes-en')):
            app.go(index)
            app.grab(out / f'{name}.png')
    print('ok', out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'shots')
