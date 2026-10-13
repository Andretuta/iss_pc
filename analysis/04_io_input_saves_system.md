# 04 — File I/O, arquivos PSARC, input, saves e serviços de sistema

Alvo: The Last Guardian (PS4, CUSA03627), `eboot.bin` v1.03 (`/home/hayatog/decomp/dump/patch0/eboot.bin`).
Os endereços são do Ghidra (base 0x1000000). Offset no arquivo = endereço − 0x1000000 + 0x4000 (texto e dados têm o mesmo delta).
Engine interna: **"anzu"** (path `D:\trico\engine\anzu\...`).

Convenção: **[C]** = confirmado (decompilação, bytes ou dados lidos) · **[H]** = hipótese/inferência.

---

## 0. Resumo

| Área | Como o jogo usa | O que já existe no gow3_pc | Trabalho novo |
|---|---|---|---|
| FS / Fios2 | Usa o `libSceFios2.prx` dele mesmo. Todos os PSARC montados em `/app0/data_trico`, com overlay de idioma `game_<lang>` → `game`. Se `trico_boot.psarc` não existir, cai em diretório solto `/data/data_trico` ou `/app0/data_trico` | `link_modules.py` já linka `libc.prx` + `libSceFios2.prx`. `runtime_file.c` cobre **todos** os imports de kernel FS do Fios2 que consegui resolver (20/20) | Quase nada. Faltam `sceKernelGetdents` (import do eboot) e testes |
| PSARC | v1.4, zlib, blocos de 64 KiB, entradas de 30 B. Os patches "p" têm flag 0x8: TOC ordenada por MD5 | Descompressão feita pelo próprio Fios2 (código PS4) | Nenhum (ou extrair tudo para loose files) |
| Input | 1 `scePadReadState` por frame, motion ligado, vibração L/R, light bar e tilt/deadband via Lua | `runtime_pad.c` (SDL3, `ScePadData` completo, touch, motion, vibração, light bar) | Só mapeamento e ajuste fino |
| Saves | `sceSaveData*Memory2`: blob de 1 MiB + ícone de 0x1c800 B. Payload de 0xffff8 B, magic `0xd0000009` | Só a API Memory **v1** (`Setup/Get/SetSaveDataMemory`) | Implementar `Setup/Get/SetSaveDataMemory2` + `SyncSaveDataMemory` (~0,5 dia) |
| Troféus | Thread "TrophyThread", Register → GetUnlockState → Unlock | Stubs em `runtime_services.c` | Nada |
| PlayGo | 27 chunks. Archive só monta se o chunk tiver locus ≠ 0. Se `scePlayGoOpen` retorna `0x80B20008`, tudo vira locus 3 | Stub "fully installed" | Nada (devolver locus 3 ou NOT_SUPPORT) |
| PlayGoDialog | Só abre se faltar chunk | Não existe | 5 stubs triviais |
| LoadExec | Reboot do jogo: `/app0/<thread>` com `-reboot` | Não existe | Reiniciar o processo ou o subsistema (~0,5–1 dia) |
| Rede | `libSceNet` importada, mas **sem nenhum call site** (byte-scan). Servidor de debug/editor ("NetMsg", `SrvSend`) | sceNet completo (desnecessário) | Nada (stubs de erro) |
| NeoMode | Tamanho de memória direta (0xd0000000 vs 0xb0000000) + libs de GPU | Não existe (trivial) | Retornar 1 (Pro) |
| Lua | **HavokScript 2013.3.0** com compilador embutido. Os 790 `.lua` são **texto-fonte**, não bytecode | — | Nada (roda como código do jogo) |

Estimativa total para esta área, partindo do runtime do gow3_pc: **~4–7 dias-pessoa** (detalhes na §7).

---

## 1. Sistema de arquivos / Fios2

### 1.1 Inicialização — `FUN_01f47900` (construtor do objeto FileSystem, vtable `PTR_FUN_026f0a00`) [C]
- `sceFiosInitialize(&params)`: params em pilha, op/chunk/fh pools nos buffers `0x6a05e70` (0x8008), `0x6a0de80` (0x14080), `0x6a21f00` (0x2e08), `0x6a24d10` (0x440). Callback de print `FUN_01f48160` e `memcpy`.
- `FUN_01f481c0("/app0/")` preenche a tabela de archives. Se `sceFiosFileExistsSync("/app0/trico_boot.psarc")` falhar, tenta `/data/`. Se também falhar:
  - `sceFiosDirectoryExistsSync("/data/data_trico")`, depois `"/app0/data_trico"`: **modo loose files** (sem PSARC). [C]
