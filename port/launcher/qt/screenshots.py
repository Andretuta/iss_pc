# SPDX-License-Identifier: GPL-2.0-or-later
"""Developer tool: renders every screen offscreen to PNG files with demo data (no game, no GPU,
no real settings touched).   QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \\
    python3 -m qt.screenshots <out-dir>   (run from port/launcher)"""
import datetime
import os
import shutil
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
tlg_run.PORT_DIR = sandbox / 'port'            # portable mode points inside the sandbox, never at real saves
from qt import logic  # noqa: E402
from qt.app import App  # noqa: E402
from qt.backend import Backend  # noqa: E402


def demo_saves(user, pt=True, auto_ts=1_792_008_146):
    """Four invented saves with synthetic thumbnails (icon0.png stand-ins, not game art)."""
    import struct
    from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
    titles = [('infamousssAuto0', 'Bem-vindo a Seattle (Bom karma) - 8%' if pt else 'Welcome to Seattle (Good Karma) - 8%'),
              ('infamousssAuto1', 'Cuidado com o Conduíte (Mau karma) - 21%' if pt else 'Mind the Conduit (Evil Karma) - 21%'),
              ('infamousssUser0', 'Bem-vindo a Seattle (Bom karma) - 8%' if pt else 'Welcome to Seattle (Good Karma) - 8%'),
              ('infamousssUser1', 'Ilha Curdun (Bom karma) - 54%' if pt else 'Curdun Island (Good Karma) - 54%')]
    colors = ['#22304a', '#4a2230', '#2a4a30', '#4a3d22']
    for n, ((slot, subtitle), color) in enumerate(zip(titles, colors)):
        game = Path(user) / 'savedata' / '1' / 'CUSA00223'
        (game / slot).mkdir(parents=True, exist_ok=True)
        (game / (slot + '.sce_sys')).mkdir(parents=True, exist_ok=True)
        (game / slot / 'dis.dat').write_bytes(b'\0' * (96 * 1024 + n * 4096))
        data = bytearray(1328)
        data[0:19] = b'inFAMOUS Second Son'
        data[128:128 + len(subtitle.encode())] = subtitle.encode()
        struct.pack_into('<Q', data, 0x508, auto_ts - n * 5400)
        (game / (slot + '.sce_sys') / 'param.bin').write_bytes(bytes(data))
        img = QImage(228, 128, QImage.Format.Format_RGB32)
        p = QPainter(img)
        g = QLinearGradient(0, 0, 228, 128)
        g.setColorAt(0, QColor(color))
        g.setColorAt(1, QColor('#101216'))
        p.fillRect(0, 0, 228, 128, g)
        p.end()
        img.save(str(game / (slot + '.sce_sys') / 'icon0.png'))
        for f in game.rglob('*'):
            os.utime(f, (auto_ts - n * 5400,) * 2)


def demo_backend(with_art=False, saves_dir=None, pt=True):
    settings = dict(tlg_run.DEFAULT_SETTINGS, ui_language='pt_BR' if pt else 'en_US', game_dir=str(sandbox / 'game'))
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
    probes['saves'] = {'running': lambda: False, 'scan': lambda: [
        {'path': '/home/demo/Downloads/infamous-windows-x86_64/infamous-windows-x86_64/user', 'saves': 3,
         'newest': 1_791_000_000.0}]}
    backend = Backend(settings=settings, probes=probes)
    backend._gpu = probes['gpu']()
    backend.fix_states = states
    backend.fixes.rebuild()
    backend.refresh()
    return backend


def saves_shots(app, backend, out):
    """The Saves and data screen in both languages, in its main states (demo data only)."""
    from qt import saves as saves_mod  # noqa: F401
    import savemanager
    import userdata
    documents = sandbox / 'Documents' / 'inFAMOUS-PC'
    for lang, pt in (('pt', True), ('en', False)):
        shutil.rmtree(documents, ignore_errors=True)
        demo_saves(documents, pt)
        userdata.set_user_dir(documents)
        savemanager.set_prefs(keep=10, extra='/mnt/disco2/backup-infamous')
        for i in range(3):   # a few backups with different dates
            pass
        shutil.rmtree(documents / 'savedata_backups', ignore_errors=True)
        for n, stamp in enumerate((datetime.datetime(2026, 10, 15, 9, 41, 12), datetime.datetime(2026, 10, 14, 22, 5, 3))):
            f = documents / 'savedata' / '1' / 'CUSA00223' / 'infamousssUser1' / 'dis.dat'
            f.write_bytes(b'\0' * (50000 + n * 1000))
            os.utime(f, (stamp.timestamp(),) * 2)
            savemanager.save_backup.backup(documents, now=stamp)
        backend.setLang('pt_BR' if pt else 'en_US')
        backend.reload_user()
        backend.saves.scan()
        app.go(4)
        app.grab(out / f'saves-{lang}.png')
        backend.saves.scrollRequested.emit(620)
        app.grab(out / f'saves-{lang}-fim.png')
        backend.saves.scrollRequested.emit(0)
    # portable mode: no pointer, data beside the game, and nothing in it
    userdata.reset_user_dir()
    backend.saves.say(backend.t_('saves_dir_changed', path=str(sandbox / 'port' / 'user')), 'good')
    backend.reload_user()
    backend.saves.scan()
    app.go(4)
    app.grab(out / 'saves-portatil-en.png')
    backend.saves.dismissMessage()
    backend.setLang('pt_BR')
    app.go(0)
    app.grab(out / 'inicio-aviso-saves.png')
    # confirmation card
    userdata.set_user_dir(documents)
    backend.reload_user()
    backend.saves.askDelete('1/infamousssUser1')
    app.go(4)
    app.grab(out / 'saves-confirmar.png')
    backend.saves.answer('cancel')


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    backend = demo_backend(with_art='--art' in sys.argv)
    app = App(backend=backend)
    names = ['inicio', 'graficos', 'controles', 'correcoes', 'saves', 'guias', 'suporte', 'atualizacoes']
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
        saves_shots(app, backend, out)
        for lang, code in (('pt', 'pt_BR'), ('en', 'en_US')):
            backend.setLang(code)
            for kind in ('xbox', 'switch'):
                backend.setGuideKind(kind)
                app.go(5)
                app.grab(out / f'guias-{kind}-{lang}.png')
        backend.setGuideKind('8bitdo')
        backend.probes['guide_dir'] = sandbox / 'no-images'
        backend.guideChanged.emit()
        app.grab(out / 'guias-sem-imagens.png')
    print('ok', out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'shots')
