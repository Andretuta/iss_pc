# 01 — Main loop, frame pacing e threading (TLG PS4 v1.03, CUSA03627)

Binário: `/home/hayatog/decomp/dump/patch0/eboot.bin` (Ghidra, image base 0x1000000). Endereços abaixo são endereços Ghidra.
Legenda: **[C]** = confirmado no código decompilado/bytes; **[G]** = inferência/palpite (marcado explicitamente).

---

## 0. Resumo executivo

* O jogo é **travado em 30 fps** por hardware: `sceVideoOutSetFlipRate(handle, 1)` (1 = 30 Hz) em `FUN_01c4f9f0` (JsDevice/JsSwapChain init) + flip `SCE_VIDEO_OUT_FLIP_MODE_VSYNC` em `sceGnmSubmitAndFlipCommandBuffers` (`FUN_01c4dfa0`, `JsSwapChain::Present`). **[C]**
* O delta-time é medido via TSC (`sceKernelReadTsc` × `DAT_069afc80 = 1/sceKernelGetTscFrequency()`) em `App::UpdateTime` (vtbl+0xc0, `FUN_01dd45c0`) e suavizado em `FUN_01d16480`, que **"encaixa" dt entre 31.7 ms e 35 ms em exatamente 1/30 s**, aplica filtro e quantiza em 1/360 s. dt máximo = 0.05 s (20 fps). **[C]** (semântica fina do filtro **[G]**)
* Arquitetura: **main thread (simulação + TaskManager)** → **thread `ps4render`** (gera e submete command buffers, 1 frame em pipeline) → **thread `ps4render_submitDone`** (espera EOP da GPU e chama `sceGnmSubmitDone`). **[C]**
* Pool de jobs próprio do engine: **`PS4TaskManager`** com **7 `workerThread%d`** (affinity 0xf p/ 0–3, 0x70 p/ 4–6, prio 0x228). Havok tem **4 `HavokWorkerThread`** (affinity 0x7f/0xf, prio 0x228). Áudio (Sony "sndx") cria ~6+ threads com affinity "1111111" = 0x7f. **[C]**
* Tudo assume **7 cores** (máscara 0x7f) e prioridades SCE (256..767). O "sleep" universal é `sceKernelAddHRTimerEvent(100 µs)+sceKernelWaitEqueue` numa equeue TLS "ThreadSleep" (usado em todo spinlock). **[C]**

---

## 1. Vtable da App (`0x26ebbe0`) e ordem do frame

`main` (`0x1207bb0`) constrói o objeto no stack: `FUN_01d16700` (ctor base, grava vtable base `0x26e89b8`), depois sobrescreve com a vtable derivada `0x26ebbe0`, `DAT_069a1b40 = &app`, chama `App::Run` (`FUN_01d169b0`) e o dtor `FUN_01cf7470`. **[C]**

A vtable da App tem 26 slots (0x00..0xc8); em `0x26ebcb0` há dois zeros (fim / offset-to-top+RTTI nulo, `-fno-rtti`) e em **`0x26ebcc0` começa a vtable de outra classe — `PS4TaskManager`** (confirmado: `FUN_01dd4d90` grava `0x26ebcc0` no objeto de 0x1c0 bytes registrado como "PS4TaskManager"/"TaskManager"). **[C]**

