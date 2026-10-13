#!/usr/bin/env bash
# Prepara e roda The Last Guardian (CUSA03627 v1.03) pelo loader nativo em port/.
# Uso: ./run_tlg.sh [segundos]   (padrão: sem limite; feche a janela ou Ctrl+C para sair)
# A pasta do jogo (game/CUSA03627) precisa existir: links para dump/ (base) e dump/patch0 (1.03).
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")" && pwd)
port=$root/port
game=${TLG_GAME_DIR:-$root/game/CUSA03627}
out=$port/out
[[ -x $out/gow3-probe ]] || { echo "Compile primeiro: (cd port && bash build.sh)" >&2; exit 1; }
[[ -f $game/eboot.bin ]] || { echo "Sem eboot.bin em $game" >&2; exit 1; }
python3 "$port/scripts/prepare.py" "$game" --out "$out" >/dev/null
python3 "$port/scripts/link_modules.py" "$game" --out "$out" >/dev/null
python3 "$port/scripts/content_profile.py" "$game" --out "$out" >/dev/null
mkdir -p "$port/user"
# O cache de pipeline binário (VK_KHR_pipeline_binary) trava no driver NVIDIA 595: desligado.
export GOW3_PIPELINE_BINARIES=${GOW3_PIPELINE_BINARIES:-0}
# O TLG lê na CPU resultados de compute da GPU (JsComputeContext::AsyncMap): readbacks precisos.
export GOW3_READBACKS=${GOW3_READBACKS:-2}
export GOW3_RESTART_COMMAND=${GOW3_RESTART_COMMAND:-"$0"}
log=$out/last_run.log
echo "Rodando (log: $log)"
exec "$out/gow3-probe" "$out/boot-linked.bin" --app0 "$game" --user "$port/user" \
    --content-profile "$out/content.bin" --timeout "${1:-0}" > >(tee "$log") 2>&1
