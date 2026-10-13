# 02 - Rendering / GPU (Gnm, Gnmx, camada Js*) - The Last Guardian v1.03 (CUSA03627)

Binario: `dump/patch0/eboot.bin` (v1.03). Todos os enderecos estao no espaco do Ghidra (base 0x1000000; vaddr do arquivo + 0x1000000).

Legenda de confianca:
- **[C]** confirmado: string de assert com nome da funcao/arquivo, chamada direta a import, ou decompilacao inequivoca.
- **[P]** provavel: deduzido por estrutura/contexto (vtable, padrao de argumentos), mas sem string com nome.
- **[?]** palpite.

Metodo: alem das ferramentas REA/Ghidra, foi feito um scan proprio do segmento de codigo (`E8/E9 rel32` contra os stubs PLT `0x24bdxxx`, e `disp32` RIP-relativos contra strings), com limites de funcao tirados da tabela `.eh_frame_hdr` (0x2686ee0). Scripts em `/tmp/claude-1000/.../scratchpad/{scan,callers,sx,fstr}.py`. Chamadas indiretas (vtables) aparecem separadamente.

---

## 1. Arquitetura geral

```
render\dev\*  (RendererDev: deferred renderer, SSAO, SMAA, Bloom, TileCull, LightBuffer, compute passes)
      |  usa API estilo D3D11 (DXGI formats, JS_BIND_*, JS_USAGE_IMMUTABLE, vs_5_0/ps_5_0/cs_5_0,
      |  "%s:%u DirectX call failed, hr=%08x")
      v
render\ps4\Js*  (JsDevice / JsDeviceContext / JsComputeContext / JsSwapChain ... = shim D3D11 -> Gnm)
      |  JsDeviceContextInline.h e inlinado nos chamadores (OMSetRenderTargets, *SetShaderResources...)
      v
Gnmx estatico (external\ps4\src\gnmx\: gfxcontext, basegfxcontext, cue*, lwcue_*, computecontext,
      computequeue, surfacetool, fetchshaderhelper) - headers "ORBIS SDKs\4.000"
      |  escreve PM4 no DCB/ACB (direto ou via packet-builders do libSceGnmDriver)
      v
libSceGnmDriver (HLE necessario): sceGnmSubmitAndFlipCommandBuffers, sceGnmDingDong, sceGnmSubmitDone ...
libSceVideoOut: Open / RegisterBuffers / SetFlipRate / ConfigureOutputMode_ ...
```

Observacao importante: o renderer de alto nivel (`render\dev`) e claramente escrito contra D3D11 (mensagem "DirectX call failed, hr=%08x", nomes `CreateShaderResourceViewDesc`, `OMSetRenderTargets`, formatos DXGI 0x1c/0x1d/0x57/0x5b, perfis `vs_5_0`/`ps_5_0`/`cs_5_0` nos nomes dos .sb). A camada `render\ps4\Js*` e um **shim D3D11 para Gnm** feito pela genDESIGN/SIE. Isso e muito relevante para a opcao (b) do port.

Threads de render (criadas em `CreateDevice` 0x1c4f9f0) **[C]**:
- `"ps4render"` -> `FUN_01c53fe0` (worker do RendererDev; mutex/cond `RenderDev:m_mutexRequest`, `RenderDev:s_condWaitRender`), afinidade 0x1, stack 0x80000.
- `"ps4render_submitDone"` -> `FUN_02494d40` (espera EOP e chama `sceGnmSubmitDone`), afinidade 0xf.

---

## 2. Tabela de funcoes-chave

### 2.1 Device / criacao de recursos

