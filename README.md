# The Last Guardian — port nativo para PC (pesquisa)

Projeto de pesquisa para rodar **The Last Guardian** (PS4, **CUSA03627**, update **01.03**) no PC,
usando a cópia do próprio usuário.

> **Nenhum arquivo do jogo é versionado aqui.** Isso inclui eboot, prx, psarc e saída bruta de descompilação.
> Para rodar, cada pessoa precisa do próprio dump. Veja `.gitignore`.

_Última atualização: 2026-10-12_

---

## Estratégia

**Runtime nativo, sem decompilação completa.** O PS4 usa CPU x86-64, então o `eboot.bin` original
roda direto no processador do PC. O projeto escreve só o que fica em volta dele:

| Peça | Função | Base de reaproveitamento |
|---|---|---|
| Loader / linker | Carrega o eboot 1.03, liga `libc.prx` e `libSceFios2.prx` do jogo e resolve as imports por NID | bloodborne_pc, gow3_pc (`prepare.py`, `link_modules.py`, `probe.c`) |
| Runtime (HLE) | Reimplementa as libs do sistema PS4 (kernel, pthread, pad, savedata, áudio…) | gow3_pc `src/runtime_*.c`, shadPS4 |
| Vídeo | Traduz Gnm/PM4 e shaders GCN para **Vulkan** | núcleo de vídeo do shadPS4 (+ forks com fixes) |
| Patches | Correções em memória (FPS, resolução), validadas por sha256 do eboot | modelo do gow3_pc |

O Ghidra/REA serve para **investigação pontual** (bugs, patches, contratos de API), e não para
reescrever o jogo.