- Prefixos guardados no objeto: `+0x230` = `"/app0/"` (ou `/data/`), `+0x270` = `"/app0/data_trico"` (**mount point**), `+0x2b0` = `"/app0/data_trico_overlay"`.
- Pilha de I/O filters:
  - `sceFiosIOFilterAdd(0, sceFiosIOFilterCache, &0x67d63f8)`: cache com buffer em `0x6a55180`, cfg `0xa0508` / blocos de 0x10000.
  - `sceFiosIOFilterAdd(1, sceFiosIOFilterPsarcDearchiver, &0x67d63c0)`: work buffer em `0x6a25180`, 0x30000 B.
- Depois chama o vmethod `+0xe8` (mount), que é `FUN_01f47740`, e loga cada archive com `"%-25s %12s %04d/%02d/%02d..."`, `==UNMOUNT==` e `==UNUSED==`.

### 1.2 Tabela de archives — `0x67d6440`, 12 entradas de 0x50 B [C] (lida dos bytes do eboot)
Layout: `+0 int slot`, `+4 u8 used`, `+8 int playgo_chunk`, `+0xc char path[0x3e]`, `+0x4c u8 mounted`, `+0x4d u8 enabled`.

| slot | arquivo | chunk PlayGo |
|---|---|---|
| 0 | trico_boot.psarc | 0 |
| 1 | trico_bootp.psarc | 0 |
| 2 | trico_%s.psarc (idioma: enu/esl/frc/ptb) | lang_id+1 (ou 2 se lang = 0x17) |
| 3 | trico_%sp.psarc | idem |
| 4/5 | trico_001(p).psarc | 24 |
| 6/7 | trico_002(p).psarc | 25 |
| 8/9 | trico_003(p).psarc | 26 |
| 10 | trico_other.psarc (opcional: `FileExists`; não existe no dump) | 0 |

### 1.3 Mount — `FUN_01f47740` [C]
Para cada entrada com `used && enabled && !mounted && playgo_locus[chunk] != 0` (byte em `*(App+0xf58)+0x14+chunk`):
`sceFiosArchiveGetMountBufferSizeSync`, depois aloca e chama `sceFiosArchiveMountSync(0, &fh[slot], path, "/app0/data_trico", buf, size, 0)`.
**Todos os archives são montados no mesmo mount point**, na ordem base → patch (boot, bootp, lang, langp, 001, 001p, ...).
- [H] O patch "p" sobrepõe o base porque é montado depois no mesmo ponto (no Fios2 o mount mais recente costuma ser o primeiro a ser resolvido). Não existe `sceFiosOverlayAdd` para os patches.
- A thread PlayGo (`FUN_01dd5500`) chama de novo o vmethod `+0xe8` do FileSystem (`*(App+0x28)`) quando o locus muda, o que monta os chunks que acabaram de chegar. [C]

### 1.4 Overlay de idioma — `FUN_01f47350` (vmethod `+0xd0`) [C]
`sceFiosOverlayAdd` com type/order `0x0101`, dst `"/app0/data_trico/game"` e src `"/app0/data_trico/game_<lang>"` (tabela de códigos em `PTR_DAT_02716230`, stride 0x20). Prefixos em lowercase. `sceFiosOverlayRemove` na troca de idioma.
Isso bate com o conteúdo de `trico_enu.psarc`, que tem `game_enu/...` e também `game/...` (1773 + 1294 entradas).

### 1.5 Paths usados pelo código [C]
- O jogo pede caminhos relativos `data_trico/game/...` (ex.: `"data_trico/game/savetitle/savetitle.dat"`, `"data_trico/game/trophy/trophy00.dat"` em `FUN_01cf7a40`), resolvidos contra `/app0/`.
- Strings em `0x25a00c0..`: `rb wb rb+ ab+ .lua FileSystemStd %s%s/game data_trico %s%s/game_%s ... /app0/ ... data_trico_overlay /data/ /data/data_trico /app0/data_trico`.
- Outros: `"/app0/%s"` (`0x2595acb`, usado no LoadExec).

