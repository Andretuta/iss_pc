#!/usr/bin/env bash
# Roda The Last Guardian (CUSA03627 v1.03) pelo loader nativo, sem a janela do launcher.
# Uso: ./run_tlg.sh [segundos]   (padrão: sem limite; feche a janela ou Ctrl+C para sair)
# As configurações vêm do launcher (~/.config/tlg-launcher/settings.json); variáveis TLG_*
# no ambiente têm prioridade (ex.: TLG_READBACKS=1 ./run_tlg.sh). Ver README.md, "Opções".
# Launcher gráfico: ./tlg_launcher.sh
exec python3 "$(dirname -- "$(realpath -- "$0")")/port/launcher/tlg_run.py" "$@"