Projetos de referência:
- [deadinside28/bloodborne_pc](https://github.com/deadinside28/bloodborne_pc), que deu origem à família, nativo no Linux
- [FelipePrado0/gow3_pc](https://github.com/FelipePrado0/gow3_pc)
- [shadPS4](https://github.com/shadps4-emu/shadPS4)

Todos são GPL-2.0.

**Hardware-alvo de teste:** Ryzen 7 5700X3D, 32 GB de RAM, RTX 2060 6 GB (Vulkan 1.3), Nobara Linux.
Pontos de atenção: os 6 GB de VRAM, e o fato de os ports atuais terem sido testados principalmente em AMD.

---

## Status

| Etapa | Estado |
|---|---|
| Dump do eboot/prx (base 1.00 e update 1.03), decriptografados | ✅ ELF verificados |
| Dump dos psarc do update 1.03 | ✅ completos |
| Dump dos psarc do jogo base | ⚠️ `trico_001/002/003` truncados pelo FTP. Novo dump via USB (Itemzflow) em andamento |
| Análise Ghidra (GhidraOrbis + REA) do eboot 1.03 | ✅ auto-análise em ~9 min (heap de 16 GB) |
| Mapeamento: loop principal e threads | ✅ [`analysis/01_main_loop_threads.md`](analysis/01_main_loop_threads.md) |
| Mapeamento: renderização / GNM | 🔄 em andamento → `analysis/02_rendering_gnm.md` |
| Mapeamento: áudio | ✅ [`analysis/03_audio.md`](analysis/03_audio.md) |
| Mapeamento: I/O, psarc, controle, saves, sistema | ✅ [`analysis/04_io_input_saves_system.md`](analysis/04_io_input_saves_system.md) |
| Loader + runtime | ⏳ não iniciado |

---

## Inventário do dump (local, fora do git)

O dump foi feito do console do usuário via GoldHEN FTP, de `/mnt/sandbox/pfsmnt/CUSA03627-app0` e
`-patch0`, com o jogo em execução. O GoldHEN decriptografa os executáveis na transferência.

| Arquivo | Versão | Tipo | sha256 |
|---|---|---|---|
| `dump/eboot.bin` | 1.00 | ELF ET_SCE_EXEC (0xFE10) | `f457d7b0fe0c99d2391cac5d63d030b50bd4d4feab9659ece9f11f5604c5d89f` |
| `dump/sce_module/libc.prx` | 1.00 | ELF | `d88f1cc336985bf02fa128e8f7bbfbc21ac6c7fa1a151ba0c40b300750f2b2dd` |
| `dump/sce_module/libSceFios2.prx` | 1.00 | ELF | `ff8c06b194e593f727a1315417a2bd174111d1e2f9961636101c438dc6dfb6c3` |
| **`dump/patch0/eboot.bin`** | **1.03** | ELF ET_SCE_EXEC (0xFE10) | `91dce685be81f8f6bc88097d4fc7a62e97ca08d109621c57fe9371ae125feb3c` |
| `dump/patch0/sce_module/libc.prx` | 1.03 | ELF ET_SCE_DYNAMIC (0xFE18) | `8369c7468717567a072704be2857f5f7fb6f5e819992413b40cda3488bbb64db` |
| `dump/patch0/sce_module/libSceFios2.prx` | 1.03 | ELF ET_SCE_DYNAMIC (0xFE18) | `b8b2d2f71efbab5334e49125a1889e9383ef476757d830eee9715aec4088e20c` |

Conteúdo (psarc, compressão zlib):

- **Base:** `trico_001` 6,2 GB, `trico_002` 5,7 GB, `trico_003` 7,2 GB, `trico_boot` 2,9 GB, e os
  idiomas `enu/esl/frc/ptb` com ~0,29 GB cada.
- **Update 1.03:** `trico_*p.psarc`, 1,7 GB no total. Eles se sobrepõem aos do jogo base por overlay do Fios2.

Os números do eboot 1.03 são 92,9 MB no total. Desses, ~23,7 MB são código e rodata. O segmento de
dados tem ~68 MB, mas é quase todo zeros (buffers estáticos).

### Problema conhecido: FTP do GoldHEN v2.2 e arquivos > 4 GiB
O servidor calcula `SIZE`/`RETR` em 32 bits e entrega apenas `tamanho mod 2^32` bytes, com sucesso
aparente. O `REST` além desse ponto volta ao byte 0. Só o `LIST` mostra o tamanho real.
**Sempre compare o tamanho local com o `LIST`.** Para arquivos acima de 4 GiB, faça o dump via USB em
exFAT (Itemzflow).

---

## Achados principais

### 1. Bibliotecas do sistema importadas (eboot 1.03)
São 23 módulos e 508 funções, todas com NID resolvido.
Listas completas em `analysis/eboot_imports_1.03.json`.

| Biblioteca | Funções | Uso |
|---|---|---|
| libc (prx do próprio jogo) | 144 | C runtime |
| **libSceGnmDriver** | 110 | GPU: submits, flip, shaders, draw/dispatch, compute queues, Razor/validação |
| libkernel | 88 | memória direct/flexible, pthreads, sema/eventflag, equeue, arquivos, TSC |
| libSceFios2 (prx do próprio jogo) | 44 | sistema de arquivos e montagem dos psarc |
| libSceNet | 23 | sockets e epoll |
| libScePosix | 22 | pthread/stat POSIX |
| libSceAudio3d | 12 | importado, mas **não usado** (ver áudio) |
| libScePad | 11 | controle, light bar, vibração, sensores de movimento |
| libSceNgs2 | 10 | mixer/vozes de áudio |
| libSceVideoOut | 10 | saída de vídeo e modo de saída (o 1.03 adicionou `ConfigureOutputMode_` e `ModeSetAny_`) |
| libSceAudioOut | 7 | saída de som |
| SaveData (6), NpTrophy (5), PlayGo (5), PlayGoDialog (5), SystemService (4), AppContent, NetCtl, Sysmodule, UserService (2 cada), CommonDialog, NpManager (1 cada) | | serviços |

O Gnm/Gnmx (SDK 3.50) vêm **linkados estaticamente** dentro do eboot. Só o driver é importado.

### 2. Ponto de entrada e loop principal
No Ghidra, a base da imagem é `0x1000000`. Detalhes em [`analysis/01_main_loop_threads.md`](analysis/01_main_loop_threads.md).

- `_start` em `0x10000a0` → `main` em `0x1207bb0`, que imprime `"trico main() start..."` e cria o objeto `App`
  (vtable `0x26ebbe0`, singleton `0x69a1b40`).
- `App::Run` em `0x1d169b0`:
  - **init:** heaps System/Object/Permanent/Assets/Temporary/Overflow, `memory.cfg`, args `-copy`/`-reboot`/`-force2k`;
  - **loop:** `while (!quit)`:
    1. GC diferido (`0x1cd5a40`, orçamento de 2 ms);
    2. callbacks;
    3. `UpdateTime` (`0x1dd45c0`);
    4. `UpdateInput` (`0x1d16380`);
    5. troca do frame context;
    6. `Frame` (`0x1dd37e0`), que chama `PS4TaskManager::RunFrame` (`0x1e4a040`).
- **Sem slot de render ou present na App.** O frame vai por mailbox para a thread `ps4render` (`0x1c53fe0`), e o
  Present (`0x1c4dfa0`) chama `sceGnmSubmitAndFlipCommandBuffers` com vsync.
- **Travado em 30 fps:**
  - `sceVideoOutSetFlipRate(h,1)` em `0x1c4f9f0`, com triple buffer;
  - o dt entre 31,7 e 35 ms é ajustado para exatamente 1/30 s, com dt máximo de 0,05 s (`0x1d16480`).
- **Threads:**
  - main;
  - `workerThread0..6` (7 fixos);
  - `ps4render` (core 0);
  - `ps4render_submitDone`;
  - `HavokWorkerThread` ×4;
  - Trophy, PlayGo;
  - ~7 threads de áudio sndx.

  As afinidades são fixas para os 7 cores do PS4.
- No shutdown, o jogo **relança a si mesmo** com `sceSystemServiceLoadExec("-reboot")`.

### 3. Renderização
_Em andamento: o relatório vai em `analysis/02_rendering_gnm.md`._

O engine **"anzu"** (genDESIGN/SIE Japan) tem um backend PS4 em forma de **D3D11**:
`render/ps4/Js{Device, DeviceContext, SwapChain, Buffer, Texture1D/2D/3D, *View, *State, InputLayout,
Vertex/PixelShader, ComputeContext/Queue}.cpp`.
Os passes, em `render/dev`, são SSAO, SMAA, Bloom, PostProcess, TileCull, LightBuffer, AmbientLighting,
LightProbes, Skinning e instancing por compute.
Os shaders PSSL vêm pré-compilados (`.sb`) no psarc (`data_trico/ps4_shader_cache/…`), e há ~51 blobs `OrbShdr`
embutidos no eboot.
Há modos checkerboard 4K para PS4 Pro (`sceKernelIsNeoMode`), desativáveis com `-force2k`.

### 4. Áudio
Detalhes em [`analysis/03_audio.md`](analysis/03_audio.md).

- **Cadeia:** sndx (SCE) → **NGS2** → **AudioOut**, em 8 canais float32 a 48 kHz.
  A thread `sndx_out_thread` (`0x11f28a0`) faz o render (`0x11b04f0`) e chama `sceAudioOutOutputs`, que é o clock do áudio.
- **Racks NGS2:** mastering, submixer e sampler (256 vozes), mais racks de efeito: reverb, EQ, compressor, upmix,
  delay e chorus.
- **Audio3d e alto-falante do controle não são usados.** O sndx é inicializado sem eles, então basta um stub.
- **Dados:** `game/sounds/**` no `trico_boot.psarc`, com descritores `.bod`, bancos `*_sbuf.data` (SXDF) e
  streams `.scs` (SXDS).
- **Codecs:** VAG/HEVAG ADPCM na maioria dos efeitos; **ATRAC9** em BGM, diálogo e ambiência.

### 5. I/O, psarc, controle, saves, sistema
Detalhes em [`analysis/04_io_input_saves_system.md`](analysis/04_io_input_saves_system.md).
Esta área **não é gargalo**: partindo do runtime do gow3_pc, a estimativa é de ~4–7 dias-pessoa.

- **Fios2:**
  - `0x1f47900` inicializa o Fios2 com os filtros Cache e PsarcDearchiver.
  - A tabela de archives fica em `0x67d6440` (12 entradas, cada uma ligada a um chunk PlayGo).
  - `0x1f47740` monta **todos** os psarc em `/app0/data_trico`, na ordem base → patch `p`.
  - O overlay de idioma (`0x1f47350`) mapeia `game_<lang>` sobre `game`.
  - **Fallback:** sem `trico_boot.psarc`, o jogo lê de um diretório solto (`/app0/data_trico`).
    Dá para extrair os psarc e dispensar o formato.
- **PSARC:**
  - Versão 1.4, só zlib, blocos de 64 KiB.
  - Nos patches `p`, a TOC é ordenada por MD5 do path em maiúsculas.
  - O `trico_boot` tem 32.567 arquivos. Os maiores grupos:
    - 24.517 shaders `.sb` (111 MB);
    - 1.431 texturas `.gnf` (1,37 GB);
    - 2.246 `.data` (948 MB);
    - 293 streams de áudio `.scs` (535 MB);
    - 620 `.lua`.
  - O `bootp` (1.03) reescreve quase todo o shader cache.
  - Não há arquivos de vídeo; as cutscenes são em tempo real.
- **Lua:** a VM é HavokScript 2013.3.0, com compilador embutido. Os ~790 `.lua` são **texto-fonte**, não
  bytecode, e o ponto de entrada é `system/scripts/startup.lua`. Isso torna a lógica de jogo legível e
  modificável.
- **Controle:**
  - Há um único `scePadReadState`, em `0x1d2e239`.
  - Usa sticks, gatilhos, botões, gyro/acelerômetro, até 2 toques no touchpad, vibração com os dois motores
    separados e light bar.
  - O `runtime_pad.c` do gow3_pc cobre tudo isso.
- **Saves:**
  - API `SaveDataMemory2`, com 1 MiB + ícone. O blob é `[u32 0xffff8][u32 0][payload]`, com magic `0xd0000009`.
  - O gow3_pc só tem a v1, então é trabalho novo (~0,5–1 dia).
- **Serviços:**
  - Troféus: stub.
  - **PlayGo** deve dizer que os 27 chunks estão disponíveis; um chunk com locus 0 faz o archive não ser montado.
  - PlayGoDialog: stub.
  - `LoadExec` (o reboot) vira reexecutar o processo.
- **Rede:** são 23 imports `sceNet*` **sem call sites**, de um servidor de debug/editor da engine
  (`netmsg.lua`), e não telemetria. Basta stub.
- **`sceKernelIsNeoMode`:** escolhe o layout de memória da GPU (Pro: 0xd0000000; base: 0xb0000000). A decisão
  depende do renderer.
- **Idiomas aceitos:** enu, ptb, esl, frc.

---

## Cobertura pelo runtime existente (gow3_pc + shadPS4)

O cruzamento estático é por NIDs presentes no código-fonte e mostra **~400 de 508 imports (79%)** com
implementação. Isso não garante que cada função esteja completa.

| Lacuna | Funções | Observação |
|---|---|---|
| libSceNgs2 | 10 | **Maior buraco**: ninguém implementou ainda |
| libSceAudio3d | 12 | stub (não é usado) |
| libkernel | 16 | event flags, `IsNeoMode`, `Getdents`, alguns `scePthread*` (triviais) |
| libSceSaveData | 5 | variante `SaveDataMemory2` |
| PlayGoDialog, `LoadExec`, `PadSetMotionSensorState`, `AudioOutSetMixLevelPadSpk` | 8 | stubs ou simples |
| Fios2 (26) e libc (31) | — | não são lacuna: resolvem para os prx do próprio jogo |

---

## Estimativa preliminar (em construção)

| Área | Esforço | Fonte |
|---|---|---|
| Loader/linker e runtime base | adaptar o gow3_pc/bloodborne_pc | a definir |
| Áudio: AudioOut, stubs e ATRAC9 | 1–2 dias | 03_audio |
| Áudio: NGS2 em software, mínimo (sem efeitos) | 2–3 semanas | 03_audio |
| Áudio: NGS2 com efeitos (reverb/EQ/comp/upmix/chorus/delay) | +3–5 semanas | 03_audio |
| _Alternativa ao NGS2 em software_ | 1–4 semanas | carregar o `libSceNgs2.sprx` do firmware do próprio console (não verificado) |
| Threads, timing e 30 fps → FPS livre | a definir | 01 |
| Vídeo (shadPS4 + fixes do engine anzu) | a definir | 02 |
| I/O, controle, saves e serviços (PlayGo, troféus, LoadExec, rede como stub) | ~4–7 dias | 04 |

---

## Estrutura do repositório

```
README.md            este documento (status + achados)
analysis/            relatórios de engenharia reversa (.md) e listas de imports (.json)
scripts/             utilitários (imports SCE, leitor de TOC PSARC, mirror/verify FTP, progresso do dump USB)
analysis/raw/ (ignorado)  pseudocódigo bruto, manifests dos psarc e snapshot do REA
dump/   (ignorado)   arquivos do jogo, apenas locais
tools/  (ignorado)   Ghidra 12.1.4, JDK 21, GhidraOrbis
```

### Ferramentas
- Ghidra 12.1.4 + GhidraOrbis, compilado do fonte com 2 patches de API para o 12.1.x
- [REA](https://github.com/morluto/rea) `rea-agents@6.4.0` como servidor MCP. Para um eboot desse tamanho,
  ajuste `REA_GHIDRA_STARTUP_TIMEOUT_MS=14400000` e `GHIDRA_HEADLESS_MAXMEM=16G`.
- `scripts/sce_imports.py <eboot> <nid_db.xml> <saida.json>` lista as imports por biblioteca, com NIDs resolvidos.