### 1.6 Implicações para o PC
- **Caminho A (recomendado):** manter o `libSceFios2.prx` do jogo (como o gow3_pc faz) e mapear `/app0` → pasta com `trico_*.psarc` + `trico_*p.psarc` lado a lado (os patches junto dos base, como no PS4 com o patch aplicado). O Fios2 faz a descompressão PSARC sozinho.
- **Caminho B:** extrair tudo para `data_trico/` (patch por cima do base, `game_<lang>` à parte) e usar o fallback de loose files que o próprio jogo já tem. Isso elimina PSARC/Fios do caminho crítico.
- Imports de kernel do `libSceFios2.prx` (resolvidos por NID com o `import_names.inc` do gow3): `sceKernelOpen/Close/Read/Write/Pread/Pwrite/Lseek/Fstat/Stat/Fsync/Ftruncate/Truncate/Mkdir/Rmdir/Rename/Unlink/Getdirentries/Usleep/ClockGettime/Gettimeofday`. **Todos já existem no gow3_pc** [C]. Cerca de 150 NIDs do prx não foram resolvidos pela tabela; a maioria deve ser libc interna [H].
- **Atenção:** `trico_001/002/003.psarc` do dump estão truncados. Pela TOC, faltam 8717/13232, 9306/13202 e 7908/15031 entradas (~4,3 GB descomprimidos cada). É preciso redumpar antes de qualquer teste fora do boot.

---

## 2. Formato PSARC (verificado)

Script: `/tmp/claude-1000/-home-hayatog-decomp/79f27d1d-d3f5-4a2e-a5f3-511e01385ae2/scratchpad/psarc/psarc_toc.py`, com helpers `cat.py` e `peek.py`. Os manifests extraídos estão em `.../scratchpad/psarc/*.manifest.txt`.

Header (big-endian, 32 B): `"PSAR"`, v1.4, `"zlib"`, toc_len, entry_size = 30, count, block = 65536, flags. Cada entrada tem MD5(16) + block_index(4) + usize(5) + offset(5). A tabela de tamanhos de bloco usa u16 (0 = bloco cheio de 64 KiB sem compressão). A entrada 0 é o manifest.

| archive | flags | entradas | conteúdo |
|---|---|---|---|
| trico_boot.psarc (2,90 GB) | 0x1 | 32568 | ps4_shader_cache 24517, game 8019, system 31 |
| trico_bootp.psarc (0,55 GB) | **0xd** | 24959 | ps4_shader_cache 24636 (shaders inteiros recompilados no 1.03, inclui `checkerboard_resolve`, `*hdr*`), game 322 |
| trico_001/002/003 | 0x1 | 13233 / 13203 / 15032 | só `game/` (assets, textures, mc_gbuf, objects, stages, ...) |
| trico_001p/002p/003p | 0xd | 257 / 446 / 468 | correções de assets |
| trico_enu/esl/frc/ptb | 0x1 | 3068 / 2994 / 2996 / 2996 | `game_<lang>/` + `game/` (subtitle, texturas de UI, objects) |
| trico_*p (idiomas) | 0xd | 113 / 21 / 21 / 21 | |

Observações [C]:
- **Compressão: só zlib** (nenhum LZMA). Blocos de 64 KiB.
- **Manifest:** no base, nomes separados por `\n` e na mesma ordem da TOC. Nos patches (flag 0x8), separados por `\0`, e a TOC está **ordenada por MD5(UPPERCASE(path))**. O mapeamento nome → entrada precisa ser feito pelo hash (validado: 24958/24958). [H] Flag 0x8 = "TOC ordenada" para busca binária pelo Fios. Flag 0x4 (absolute/sem `/` inicial) [H].
- Paths sem `/` inicial, ignorecase.

Extensões (trico_boot, uncompressed):