| Endereco | Nome (guess) | Conf. | Evidencia |
|---|---|---|---|
| 0x1c4f9f0 | `RendererDev::Create` -> `JsDevice::CreateDevice` + `JsDevice::Initialize` + `JsSwapChain::Initialize/CreateBackBuffers` (tudo inlinado) | C | asserts `CreateDevice`, `Initialize`, `CreateBackBuffers`, `launch` em JsDevice.cpp/JsSwapChain.cpp; ponteiro na tabela de fabrica 0x26e6f68 ao lado da string "CreateRenderer" (0x2595aa9) |
| 0x1c51cc0 | construtor do objeto RendererDev (0x18a80 bytes) | P | chamado logo apos `operator_new(0x18a80)` em 0x1c4f9f0 |
| 0x248f4a0 | `JsGraphics` heap `Initialize` ("Garlic"/"Onion") | C | JsGraphics.cpp + strings "Garlic"/"Onion" |
| 0x2475f90 | `JsDevice::AllocateGarlicMemory` | C | assert `AllocateGarlicMemory` |
| 0x2476730 | `JsDevice::AllocateOnionMemory` | C | assert `AllocateOnionMemory` |
| 0x24756d0 | `JsDevice::~JsDevice` / `Destory` | C | `~JsDevice`, `~JsUnknown` |
| 0x246ddd0 | `JsDevice::CreateBuffer` (JsBuffer::Initialize) | C | `CreateBuffer`, JsBuffer.cpp; 149 call sites |
| 0x2477370 | `JsDevice::CreateTexture2D` | P | chama 0x2496f60; usado em CreateBackBuffers |
| 0x2496f60 | `JsTexture2D::Initialize` / `CreateGnmTexture` | C | JsTexture2D.cpp, `CreateGnmTexture`, `setHtileAddress` |
| 0x2477740 | `CreateTexture1D` | C | "JsGraphics :CreateTexture1D: invalid args" |
| 0x2476850 | `CreateTexture3D` | C | "JsGraphics :CreateTexture3D: ..." |
| 0x1c96930 | `JsCreateTextureFromMemory` | C | string JsTex.cpp/`JsCreateTextureFromMemory` |
| 0x1c982e0 | `JsCreateTextureFromFile` | C | idem |
| 0x2491370 | `CreateRenderTargetView` | C | `CreateRenderTargetViewDesc`, `JS_BIND_RENDER_TARGET` |
| 0x2491a30 | setup de `Gnm::RenderTarget` (cmask, tile mode; checa NeoMode) | C | rendertarget.h asserts |
| 0x2492370 | setup de `Gnm::DepthRenderTarget` (htile; checa NeoMode) | C | depthrendertarget.h asserts |
| 0x2474fb0 | `CreateDepthStencilView` | C | `CreateDepthStencilViewDesc` |
| 0x2493620 | `CreateShaderResourceView` | C | `CreateShaderResourceView`, `JS_BIND_SHADER_RESOURCE` |
| 0x24999e0 | `CreateUnorderedAccessView` | C | `CreateUnorderedAccessViewDesc` |
| 0x246d7f0 | `CreateBlendState` | P | unica funcao que referencia JsBlendState.cpp |
| 0x2490e70 | `CreateRasterizerState` | C | assert |
| 0x2474e00 | `CreateDepthStencilState` | P | referencia JsDepthStencilState.cpp, padrao `hr == S_OK` |
| 0x2492e40 | `CreateSamplerState` | C | assert |
| 0x249b400 | `JsDevice::CreateVertexShader` (despacha p/ VsVs/VsEs/VsLs/VsDd) | C | chama 0x249a7b0/0x249aa40/0x249acc0/0x249af40; chamado pelos loaders de .sb `vs_5_0` |
| 0x249a7b0 / 0x249aa40 / 0x249acc0 / 0x249af40 | `CreateVsVs` / `CreateVsEs` / `CreateVsLs` / `CreateVsDd` (dispatch-draw CsVs) | C | asserts com esses nomes |
| 0x2490440 | `JsDevice::CreatePixelShader` | C | `CreatePixelShader`, "PsShader gpu address has already been patched." |
| 0x2473890 | `JsDevice::CreateComputeShader` (gera tabela LCUE `generateInputResourceOffsetTable`) | C | lwcue_base.cpp asserts; chamado pelos loaders `cs_5_0` e `system/` |
| 0x2488580 | `JsDeviceContext::PrepareDraw` (+ `CreateFetchShader`, input layout, `setVertexBuffers`, Es/Gs/Ls/Hs) | C | asserts `PrepareDraw`, `CreateFetchShader` |
| 0x24944c0 | criacao da EOP queue (`sceKernelCreateEqueue` + `sceGnmAddEqEvent`, "EOP QUEUE", `submitWait:*`) | C | strings |

### 2.2 JsDeviceContext (fila grafica, DCB em +0x47c0, CUE em +0x4aa8)

vtable do JsDeviceContext a partir de ~0x26fe138 (sem RTTI). Os metodos de *set* de estado vem de `JsDeviceContextInline.h` e sao **inlinados** no codigo de `render\dev` (ex.: 11 copias de `OMSetRenderTargets` dentro de 0x1c593d0); so o "flush" de estado (`PrepareDraw`/`PrepareDispatch`) e os draws sao funcoes reais.

