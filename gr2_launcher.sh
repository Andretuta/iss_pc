#!/usr/bin/env bash
# Gravity Rush 2 launcher (pt_BR/en_US): game folder, languages, video, audio, Play.
exec python3 "$(dirname -- "$(readlink -f -- "$0")")/port/launcher/gr2_launcher.py" "$@"