| Slot | Endereço | Base (`0x26e89b8`) | Papel identificado |
|---|---|---|---|
| +0x00/+0x08 | 0x1dd3650 / 0x1dd3660 | 0x1cf7470/0x1cf78f0 | destrutores **[C]** |
| +0x10..+0x20 | 0x1cf7910/920/930 | iguais | herdados (não analisados) |
| +0x28 | 0x1dd3680 | 0x1cf7940 | `SetupScreenCenter`: grava resolução/2 (app+0x17c0) **[C]** |
| +0x30..+0x50 | 0x1dd36c0..0x1dd3750 | — | não analisados |
| +0x58 | 0x1dd3760 | **pure** | `OnPadButton(btn, pressed)`: grava em fila circular de 256 eventos (app+0xfb0), estado em app+0x13b0 **[C]** |
| +0x60..+0x78 | 0x1cf79a0, 0x1dd37d0, 0x1cf79c0, 0x1cf7a20 | — | não analisados |
| **+0x80** | **0x1dd37e0** | **pure** | **`App::Frame`/Update**: copia snapshot de input (0x400 bytes app+0x13b0→+0x220, eventos→+0x620), libera módulos com refcount<0 (`ModuleRelease`), e faz **tail-call `TaskManager->vtbl+0x58` = `FUN_01e4a040` (`TaskManager::RunFrame`)**. Aqui roda toda a simulação (tasks "%sJob") **e** a task que dispara o render. **[C]** |
| +0x88 | 0x1dd39d0 | 0x1cf7a40 | `App::Init`: aloca direct memory (Onion 0x6000000; Garlic 0xb0000000, ou **0xd0000000 se `sceKernelIsNeoMode`**), carrega "módulos" internos: `render_dev`→`CreateRenderer` (app[9]), `havok`→`CreatePhysics` (app[0x16]), som→`CreateSoundManager` (app[0x20]), jogo→`CreateGame` (app[6]); `sceUserServiceInitialize`, `scePadInit`, `sceSaveDataInitialize3`; chama +0x28, +0xc0 e `FUN_01cf7a40` (init base do engine: resource mgr, world, TaskManager em app[10]). **[C]** |
| **+0x90** | **0x1dd3f50** | 0x1cfba10 | `App::Shutdown` PS4: `sceSaveDataTerminate` (retry 100×100 ms) e **`sceSystemServiceLoadExec("/app0/<thread name>", "-reboot")` em loop infinito** — o jogo nunca "sai", ele se relança. **[C]** |
| +0x98 | 0x1dd4140 | **pure** | `ReleaseModules` (4 módulos, chama `ModuleRelease`) **[C]** |
| +0xa0 | 0x1dd4320 | 0x1cff000 | `App::PreInit`: `sceSysmoduleLoadModule(0xa4 = MESSAGE_DIALOG)`, `sceCommonDialogInitialize`, **`DAT_069afc80 = 1.0/sceKernelGetTscFrequency()`**, app+0x17f0 = idem, TSC inicial em app+0x17e0, timescale app+0x1b8 = 1.0 **[C]** |
| +0xa8 | 0x1cff010 | igual | herdado (função enorme, não analisada) |
| +0xb0 | 0x1d13230 | igual | herdado (não analisado) |
| **+0xb8** | **0x1d16380** | igual | **`UpdateInput`**: `FUN_01d2e1d0/FUN_01d2eaf0` nos 2 devices de pad (app[0x13], app[0x14]) e gera eventos via +0x58 para botões 0xbe..0xcf **[C]** |
| **+0xc0** | **0x1dd45c0** | **pure** | **`UpdateTime`**: `sceKernelReadTsc`, dt em ticks (app+0x17e8), consulta `sceSystemServiceGetStatus` (se overlay do sistema ativo → escala 0 = pausa, dispara eventos "SystemScreen.enter/leave" categoria "Engine"), chama +0xc8 **[C]** |
| +0xc8 | 0x1d16480 | igual | `SmoothDeltaTime(time, dt)` — ver §3 **[C]** |

Não existe um slot "Render" ou "Present" na App: o render é disparado por uma **Task** dentro de `TaskManager::RunFrame` e o present acontece na thread `ps4render` (ver §2/§3).

### Pseudocódigo do frame (App::Run `0x1d169b0`, loop em ~0x1d18200..)