| Endereco | Nome (guess) | Conf. | Evidencia |
|---|---|---|---|
| 0x2481830 | `JsDeviceContext::init` (DCB/CCB, `initializeRingBuffer` do CUE, GDS) | C | `JsDeviceContext`, `initializeRingBuffer`, cue.cpp |
| 0x24826c0 | reset de frame / `initDefaultHardwareState` (`sceGnmDrawInitDefaultHardwareState350`, `sceGnmDispatchInitDefaultHardwareState`, tess-factor ring) | C | imports + `allocateTessellationFactorRingBuffer` |
| 0x2478df0 | `XXSetConstantBuffers` (vtable) | C | assert `SetConstantBuffers` (Inline.h) |
| 0x2479070 | `XXSetSamplers` | C | assert `SetSamplers` |
| 0x24792b0 | `XXSetShaderResources` | C | assert `SetShaderResources` |
| 0x2479540 | `CSSetUnorderedAccessViews` | C | assert |
| 0x2479b70 | `PrepareDispatch` | C | assert |
| 0x2479810 | `JsDeviceContext::Dispatch` (vtable 0x26fe188) | P | `sceGnmDispatchDirect` na DCB, chama PrepareDispatch |
| 0x247e340 | `Dispatch` variante (vtable 0x26fe190; ex. com contador/flag) | P | idem |
| 0x2479db0 / 0x247c680 | aplicacao de estado grafico (viewports, topology, `sceGnmSetPsShader350`, `eliminateFastClear`) | C | asserts `RSSetViewports`, `IASetPrimitiveTopology`, surfacetool.cpp |
| 0x2488220 | `JsDeviceContext::Draw` (`sceGnmDrawIndexAuto`) | C | assert com nome "Draw" (0x25aa26e); 48 call sites |
| 0x1c71680 | `DrawInstanced` (`sceGnmDrawIndexAuto`) | C | assert `DrawInstanced` |
| 0x248e080 | `DrawIndexed` (`DrawIndexedCommon`, `sceGnmDrawIndexOffset`) | C | assert |
| 0x248e1d0 | `DrawIndexedInstanced` (`sceGnmDrawIndexOffset`) | C | assert |
| 0x248e340 | `DrawIndexedInstancedIndirect` (`sceGnmDrawIndexIndirect`) | C | assert |
| 0x248dec0 | `DispatchIndirect` (`sceGnmDispatchIndirect`) | P | unico caller = Render 0x1c593d0 |
| 0x2483380 | `ClearRenderTargetView` (`CalcClearColor`, `ClearCmaskSurface`) | C | asserts |
| 0x24860c0 | `ClearDepthStencilView` | C | asserts |
| 0x24879c0 | clear via quad com `g_pClearPs` | C | "JsDevice::GetNativeShader( g_pClearPs )" |
| 0x2487ce0 / 0x2487e40 | `ClearHtileSurface` | C | assert |
| 0x24a79e0 | Gnmx `SurfaceTool::renderFullScreenQuad` (`sceGnmSetEmbeddedVsShader` + `sceGnmDrawIndexAuto`) | C | surfacetool.cpp |
| 0x247e860 -> 0x247eb00 | `CopyResource` (implementado com compute `sceGnmDispatchDirect`) | C | strings "JsDeviceContext::CopyResource Error..." |
| 0x248e800 | `ExCsDepthCopy` (copia de depth via CS) | C | string |
| 0x247f990 | `JsDeviceContext::Map` (discard/rename de buffers) | C | "ERROR: JsDeviceContext::Map failed!" |
| 0x2480f90 | `UpdateSubresource` | C | assert |
| 0x24727e0 / 0x2481720, 0x2472860 / 0x24817b0 | `PushMarker` / `PopMarker` (compute / grafico) | C | `sceGnmInsertPushMarker`/`PopMarker` |
| 0x247b920 / 0x249ec50 | Gnmx `endDispatchDraw` / `beginDispatchDraw` (`sceGnmSetVgtControl`) | C | basegfxcontext.cpp |

### 2.3 Gnmx CUE / LCUE (shader binding)

| Endereco | Nome | Conf. | Evidencia |
|---|---|---|---|
| 0x24a0c30 | `ConstantUpdateEngine::setVsShader` (`sceGnmSetVsShader`/`sceGnmUpdateVsShader`) | C | cue-shader.cpp |
| 0x24a0fd0 | `CUE::setPsShader` (`sceGnmSetPsShader350`/`UpdatePsShader350`) | C | idem |
| 0x24a1370 | `CUE::setCsShader` (`sceGnmSetCsShaderWithModifier`) | C | idem |
| 0x24a1890 | `CUE::setCsVsShaders` (dispatch draw) | C | idem |
| 0x24a15b0 | `CUE::setOnChipEsShader` (`sceGnmSetEsShader`) | C | idem |
| 0x24a57b0 | `CUE::setLsShader`/`setHsShader` (tesselacao) | C | idem |
| 0x2488580 (inline) | `setGsShader`/`updateGsShader` | C | imports dentro de PrepareDraw |
| 0x24a4ab0 | `CUE::preDraw` | C | cue.cpp |
| 0x24a6590 | `LCUE ComputeContext::preDispatch` (`sceGnmSetCsShaderWithModifier`) | C | lwcue_compute.cpp |
| 0x2473340 | LCUE `ComputeContext::setCsShader/setBuffers/...` + dispatch | C | lwcue_compute.cpp, computecontext.h |

### 2.4 JsComputeContext (async compute, LCUE)

vtable 0x26fdee0... (sem RTTI).

| Endereco | Nome | Conf. | Evidencia |
|---|---|---|---|
| 0x24728d0 | `JsComputeContext::JsComputeContext(pipe, queue, prio)` -> `sceGnmMapComputeQueueWithPriority` (ring 0x400 DW) | C | strings `JsComputeContext`, `AllocateGdsMemory` |
| 0x246e8e0 | reset (`sceGnmDispatchInitDefaultHardwareState`) | C | import |
| 0x246eb90 / 0x246ed90 / 0x246efa0 / 0x246f2c0 | `CSSetConstantBuffers` / `CSSetSamplers` / `CSSetShaderResources` / `CSSetUnorderedAccessViews` | C | asserts |
| 0x246f8e0 | `PrepareDispatch` (LCUE `setBuffers/setRwTextures/...`) | C | assert |
| 0x246f5f0 / 0x24711c0 | `Dispatch` (vtable 0x26fdf30 / 0x26fdf38) | P | `sceGnmDispatchDirect` no ACB |
| 0x24717c0 | `AsyncCopyResource` | C | assert |
| 0x24721a0 | `UpdateSubresource` | C | assert |
| 0x2472640 / 0x2472700 | `BeginOcclusion` / `EndOcclusion` | C | assert |
| 0x2472ed0 | `JsComputeContext::Submit` -> `ComputeQueue::submit` | C | assert `state == sce::Gnmx::ComputeQueue::kSubmitOK`, `Submit` |
| 0x2473180 | `StallUntilSignaled` | C | assert |
| 0x2473600 | `AsyncMap` (readback CPU de resultados da GPU) | C | assert |
| 0x249f320 | Gnmx `ComputeQueue::submit` -> **`sceGnmDingDong`** | C | computequeue.cpp, `prepareBuffersForSubmit` |
| 0x249e740 / 0x249e7e0 | `ComputeQueue::unmap` (`sceGnmUnmapComputeQueue`) | C | import |

