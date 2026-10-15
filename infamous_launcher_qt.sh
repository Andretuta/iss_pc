#!/usr/bin/env bash
# inFAMOUS Second Son launcher, Qt Quick edition (em desenvolvimento; o padrão ainda é infamous_launcher.sh).
# Usa o venv ~/.../.venv-qt ou o python do sistema com PySide6-Essentials instalado.
here="$(dirname -- "$(readlink -f -- "$0")")"
py=python3
[ -x "$here/.venv-qt/bin/python" ] && py="$here/.venv-qt/bin/python"
exec "$py" "$here/port/launcher/infamous_launcher_qt.py" "$@"
