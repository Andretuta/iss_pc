#!/usr/bin/env bash
# Prepara e roda The Last Guardian (CUSA03627 v1.03) pelo loader nativo em port/.
# Uso: ./run_tlg.sh [segundos]   (padrão: sem limite; feche a janela ou Ctrl+C para sair)
# Opções: variáveis TLG_* (ex.: TLG_READBACKS=1 ./run_tlg.sh). Lista em README.md, "Opções".
# A pasta do jogo (game/CUSA03627) precisa existir: links para dump/ (base) e dump/patch0 (1.03).
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")" && pwd)
port=$root/port
game=${TLG_GAME_DIR:-$root/game/CUSA03627}
out=$port/out
[[ -x $out/tlg-probe ]] || { echo "Compile primeiro: (cd port && bash build.sh)" >&2; exit 1; }
[[ -f $game/eboot.bin ]] || { echo "Sem eboot.bin em $game" >&2; exit 1; }
python3 "$port/scripts/prepare.py" "$game" --out "$out" >/dev/null
python3 "$port/scripts/link_modules.py" "$game" --out "$out" >/dev/null
python3 "$port/scripts/content_profile.py" "$game" --out "$out" >/dev/null
mkdir -p "$port/user"
# O cache de pipeline binário (VK_KHR_pipeline_binary) trava no driver NVIDIA 595: desligado.
export TLG_PIPELINE_BINARIES=${TLG_PIPELINE_BINARIES:-0}
# O TLG lê na CPU resultados de compute da GPU (JsComputeContext::AsyncMap): readbacks precisos.
export TLG_READBACKS=${TLG_READBACKS:-2}
# Orçamento do cache de texturas: o cálculo padrão pressiona a partir de ~2 GB de uso total, e o TLG
# usa ~3,5 GB (texturas descartadas e recarregadas = engasgos e glitches). 5600 MB serve para 6 GB de
# VRAM; ajuste para outras placas (ex.: 7000 em 8 GB).
export TLG_GC_BUDGET_MB=${TLG_GC_BUDGET_MB:-5600}
# Imagem nativa do jogo: sem os extras do port de GoW3 (upscaler FSR3/TAA, jitter de câmera e
# motion vectors injetados). Eles foram feitos para o pipeline do GoW3 e no TLG causavam tremor.
export TLG_UPSCALER=${TLG_UPSCALER:-off}
export TLG_JITTER=${TLG_JITTER:-0}
export TLG_OBJECT_MOTION=${TLG_OBJECT_MOTION:-0}
# FPS a cada 5 s e diagnóstico de engasgos no log (o vigia scripts/watch_session.sh usa como batimento).
export TLG_FRAME_STATS=${TLG_FRAME_STATS:-1}
export TLG_RESTART_COMMAND=${TLG_RESTART_COMMAND:-"$0"}
# Um log por execução em out/logs/ (mantém os 30 mais recentes); last_run.log aponta para o último.
mkdir -p "$out/logs"
log=$out/logs/run-$(date +%Y%m%d-%H%M%S).log
ln -sfn "$log" "$out/last_run.log"
ls -1t "$out"/logs/run-*.log 2>/dev/null | tail -n +31 | xargs -r rm -f
echo "Rodando (log: $log)"
exec "$out/tlg-probe" "$out/boot-linked.bin" --app0 "$game" --user "$port/user" \
    --content-profile "$out/content.bin" --timeout "${1:-0}" > >(tee "$log") 2>&1