```c
FUN_01d4cc10(log, fmt, DAT_069afc80 * (tsc_now - tsc_boot));   // log tempo de boot [G: formato]
while (app->quit(0x1f8)==0 || app->busy(0x1c8)!=0) {
    // 1. limpa lista "pending" do object manager
    spin_lock(objmgr+0x201054);            // FUN_014f2e80
    for (o in objmgr->list) o->flags16 |= 2;
    FUN_0188d550(&objmgr->list, 0);        // release de todas as refs + capacity=0
    spin_unlock();
    // 2. GC de objetos com refcount 0 (fila diferida), com orçamento
    lock(objmgrMutex);
    app->pendingDeletes = FUN_01cd5a40(taskMgr->flush(0x104)==0 ? 2000 /*µs*/ : 0);
    unlock(objmgrMutex);
    FUN_01d71f80(0);                       // varre tabela global de heaps DAT_069ac2c0
    // 3. callbacks one-shot (array app[1], count app[2]); remove os que retornam !=0
    app->frameCounter(0x1a8)++;
    if (app[0x22] && (app[0x22]->flags & 2)) FUN_01d4cc10();  // log/debug
    app->UpdateTime();    // vtbl+0xc0
    app->UpdateInput();   // vtbl+0xb8
    // 4. troca double-buffer do "frame context" (render data)
    app->ctxIdx(0x8c) ^= 1; DAT_069a1608 = app->ctx[ctxIdx] (app+0x68/0x70);
    ctx->+0x250 = ratio(...); reset de 3 contadores GPU (flags |=2)       // [G] stats de tempo GPU/dyn-res
    DAT_069b1678 = (DAT_069b1678+1) % 3;   // índice triple-buffer (3 display buffers)
    app->Frame();         // vtbl+0x80 -> TaskManager::RunFrame (simulação + kick render)
    sceKernelReadTsc();   // resultado descartado (profiling stripped)
}
app->Shutdown();          // vtbl+0x90 -> LoadExec -reboot
```

---

## 2. Funções auxiliares pedidas

| Função | O que faz | Conf. |
|---|---|---|
| `FUN_014f2e80` (lock) | Spinlock por CAS em `param+0x14`; em contenção dorme 100 µs via `sceKernelAddHRTimerEvent(eq_TLS, {0,100000ns})` + `sceKernelWaitEqueue` (fallback `sceKernelUsleep(1)`). A equeue vem do TLS `fs:-0x28` ("ThreadSleep"). **Não tem nada a ver com vsync.** | [C] |
| `FUN_0188d550(list, newCap)` | Para cada ponteiro no array: zera, decrementa refcount (`-0x21523f22` = 0xDEADC0DE "morto"); se chegou a 0 destrói (vtbl+0x10) ou enfileira destruição diferida (`FUN_01cd54c0`). Depois realoca array para `newCap` via heap `DAT_069ac2c0[id]` (vtbl+0x20 alloc / +0x28 realloc). | [C] |
| `FUN_01cd5a40(budget_us)` | **Drena a fila de destruição diferida** (ring buffer `DAT_06920428`, 64K entradas, head `DAT_069a0428`, tail `DAT_069a042c`, spinlock `DAT_069a0430`) com TLS flag `fs:-0x48=1` (destrói imediatamente). Limita tempo com `sceKernelGetProcessTimeCounter` a `budget` µs (2000 = 2 ms por frame). Com budget 0 drena tudo e chama `FUN_01cd5720` + libera o array `DAT_069a0438`. Retorna itens restantes. | [C] |
| `FUN_01d71f80(final)` | Sob `objmgrMutex` (se final==0) e lock `DAT_069ac2b0`: varre `DAT_069ac2c0[0..DAT_069ae2c4]` (registro global de heaps/allocators, índice = heap id usado em todas as alocações) e libera entradas cujo refcount==1 (só o registro as segura) — "GC de heaps temporários". Com 1 é usado no shutdown. | [C] (nome [G]) |
| `FUN_01d4cc10(chan, fmt, ...)` | Logger variádico: `vsnprintf` em buffer de 4 KB → `PTR_PTR_02714920->vtbl+0x30` (sink de log). Ghidra errou a assinatura (args XMM). No Run é usado para logar tempo de boot. | [C] |
| `FUN_01dd4f10` | Cria/obtém singleton **`PS4TaskManager`** (`DAT_069f2b48`) via factory de tipos (`FUN_01d8d7f0`, ctor `FUN_01dd4d90`). App[10] = este objeto. | [C] |
| `FUN_01e4a040` (`TaskManager::RunFrame`, vtbl TM+0x58) | Atualiza listas de tasks por módulo, espera tasks em execução (spin-sleep 100 µs), e despacha tasks pendentes como jobs nomeados `"%sJob"` (nome do módulo de `PTR_DAT_02716230`) para o job system `DAT_069f2b40` (=o próprio TaskManager, vtbl+0x70 ou `FUN_01e4baf0`). Loop até esvaziar (vtbl+0x78/+0x80 = esperar/executar no main). | [C] |
| `FUN_01d0adf0` / `FUN_01d0afa0` | Cria uma Task (vtable `0x26e8a98`, ctor `FUN_01e47070(...,0xffff3020,0x19,0x3d4)` — ordem/prioridade baixa = roda no fim do frame) cujo `Run` (`FUN_01d0afa0`) pega o frame context atual (`app+0x58[app+0x88]`), chama **`FUN_01c551a0` (KickRender)** e **espera em spin (busy-wait sem sleep!) até `ctx+0x31ef8 >= 2`**. | [C] |
| `FUN_01c551a0` (KickRender) | Mailbox de 1 slot (`DAT_0689ef00`) protegido por `RenderDev:m_mutexRequest/m_condRequest` (`DAT_0691f070/80`): espera slot livre, publica ctx, `CondSignal`. | [C] |

