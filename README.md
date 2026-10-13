<h1 align="center">inFAMOUS Second Son — port nativo para PC</h1>

<p align="center">
  <a href="#english"><b>English below</b></a> ·
  <a href="https://www.youtube.com/@hayatog-dev">YouTube</a> ·
  <a href="https://discord.gg/UMkdMYZh9g">Discord</a>
</p>

<p align="center"><a href="https://github.com/HayatoG/infamous_pc/actions/workflows/build.yml"><img src="https://github.com/HayatoG/infamous_pc/actions/workflows/build.yml/badge.svg" alt="Build"></a></p>

> **Em desenvolvimento — ainda não inicia.** O jogo ainda cai logo no começo do boot. Não há o que jogar por enquanto.

**inFAMOUS Second Son** (PS4, CUSA00223, update 1.07) rodando no PC sem emulador de CPU: o código original do jogo roda nativo no processador, o sistema do PS4 é reimplementado e a GPU é traduzida para Vulkan. Usa o mesmo núcleo dos ports de [The Last Guardian](https://github.com/HayatoG/tlg_pc) e [Gravity Rush 2](https://github.com/HayatoG/gr2_pc).

> **Nenhum arquivo do jogo vem com este projeto.** Para jogar, você precisa da sua própria cópia, tirada do seu PS4.

Por **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

Ainda sem capturas de tela: elas entram aqui quando o jogo mostrar o primeiro quadro.

## Status

| Área | Estado |
|---|---|
| Carregar o `eboot.bin` 1.07 e ligar `libc` e `Fios2` do jogo | ✅ Funciona |
| Funções de sistema que o jogo importa | ⏳ Faltam ~16 (NpManager, PlayGo, Http, NetCtl, AppContent...) |
| Boot | ❌ Cai em menos de 1 s, dentro do `main` do jogo |
| Imagem, áudio, controle, saves | 📋 Depois do boot |
| Linux | 🧪 Compila; é onde o port é desenvolvido (Nobara/Fedora 44) |
| Windows | 📋 Planejado (o build usa o mesmo processo dos outros ports) |

## Download

Ainda não há download: o port ainda não inicia. Quando houver, o **build nightly** sai pelo GitHub Actions a cada mudança:

- **Linux x86-64** (glibc 2.39+): `infamous-linux-x86_64.tar.gz`
- **Windows 10/11 64 bits**: `infamous-windows-x86_64.zip`

## Arquivos do jogo necessários

Tudo vem do **seu** PS4 (GoldHEN + Itemzflow). Nada disso vai no download. Use **inFAMOUS Second Son CUSA00223 (EUA), jogo base 1.00 com o update 1.07**, montado numa pasta só, com o jogo base e o update por cima. São ~33 GB.

| Arquivo | Vem de | Para quê |
|---|---|---|
| `eboot.bin` | update 1.07 | o código do jogo (tem que ser o do 1.07) |
| `sce_module/libc.prx`, `sce_module/libSceFios2.prx` | update 1.07 | bibliotecas do próprio jogo |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic1.png`) | jogo base (+ `param.sfo` do update) | metadados, instalação e a arte do launcher |
| `art/` (`cache/`, `movies/`, `ui/`) | base + update | conteúdo do jogo |
| `playgo.pgm`, `sce_discmap.plt`, `sce_discmap_patch.plt` | base + update | mapa de arquivos e instalação |

**Do firmware do console:** nada. Este jogo não usa módulos do sistema do PS4.

A lista completa e o passo a passo estão em [`docs/ARQUIVOS_NECESSARIOS.md`](docs/ARQUIVOS_NECESSARIOS.md).

## Como jogar

Ainda não dá para jogar. Quando o port iniciar:

1. Extraia o pacote.
2. Abra o **inFAMOUS Second Son**, escolha a pasta do jogo e o idioma, e clique em **Jogar**.
3. No jogo, **F10** liga o contador de FPS, e **Insert** (ou R3 + L2 no controle) abre o menu do port.

## Compilar do código-fonte

```bash
git clone --recursive https://github.com/HayatoG/infamous_pc.git && cd infamous_pc
cd port && TLG_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, FreeType, Boost, fmt, Zydis, glslang
cd .. && ./infamous_launcher.sh        # ou ./run_infamous.sh pelo terminal
```

No Windows, o build roda no MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). O workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) mostra o processo completo nas duas plataformas.

## Como funciona

| Camada | O que faz | Base |
|---|---|---|
| Loader | Carrega o `eboot.bin` e liga os módulos do próprio jogo (`libc`, `Fios2`) | [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) |
| Runtime | Reimplementa as bibliotecas do PS4 (NpManager, Trophy, Http, Ssl, PlayGo, SaveData, AppContent...) | `port/src/` |
| Vídeo | Traduz os comandos Gnm e os shaders GCN para Vulkan/SPIR-V | núcleo de vídeo do [shadPS4](https://github.com/shadps4-emu/shadPS4) |

O plano está em [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Créditos e aviso legal

Base de código: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) e [shadPS4](https://github.com/shadps4-emu/shadPS4), todos GPL-2.0, assim como este projeto ([LICENSE](port/LICENSE)). Áudio ATRAC9 via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9); fontes via [FreeType](https://freetype.org).

Este projeto não tem vínculo com a Sony Interactive Entertainment ou a Sucker Punch Productions. inFAMOUS é marca da Sony Interactive Entertainment. Nenhum código, arquivo ou arte do jogo é distribuído aqui.

---

<a id="english"></a>

# inFAMOUS Second Son — native PC port

> **In development — doesn't boot yet.** The game still crashes early in boot. There is nothing to play for now.

**inFAMOUS Second Son** (PS4, CUSA00223, update 1.07) running on PC without a CPU emulator: the game's original code runs natively on the processor, the PS4 system is reimplemented, and the GPU is translated to Vulkan. It uses the same core as the [The Last Guardian](https://github.com/HayatoG/tlg_pc) and [Gravity Rush 2](https://github.com/HayatoG/gr2_pc) ports.

> **No game files come with this project.** To play, you need your own copy, dumped from your own PS4.

By **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

No screenshots yet: they will be added once the game shows its first frame.

## Status

| Area | State |
|---|---|
| Loading the 1.07 `eboot.bin` and linking the game's `libc` and `Fios2` | ✅ Works |
| System functions the game imports | ⏳ ~16 missing (NpManager, PlayGo, Http, NetCtl, AppContent...) |
| Boot | ❌ Crashes in under 1 s, inside the game's `main` |
| Graphics, audio, controller, saves | 📋 After boot |
| Linux | 🧪 Builds; the port is developed there (Nobara/Fedora 44) |
| Windows | 📋 Planned (same build process as the other ports) |

## Download

No download yet: the port does not boot. Once it does, the **nightly build** will come from GitHub Actions on every change:

- **Linux x86-64** (glibc 2.39+): `infamous-linux-x86_64.tar.gz`
- **Windows 10/11 64-bit**: `infamous-windows-x86_64.zip`

## Required game files

Everything comes from **your own** PS4 (GoldHEN + Itemzflow). None of it is in the download. Use **inFAMOUS Second Son CUSA00223 (US), base game 1.00 with update 1.07**, merged into one folder, with the base game and the update on top. About 33 GB.

| File | From | Purpose |
|---|---|---|
| `eboot.bin` | update 1.07 | the game code (must be the 1.07 one) |
| `sce_module/libc.prx`, `sce_module/libSceFios2.prx` | update 1.07 | the game's own libraries |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic1.png`) | base game (+ the update's `param.sfo`) | metadata, install info and the launcher art |
| `art/` (`cache/`, `movies/`, `ui/`) | base + update | game content |
| `playgo.pgm`, `sce_discmap.plt`, `sce_discmap_patch.plt` | base + update | file map and install info |

**From the console firmware:** nothing. This game uses no PS4 system module.

The full list and the step-by-step guide are in [`docs/ARQUIVOS_NECESSARIOS.md`](docs/ARQUIVOS_NECESSARIOS.md).

## How to play

Not playable yet. Once the port boots:

1. Extract the package.
2. Open **inFAMOUS Second Son**, pick the game folder and the language, and click **Play**.
3. In game, **F10** toggles the FPS counter, and **Insert** (or R3 + L2 on a controller) opens the port's menu.

## Building from source

```bash
git clone --recursive https://github.com/HayatoG/infamous_pc.git && cd infamous_pc
cd port && TLG_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, FreeType, Boost, fmt, Zydis, glslang
cd .. && ./infamous_launcher.sh        # or ./run_infamous.sh from a terminal
```

On Windows, the build runs in MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). The workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) shows the full process on both platforms.

## How it works

| Layer | What it does | Based on |
|---|---|---|
| Loader | Loads `eboot.bin` and links the game's own modules (`libc`, `Fios2`) | [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) |
| Runtime | Reimplements the PS4 libraries (NpManager, Trophy, Http, Ssl, PlayGo, SaveData, AppContent...) | `port/src/` |
| Video | Translates Gnm commands and GCN shaders to Vulkan/SPIR-V | [shadPS4](https://github.com/shadps4-emu/shadPS4) video core |

The plan is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Credits and legal notice

Code base: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) and [shadPS4](https://github.com/shadps4-emu/shadPS4), all GPL-2.0, as is this project ([LICENSE](port/LICENSE)). ATRAC9 audio via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9); fonts via [FreeType](https://freetype.org).

This project is not affiliated with Sony Interactive Entertainment or Sucker Punch Productions. inFAMOUS is a trademark of Sony Interactive Entertainment. No game code, files or art are distributed here.
