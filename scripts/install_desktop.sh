#!/usr/bin/env bash
# Instala o atalho do launcher no menu de aplicativos (Linux, padrão freedesktop: GNOME, KDE...).
# O ícone é o icon0.png do dump do próprio usuário (arte oficial; não vem no repositório).
# Uso: scripts/install_desktop.sh [--remove]
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
apps=${XDG_DATA_HOME:-$HOME/.local/share}/applications
icons=${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor
desktop=$apps/tlg-pc.desktop
if [[ ${1:-} == --remove ]]; then
    rm -f "$desktop"; find "$icons" -name tlg-pc.png -delete 2>/dev/null || true
    echo "Atalho removido."; exit 0
fi
icon_src=""
for f in "$root/game/CUSA03627/sce_sys/icon0.png" "$root/dump/sce_sys/icon0.png"; do
    [[ -f $f ]] && { icon_src=$f; break; }
done
icon=tlg-pc
if [[ -n $icon_src ]]; then
    for size in 512 256 128 64 48; do
        mkdir -p "$icons/${size}x${size}/apps"
        if [[ $size == 512 ]] || ! command -v magick >/dev/null; then
            cp "$icon_src" "$icons/${size}x${size}/apps/tlg-pc.png"
        else
            magick "$icon_src" -resize ${size}x${size} "$icons/${size}x${size}/apps/tlg-pc.png"
        fi
    done
    command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t "$icons" 2>/dev/null || true
else
    echo "Aviso: icon0.png não encontrado no dump; usando um ícone genérico."
    icon=applications-games
fi
mkdir -p "$apps"
cat > "$desktop" <<DESK
[Desktop Entry]
Type=Application
Name=The Last Guardian
Comment=Native PC port launcher (your own PS4 dump)
Comment[pt_BR]=Launcher do port nativo para PC (com o seu dump do PS4)
Exec=$root/tlg_launcher.sh
Path=$root
Icon=$icon
Terminal=false
Categories=Game;
StartupWMClass=tlg-pc
DESK
command -v update-desktop-database >/dev/null && update-desktop-database -q "$apps" 2>/dev/null || true
echo "Atalho instalado: $desktop (ícone: ${icon_src:-genérico})"
