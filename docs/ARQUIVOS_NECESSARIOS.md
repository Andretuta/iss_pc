# Arquivos do jogo necessários / Required game files

[Português](#arquivos-do-jogo-necessários) · [English](#required-game-files)

## Arquivos do jogo necessários

Tudo vem do **seu** PS4 (GoldHEN + Itemzflow). Nada disso vai no download. Use **Gravity Rush 2 CUSA03694 (EUA) com o update 01.11**, montado numa pasta só, com o jogo base e o update por cima. São ~28 GB.

| Arquivo | Vem de | Tamanho | Para quê |
|---|---|---|---|
| `eboot.bin` | update 01.11 | 28 MB | o código do jogo (tem que ser o do 1.11) |
| `sce_module/libc.prx`, `libSceFios2.prx`, `libSceJobManager.prx` | jogo base | 1,7 MB | bibliotecas do próprio jogo |
| `sysdata/libSceSecure.prx` | jogo base | pequeno | criptografia do próprio jogo |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic1.png`) | base + update | ~5 MB | metadados, instalação e a arte do launcher |
| `Gravite2_Chunk0.psarc`, `Gravite2_Chunk1.psarc` | jogo base | 10 + 15,8 GB | conteúdo principal |
| `Gravite2_Patch_Chunk0.psarc`, `Gravite2_Patch_Chunk1.psarc` | update 01.11 | 0,5 + 1,6 GB | correções do update |
| `sce_discmap.plt`, `sce_discmap_patch.plt` | update 01.11 | pequenos | mapa de arquivos |

**Do firmware do console (opcional, para ter som):** `libSceNgs2.sprx`, de `/system/common/lib/` do seu PS4. Ele vai na pasta `system_lib/` ao lado do executável.

**Como montar a pasta:**
1. No Itemzflow, faça o dump do jogo (`CUSA03694`) e do update (`CUSA03694-patch`) para um pendrive exFAT.
2. No PC, copie a pasta do jogo base e depois copie o conteúdo do update **por cima**, substituindo os arquivos. Também dá para usar `scripts/make_game_view.py <base> <update> <saída>`, que monta a pasta com links, sem ocupar espaço.
3. Confira os tamanhos. Arquivos acima de 4 GB vindos pelo FTP do GoldHEN 2.2 chegam cortados, então use o pendrive.

## Required game files

Everything comes from **your own** PS4 (GoldHEN + Itemzflow). None of it is in the download. Use **Gravity Rush 2 CUSA03694 (US) with update 01.11**, merged into one folder, with the base game and the update on top. About 28 GB.

| File | From | Size | Purpose |
|---|---|---|---|
| `eboot.bin` | update 01.11 | 28 MB | the game code (must be the 1.11 one) |
| `sce_module/libc.prx`, `libSceFios2.prx`, `libSceJobManager.prx` | base game | 1.7 MB | the game's own libraries |
| `sysdata/libSceSecure.prx` | base game | small | the game's own cryptography |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic1.png`) | base + update | ~5 MB | metadata, install info and the launcher art |
| `Gravite2_Chunk0.psarc`, `Gravite2_Chunk1.psarc` | base game | 10 + 15.8 GB | main content |
| `Gravite2_Patch_Chunk0.psarc`, `Gravite2_Patch_Chunk1.psarc` | update 01.11 | 0.5 + 1.6 GB | update fixes |
| `sce_discmap.plt`, `sce_discmap_patch.plt` | update 01.11 | small | file map |

**From the console firmware (optional, for audio):** `libSceNgs2.sprx`, from `/system/common/lib/` on your PS4. It goes in the `system_lib/` folder next to the executable.

**How to build the folder:**
1. In Itemzflow, dump the game (`CUSA03694`) and the update (`CUSA03694-patch`) to an exFAT USB drive.
2. On the PC, copy the base game folder, then copy the update's contents **over it**, replacing files. Or use `scripts/make_game_view.py <base> <update> <out>`, which builds the folder with links and uses no extra space.
3. Check the sizes. Files over 4 GB sent through GoldHEN 2.2's FTP arrive truncated, so use the USB drive.
