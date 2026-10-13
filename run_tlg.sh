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
# Orçamento do cache de texturas: o cálculo padrão pressiona a partir de ~2 GB de uso total, e o TLG
# usa ~3,5 GB (texturas descartadas e recarregadas = engasgos e glitches). 5200 MB serve para 6 GB de
# VRAM; ajuste para outras placas (ex.: 7000 em 8 GB).
export GOW3_GC_BUDGET_MB=${GOW3_GC_BUDGET_MB:-5200}
# Imagem nativa do jogo: sem os extras do port de GoW3 (upscaler FSR3/TAA, jitter de câmera e
# motion vectors injetados). Eles foram feitos para o pipeline do GoW3 e no TLG causavam tremor.
export GOW3_UPSCALER=${GOW3_UPSCALER:-off}
export GOW3_JITTER=${GOW3_JITTER:-0}
export GOW3_OBJECT_MOTION=${GOW3_OBJECT_MOTION:-0}
# FPS a cada 5 s e diagnóstico de engasgos no log (o vigia scripts/watch_session.sh usa como batimento).
export GOW3_FRAME_STATS=${GOW3_FRAME_STATS:-1}
export GOW3_RESTART_COMMAND=${GOW3_RESTART_COMMAND:-"$0"}
# Um log por execução em out/logs/ (mantém os 30 mais recentes); last_run.log aponta para o último.
mkdir -p "$out/logs"
log=$out/logs/run-$(date +%Y%m%d-%H%M%S).log
ln -sfn "$log" "$out/last_run.log"
ls -1t "$out"/logs/run-*.log 2>/dev/null | tail -n +31 | xargs -r rm -f
echo "Rodando (log: $log)"
exec "$out/gow3-probe" "$out/boot-linked.bin" --app0 "$game" --user "$port/user" \
    --content-profile "$out/content.bin" --timeout "${1:-0}" > >(tee "$log") 2>&1
