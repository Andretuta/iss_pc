# SPDX-License-Identifier: GPL-2.0-or-later
"""Windows Defender exclusion for the shader cache folder (Windows only, opt-in).

After the first start the cache holds tens of thousands of small files, and the game writes more
while it plays. Defender scans each one when it is written or read, which slows the first-start
compilation and every walk of the folder. Adding an exclusion needs administrator rights, so only
this one command runs elevated: Windows shows its permission prompt (UAC) once, and the launcher
and the game keep running as the normal user (running them as administrator would not stop the
scans, and would leave saves and settings owned by the administrator).

The player's choice is remembered in the settings (defender_excluded = the folder): reading the
exclusion list back needs administrator rights too.
"""
import base64
import os
from pathlib import Path

OK, CANCELLED, FAILED, UNSUPPORTED = 'ok', 'cancelled', 'failed', 'unsupported'
ERROR_CANCELLED = 1223   # the player answered No in the permission prompt


def supported():
    return os.name == 'nt'


def ps_quote(text):
    """A PowerShell single-quoted string: nothing inside is expanded; ' is doubled."""
    return "'" + str(text).replace("'", "''") + "'"


def command(folder):
    """The PowerShell command that adds the exclusion; exit code 0 when it was added."""
    return (f"try {{ Add-MpPreference -ExclusionPath {ps_quote(folder)} -ErrorAction Stop; exit 0 }} "
            f"catch {{ exit 2 }}")


def arguments(folder):
    """powershell.exe arguments: the command goes encoded (UTF-16LE base64), so no path can break
    out of the quoting of the command line."""
    encoded = base64.b64encode(command(folder).encode('utf-16-le')).decode('ascii')
    return f'-NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand {encoded}'


def _run_elevated(executable, params):
    """ShellExecuteEx with the "runas" verb, waits for it; returns (exit code, error)."""
    import ctypes
    from ctypes import wintypes

    class SHELLEXECUTEINFOW(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('fMask', ctypes.c_ulong), ('hwnd', wintypes.HWND),
                    ('lpVerb', wintypes.LPCWSTR), ('lpFile', wintypes.LPCWSTR),
                    ('lpParameters', wintypes.LPCWSTR), ('lpDirectory', wintypes.LPCWSTR),
                    ('nShow', ctypes.c_int), ('hInstApp', wintypes.HINSTANCE), ('lpIDList', ctypes.c_void_p),
                    ('lpClass', wintypes.LPCWSTR), ('hkeyClass', wintypes.HKEY), ('dwHotKey', wintypes.DWORD),
                    ('hIconOrMonitor', wintypes.HANDLE), ('hProcess', wintypes.HANDLE)]

    SEE_MASK_NOCLOSEPROCESS, SEE_MASK_NO_CONSOLE, SW_HIDE, INFINITE = 0x40, 0x8000, 0, 0xFFFFFFFF
    info = SHELLEXECUTEINFOW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NO_CONSOLE
    info.lpVerb = 'runas'
    info.lpFile = executable
    info.lpParameters = params
    info.nShow = SW_HIDE
    shell32 = ctypes.WinDLL('shell32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    shell32.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFOW)]
    shell32.ShellExecuteExW.restype = wintypes.BOOL
    if not shell32.ShellExecuteExW(ctypes.byref(info)):
        return None, ctypes.get_last_error()
    if not info.hProcess:
        return None, 0
    try:
        kernel32.WaitForSingleObject(info.hProcess, INFINITE)
        code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(code))
        return code.value, 0
    finally:
        kernel32.CloseHandle(info.hProcess)


def powershell():
    root = os.environ.get('SystemRoot', r'C:\Windows')
    path = Path(root) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'
    return str(path) if path.is_file() else 'powershell.exe'


def add_exclusion(folder, run=None):
    """Asks Windows for administrator rights and excludes `folder`. Blocks until the prompt is
    answered (call it off the UI thread). Returns OK | CANCELLED | FAILED | UNSUPPORTED."""
    if run is None:
        if not supported():
            return UNSUPPORTED
        run = _run_elevated
    try:
        Path(folder).mkdir(parents=True, exist_ok=True)   # the cache may not exist before the first start
    except OSError:
        pass
    try:
        code, error = run(powershell(), arguments(folder))
    except Exception:
        return FAILED
    if code is None:
        return CANCELLED if error == ERROR_CANCELLED else FAILED
    return OK if code == 0 else FAILED


def is_marked(settings, folder):
    """The player already added this folder (remembered; the exclusion list needs admin to read)."""
    return bool(folder) and settings.get('defender_excluded') == str(folder)