---

## 3. Frame pacing

### 3.1 Threads de render
* **`ps4render`** — entry `FUN_01c53fe0`, criada em `FUN_01c4f9f0` (~0x1c51c7d): stack 0x80000 em endereço fixo `DAT_0689f070`, **prio 0x100 (a mais alta da faixa SCE)**, **affinity 1 (só core 0)**. Loop: espera ctx no mailbox → `FUN_01dfdea0`/`FUN_01e15db0` (se ctx+0x31efc) → `renderer->vtbl+0x10(ctx)` → `+0x18(ctx,0)` → **ctx state = 2** (libera main thread) → `+0x28(ctx)` (submit/Present) → `CondBroadcast(RenderDev:s_condWaitRender)`. Cada etapa cercada por `sceKernelReadTsc` (profiling). **[C]** (papéis exatos +0x10/+0x18/+0x28 **[G]**: "build scene", "build command buffers", "submit+present")
* **`ps4render_submitDone`** — entry `FUN_02494d40`, criada em `FUN_01c4f9f0` (~0x1c51b1c): stack 0x8000 em `DAT_06b037b0`, prio = `device+0x398`, **affinity 0xf**. Loop: espera contador de frames submetidos (`DAT_06b03790`) → `sceKernelWaitEqueue(eq, …, timeout=NULL)` (evento EOP da GPU) → espera flag `DAT_067d6b20` (spin) → **`sceGnmSubmitDone()`** → incrementa "frames completados" (`DAT_06b03798`) e `CondSignal`. **[C]**

### 3.2 Present (`FUN_01c4dfa0`, `JsSwapChain::Present`, ref. em vtable `0x26e6e98`)
1. Escreve packets de fim de frame (EOP label) no DCB.
2. **Bloqueia** em `scePthreadCondWait(DAT_06b03780)` enquanto `DAT_06b03798 == 0` (nenhum frame anterior completado pela GPU) → **limita frames em voo** (throttle CPU↔GPU). **[C]**
3. `sceGnmSubmitAndFlipCommandBuffers(n, dcb, dcbSz, ccb, ccbSz, videoHandle, bufferIdx, flipMode=1 (VSYNC), flipArg=0)` em 0x1c4eac0 (+ caminho de dispatch-draw/ACB via `FUN_0249f320`). `...ForWorkload` **não é usado** (0 callers). **[C]**
4. Incrementa `DAT_06b03790` e sinaliza a thread submitDone.
5. `FUN_02495480` (`JsSwapChain::BeginFrame`): avança índice de back-buffer (mod 3), imprime stats de memória Garlic/Onion/DCB/CCB, e **`sceGnmInsertWaitFlipDone(dcb, videoHandle, bufferIdx)`** (0x2495ee4) — a GPU espera o buffer sair da tela antes de renderizar nele. **[C]**

### 3.3 Video out
`FUN_01c4f9f0` (JsDevice::CreateDevice + JsSwapChain::Initialize/CreateBackBuffers): `sceVideoOutOpen(0xff,0,0,0)`, **`sceVideoOutSetFlipRate(h, 1)` → 30 Hz** (0x1c51…, linha "SetFlipRate(iVar8,1)"), `sceVideoOutRegisterBuffers(..., 3 buffers)` = triple buffering, `sceVideoOutConfigureOutputMode_`/`ModeSetAny_` (HDR). Lista de resoluções:
* Saída >1080p (4K, `sceVideoOutGetResolutionStatus` height>0x438) e sem `-force2k` (app+0x210): `1680x1890(cb)`, `1920x1080(scale)`, `3840x2160(native)`, `1920x2160(cb)`, `1840x2070(cb)`, `1760x1980(cb)`, `1600x1800(cb)`, `1520x1710(cb)`, `1600x2160(cb)` (cb = checkerboard). **[C]**
* Caso contrário: `1920x1080`, `1760x990`, `1600x900` (3 degraus — provavelmente resolução dinâmica **[G]**).

