# inFAMOUS Second Son PC: roadmap

Port de inFAMOUS Second Son (Sucker Punch, PS4, CUSA00223, base 1.00 + update 1.07, SDK 4.00).
Atualizado em 13/10/2026. O estado de quem joga está no [README](../README.md#status); a lista de
trabalho completa, com as investigações, fica em `~/decomp/PORT_INFAMOUS.md` (fora do repositório),
e cada item aberto vira uma issue com o tempo.

## Onde estamos

**Jogável, em desenvolvimento:** boot, título, intro e gameplay (testado até "Go to Longhouse"),
com som próprio (AudioOut + Ajm, sem arquivo do firmware), saves, HUD correto, sensor de movimento
(real ou simulado), touchpad simulado e partículas da GPU com a leitura precisa (padrão).
20–30 FPS típicos numa RTX 2060, instável.

## Feito

| Item | Detalhe |
|---|---|
| Boot | `mov reg, fs:[0]` em qualquer registrador (TLS); os 15 imports só deste jogo (`runtime_infamous.c`) |
| Sensor de movimento | giroscópio real pela SDL3 e "modo sensor" simulado (Share ou L3+R3; teclado T/G/Y) |
| Analógicos | zona morta de 10% (`ISS_STICK_DEADZONE`, também no launcher) e o último controle usado |
| Touchpad sem touchpad | View/Select (ou Tab) + analógico direito desliza ("Open Door") |
| VRAM | orçamento padrão de 3500 MB (falta de VRAM no carregamento) |
| FPS caindo com o tempo | variantes de shader com a chave tirada antes da tradução: de 60→6 FPS para estável |
| Partículas da GPU (fumaça do dreno, drones) | leitura precisa da GPU por padrão; modo rápido no launcher ("Precisão da GPU") |
| Stencil `test_val`/`op_val` | uma referência Vulkan quando as máscaras permitem |
| Cache de shaders | pasta com a chave do tradutor; o cache antigo é apagado sozinho |

## Aberto (por prioridade)

| # | Item | Detalhe |
|---|---|---|
| 1 | Desempenho | a thread do jogo espera leituras da GPU (escritas de `memcpy` em páginas modificadas pela GPU); correção: rastrear a memória em pedaços menores que a página (`ISS_WRITE_MERGE=1` é o primeiro passo, desligado por padrão) |
| 2 | Engasgo de shader | 64–118 compilações por janela de 5 s em cenas novas; precisa do cache de pipelines em disco (`ISS_PIPELINE_BINARIES=1` ainda derruba o jogo) |
| 3 | Névoa, água, fogo e luzes piscando; grade fina de linhas escuras | suspeitas: ballots wave64 em fluxo divergente, texturas BC 1D |
| 4 | Brilho azul do dreno de drones | não aparece; ballot wave64, stencil ou readback |
| 5 | Texturas BC 1D | promoção para 2D automática nos drivers que recusam BC 1D, menos a NVIDIA; `ISS_BLOCK1D=0/1` decide. Na NVIDIA fica desligada porque estraga o HUD. O driver da AMD no Windows quebrava com BC 1D e também com a promoção (#16, #31, #49): lá as BC1–BC5 1D ou menores que um bloco são decodificadas na CPU (`ISS_BC_TINY=0/1`); falta confirmar numa RX 580 |
| 6 | Idiomas do jogo no launcher | a lista ainda é a do GR2; ler do `param.sfo`/dados |
| 7 | `param.sfo` 1.07 na visão do jogo | a visão usa o 1.00 |
| 8 | Prefixo `ISS_` nas variáveis | ✅ feito: o jogador usa `ISS_*`; o núcleo ainda lê `TLG_*` por dentro (o `tlg-probe` traduz na partida). Quando todos os ports usarem o ps4_core, o prefixo comum vira `PSCORE_` |
| 9 | Launcher novo (C++/SDL3/ImGui) | protótipo aqui, depois em todos os ports |

---

# inFAMOUS Second Son PC: roadmap (English)

Port of inFAMOUS Second Son (Sucker Punch, PS4, CUSA00223, base 1.00 + update 1.07, SDK 4.00).
Updated 13/10/2026. The player-facing status is in the [README](../README.md#english); the full work
list with the investigations lives in `~/decomp/PORT_INFAMOUS.md`, outside the repository.

**Playable, in development:** boot, title, intro and gameplay (tested up to "Go to Longhouse"), own
audio (no firmware file), saves, correct HUD, real or simulated motion sensor, simulated touchpad and
GPU particles with precise readbacks (default). 20–30 FPS typical on an RTX 2060, unstable.

Open, by priority: (1) performance — the game thread waits on GPU readbacks; (2) shader-compile
stutter — needs an on-disk pipeline cache; (3) flickering fog/water/fire/lights and a fine dark grid;
(4) the missing blue drone-drain glow; (5) BC 1D textures; (6) game languages in the launcher;
(7) the 1.07 `param.sfo` in the game view; (8) `ISS_` variable prefix; (9) new C++/ImGui launcher.