### 2.5 Swap chain / apresentacao

| Endereco | Nome | Conf. | Evidencia |
|---|---|---|---|
| 0x1c4dfa0 | `JsSwapChain::Present` (+ Gnmx `GfxContext::internalSubmitAndFlip` inlinado) - **unico ponto de submit da fila grafica** | C | assert `Present` JsSwapChain.cpp:0x158 e `internalSubmitAndFlip` gfxcontext.cpp; slot 6 da vtable RendererDev (0x26e6e98) |
| 0x2495480 | `JsSwapChain::BeginFrame` (`sceGnmInsertWaitFlipDone`, deleção diferida de objetos, stats "Peak DCB/ACB", `sceVideoOutUnregisterBuffers`) | C | assert `BeginFrame` |
| 0x1c4df90 -> 0x1c55690 | `RendererDev::Render` (slot 5 da vtable, thunk) contendo `JsSwapChain::ResizeBuffers` (troca HDR em runtime) | C/P | assert `ResizeBuffers`; 0x1c4df90 so faz jump |
| 0x1c593d0 | corpo principal do frame (deferred: "Albedo", "Normal", "Roughness", "SpecAlbedo", "VelocityMap", "Depth", "ShadowCascade#%d", "ShadowSpot#%d", "SSAO", "Bloom", "LightVolume", "FakeSun") ~11.6k linhas de pseudo-C | C | strings; chamado so por 0x1c55690 |
| 0x2494d40 | thread `ps4render_submitDone`: `sceKernelWaitEqueue` (EOP) -> `sceGnmSubmitDone` | C | imports |
| 0x1c53e20 | `CreateBlob(path)` - le arquivo inteiro via FS do app (DAT_069a1b40+0x28), blob {+0x30 data, +0x38 size} | C | "CreateBlob: Error. Cannot open file %s." |

vtable RendererDev em 0x26e6e68 (slots): [0]0x1c460e0 [1]0x1c490c0 [2]0x1c490e0 [3]0x1c49540 (trabalho de compute pre-frame, usa JsComputeContext) [4]0x1c4c570 [5]0x1c4df90 (Render) [6]0x1c4dfa0 (Present) [7]0x1c4efa0 [8]0x1c80170 [9]0x1c4efb0 [10]0x1c71670 [11]0x1c49020 [12]0x1c4f340 [13]0x1c4f730 [14]0x1c4f7b0. Nomes de slots diferentes de 5/6 sao **[?]**.

---

## 3. Mapa dos imports libSceGnmDriver / libSceVideoOut realmente usados

Scan de chamadas diretas (`call`/`jmp` para o stub PLT). Formato: import (n call sites) -> funcao(oes).

| Import | # | Caller(s) |
|---|---|---|
| sceGnmSubmitAndFlipCommandBuffers | 1 | 0x1c4dfa0 `JsSwapChain::Present` |
| sceGnmSubmitDone | 1 | 0x2494d40 thread submitDone |
| sceGnmDingDong | 1 | 0x249f320 `ComputeQueue::submit` |
| sceGnmMapComputeQueue | 1 | 0x1c4f9f0 (JsComputeQueue de dispatch-draw: pipe 0, queue 3, ring 1 MiB) |
| sceGnmMapComputeQueueWithPriority | 1 | 0x24728d0 `JsComputeContext` ctor |
| sceGnmUnmapComputeQueue | 2 | 0x249e740, 0x249e7e0 |
| sceGnmRegisterOwner | 1 | 0x1c4f9f0 ("JsDevice") |
| sceGnmAddEqEvent | 1 | 0x24944c0 |
| sceGnmInsertWaitFlipDone | 1 | 0x2495480 `BeginFrame` |
| sceGnmInsertPushMarker / PopMarker | 2/2 | 0x24727e0, 0x2481720 / 0x2472860, 0x24817b0 |
| sceGnmDrawInitDefaultHardwareState350 | 1 | 0x24826c0 |
| sceGnmDispatchInitDefaultHardwareState | 2 | 0x246e8e0, 0x24826c0 |
| sceGnmGetTheTessellationFactorRingBufferBaseAddress | 3 | 0x24826c0 |
| sceGnmDrawIndexAuto | 3 | 0x1c71680 DrawInstanced, 0x2488220 Draw, 0x24a79e0 renderFullScreenQuad |
| sceGnmDrawIndexOffset | 2 | 0x248e080 DrawIndexed, 0x248e1d0 DrawIndexedInstanced |
| sceGnmDrawIndexIndirect | 1 | 0x248e340 DrawIndexedInstancedIndirect |
| sceGnmDispatchDirect | 15 | 0x246f5f0, 0x24711c0 (JsComputeContext); 0x2479810, 0x247e340 (JsDeviceContext); 0x2473340 (LCUE); 0x247eb00 CopyResource; 0x247f990 Map; 0x2480b70; 0x2485c00 (clears via CS); 0x248e800 ExCsDepthCopy |
| sceGnmDispatchIndirect | 1 | 0x248dec0 |
| sceGnmSetVsShader / UpdateVsShader | 1/1 | 0x24a0c30 |
| sceGnmSetPsShader350 | 5 | 0x24a0fd0, 0x2479db0, 0x247c680 |
| sceGnmUpdatePsShader350 | 2 | 0x24a0fd0 |
| sceGnmSetCsShaderWithModifier | 3 | 0x24a1370, 0x24a1890, 0x24a6590 |
| sceGnmSetEsShader | 1 | 0x24a15b0 |
| sceGnmSetGsShader / UpdateGsShader | 1/1 | 0x2488580 |
| sceGnmSetLsShader / SetHsShader / UpdateHsShader | 1/1/1 | 0x24a57b0 |
| sceGnmSetEmbeddedVsShader | 1 | 0x24a79e0 |
| sceGnmSetVgtControl | 2 | 0x247b920, 0x249ec50 |
| sceVideoOutOpen | 3 | 0x1c4f9f0 (handle global DAT_067d6b24, `Open(0xff,0,0,0)`) |
| sceVideoOutGetResolutionStatus | 1 | 0x1c4f9f0 |
| sceVideoOutGetDeviceCapabilityInfo_ | 1 | 0x1c4f9f0 (bit 7 = HDR) |
| sceVideoOutSetFlipRate | 1 | 0x1c4f9f0 (`SetFlipRate(h, 1)` = 30 Hz) |
| sceVideoOutSetBufferAttribute | 2 | 0x1c4f9f0, 0x1c55690 |
| sceVideoOutRegisterBuffers | 1 | 0x1c4f9f0 (3 buffers) |
| sceVideoOutModeSetAny_ / ConfigureOutputMode_ | 2/2 | 0x1c4f9f0, 0x1c55690 |
| sceVideoOutSubmitChangeBufferAttribute | 1 | 0x1c55690 (troca SDR<->HDR) |
| sceVideoOutUnregisterBuffers | 1 | 0x2495480 |
| sceKernelIsNeoMode | 51 | 0x246ba90 (wrapper cacheado), 0x1207cc0 (heap malloc), 0x1dd39d0 (init app/memoria), 0x2481330 (CU mask 0x7fffc00 Neo vs 0x7fc00 base), 0x2491a30/0x2492370/0x2496f60/0x2476850/0x2477740 (tile modes de textura/RT), 0x2488580, 0x249ec50, 0x24a4ab0, 0x24a79e0 ... |