| ext | qtde | MB | magic / natureza |
|---|---|---|---|
| `.sb` | 24517 | 111 | Shader binário PSSL (header `00 04 ..`, depois `"Shdr"`), em `ps4_shader_cache/{material,particle,system}` |
| `.gnf` | 1431 | 1366 | Texturas GNF (`"GNF "`) |
| `.data` | 2246 | 948 | `"CDAT"`: buffers de geometria (`*_gbuf_verts/elems/uv1`), animgraphs |
| `.bod` | 3220 | 37 | Objetos/params binários da engine (header `01 00 00 00 15 00 00 00`) |
| `.scs` | 293 | 535 | Áudio `"SXDS"`: bancos de som (dialog/se/bgm stream) |
| `.lua` | 620 | 17 | **Texto-fonte Lua** (comentários em japonês, CRLF) |
| `.weights` | 207 | 17 | `"CDAT"`: pesos de cloth/skin |
| `.csv` | 29 | 0,8 | Tabelas de som (`snd_*.csv`) e config (`_config/ps4_anim_tracker.csv`) |
| `.dat` | 2 | — | `savetitle.dat` (`"TSDL"`), `trophy00.dat` (`"TTDT"`) |
| `.abc` | 1 | — | Fonte bitmap de debug `system/fonts/dina_8.abc` |
| `.psd` | 1 | 5 | Sobra de produção (`credit_ed_movieframe_work.psd`) |

- `game/sounds`: 810 em `dialog`, 58 em `se`, 35 em `bgm`, além de `trico_buss.bod` e CSVs.
- `game/scripts`: ai2 269, stages 234, common 48, modules 12, `_editor` 11, camera 10, guide 5, demo 2. `system/scripts`: `startup.lua`, `states/main.lua`, `netmsg.lua`, `keybinder.lua`, etc.
- **Nenhum arquivo de vídeo** (bk2/mp4/pam) em nenhum archive nem no diretório do jogo. [H] As cutscenes são em tempo real.

---

## 3. Input (libScePad)

### 3.1 Leitura — `FUN_01d2e1d0` (update por pad; único call site de `scePadReadState` em `0x1d2e239`) [C]
- `scePadOpen(userId (obj+0x1c), 0 /*standard*/, 0)` sob demanda, seguido de **`scePadSetMotionSensorState(h, 1)`**: o motion sensor fica ligado.
- `scePadReadState(h, obj+0x10 /*ScePadData*/)` uma vez por frame.
- Vibração: mistura uma lista de "VibrationFx" ativos (array de 0x18 B em obj+0x28, curvas com escala) e faz `max` separado de large/small → `scePadSetVibration(h, {u8 large, u8 small})` (valores ×255). Zera quando `dt < 1e-5` (pausa).
- `scePadClose` em `0x1d2df5c` e `0x1d2e12c`. `scePadInit` em `FUN_01dd39d0`.
- Objetos de pad: `*(App+0x98+i*8)`, com i = 0..1. `App` = global `DAT_069a1b40`.

### 3.2 Estado normalizado exposto ao Lua — `FUN_01d53420` (tabela global `Input`) [C]
Mostra exatamente o que a engine consome (o struct App é preenchido a partir do ScePadData por código que não localizei) [C para os campos, H para a origem]:
- Teclado/mouse (dev): `shift/ctrl/alt` (App+0x430..0x438), `cursor.x/y` (App+0xe24/0xe28).
- `pad1`, `pad2`: `LX LY RX RY LMag RMag LTMag RTMag` (floats, App+0xe38..), `hold/down/up/rept` (bitmasks de botão, App+0xe78..).
- `sensor1/2`: `orientation` (quat), `acceleration`, `angularVelocity` (App+0xec0.., stride 0x30).
- `touch1/2`: `num` + 2 pontos `{x, y, id}` (App+0xea4..).
- `vib1/2`: `L/R` (App+0xf20/0xf24).
- Bindings Lua (strings em `0x2593879..`): `SetPadVibration`, `StartVibration`, `StopAllVibration`, `SetLightBar` (`FUN_01d52090`), `ResetLightBar`, `SetTiltCorrectionState`, `SetAngularVelocityDeadbandState`, `ResetOrientation`. `FUN_01d51d30` = vibração direta via Lua.
- Strings de remapeamento: `RemapDButtonInputFrame_{L3,R3,Touch}`, `RemapDButtonIntervalTime_*`, `AnalogStickLeft_InputAcceleration`. [H] O clique do touchpad é usado como botão (mapa/menu). Não há evidência de uso gameplay de gyro além de ficar disponível para scripts.

