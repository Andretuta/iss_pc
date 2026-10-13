#!/usr/bin/env bash
# Runs Gravity Rush 2 from a terminal with the launcher settings: ./run_gr2.sh [seconds]
exec python3 "$(dirname -- "$(readlink -f -- "$0")")/port/launcher/gr2_run.py" "$@"