**Importados mas sem call site direto encontrado** (provavelmente so ligados pela stub lib ou usados apenas em builds debug): `sceGnmSubmitCommandBuffers`, `sceGnmSubmitCommandBuffersForWorkload`, `sceGnmSubmitAndFlipCommandBuffersForWorkload`, `sceGnmRequestFlipAndSubmitDone*`, `sceGnmDispatchIndirectOnMec`, `sceGnmDrawIndex`, `sceGnmDrawIndexMultiInstanced`, `sceGnmDraw*Multi*`, `sceGnmDrawOpaqueAuto`, `sceGnmDrawInitToDefaultContextState400`, `sceGnmDingDongForWorkload`, `*Workload*`, `sceGnmRegisterResource`/`Unregister*`, todos `sceGnmValidate*`, `sceRazor*`, `sceGnmGetResource*`, `sceGnmFlushGarlic`, `sceGnmSetEmbeddedPsShader`, `sceGnmSetGsRingSizes`, `sceGnmSetWaveLimitMultipliers`, `*MipStats*`, markers de cor, etc. (o scan nao cobre chamadas via ponteiro de funcao; um HLE deve implementa-los como stubs de qualquer forma.)

### Como o command buffer e construido e submetido
1. Cada frame em voo tem um `JsDeviceContext` proprio (3 instancias de 0x130f0 bytes em `swapchain+0x40..0x50`) e um `JsComputeContext` proprio (3 instancias de 0x2320 bytes em `swapchain+0x78..0x88`, pipe 2 queues 0/1/2). Indice do frame em `swapchain+0x38`.
2. O `JsDeviceContext` embute um Gnmx `GfxContext`: DCB em +0x47c0 (ptr inicio/fim/cursor em +0x47c0/+0x47c8/+0x47d0, callback "buffer cheio" em +0x47d8) e o `ConstantUpdateEngine` (CUE, CCB) em +0x4aa8. Os setters inline gravam estado no contexto; `PrepareDraw` (0x2488580) / `PrepareDispatch` (0x2479b70) materializam o estado via CUE (`setVsShader`, `setPsShader`, user-data SGPRs, fetch shader, etc.).
3. Os pacotes PM4 sao gerados de duas formas: (a) pelas funcoes "packet builder" do `libSceGnmDriver` que recebem o ponteiro do cursor do DCB (`sceGnmDrawIndexAuto(cursor, n, ...)`, `sceGnmDispatchDirect(cursor, 9, x, y, z, flags)`, `sceGnmSet*Shader`), e (b) escrita direta inline (ex.: em Present `0xC0001000` NOP de alinhamento e `0xC0044700` = `EVENT_WRITE_EOP`, label/flip; em Dispatch `0xC0008500`).
4. `Present` (0x1c4dfa0): submete primeiro o ACB do `JsComputeContext` do frame (`FUN_02472ed0` -> `ComputeQueue::submit` -> `sceGnmDingDong`), depois escreve o EOP e chama **uma unica vez por frame** `sceGnmSubmitAndFlipCommandBuffers(count, dcb[], dcbSize[], ccb[], ccbSize[], videoOutHandle=swapchain+0x520, bufferIndex, flipMode=1 (VSYNC), flipArg=0)`. Em seguida sinaliza a thread submitDone (cond var DAT_06b03770) e chama `BeginFrame` (0x2495480) para o proximo frame (que injeta `sceGnmInsertWaitFlipDone`).
5. A thread `ps4render_submitDone` (0x2494d40) espera o evento EOP (`sceKernelWaitEqueue`) e chama `sceGnmSubmitDone`.