### 3.4 Delta time
* `DAT_069afc80` = `1/TscFrequency` (float) — `FUN_01dd4320` (+0xa0). **[C]**
* `UpdateTime` (`FUN_01dd45c0`): `dt_ticks = tsc - last`; `time = tsc*scale`, `dt = dt_ticks*scale`; se overlay do sistema (`sceSystemServiceGetStatus`) ativo, scale=0 → dt=0. **[C]**
* `SmoothDeltaTime` (`FUN_01d16480`), campos da App: 0x18c time, 0x190 dt bruto, 0x194 dt usado, 0x188 **dtMax = 0.05** (ctor), 0x1b0 game speed (1.0), 0x1b4/0x1b8 escalas (1.0), 0x1c0 pausa, 0x1a4 acumulador de erro [-1,1]:
  ```c
  if (smooth(0x1b8) > 0.5) dt = clamp(dt + dt*2*accum, 0.8*dt, 1.25*dt);
  dt = min(dt, 0.05) * speed;  if (paused) dt = 0;
  if (frameRateObj = app+0xb0) {               // [G] objeto "frame rate"
      v = app->dt19c;
      if (0.0317 < v && v < 0.035) v = 1/30.f;  // 0x3d01b4e8, 0x3d0f5c29 -> 0x3d088889  [C]
      filtro 2ª ordem (0.8333, 0.0245, 0.7347); v = round(v*360+0.1)/360;   [C]
  }
  ```
  → **o tempo de jogo é "quantizado" para 1/30 s** quando o frame real está perto de 33 ms. A 60/144 fps o snap não ocorre, mas o filtro/clamp foram tunados p/ 30 Hz. **[C]** (efeito sobre física/animação **[G]**)

### 3.5 Quem dita o ritmo do loop (conclusão)
Não há timer/sleep explícito no main loop. O ritmo vem de: (a) VSYNC a 30 Hz no flip; (b) `Present` bloqueando até a GPU terminar o frame anterior; (c) a Task de render (`FUN_01d0afa0`) que espera a thread `ps4render` chegar ao estado 2; (d) `sceGnmInsertWaitFlipDone` no lado GPU. Resultado: **1 frame de pipeline CPU-sim → CPU-render → GPU, travado a 30 fps**. **[C]** (montagem do conjunto)

`sceKernelWaitEqueue` tem >1000 callers: quase todos são o idioma de "sleep 100 µs" em spinlocks (inline). Só o de `FUN_02494d40` é espera de evento GPU. **[C]**

---

## 4. Threads

Wrappers de criação:
* `FUN_01dd4a90` = **`PS4TaskManager::CreateThread(stack, fn, arg, prio, name)`** (vtbl TM+0x68, `0x26ebd28`): detached, inheritsched=0, guard 4 KB, **sem affinity** (default do SO), entry wrapper `FUN_01e4cf20` (cria equeue TLS "ThreadSleep", chama fn, `scePthreadExit`). **[C]**
* `FUN_01dd4c50` = **`PS4TaskManager::CreateWorkerThread`** (vtbl TM+0x90, `0x26ebd50`), chamada 7× por `TaskManager::Init` (`FUN_01e48270`, vtbl TM+0x28, chamada de `FUN_01cf7a40` com 0x1000 jobs). **[C]**
* `FUN_01010580` = `hkThread::startThread` (Havok, `pthread_create_name_np`, POSIX). **[C]**
* `FUN_011e4340` = wrapper genérico do sndx (affinity `mask & 0x7f`, prio de config). **[C]**