### 3.3 O que a camada de input no PC precisa entregar
`ScePadData` padrão (botões, 4 eixos u8, L2/R2 analógicos, orientação/accel/gyro, touch com 2 pontos e clique do touchpad), vibração de 2 motores e light bar (ignorável). **O `runtime_pad.c` do gow3_pc já implementa tudo isso** (SDL3, layout verificado por `_Static_assert`, touch emulado, keyboard fallback). Basta ajustar o keymap padrão para TLG.

---

## 4. Saves, troféus e serviços

### 4.1 SaveData Memory2 [C]
- Init: `sceSaveDataInitialize3(0)` em `FUN_01dd39d0`.
- Setup: `FUN_01cf7a40` (linha "sceSaveDataSetupSaveDataMemory2") → `{option=1, userId, memorySize=0x100000 (1 MiB), iconMemorySize=0x1c800}`.
- **Set:** `FUN_01e20300`. Monta um buffer de 0x100000: `u32 size=0xffff8`, `u32 0`, `payload[0xffff8]` (cópia direta do struct de estado do jogo). Parâmetros title/subtitle/detail localizados vêm de `savetitle.dat` ("TSDL") por idioma. Retry a cada 25 ms enquanto retornar `0x809F0016` (BUSY).
- **Get:** `0x12309d7` / `0x1230aac`, dentro de `FUN_01230810` (função gigante, o Ghidra estoura o buffer ao decompilar; análise por objdump). Lê 1 MiB, valida `size == 0xffff8` e **magic do payload `0xd0000009`**, depois `memcpy` para `obj+0x40`. Mesmo retry no BUSY.
- **Sync:** `sceSaveDataSyncSaveDataMemory({userId})` em `FUN_0126b200`, disparado por timer depois de um save.
- `sceSaveDataTerminate` com retry no shutdown/reboot (`FUN_01dd3f50`).
- **Formato:** blob binário POD de ~1 MiB. [H] É uma imagem crua de struct, então o save de PS4 deve ser portável byte a byte se o struct não tiver ponteiros.
- **PC:** um arquivo de 1 MiB por usuário (o `memory.dat` do gow3_pc serve), mais as variantes `*Memory2` (structs de param diferentes: `SceSaveDataMemorySetup2`/`Get2`/`Set2` com `SceSaveDataMemoryData*` e `SceSaveDataParam*`) e `SyncSaveDataMemory`.

### 4.2 Troféus [C]
`FUN_01cf7a40`: se `AppParam USER_DEFINED_PARAM_3 == 1` (offset `cfg+0x28`), troféus ficam desligados. Caso contrário: `sceSysmoduleLoadModule(0xad)`, `sceNpTrophyCreateContext`/`CreateHandle`, carrega `trophy00.dat` ("TTDT", tabela ID → nome), cria a thread "TrophyThread" (`FUN_01d870c0`: `RegisterContext`, `GetTrophyUnlockState`, loop `UnlockTrophy` via semáforo). `sceNpSetNpTitleId` com um ID por SKU (`PTR_DAT_026ea6a0`). Os stubs do gow3 bastam. Pode-se logar os unlocks.

### 4.3 PlayGo [C]
- `FUN_01dd52c0`: `sceSysmoduleLoadModule(0x83)` e `(0xf1)`, `scePlayGoInitialize({buf 2 MiB})`, `scePlayGoOpen`. **Se retornar `0x80B20008` (NOT_SUPPORT_PLAYGO), marca os 27 chunks com locus 3** (LOCAL_FAST). Senão chama `scePlayGoGetLocus` com os chunks 0..26.
- Thread "PlayGoThread" (`FUN_01dd5500`): para chunks com locus ≠ 3, refaz `GetLocus` e remonta os archives.
- **Stub:** `scePlayGoOpen` → `0x80B20008`, ou `GetLocus` → 3 para tudo. Trivial. Atenção: se o locus vier 0, o archive **não é montado**.

### 4.4 PlayGoDialog [C]
`FUN_0126b200` (update do título): máquina de estados em `*(App+0xf58)+0xc`. Só chega ao `scePlayGoDialogInitialize/Open/UpdateStatus/GetResult/Terminate` quando algum chunk falta. Com o PlayGo stubado nunca é chamado, mas precisa de stubs para resolver os imports.