---

## 4. Shaders

- Formato: PSSL compilado (`.sb`, contem o footer `ShaderBinaryInfo` com assinatura "OrbShdr"). Os nomes indicam origem HLSL SM5: `ps4_shader_cache/%s_%s_%s_%08x.sb` com perfil `vs_5_0` / `ps_5_0` / `cs_5_0` e um hash de permutacao.
- Carregamento: `CreateBlob` (0x1c53e20, ponteiro de funcao guardado em `DAT_06b03738` e em `desc+0x388`) le o arquivo inteiro do psarc em memoria; o blob e passado para `CreateVertexShader` (0x249b400) / `CreatePixelShader` (0x2490440) / `CreateComputeShader` (0x2473890), que copiam o codigo para memoria Garlic, fazem `patchShaderGpuAddress` e geram as tabelas de input (CUE `InputResourceOffsets` / LCUE `generateInputResourceOffsetTable`). O binding real acontece no draw: CUE `setVsShader/setPsShader/setCsShader` -> `sceGnmSet*Shader` (PM4 SET_SH_REG).
- Loaders por categoria **[C]**:
  - 0x1c861a0: material - `data_trico/ps4_shader_cache/material/%s_%s_%08x_m%08x_%08x_ex%08x.sb` (VS+PS)
  - 0x1c82cf0: particulas - `.../particle/vs_%s_%08x.sb` / `ps_%s_%08x.sb` (CustomParticles, RippleParticles, CustomPolygonParticles, CustomPolyLineParticles)
  - 0x1c8e9d0 (vs_5_0), 0x1c8efc0 (ps_5_0), 0x1c8f500 (cs_5_0): `data_trico/ps4_shader_cache/%s_%s_%s_%08x.sb` ("file not found %s")
  - 0x1c8fa50 (CS) / 0x1c8fbc0 (VS/PS/CS): `data_trico/ps4_shader_cache/system/%s_%s_%s_%08x.sb`
  - 0x1c793f0 `RendererDev_Setup` (chamado no fim de CreateDevice) cria os shaders/estados de Skinning, RayCastCompute, AabbCompute, TrackingCompute, AmbientLighting.
- **Blobs OrbShdr embutidos**: 49 shaders estaticos no .rodata (0x24e4a30..0x24ea2xx; assinatura "OrbShdr" em 0x24e4ae4...0x24ea174, mais uma em 0x24ea894 e uma constante de comparacao em codigo 0x2473cd3 = 51 ocorrencias). Sao criados em `CreateDevice` 0x1c4f9f0 linhas ~577-673: 1 VS (`PTR 0x2706cc0`, 0x1ac bytes -> `DAT_06b033d0`), 1 PS (`0x2706bb8`, 0x16c -> `DAT_06b033d8`, provavelmente o `g_pClearPs`) e 47 CS via `CreateComputeShader` (tamanhos 0x148-0x2b8 em grupos de 4 -> globais `DAT_06b033e0..0x6b03550`). Uso **[P]**: shaders internos do shim Js* - clear por compute (`0x2485c00`), `CopyResource`/`ExCsDepthCopy` por compute com variantes por formato/dimensao (`MakeTypeless`), clear de RT/HTILE e quad de tela cheia. Nao fazem parte do conteudo do jogo, mas sao necessarios para o shim funcionar.
- `sceGnmSetEmbeddedVsShader` (driver-embedded fullscreen VS) e usado por `renderFullScreenQuad` (0x24a79e0).

---

## 5. Resolucao, saida, Pro, HDR, flip rate

Tudo em 0x1c4f9f0 **[C]** (tabela de modos em `DAT_069b1820`, 0x18 bytes por entrada: `u16 renderW, renderH, outW, outH; u64 checkerboard; char* nome`):

- Se `sceVideoOutGetResolutionStatus` reporta altura > 1080 (TV 4K, so possivel no PS4 Pro) **e** `App+0x210 == 0`:
  - indice 0 (default): **"1680x1890(cb)"** -> render 1680x1890 checkerboard, swapchain **3360x1890** (o famoso "1890p CB" do Pro)
  - depois: "1920x1080(scale)" (1920x1080 -> 3840x2160), "3840x2160(native)", "1920x2160(cb)", "1840x2070(cb)", "1760x1980(cb)", "1600x1800(cb)", "1520x1710(cb)", "1600x2160(cb)" (lista de debug/selecao).