| Thread (nome) | Entry | Criada em | Stack | Prio | Affinity | Papel | Conf. |
|---|---|---|---|---|---|---|---|
| main ("trico", eboot) | `0x1207bb0` | kernel | — | **0x226** (setado em `FUN_01e48270`) | **0xf** (cores 0–3) | simulação, TaskManager, input, GC | [C] |
| `workerThread0..3` | `FUN_01e4c420` | `FUN_01dd4c50` | 0x80000 | 0x228 | **0xf** | worker pool do TaskManager (jobs "%sJob"), dorme em sema | [C] |
| `workerThread4..6` | `FUN_01e4c420` | `FUN_01dd4c50` | 0x80000 | 0x228 | **0x70** (cores 4–6) | idem | [C] |
| `ps4render` | `FUN_01c53fe0` | `FUN_01c4f9f0` | 0x80000 (`DAT_0689f070`) | **0x100** | **0x1** (core 0) | render thread: build+submit+present | [C] |
| `ps4render_submitDone` | `FUN_02494d40` | `FUN_01c4f9f0` | 0x8000 (`DAT_06b037b0`) | device+0x398 | 0xf | espera EOP GPU, `sceGnmSubmitDone`, throttle | [C] |
| `HavokWorkerThread` ×4 | Havok (via `hkThread`, `FUN_01006d70`) | `FUN_01f835b0` (CreatePhysics) | — | 0x228 (`scePthreadSetprio` pós-criação) | threads 0–1: **0x7f**, 2–3: **0xf** | `hkCpuJobThreadPool` (numThreads=4), física | [C] |
| `TrophyThread` | `FUN_01d870c0` | `FUN_01cf7a40` via TM+0x68 | 0x20000 | 700 (0x2bc) | default | NpTrophy assíncrono | [C] |
| `PlayGoThread` | `FUN_01dd5500` | `FUN_01cf7a40` via TM+0x68 | 0x20000 | 700 | default | PlayGo (instalação em chunks) | [C] |
| `sndx_out_thread` | `FUN_011f28a0` | `FUN_011f1090` | cfg (0x10000) | cfg (0x100) | cfg "1111111" → **0x7f** | saída de áudio (`sceAudioOutOutput`) | [C] |
| `sndx_audio3d_out_thread` | `FUN_011b1050` | `FUN_011a69c0` | cfg (0x10000) | cfg (0x100) | 0x7f | saída Audio3D | [C] |
| `sndx_stream_schedule_thread` | `FUN_011e0fb0` | `FUN_011dff40` | cfg | cfg | 0x7f | streaming de áudio | [C] |
| `sndx_loader_thread` | `FUN_011f7d10` | `FUN_011f6840` | 0x8000 | 0x102 | 0x7f | loader de bancos de som | [C] |
| `sndx_file_queue_%d` (×maxFileQueues, default 1) | `FUN_011fd940` | `FUN_011fc3d0` | 0x8000 | 0x102 | 0x7f | fila de I/O de arquivos do áudio | [C] |
| `sceSndx-async-thread` | via `FUN_011e4340` (`FUN_011e4580`) | `FUN_011e3030` | cfg | cfg | 0x7f | update assíncrono do sndx | [C] (entry real [G]) |
| `sndx_capture_thread` | via `FUN_011e4340` | `FUN_011e32b0` | cfg | cfg | 0x7f | captura de áudio (mic) | [C] |
| (navmesh builder) | `FUN_019a9b30` | indireto (ref. em `FUN_01230810`) | — | 0x2d2 (self) | 0xf (self) | "buildTiledNavigation" (Recast) — se auto-configura ao iniciar | [G] |

Notas:
* Prioridades SCE: 256 (0x100) = mais alta … 767 = mais baixa. Render 0x100 > áudio 0x100/0x102 > main 0x226 > workers/Havok 0x228 > navmesh 0x2d2 > Trophy/PlayGo 700. **[C]**
* Não foram encontrados threads de Fios2 criadas pelo jogo (Fios cria as próprias internamente na lib). **[G]**
* Total aproximado de threads do jogo: ~1 main + 2 render + 7 workers + 4 Havok + ~8 áudio + 2 sistema = **~24**.

---

## 5. Implicações para o port PC