### 4.5 SystemService / UserService / AppContent [C]
- `sceUserServiceInitialize(0)` e `GetInitialUser` (vários pontos).
- `FUN_01d4c960`: `sceSysmoduleLoadModule(0xb4)`, `sceAppContentInitialize`, `AppParamGetInt(1)` = SKU (param.sfo `USER_DEFINED_PARAM_1 = 1`, US), `(2)` = build (`1612131828` → string `"%c20%d-%04d0"`), `(3)` = flag (0). `sceSystemServiceParamGetInt(1 = LANG)`: para o SKU 1, os idiomas aceitos são a máscara `0x520002` (1 en-US, 17 pt-BR, 20 es-LA, 22 fr-CA = enu/ptb/esl/frc). Fallback é 1. O config fica em `*(App+0xf70)`: `[0]` SKU, `[1]` idioma, `+8` código ("enu"...), `+0x10` title ID por SKU (`PTR_s_CUSA05152_026e9d20`), `+0x28` param3.
- `sceSystemServiceGetStatus` em `0x1dd462f` (poll de eventos/quit). `sceSystemServiceHideSplashScreen` via thunk `0x1dd37d0`.
- **LoadExec** (`FUN_01dd3f50`, call em `0x1dd40c4`): restart. Faz `sceSaveDataTerminate` (retry) e depois `sceSystemServiceLoadExec("/app0/<nome da thread>", {"-reboot", NULL})` em loop. É usado em "restart" (troca de idioma/estado), referenciado por `system/scripts/restartcallback.lua` [H]. No PC: `execv` de si mesmo com `-reboot` (o caminho mais simples), ou sair com código e deixar o launcher relançar.

### 4.6 Rede (libSceNet/NetCtl) [C]
- 23 imports `sceNet*` (socket/bind/listen/accept/epoll/resolver) e `sceNetCtlGetInfo/GetState`. **Nenhum call site** (`call`/`jmp` rel32 nos stubs `0x24be698..0x24be818`), nenhuma xref do Ghidra, nenhuma referência ao GOT `0x6b0c580..` fora da tabela de relocação.
- Propósito: servidor de debug/editor ao vivo da engine. Lua `system/scripts/netmsg.lua` (autor "izawa"): `RegisterReceive`, `SrvSend(client_id,'msg')`, comandos `version/echo/get/getprops/geth...` para inspecionar objetos. Bindings `ClientConnect/ClientSend/ClientDisconnect/IsClientConnected` (strings em `0x2593920..`). Não é telemetria.
- **PC:** stubs que retornam erro. Nada a portar.

### 4.7 sceKernelIsNeoMode [C]
- 51 call sites. Em `FUN_01207cc0` (heaps "MallocHeapHi" 0x49800000 + "MallocHeapLo" 0x31800000; o resultado de NeoMode é ignorado e a flag é forçada a 1) e `FUN_01dd39d0` (direct memory da GPU: **0xd0000000 se Neo, 0xb0000000 se base**, mais 0x6000000 de onion).
- Os demais (`0x246ba90`, `0x2476850` ... `0x24a79e0`) estão no bloco final do texto. [H] São libs estáticas Sony (Gnm/Gnmx/driver helpers), que escolhem paths Pro. Também há shaders Pro no 1.03 (`checkerboard_resolve`). Isso é assunto do relatório de GPU.
- **PC:** retornar 1 (Pro) dá mais memória e o modo de maior resolução [H]. Validar com quem cuida do renderer.

### 4.8 Ordem de boot relevante (`FUN_01dd39d0`) [C]
Direct memory → módulos internos por nome (`render_dev`:`CreateRenderer`, `havok`:`CreatePhysics`, som:`CreateSoundManager`, game:`CreateGame`, registry interno em `FUN_01d86780`) → `sceUserServiceInitialize` → `scePadInit` → `sceSaveDataInitialize3` → `FUN_01cf7a40` (resmgr, SaveDataMemory2 setup, savetitle, NpTitleId, troféus, PlayGoThread).

---

