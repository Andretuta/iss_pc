<h1 align="center">Gravity Rush 2 — port nativo para PC</h1>

<p align="center"><a href="#english"><b>English below</b></a> · <a href="https://www.youtube.com/@hayatog-dev">YouTube</a> · <a href="https://discord.gg/UMkdMYZh9g">Discord</a></p>

**Gravity Rush 2** (PS4, CUSA03694) rodando no PC, sem emulador de CPU. O código original do jogo roda nativo no processador. O sistema do PS4 é reimplementado, e a GPU é traduzida para Vulkan. Mesmo núcleo do port de [The Last Guardian](https://github.com/HayatoG/tlg_pc), também da Japan Studio.

> **Nenhum arquivo do jogo vem com este projeto.** Para jogar, você precisa da sua própria cópia, tirada do seu PS4.

Por **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

## Status (em desenvolvimento)

| Área | Estado |
|---|---|
| Boot, abertura com créditos e legendas | ✅ |
| Tela de título, menu e começo jogável | ✅ 30 FPS, 1080p |
| Som | ✅ NGS2 nativo do firmware + Audio3d reimplementado |
| Imports do sistema | ✅ 863/863 |
| Linhas pretas perto dos personagens | 🔧 Contorno do geometry shader desligado por padrão ([docs/BUG_LINHAS_PRETAS.md](docs/BUG_LINHAS_PRETAS.md)) |
| Update 1.11 | ⏳ Em dump |
| Pacotes para download | ⏳ Ainda não |

O plano completo está em [docs/ROADMAP.md](docs/ROADMAP.md).

## Arquivos do jogo necessários (base 1.00)

| Arquivo | Para quê |
|---|---|
| `eboot.bin` | o código do jogo |
| `sce_module/libc.prx`, `libSceFios2.prx`, `libSceJobManager.prx` | bibliotecas do próprio jogo |
| `sysdata/libSceSecure.prx` | criptografia do próprio jogo |
| `sce_sys/` | metadados e a arte do launcher |
| `Gravite2_Chunk0.psarc` (10 GB), `Gravite2_Chunk1.psarc` (15,8 GB) | conteúdo; arquivos acima de 4 GB precisam vir por pendrive (Itemzflow), não pelo FTP do GoldHEN 2.2 |
| `libSceNgs2.sprx` (firmware, `/system/common/lib/`) | opcional, para ter som |

## Rodar do código-fonte

```bash
git clone --recursive https://github.com/HayatoG/gr2_pc.git && cd gr2_pc
cd port && TLG_LTO=OFF bash build.sh && cd ..
./gr2_launcher.sh     # ou ./run_gr2.sh pelo terminal
```

## Créditos e aviso legal

Base de código: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) e [shadPS4](https://github.com/shadps4-emu/shadPS4), todos GPL-2.0, como este projeto. Este projeto não tem vínculo com a Sony Interactive Entertainment ou a SIE Japan Studio. Gravity Rush é marca da Sony Interactive Entertainment. Nenhum código, arquivo ou arte do jogo é distribuído aqui.

---

<a id="english"></a>

# Gravity Rush 2 — native PC port

**Gravity Rush 2** (PS4, CUSA03694) running on PC without a CPU emulator. The game's original code runs natively on the processor, the PS4 system is reimplemented, and the GPU is translated to Vulkan. It uses the same core as the [The Last Guardian](https://github.com/HayatoG/tlg_pc) port, another Japan Studio game.

> **No game files come with this project.** You need your own copy, dumped from your own PS4.

**Status (in development):**
- Boots to the main menu and the playable start, at 30 FPS and 1080p, with sound.
- All 863 system imports are covered.
- Black streaks near characters come from the geometry-shader outline, which is off by default for now.
- The 1.11 update is being dumped.
- No download packages yet.

**Required files** (base 1.00):
- `eboot.bin`
- `sce_module/libc.prx`, `libSceFios2.prx`, `libSceJobManager.prx`
- `sysdata/libSceSecure.prx`
- `sce_sys/`
- `Gravite2_Chunk0.psarc` and `Gravite2_Chunk1.psarc` (copy them over USB: they are larger than 4 GB)
- optionally `libSceNgs2.sprx` from the firmware, for audio

**Build:** see "Rodar do código-fonte" above. **Credits and legal notice:** as above. Not affiliated with Sony Interactive Entertainment or SIE Japan Studio. No game code, files or art are distributed here.