- Caso contrario (base PS4, Pro em TV 1080p, ou `-force2k`): "1920x1080" (default), "1760x990", "1600x900" -> saida 1920x1080.
- **`-force2k`**: parseado em `App::Run` (0x1d169b0, xref 0x1d17f21) -> `*(int*)(App+0x210) = 1` -> desliga a lista 4K/checkerboard **[C]** (que App == DAT_069a1b40 e **[P]**).
- A decisao de 4K nao chama `sceKernelIsNeoMode` diretamente; `IsNeoMode` (wrapper 0x246ba90) afeta tile modes, CU masks (0x2481330), heap de memoria (0x1207cc0: 0x69800000 direct + 0x11800000 flexible) etc.
- Shader de resolve checkerboard: string `checkerboard_resolve_c` (0x259083e).
- **HDR**: `sceVideoOutGetDeviceCapabilityInfo_` bit 7 -> flags `RendererDev+0x18a50..52`. Sem HDR: back buffer DXGI 0x1c (R8G8B8A8_UNORM) -> VideoOut `0x80002200` (A8B8G8R8_SRGB). Com HDR: formato interno 0x65 (10-bit) -> VideoOut `0x88740000` (A2R10G10B10_BT2020_PQ) ou `0x88000000` (A2R10G10B10_SRGB) conforme opcao; troca em runtime em `ResizeBuffers` (0x1c55690) via `sceVideoOutSetBufferAttribute` + `SubmitChangeBufferAttribute` + `ModeSetAny_`/`ConfigureOutputMode_` (colorimetria 0xc quando HDR). Strings `PS_ConvertHdr`, `HDR_ENABLE`, `OptionMenu_ITEM_SCREEN_HDR_ENABLE`.
- **Flip rate**: `sceVideoOutSetFlipRate(handle, 1)` = **30 Hz** fixo; flip em modo VSYNC (flipMode=1). 3 display buffers registrados (`RegisterBuffers(..., 3, ...)`). Para 60 fps num port: trocar para 0 e verificar o timestep da logica (ver relatorio do loop principal).

---

## 6. Async compute

Filas criadas **[C]**:
| Objeto | Pipe/Queue | Onde | Uso |
|---|---|---|---|
| `JsComputeContext` do device | pipe 1, queue 4, prio 0 | 0x1c4f9f0 -> 0x24728d0 | trabalho assincrono do device (AsyncCopyResource/AsyncMap/UpdateSubresource) |
| 3x `JsComputeContext` por frame | pipe 2, queues 0/1/2, prio 1 | 0x1c4f9f0 (CreateBackBuffers) | ACB do frame, submetido em `Present` antes do DCB |
| `JsComputeQueue` (Gnmx ComputeQueue) | pipe 0, queue 3, ring 1 MiB, `sceGnmMapComputeQueue` | 0x1c4f9f0 | dispatch draw ACB (`internalSubmitAndFlip` verifica "ComputeQueue was not mapped/set before submitting for dispatch draw") |

`sceGnmDispatchIndirectOnMec` nao e chamado. Submissao de compute so via `sceGnmDingDong` (0x249f320).

Quem usa o compute assincrono:
- Slot 3 do RendererDev (0x1c49540) **[C/P]**: sequencia de `Dispatch` (0x24711c0), `AsyncCopyResource` (0x24717c0), `AsyncMap` (0x2473600), LCUE dispatch (0x2473340) e `Submit` (0x2472ed0). Pelo conjunto de shaders criados em RendererDev_Setup (Skinning, InstanceBufferCompute, AabbCompute, RayCastCompute, TrackingCompute) e pelo uso de `AsyncMap` (readback para CPU), isso e o bloco de compute pre-frame: skinning por compute, instance buffers, e **consultas de raycast/AABB/tracking cujos resultados voltam para a CPU (logica de jogo/IA do Trico)** **[P]**.
- 0x1c97a00 e 0x1e13270 (via 0x1f7e850/0x1f7e520, lado do jogo) tambem fazem dispatch LCUE + `Submit` **[P]**: provavelmente as consultas de RayCastCompute disparadas pelo gameplay.
- `ComputeInterface.cpp` (0x1c4f340, 0x1ee2610, 0x1ee2b30, 0x1ee2ef0) = interface generica de jobs de compute (cria buffers/UAVs) **[P]**.
- Na fila grafica (nao assincrono): TileCull (0x1eee4a0), LightBuffer (0x1eeaa40), SSAO/SMAA (0x1eebfc0), PostProcess (0x1eebdf0/0x1eecf40), Bloom (0x1f82b50), InstanceBufferCompute (0x1ee5130), CopyResource/clears via CS.
- Dispatch draw (culling de triangulos em compute do Gnmx): suporte compilado (CreateVsDd, setCsVsShaders, begin/endDispatchDraw, JsComputeQueue) - uso real depende dos .sb carregados **[?]**.

Implicacao: um port precisa manter **sincronizacao GPU->CPU correta** (readback dos raycasts), pois o gameplay depende disso.

---

## 7. Avaliacao para port PC (rendering)

Fatos que pesam na decisao:
- CPU e x86-64: o codigo do jogo pode rodar nativamente num loader estilo shadPS4 (como gow3_pc / bloodborne_pc), sem recompilar CPU.
- Superficie Gnm pequena: ~33 imports Gnm efetivamente chamados + 10 VideoOut. Um unico submit grafico por frame (`SubmitAndFlip`) + DingDong para compute.
- Os shaders existem **apenas** como GCN binario (.sb no psarc + 49 embutidos). Nao ha HLSL fonte no disco.
- A camada Js* e um shim D3D11: o renderer `render\dev` ja foi escrito para D3D11 (provavelmente o motor tinha backend PC/Windows de desenvolvimento).