1. **30 fps hard-coded**: `sceVideoOutSetFlipRate(h,1)` + snap de dt em 1/30 + filtro tunado p/ 33 ms + dtMax 0.05 s. Para 60+ fps: trocar flip-rate por present com vsync/limitador, desabilitar o snap em `FUN_01d16480` (constantes `0x3d01b4e8/0x3d0f5c29/0x3d088889`) e validar física (Havok step) e animação; scripts Lua/HavokScript podem assumir 30 Hz (**[G]**, verificar).
2. **Affinity para 7 cores**: máscaras 0xf/0x70/0x7f/0x1 fixas (`FUN_01dd4c50`, `FUN_01f835b0`, `FUN_01c4f9f0`, `FUN_01e48270`, sndx "1111111"). No PC: ignorar `scePthreadAttrSetaffinity/SetAffinity` (ou mapear para todos os cores) e escalar o número de workers (7 fixo em `FUN_01e48270`; Havok numThreads=4 em `FUN_01f835b0`).
3. **Prioridades SCE** (0x100..0x2d2, 700) precisam de mapeamento para prioridades do SO (render/áudio "above normal", resto normal).
4. **Spin-sleep de 100 µs** via HRTimer+equeue por thread (TLS `fs:-0x28` = equeue "ThreadSleep", `fs:-0x48` = flag "destruição imediata", `fs:-0x40` = heap atual, `fs:-0x20` = worker index): emular com `SleepEx`/`nanosleep` ou `_mm_pause`+yield; TLS layout precisa ser preservado se rodar código original (HLE).
5. **Busy-wait sem yield** em `FUN_01d0afa0` (espera ctx state ≥2) e em `FUN_02494d40` (`while(!DAT_067d6b20)`) — inofensivo no PS4 com cores dedicados, mas pode travar/derrubar performance no PC se a thread render estiver no mesmo core (render fixo no core 0 + main em 0–3!).
6. **`sceGnmSubmitDone`** obrigatório no PS4 (thread dedicada) — no PC desaparece; o throttle de frames em voo (`DAT_06b03798`) deve ser reimplementado com fences.
7. **PS4 Pro**: `sceKernelIsNeoMode` em `FUN_01dd39d0` (Garlic 3.25 GB vs 2.75 GB), em `0x1207cc0` e em ~15 funções gnmx/render (`0x246ba90`…`0x24a79e0`, não analisadas). Modos checkerboard 4K dependem de saída >1080p. Para PC: forçar caminho "2k" (`-force2k`, app+0x210) ou Neo conforme o renderer recriado.
8. **Shutdown = relançar**: `App::Shutdown` (`FUN_01dd3f50`) chama `sceSystemServiceLoadExec(... "-reboot")` em loop infinito — no PC deve ser trocado por reinício do processo/estado ou saída limpa.
9. **Pausa por overlay do sistema** (`sceSystemServiceGetStatus` em `FUN_01dd45c0`) → mapear para perda de foco da janela.

---

## 6. Endereços-chave (cola rápida)

```
main                      0x1207bb0     App::Run             0x1d169b0
App vtable                0x26ebbe0     App base vtable      0x26e89b8
PS4TaskManager vtable     0x26ebcc0     TaskManager singleton DAT_069f2b48 / jobsys DAT_069f2b40
App::Frame (+0x80)        0x1dd37e0  -> TaskManager::RunFrame 0x1e4a040
App::Init (+0x88)         0x1dd39d0     App::Shutdown(+0x90)  0x1dd3f50
App::PreInit (+0xa0)      0x1dd4320     UpdateInput (+0xb8)   0x1d16380
UpdateTime (+0xc0)        0x1dd45c0     SmoothDeltaTime(+0xc8)0x1d16480
TaskManager::Init         0x1e48270     CreateThread 0x1dd4a90  CreateWorker 0x1dd4c50
worker entry              0x1e4c420     thread wrapper        0x1e4cf20
RenderKick task Run       0x1d0afa0     KickRender mailbox    0x1c551a0 (DAT_0689ef00)
ps4render entry           0x1c53fe0     submitDone entry      0x2494d40
JsDevice/SwapChain init   0x1c4f9f0     Present               0x1c4dfa0   BeginFrame 0x2495480
Havok init (CreatePhysics)0x1f835b0     hkThread start        0x1010580
GC deferred delete        0x1cd5a40     heap sweep            0x1d71f80
spinlock                  0x14f2e80     ptr-array release     0x188d550   logger 0x1d4cc10
DAT_069afc80 = 1/TSC freq  DAT_069a1b40 = App*  DAT_069a1608 = frame ctx atual  DAT_069b1678 = idx mod 3
```
