#!/usr/bin/env bash
# Abre o launcher do The Last Guardian (configurações, idioma, jogar).
exec python3 "$(dirname -- "$(realpath -- "$0")")/port/launcher/tlg_launcher.py" "$@"