### (a) Manter Gnm/PM4 e traduzir com o video core do shadPS4
O que e preciso concretamente:
1. HLE de `libSceGnmDriver`: implementar os packet builders (DrawIndexAuto/Offset/Indirect, DispatchDirect/Indirect, Set{Vs,Ps,Cs,Es,Gs,Ls,Hs}Shader, Update*, SetEmbeddedVsShader, InitDefaultHardwareState, SetVgtControl, markers) gerando PM4 identico ao driver; `SubmitAndFlipCommandBuffers`, `SubmitDone`, `DingDong`, `MapComputeQueue[WithPriority]`, `AddEqEvent` (EOP via equeue), `InsertWaitFlipDone`, `RegisterOwner`. O shadPS4 ja tem quase tudo isso (`src/core/libraries/gnmdriver`).
2. HLE de `libSceVideoOut` (Open, RegisterBuffers 3 buffers, SetFlipRate, SetBufferAttribute com formatos 0x80002200/0x88000000/0x88740000, ConfigureOutputMode_/ModeSetAny_, GetResolutionStatus, GetDeviceCapabilityInfo_). Reportar 1080p e sem HDR evita checkerboard e o caminho PQ no inicio.
3. Liverpool PM4 parser + recompilador GCN->SPIR-V + emulacao de memoria GPU = CPU (Garlic/Onion via direct memory; o jogo usa ponteiros CPU como enderecos GPU, faz `Map`/discard e `AsyncMap`), detiling de texturas (inclusive tile modes Neo se emular Pro), CMASK/HTILE fast clear (`eliminateFastClear`, `ClearHtileSurface`) e filas ACB (pipe 0-2).
4. Ajustes: `SetFlipRate` -> 0 para 60 fps (se a logica aguentar), resolucao: forcar a lista 1080p (equivalente a `-force2k`, ou patchar `App+0x210`/`GetResolutionStatus`) ou expor a lista 4K (3840x2160 native) para render alto em PC.
5. Riscos: bugs/perf do shadPS4 com este titulo (checkerboard, dispatch draw, readback de compute que o gameplay usa); cache de shaders SPIR-V grande (milhares de permutacoes de material).
Esforco: **menor**, comecando pelo que gow3_pc/bloodborne_pc ja fazem; a maior parte do trabalho e compatibilidade/depuracao no video core.

### (b) Reimplementar a camada Js* sobre D3D11/D3D12/Vulkan
O que e preciso concretamente:
1. Substituir (hook/detour) as funcoes reais do shim: ~20 `JsDevice::Create*` (tabela 2.1), `JsDeviceContext` (Draw/DrawInstanced/DrawIndexed*/Dispatch*/Clear*/CopyResource/Map/UpdateSubresource, `PrepareDraw` 0x2488580 e `PrepareDispatch` 0x2479b70), `JsComputeContext` (2.4) e `JsSwapChain` (Present/BeginFrame/ResizeBuffers). Como os setters (`OMSetRenderTargets`, `*SetShaderResources`, viewports, topology...) estao **inlinados** em `render\dev`, eles escrevem direto na struct `JsDeviceContext`; a estrategia viavel e mapear o layout dessa struct (offsets de RTVs, SRVs, CBs, shaders, estados) e ler o estado em cache dentro dos hooks de `PrepareDraw`/`Draw*`, traduzindo para chamadas D3D11/Vulkan. Alternativa mais limpa, porem mais cara: recompilar/levantar as funcoes de `render\dev` para chamar uma API real.
2. Recursos: os objetos Js* guardam `Gnm::Texture/Buffer/RenderTarget` com memoria em Garlic; seria preciso criar recursos espelho na GPU do PC e manter coerencia nos `Map`/`UpdateSubresource`/`AsyncMap`. Texturas de asset chegam pre-tiled (GNF, `JsCreateTextureFromMemory` 0x1c96930) -> detiler necessario no load.
3. Shaders: converter os .sb (GCN) offline para SPIR-V (recompilador do shadPS4) e dai para DXIL/HLSL (SPIRV-Cross) ou usar Vulkan direto; gerar o mapeamento de slots a partir dos metadados de input usage do .sb (o mesmo que `generateInputResourceOffsetTable`/CUE fazem). Os 49 shaders embutidos podem ser reescritos a mao (clear/copy). Reescrever em HLSL so seria viavel para passes pontuais.
4. Compute assincrono: mapear pipe1/pipe2 para fila compute D3D12/Vulkan (ou serializar em D3D11) com fences para os readbacks.
5. Ganhos: render nativo sem emular PM4/registradores, resolucao arbitraria, MSAA/AA melhor, sem shader cache de emulador; perfeito alvo para D3D11 porque a semantica (formatos DXGI, bind flags, usage) ja e D3D11.
Esforco: **muito maior** (engenharia reversa do layout de `JsDeviceContext` 0x130f0 bytes, de cada objeto Js*, e traducao de todos os shaders), mas resultado mais robusto e "nativo".

Recomendacao: comecar por (a) para ter o jogo rodando e instrumentado; usar o conhecimento do shim Js* (esta tabela) para, depois, migrar gradualmente para (b) hookando `Present`, `CreateBackBuffers` e `PrepareDraw`/`Draw*`, ou ficar em (a) com patches pontuais (flip rate, resolucao, HDR desligado).

---

## 8. Pendencias / incertezas
- Nomes dos slots da vtable RendererDev alem de 5 (Render) e 6 (Present) sao palpite.
- Conteudo exato de cada um dos 47 CS embutidos (copy/clear por formato) nao foi verificado shader a shader.
- Se dispatch draw e efetivamente usado em runtime depende dos .sb do psarc (nao inspecionados).
- Layout completo da struct `JsDeviceContext` (necessario para a opcao b) nao foi mapeado.
