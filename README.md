<h1 align="center">Gravity Rush 2 — port nativo para PC</h1>

<p align="center">
  <a href="#english"><b>English below</b></a> ·
  <a href="https://github.com/HayatoG/gr2_pc/releases/tag/nightly">Download</a> ·
  <a href="https://www.youtube.com/@hayatog-dev">YouTube</a> ·
  <a href="https://discord.gg/UMkdMYZh9g">Discord</a>
</p>

<p align="center"><a href="https://github.com/HayatoG/gr2_pc/actions/workflows/build.yml"><img src="https://github.com/HayatoG/gr2_pc/actions/workflows/build.yml/badge.svg" alt="Build"></a></p>

**Gravity Rush 2** (PS4, CUSA03694, update 01.11) rodando no PC com imagem, som e controle, a 30 FPS estáveis e sem emulador de CPU. O código original do jogo roda nativo no processador. O sistema do PS4 é reimplementado, e a GPU é traduzida para Vulkan. Usa o mesmo núcleo do port de [The Last Guardian](https://github.com/HayatoG/tlg_pc), também da Japan Studio.

> **Nenhum arquivo do jogo vem com este projeto.** Para jogar, você precisa da sua própria cópia, tirada do seu PS4.

Por **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

| | |
|---|---|
| ![Tela de título](docs/screenshots/01-titulo.jpg) | ![Menu de pausa](docs/screenshots/02-menu.jpg) |
| ![Kat nas ruínas](docs/screenshots/03-ruinas.jpg) | ![Gameplay com legenda em português](docs/screenshots/04-gameplay.jpg) |
| ![Cena em quadrinhos: a capitã](docs/screenshots/05-quadrinho-capita.jpg) | ![Cena em quadrinhos: Kat acorda](docs/screenshots/06-quadrinho-kat.jpg) |

![Navios voadores da vila de mineradores](docs/screenshots/07-navios.jpg)

<sub>Capturas na resolução nativa (1920×1080), direto da GPU, no Linux com uma RTX 2060, com o jogo em português.</sub>

## Status

| Área | Estado |
|---|---|
| Boot, abertura com créditos e legendas | ✅ Funciona |
| Título, menu e gameplay | ✅ 30 FPS, 1080p nativo |
| Áudio | ✅ Com o `libSceNgs2.sprx` do firmware do seu console + Audio3d reimplementado |
| Idioma | ✅ Escolhido no launcher (legendas e menus em português testados) |
| Controle | ✅ DualSense, DualShock 4, Xbox e 8BitDo via SDL3 |
| Linhas pretas perto dos personagens | 🔧 Contorno do geometry shader desligado por padrão ([#1](https://github.com/HayatoG/gr2_pc/issues/1)) |
| Saves e mundo aberto | ⏳ Testando ([#6](https://github.com/HayatoG/gr2_pc/issues/6)) |
| Linux | ✅ Testado (Nobara/Fedora 44) |
| Windows | 🧪 Em preparação ([#5](https://github.com/HayatoG/gr2_pc/issues/5)) |
| macOS (Apple Silicon) | 📋 Planejado ([#5](https://github.com/HayatoG/gr2_pc/issues/5)) |

![Desempenho de uma sessão de 5 minutos](docs/screenshots/desempenho.png)

<sub>FPS, pior quadro e draws por quadro a cada 5 s, tirados do log do port (`TLG_FRAME_STATS=1`). Gerado por `scripts/session_chart.py`.</sub>

## Download

O [**build nightly**](https://github.com/HayatoG/gr2_pc/releases/tag/nightly) é gerado pelo GitHub Actions a cada mudança e substitui o anterior:

- **Linux x86-64** (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 ou mais novos): `gr2-linux-x86_64.tar.gz`
- **Windows 10/11 64 bits**: `gr2-windows-x86_64.zip`

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

## Como jogar

1. Extraia o pacote e coloque o `libSceNgs2.sprx` na pasta `system_lib/`.
2. Abra o **Gravity Rush 2**, escolha a pasta do jogo e o idioma, e clique em **Jogar**.
3. No jogo, **F10** liga o contador de FPS, e **Insert** (ou R3 + L2 no controle) abre o menu do port.

## Compilar do código-fonte

```bash
git clone --recursive https://github.com/HayatoG/gr2_pc.git && cd gr2_pc
cd port && TLG_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, FreeType, Boost, fmt, Zydis, glslang
cd .. && ./gr2_launcher.sh             # ou ./run_gr2.sh pelo terminal
```

No Windows, o build roda no MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). O workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) mostra o processo completo nas duas plataformas.

## Como funciona

| Camada | O que faz | Base |
|---|---|---|
| Loader | Carrega o `eboot.bin` e liga os módulos do jogo (`libc`, `Fios2`, `JobManager`, `libSceSecure`) e o `libSceNgs2.sprx` do console | [tlg_pc](https://github.com/HayatoG/tlg_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) |
| Runtime | Reimplementa as bibliotecas do PS4. Específicos do GR2: Fiber, Audio3d, fontes (FreeType), Json2, PSN offline (NpToolkit) | `port/src/runtime_gr2*.c` |
| Vídeo | Traduz os comandos Gnm e os shaders GCN para Vulkan/SPIR-V | núcleo de vídeo do [shadPS4](https://github.com/shadps4-emu/shadPS4) |

O plano completo está em [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Próximos passos

[Issues](https://github.com/HayatoG/gr2_pc/issues):
- [#1](https://github.com/HayatoG/gr2_pc/issues/1) linhas pretas (geometry shader);
- [#2](https://github.com/HayatoG/gr2_pc/issues/2) 60 FPS;
- [#3](https://github.com/HayatoG/gr2_pc/issues/3) imagem (pós-processamento, resolução, FSR/DLSS);
- [#4](https://github.com/HayatoG/gr2_pc/issues/4) mouse, teclado, giroscópio e touchpad;
- [#5](https://github.com/HayatoG/gr2_pc/issues/5) pacotes Linux/Windows/macOS;
- [#6](https://github.com/HayatoG/gr2_pc/issues/6) jogar do início ao fim.

## Créditos e aviso legal

Base de código: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) e [shadPS4](https://github.com/shadps4-emu/shadPS4), todos GPL-2.0, assim como este projeto ([LICENSE](port/LICENSE)). Áudio ATRAC9 via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9); fontes via [FreeType](https://freetype.org).

Este projeto não tem vínculo com a Sony Interactive Entertainment ou a SIE Japan Studio. Gravity Rush é marca da Sony Interactive Entertainment. Nenhum código, arquivo ou arte do jogo é distribuído aqui.

---

<a id="english"></a>

# Gravity Rush 2 — native PC port

**Gravity Rush 2** (PS4, CUSA03694, update 01.11) running on PC with graphics, audio and controller support, at a steady 30 FPS and without a CPU emulator. The game's original code runs natively on the processor, the PS4 system is reimplemented, and the GPU is translated to Vulkan. It uses the same core as the [The Last Guardian](https://github.com/HayatoG/tlg_pc) port, another Japan Studio game.

> **No game files come with this project.** To play, you need your own copy, dumped from your own PS4.

By **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

The screenshots and the performance chart are at the top of this page.

## Status

| Area | State |
|---|---|
| Boot, opening with credits and subtitles | ✅ Works |
| Title, menu and gameplay | ✅ 30 FPS, native 1080p |
| Audio | ✅ With `libSceNgs2.sprx` from your console's firmware + reimplemented Audio3d |
| Language | ✅ Chosen in the launcher (Portuguese subtitles and menus tested) |
| Controller | ✅ DualSense, DualShock 4, Xbox and 8BitDo via SDL3 |
| Black streaks near characters | 🔧 Geometry-shader outline off by default ([#1](https://github.com/HayatoG/gr2_pc/issues/1)) |
| Saves and open world | ⏳ Testing ([#6](https://github.com/HayatoG/gr2_pc/issues/6)) |
| Linux | ✅ Tested (Nobara/Fedora 44) |
| Windows | 🧪 In preparation ([#5](https://github.com/HayatoG/gr2_pc/issues/5)) |
| macOS (Apple Silicon) | 📋 Planned ([#5](https://github.com/HayatoG/gr2_pc/issues/5)) |

## Download

The [**nightly build**](https://github.com/HayatoG/gr2_pc/releases/tag/nightly) is produced by GitHub Actions on every change and replaces the previous one:

- **Linux x86-64** (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 or newer): `gr2-linux-x86_64.tar.gz`
- **Windows 10/11 64-bit**: `gr2-windows-x86_64.zip`

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

## How to play

1. Extract the package and put `libSceNgs2.sprx` in the `system_lib/` folder.
2. Open **Gravity Rush 2**, pick the game folder and the language, and click **Play**.
3. In game, **F10** toggles the FPS counter, and **Insert** (or R3 + L2 on a controller) opens the port's menu.

## Building from source

```bash
git clone --recursive https://github.com/HayatoG/gr2_pc.git && cd gr2_pc
cd port && TLG_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, FreeType, Boost, fmt, Zydis, glslang
cd .. && ./gr2_launcher.sh             # or ./run_gr2.sh from a terminal
```

On Windows, the build runs in MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). The workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) shows the full process on both platforms.

## How it works

| Layer | What it does | Based on |
|---|---|---|
| Loader | Loads `eboot.bin` and links the game's modules (`libc`, `Fios2`, `JobManager`, `libSceSecure`) and the console's `libSceNgs2.sprx` | [tlg_pc](https://github.com/HayatoG/tlg_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) |
| Runtime | Reimplements the PS4 libraries. GR2-specific: Fiber, Audio3d, fonts (FreeType), Json2, offline PSN (NpToolkit) | `port/src/runtime_gr2*.c` |
| Video | Translates Gnm commands and GCN shaders to Vulkan/SPIR-V | [shadPS4](https://github.com/shadps4-emu/shadPS4) video core |

The full plan is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Next steps

[Issues](https://github.com/HayatoG/gr2_pc/issues):
- [#1](https://github.com/HayatoG/gr2_pc/issues/1) black streaks (geometry shader);
- [#2](https://github.com/HayatoG/gr2_pc/issues/2) 60 FPS;
- [#3](https://github.com/HayatoG/gr2_pc/issues/3) graphics (post-processing, resolution, FSR/DLSS);
- [#4](https://github.com/HayatoG/gr2_pc/issues/4) mouse, keyboard, gyro and touchpad;
- [#5](https://github.com/HayatoG/gr2_pc/issues/5) Linux/Windows/macOS packages;
- [#6](https://github.com/HayatoG/gr2_pc/issues/6) playing start to finish.

## Credits and legal notice

Code base: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) and [shadPS4](https://github.com/shadps4-emu/shadPS4), all GPL-2.0, as is this project ([LICENSE](port/LICENSE)). ATRAC9 audio via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9); fonts via [FreeType](https://freetype.org).

This project is not affiliated with Sony Interactive Entertainment or SIE Japan Studio. Gravity Rush is a trademark of Sony Interactive Entertainment. No game code, files or art are distributed here.