## 5. Lua / HavokScript [C]
- VM: **HavokScript 2013.3.0** (`D:\trico\engine\anzu\external\havok\HavokScriptVM-2013.3.0\...`), API `hksi_lua_*`/`hksi_luaL_*` com `hksi_luaL_loadbuffer`/`loadstring`, **compilador incluso** (`.../virtualMachine/Compiler/...`, "int literals not enabled in compiler options"). Também suporta bytecode ("Header mismatch when loading bytecode", "Inplace bytecode must be aligned").
- **Todos os `.lua` dos archives são texto-fonte** (620 no boot, 170 no bootp; nenhum começa com `\x1bLua`), compilados em runtime. Entrada: `system/scripts/startup.lua` → `Load("system/scripts/states/" .. SysInfo.state)`. Os globais `SysInfo` (`isCooker`, `devParam`, `ps4`, `config/gamecfg/rendercfg`, `dt/edt/hdt`, `screenW/H`) e `Input` vêm do C.
- **PC:** a VM HKS é código do eboot (x86-64) e roda como está. Bônus: scripts editáveis/moddáveis em texto.

---

## 6. Comparação com o gow3_pc

| Item TLG | gow3_pc | Status |
|---|---|---|
| Link de `libc.prx` + `libSceFios2.prx` | `scripts/link_modules.py` (DEFAULT_MODULES exatamente esses dois) | ✅ Reaproveitar |
| Kernel FS (`sceKernelOpen/Pread/Stat/Getdirentries`...), mounts `/app0`, `/data` | `runtime_file.c` | ✅ (faltam `sceKernelGetdents` e checar `/data/data_trico`) |
| Fios ArchiveMount/PsarcDearchiver/Overlay | Executados pelo prx do jogo | ✅ (validar: o gow3 talvez não exercite PSARC/overlay; risco baixo-médio) |
| scePad* (11 funções usadas) | `runtime_pad.c` cobre as 11 | ✅ |
| SaveData Memory2 + Sync | Só Memory v1 | ⚠️ Novo (~0,5 dia) |
| NpTrophy (5), NpSetNpTitleId | `runtime_services.c` | ✅ |
| PlayGo (5) | `runtime_services.c` | ✅ (garantir locus 3 para os 27 chunks) |
| PlayGoDialog (5) | — | ⚠️ Stubs (1 h) |
| SystemService LoadExec | — | ⚠️ Novo (0,5–1 dia) |
| SystemService ParamGetInt/GetStatus/HideSplash, UserService | ✅ | ✅ (idioma por env var: 1/17/20/22) |
| AppContent (Init + AppParamGetInt 1..3), Sysmodule | `runtime_content.c` | ✅ (configurar params: 1, 1612131828, 0) |
| sceNet / NetCtl | Implementado | ✅ (bastaria stub) |
| sceKernelIsNeoMode | — | ⚠️ 1 linha |
| CommonDialog/MsgDialog | ✅ | ✅ |

## 7. Estimativa de esforço (só esta área)
- Ligar FS + Fios2 + PSARC ao runtime existente e depurar mounts/overlay: **1–2 dias**. Opcional: script de extração para o modo loose-files, ~0,5 dia (o `psarc_toc.py` já tem 80% disso).
- SaveData Memory2/Sync, com teste de roundtrip do blob 0xd0000009: **0,5–1 dia**.
- LoadExec/reboot: **0,5–1 dia**.
- Stubs (PlayGoDialog, IsNeoMode, Getdents, net) e configuração de AppContent/idioma: **0,5 dia**.
- Input (keymap TLG, vibração, testes de touch/motion): **0,5–1 dia**.
- Folga para integração e bugs: **1–2 dias**.
- **Total: ~4–7 dias-pessoa.** Esta área **não** é o gargalo do port (o gargalo é GPU/Gnm + áudio Ngs2/Audio3d).

## 8. Riscos e pendências
1. Redumpar `trico_001/002/003.psarc` completos (faltam ~13 GB descomprimidos).
2. [H] A precedência patch > base depende da ordem de mount do Fios2. Validar em runtime abrindo um arquivo que só existe no `*p`.
3. Não localizei a função que converte `ScePadData` nos floats `App+0xe38..` (a busca terminou em `FUN_01d2e1d0`/`+0x10`). Não é bloqueante.
4. O Ghidra não decompila `FUN_01230810` (load do save; buffer excedido). Os detalhes do Get vieram de objdump (`0x1230940..0x1230c80`).
