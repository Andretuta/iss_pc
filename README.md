<p align="center"><img src="port/packaging/icon/infamous-icon-1024.png" width="160" alt=""></p>

<h1 align="center">inFAMOUS Second Son — port nativo para PC</h1>

<p align="center">
  <a href="#english"><b>English below</b></a> ·
  <a href="https://github.com/HayatoG/iss_pc/releases/latest">Download</a> ·
  <a href="https://www.youtube.com/@hayatog-dev">YouTube</a> ·
  <a href="https://discord.gg/UMkdMYZh9g">Discord</a>
</p>

<p align="center"><a href="https://github.com/HayatoG/iss_pc/actions/workflows/build.yml"><img src="https://github.com/HayatoG/iss_pc/actions/workflows/build.yml/badge.svg" alt="Build"></a></p>

> **Jogável, em desenvolvimento.** O jogo inicia, chega ao gameplay e passa pelos primeiros capítulos, mas o desempenho ainda é instável (20–30 FPS típicos numa RTX 2060) e há falhas de imagem conhecidas. Veja o [Status](#status).

**inFAMOUS Second Son** (PS4, CUSA00223, jogo base 1.00 + update 1.07) rodando no PC sem emulador de CPU: o código original do jogo roda nativo no processador, o sistema do PS4 é reimplementado e a GPU é traduzida para Vulkan. Usa o mesmo núcleo dos ports de [The Last Guardian](https://github.com/HayatoG/tlg_pc) e [Gravity Rush 2](https://github.com/HayatoG/gr2_pc).

> **Nenhum arquivo do jogo vem com este projeto.** Para jogar, você precisa da sua própria cópia, tirada do seu PS4.

Por **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

| | |
|---|---|
| ![Delsin diante do outdoor, com o pedido de virar o controle de lado](docs/screenshots/01-grafite-sensor.jpg) | ![Delsin no galpão do cais](docs/screenshots/02-galpao.jpg) |
| ![Na cerca do cais](docs/screenshots/03-cerca.jpg) | ![Correndo pela praia ao pôr do sol](docs/screenshots/04-praia.jpg) |

![Escalando as rochas acima da vila](docs/screenshots/05-escalada.jpg)

<sub>Capturas na resolução nativa (1920×1080, reduzidas para 1280), direto da GPU, no Linux com uma RTX 2060.</sub>

## Novidades

- **Processadores sem F16C (Sandy Bridge, #51):** as 13 conversões de meia precisão do jogo (`VCVTPH2PS`/`VCVTPS2PH`) passam a ser emuladas na partida, com o mesmo resultado bit a bit do processador (arredondamento, denormais, Inf e NaN). Antes o jogo parava com "13 sites use encodings the rewrite cannot emulate".
- **Mouse:** o mouse gira a câmera (analógico direito) e também faz o papel do **touchpad**. Esquerdo = R2, direito = L2, do meio = R3. **Segure Ctrl esquerdo (ou o botão lateral X1)** e o mouse vira um dedo no touchpad: esquerdo toca/clica (segurar = absorver poder), arrastar com o esquerdo desliza (porta "Open Door", scanner), direito = dois dedos (levantar o carro do Reggie). A janela prende o mouse; Esc solta e um clique prende de novo. Veja [Mouse](#mouse).
- **Explicação do grafite na tela:** na primeira vez que o modo sensor liga, uma tela no meio mostra os passos (sacudir, pintar, mirar, sair) com os botões do seu controle; fecha com "Entendi". O menu Insert ganhou a aba **Controle**, que mostra essa tela de novo e ajusta a **velocidade da mira do grafite** (25–200%, também `ISS_SENSOR_AIM`).
- **Grafite mais fácil (modo sensor):** o modo sensor agora é a lata de spray do grafite: ao ligar (L3+R3), o controle já fica de lado, como o jogo pede ("Hold Wireless Controller Sideways"); **X/A sacode**, **R2 pinta** e o **analógico esquerdo mira** o cursor para os lados e para cima/baixo (antes ele só subia e descia), mais devagar com o analógico pouco inclinado, para contornar o desenho. No teclado, enquanto T ou G seguram o controle de lado, as **setas** miram.
- **Em teste: fumaça e partículas da GPU piscando (#7, #50).** Correções do tradutor de shaders, parte delas vinda do port nativo de [Shadow of the Colossus](https://github.com/AjncSystem/ShadowOfTheColossus-PC):
  - barreiras de memória compartilhada (LDS) nos shaders de compute de qualquer tamanho de workgroup, inclusive os que não são múltiplos de 64 (96, 192...): `ISS_LDS_SMALL` (menos de 64 threads), `ISS_LDS_MULTI` (mais de 64; em GPU de 32 lanes a barreira cobre o workgroup inteiro, porque cada wave de 64 do PS4 ocupa dois subgrupos), `ISS_LDS_READLANE`;
  - `ISS_LANE_DIVERGENCE`: desvios que dependem do `v_mbcnt`, do número da lane ou do valor devolvido por um atomic contam como divergentes, para nenhuma barreira cair dentro de um desvio que só uma lane toma;
  - `S_WQM_B64`, que não fazia nada (`ISS_WQM`).
  - Todas ligadas por padrão no inFAMOUS; `0` desliga cada uma, para comparar. O log mostra uma linha `shader switch` por chave.
  - Experimento, desligado: `ISS_RFL_ALL=1` troca o `ReadFirstLane` pela primeira lane da wave de 64 inteira em todos os shaders de compute largos (não só nos que usam ballot).
  - O cache de shaders se refaz sozinho a cada combinação.
- **Correções vindas do [shadPS4-Infamous-FixBuild](https://github.com/rayhlancaner-png/shadPS4-Infamous-FixBuild):**
  - **Brilho do Delsin ao drenar energia corrigido:** o stencil passa a respeitar o valor de teste e o de escrita, que são separados no PS4.
  - **Mais FPS:** quando o jogo lê algo da GPU, só a thread que pediu espera, não a GPU inteira (`ISS_DEFERRED_READBACK`, ligado por padrão), e o trabalho vai para a GPU em partes (`ISS_SUBMIT_DRAWS`, padrão 1024).
  - **Menos travadas ao surgir um efeito novo:** os shaders de compute compilam fora da thread da GPU (`ISS_COMPUTE_ASYNC_BUILD`), e o jogo tenta de novo quando o driver falha ao criar um pipeline.
  - **VRAM:** quando a memória de vídeo aperta, o port libera texturas antigas e tenta de novo, em vez de fechar. Uploads gigantes, como ao carregar um save, vão em partes, e o driver pode mover memória para a RAM.
  - **Atomics de float** corrigidos em placas sem suporte nativo, como as NVIDIA.
- **Sensor de movimento:** o giroscópio do DualShock 4/DualSense funciona direto. Em controles sem sensor, um toque em L3+R3 (ou Share no Xbox Series) liga o "modo sensor", a lata de spray do grafite: o controle fica de lado, X/A sacode, R2 pinta e o analógico esquerdo mira. No teclado, T/G viram de lado (com as setas mirando enquanto seguram) e Y sacode. É o que passa do grafite ("Hold Wireless Controller Sideways").
- **Analógicos:** zona morta de 10% contra drift (`ISS_STICK_DEADZONE`, também no launcher), e o último controle usado é o que vale.
- **Touchpad sem touchpad:** segure View/Select (ou Tab) e mova o analógico direito (ou as setas) para deslizar o dedo, como no "Open Door"; um toque rápido continua sendo clique.
- **Desempenho:** o FPS não cai mais com o tempo (caía de 60 para 6 em 2 minutos: as variantes de shader nunca se repetiam), e transições parciais de imagem repetidas são puladas.
- **Leitura precisa da GPU por padrão:** a fumaça do dreno de energia, os drones e outras partículas calculadas na GPU aparecem. O modo rápido continua no launcher ("Precisão da GPU").
- **Cache de shaders automático:** fica em `user/cache/`, junto dos saves (em Linux e Windows; o cache antigo de `~/.local/share/shadPS4` ou `user/user/` é trazido sozinho na primeira partida). A pasta leva a versão do tradutor de shaders, e o cache antigo é apagado sozinho depois de uma atualização. Para recompilar tudo, o launcher tem o botão **Limpar cache de shaders** (ou `./run_infamous.sh --clear-shader-cache`); ele apaga só os shaders compilados deste jogo, nunca saves ou configurações.

## Status

| Área | Estado |
|---|---|
| Boot, título, intro e gameplay | ✅ Funciona; testado até "Go to Longhouse", com escalada, corrida, poderes e cutscenes |
| Sensor de movimento (grafite, pedidos de movimento) | ✅ Giroscópio real ou simulado em qualquer controle e no teclado |
| Fumaça do dreno, drones e partículas da GPU | ✅ Com a leitura precisa da GPU (padrão) |
| HUD | ✅ Correto |
| Áudio | ✅ AudioOut + Ajm próprios, sem nenhum arquivo do firmware |
| Saves | ✅ O save é criado e o "Continue" funciona |
| Controle | ✅ DualSense, DualShock 4, Xbox e 8BitDo via SDL3 |
| Desempenho | 🔧 20–30 FPS típicos numa RTX 2060, instável; otimização em andamento |
| Engasgos | 🔧 Na primeira vez que cada shader é compilado (cutscenes e áreas novas) |
| Imagem | 🔧 Alguns efeitos de névoa, água e luz piscam |
| Linux | ✅ Testado (Nobara/Fedora 44) |
| Windows | 🧪 Build automático, ainda sem teste em jogo |

![Desempenho de uma sessão de 7 minutos andando pela cidade](docs/screenshots/desempenho.png)

<sub>FPS, pior quadro e draws por quadro a cada 5 s, tirados do log do port (`ISS_FRAME_STATS=1`), na RTX 2060: mediana de 27 FPS, 44% do tempo acima de 30 FPS. O jogo não tem trava de FPS. Gerado por `scripts/session_chart.py` (com `0` = sem trava).</sub>

## Download

A [**última versão**](https://github.com/HayatoG/iss_pc/releases/latest) é gerada pelo GitHub Actions a cada mudança; as anteriores ficam em [Releases](https://github.com/HayatoG/iss_pc/releases) como histórico:

- **Linux x86-64** (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 ou mais novos): `infamous-linux-x86_64.tar.gz`
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

**Do firmware do console:** nada. O áudio usa o nosso AudioOut + Ajm; o jogo não importa `libSceNgs2` nem outro módulo do sistema do PS4.

A lista completa e o passo a passo, que também vão nas notas de cada Release, estão em [`docs/ARQUIVOS_NECESSARIOS.md`](docs/ARQUIVOS_NECESSARIOS.md).

**PC:** placa de vídeo com Vulkan 1.3 (6 GB de VRAM recomendados) e ~33 GB livres.

## Como jogar

1. Extraia o pacote.
2. Abra o **inFAMOUS Second Son**, escolha a pasta do jogo e o idioma e clique em **Jogar**. Se a imagem engasgar demais, a opção "Precisão da GPU" tem um modo rápido (sem as partículas da GPU).
3. No jogo, **F10** liga o contador de FPS, e **Insert** (ou R3 + L2 no controle) abre o menu do port.
4. Quando o jogo pedir para virar ou sacudir o controle e o seu não tiver sensor: toque em L3+R3 (ou Share no Xbox Series). O controle já fica de lado; X/A sacode, R2 pinta e o analógico esquerdo mira. Toque de novo para sair. No teclado: T/G (com as setas para mirar) e Y. Veja [Sensor de movimento e touchpad](#sensor-de-movimento-e-touchpad).

O passo a passo completo está em [`README-player.md`](port/packaging/README-player.md), que também vem dentro do pacote.

**Correções experimentais:** o botão **Correções experimentais…** do launcher liga e desliga as 12 correções `TLG_BP01` a `TLG_BP12` (de outros ports de PS4 e do shadPS4), as chaves de diagnóstico (`TLG_WQM`, `TLG_LDS_*`, `TLG_BC_TINY`...) e as opções do menu Insert, com etiqueta de "no jogo" ou "reinicia o jogo". Sem mexer em nada valem os padrões. Lista completa: [`docs/EXPERIMENTAL_FIXES.md`](docs/EXPERIMENTAL_FIXES.md).

## Mouse

O mouse funciona com ou sem controle (os botões dele somam aos do controle). A janela do jogo prende o mouse enquanto tem o foco e o menu Insert está fechado; **Esc solta** (o cursor volta) e **um clique na janela prende de novo** (esse clique não vira botão do jogo).

**Câmera e botões:**

| Mouse | No jogo |
|---|---|
| Mover | gira a câmera (analógico direito) |
| Botão esquerdo | R2 (usar o poder / atirar) |
| Botão direito | L2 (mirar) |
| Botão do meio | R3 |
| Botões laterais X1 / X2 e rodinha | livres (veja `ISS_KEY_MAP`); X1 também é a tecla do modo touchpad |
| Sensor ligado (modo sensor, T ou G) | o mouse aponta a lata de spray do grafite em vez de girar a câmera |

**Modo touchpad:** segure **Ctrl esquerdo** ou o **botão lateral X1** do mouse. Enquanto o modo está ligado a câmera não gira: o movimento do mouse leva um dedo virtual pelo touchpad (um quadradinho no canto inferior esquerdo da tela mostra onde ele está) e os botões viram o dedo:

| Gesto (mouse no modo touchpad) | O que o jogo vê | Onde usar |
|---|---|---|
| Só mover | dedo suspenso (nenhum toque): posiciona o dedo | antes de um gesto |
| Esquerdo, tocar rápido | toque + clique do touchpad | interações "aperte o touchpad" |
| Esquerdo, segurar parado | toque + clique mantidos | absorver/drenar poderes (fumaça, neon...) |
| Esquerdo, arrastar mais de 80 unidades | o clique solta e o dedo desliza | porta "Open Door", scanner de mão |
| Botão do meio (segurar e mover) | dedo sem clique | deslizar sem clicar, se um gesto não gostar do clique |
| Direito | dois dedos nas duas pontas com o touchpad apertado | levantar o carro de cima do Reggie |

O dedo começa no meio do touchpad e fica onde você o deixou. Os atalhos do teclado (Tab/Backspace, Tab + setas) continuam como antes.

**Variáveis de ambiente** (`ISS_` e `TLG_` valem igual; `mouse_*` também podem ir no `tlg.ini`):

| Variável | Padrão | O que faz |
|---|---|---|
| `ISS_MOUSE` | `1` | `0` desliga o mouse (a janela não prende mais) |
| `ISS_MOUSE_SENS` | `1.0` | sensibilidade da câmera (0,05–10) |
| `ISS_MOUSE_INVERT_Y` | `0` | `1` inverte o eixo Y |
| `ISS_MOUSE_SMOOTHING` | `0.5` | suavização (0–0,95) |
| `ISS_MOUSE_ACCEL` | `0` | aceleração (0–2) |
| `ISS_MOUSE_DEADZONE` | `0.1` | anti-zona morta: movimentos pequenos pulam a zona morta do jogo (0–0,5) |
| `ISS_MOUSE_PAD` | `1` | `0` desliga o modo touchpad do mouse |
| `ISS_MOUSE_PAD_KEY` | `Left Ctrl\|Mouse X1` | tecla(s) do modo touchpad; nomes do SDL ou `Mouse Left/Middle/Right/X1/X2`, separados por `\|` |
| `ISS_MOUSE_PAD_MODE` | `hold` | `toggle`: um toque na tecla liga, outro desliga |
| `ISS_MOUSE_PAD_SENS` | `1.0` | velocidade do dedo (0,1–10) |
| `ISS_MOUSE_PAD_DRAG` | `80` | unidades (touchpad de 1920 de largura) de arrasto até o clique virar deslize; `0` = nunca |
| `ISS_KEY_MAP` | — | remapeia teclas e mouse: `"r2=Mouse Left\|F,l2=Mouse Right\|R,r1=Mouse X2,l1=Wheel Down"`; vários por botão com `\|`, `none` tira todos |
| `ISS_MOUSE_LOG` | `0` | `1` mostra no log o que o jogo recebe do mouse |

O menu Insert, aba **Controle**, tem os ajustes da câmera do mouse.

### Onde ficam seus saves e como atualizar sem perdê-los

Por padrão os saves e configurações ficam em `user/`, ao lado do jogo. **A atualização não apaga nada**, mas se você extrair o zip novo em outra pasta (ou apagar a antiga), o jogo abre sem saves: eles continuam na pasta antiga, em `user/savedata`. Para nunca mais passar por isso, abra o launcher Qt, vá em **Saves e dados** e escolha uma pasta fixa fora do jogo (sugestão: `Documentos\inFAMOUS-PC` no Windows, `~/.local/share/infamous-pc` no Linux); o launcher copia seus saves para lá e guarda a escolha num arquivo do seu usuário (`%APPDATA%\inFAMOUS-PC\launcher.json` / `~/.config/infamous-pc/launcher.json`), que sobrevive a reinstalações. A mesma tela acha saves de outras pastas do port, importa e exporta `.zip`, e faz backups (também antes de cada partida). Variável `ISS_USER_DIR` tem prioridade sobre tudo.

## Sensor de movimento e touchpad

O jogo pede o sensor de movimento e o touchpad em várias cenas: grafite, absorver poderes (fumaça, neon...), abrir portas e outras interações. No **DualShock 4 e no DualSense** o giroscópio e o touchpad funcionam direto, sem ligar nada. Nos outros controles e no teclado, o port simula os dois.

**Modo sensor (ligar e desligar):**
- **Um toque em L3+R3 juntos** liga o modo sensor; outro toque desliga. Funciona em qualquer controle. Também serve o botão extra do controle: **Share** no Xbox Series, **Capture** no Switch Pro e **microfone** no DualSense. No DualShock 4 e no DualSense, o Share/Create **não** liga o modo sensor: ele é o clique do touchpad.
- Um aviso na tela confirma: "Modo sensor LIGADO (lata de spray): X sacode, R2 pinta, analógico esquerdo mira" ou "Modo sensor desligado".
- Com o modo ligado, o controle fica **de lado**, como uma lata de spray (o que o grafite pede), **X/A sacode** e o **analógico esquerdo mira**, girando a lata para os lados e para cima/baixo (é o que move o cursor do grafite; ele fica onde você soltou; pouco inclinado vai devagar, para contornar o desenho; o direito também serve). R2 continua pintando. O analógico e o X/A ficam escondidos do jogo, então o Delsin não anda, não pula e a câmera não gira: **desligue o modo depois da cena**. O L3+R3 juntos também não chega ao jogo.
- Com o modo ligado, a inclinação simulada substitui o giroscópio real.
- **Teclado** (sem modo, a qualquer hora): segure **T** ou **G** para virar o controle de lado (um lado ou o outro) e **Y** para sacudir.

**Touchpad em controle sem touchpad:**
- **View/Select/Back** é o clique do touchpad (lado direito; com L1 segurado, o lado esquerdo). Segurar o botão é segurar o touchpad.
- **Segure View/Select e mova o analógico direito** para deslizar o dedo a partir do meio do touchpad. Um toque rápido sem mover continua sendo clique.
- **Teclado:** Tab (lado esquerdo) e Backspace (lado direito) clicam; **segure Tab e use as setas** para deslizar.
- **Dois dedos nas duas pontas do touchpad** (levantar o carro de cima do Reggie): **segure View/Select + R1**; no teclado, **segure Tab + Backspace**.

| Ação no jogo | DualShock 4 / DualSense | Xbox / outro controle | Teclado |
|---|---|---|---|
| Absorver/drenar um poder (fumaça, neon...) e interações de "segure o touchpad" | segurar o touchpad | segurar View/Select (sem mexer o analógico direito, senão vira deslize) | segurar Tab ou Backspace (sem as setas); no mouse: Ctrl esquerdo (ou X1) + segurar o esquerdo parado |
| Interação de "toque no touchpad" | clicar o touchpad | toque em View/Select | Tab ou Backspace |
| Grafite: virar o controle de lado | virar o controle | L3+R3 (modo sensor): já fica de lado | segurar T ou G |
| Grafite: sacudir a lata | sacudir o controle | X/A no modo sensor | Y |
| Grafite: pintar | R2, mirando com o controle | R2, mirando com o analógico esquerdo no modo sensor | F (R2), mirando com as setas enquanto segura T ou G |
| Apertar as duas pontas do touchpad (levantar o carro de cima do Reggie) | dois dedos, um em cada ponta | segurar View/Select + R1 | segurar Tab + Backspace; no mouse: Ctrl esquerdo (ou X1) + botão direito |
| Deslizar no touchpad (porta "Open Door", scanner de mão) | deslizar o dedo | segurar View/Select + analógico direito na direção pedida | segurar Tab + setas; no mouse: segurar Ctrl esquerdo (ou X1), esquerdo e arrastar |
| Voltar ao normal depois do grafite | — | L3+R3 de novo ("Modo sensor desligado") | — |

**Launcher:** o quadro **Controle** tem a **Zona morta dos analógicos** (0–40%, padrão 10%). Aumente se o personagem, a câmera ou a inclinação do modo sensor se mexerem sozinhos (drift).

**Variáveis de ambiente:** `ISS_MOTION_BUTTON=<botão do SDL>` troca o botão do modo sensor (padrão `misc1`; o L3+R3 vale sempre), e `ISS_MOTION=off` ignora o giroscópio real (a simulação continua funcionando).

**Processadores Intel:** o código do jogo usa instruções SSE4A (EXTRQ), que só existem em processadores AMD. Num Intel o port troca essas instruções por uma emulação na partida (precisa do `iced-x86`, que já vem nos pacotes). Processadores mais antigos (Sandy e Ivy Bridge) também não têm MOVBE, F16C, BMI1 ou LZCNT, que são emulados do mesmo jeito; o AVX continua obrigatório. `ISS_ISA_REWRITE=sse4a` (ou `f16c`, ou uma lista como `f16c,movbe`) força a emulação num processador que tem a instrução (teste), `ISS_ISA_REWRITE=1` força todos os conjuntos emulados (MOVBE, BMI1, LZCNT, F16C, SSE4A) e `ISS_ISA_REWRITE=0` desliga. Detalhes: [port/docs/isa_rewrite.md](port/docs/isa_rewrite.md).

**Windows: proteção da red zone.** O código do PS4 guarda variáveis nos 128 bytes abaixo do `rsp` (a "red zone"), e o Windows escreve ali a cada exceção (o port usa exceções para acompanhar a memória da GPU). Na partida o port reescreve as instruções de memória das funções que usam a red zone para rodarem com o `rsp` 128 bytes mais baixo (crash em `0x1cfaaf`, #29/#41). Vem ligada no Windows; `ISS_RED_ZONE_REWRITE=0` desliga e `ISS_RED_ZONE_REWRITE=1` liga no Linux (teste). Teste no Linux: `TLG_CLOBBER_RED_ZONE=<bytes>` apaga essa quantidade de bytes abaixo do `rsp` a cada exceção, como o Windows (`1` = 128). Detalhes: [port/docs/red_zone.md](port/docs/red_zone.md).

**Tela congelada:** se o jogo passa 10 s sem mostrar um quadro novo, o log (`out/last_run.log`) ganha um bloco `FREEZE: no frame for 10 s; threads:` com cada thread do jogo, o que ela está esperando (mutex, semáforo, fila de eventos, leitura de arquivo, GPU...) e onde está no código. O jogo continua rodando, e o relatório só se repete depois que os quadros voltarem e pararem de novo. Mande esse log junto com o relato. `ISS_FREEZE_REPORT_SECONDS=<s>` muda o tempo (`0` desliga).

**Placas AMD no Windows (RX 580): texturas BC minúsculas.** O driver da AMD no Windows (`amdvlk64.dll`) quebra logo depois dos logos (`Fault: write access to 0 at amdvlk64.dll+0xebbbb`, #16/#31/#49) na primeira textura comprimida BC 1D do jogo (512x1), seja ela criada 1D ou 2D. No driver da AMD o port decodifica na CPU as texturas BC1–BC5 que são 1D ou menores que um bloco de 4x4 e manda ao driver imagens comuns (RGBA8, R8 ou RG8, mantendo sRGB e snorm); o log mostra `GPU: tiny block-compressed textures ...` dizendo o modo. `ISS_BC_TINY=0` desliga e `ISS_BC_TINY=1` liga em qualquer placa (teste).

## Compilar do código-fonte

```bash
git clone --recursive https://github.com/HayatoG/iss_pc.git && cd iss_pc
cd port && ISS_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, FreeType, Boost, fmt, Zydis, glslang
cd .. && ./infamous_launcher.sh        # ou ./run_infamous.sh pelo terminal
```

No Windows, o build roda no MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). O workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) mostra o processo completo nas duas plataformas.

## Como funciona

| Camada | O que faz | Base |
|---|---|---|
| Loader | Carrega o `eboot.bin` 1.07 e liga os módulos do próprio jogo (`libc`, `Fios2`) | [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) |
| Runtime | Reimplementa as bibliotecas do PS4 (NpManager, Trophy, Http, PlayGo, SaveData, AppContent, AudioOut, Ajm...). Específicos do inFAMOUS: `port/src/runtime_infamous.c` | `port/src/` |
| Vídeo | Traduz os comandos Gnm e os shaders GCN para Vulkan/SPIR-V | núcleo de vídeo do [shadPS4](https://github.com/shadps4-emu/shadPS4) |

## Próximos passos

O que falta está em [`docs/ROADMAP.md`](docs/ROADMAP.md): desempenho (esperas por leituras da GPU), cache de pipelines em disco contra os engasgos, os efeitos que piscam, o brilho do dreno de drones e os idiomas do jogo no launcher.

## Créditos e aviso legal

Base de código: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) e [shadPS4](https://github.com/shadps4-emu/shadPS4) o fork [shadPS4-Infamous-FixBuild](https://github.com/rayhlancaner-png/shadPS4-Infamous-FixBuild) (Eye Of The Ruins/rayhlancaner-png, TOXIC-KID, 0xDeftones) e o port nativo [ShadowOfTheColossus-PC](https://github.com/AjncSystem/ShadowOfTheColossus-PC) (AjncSystem; com partes do Pink-shadPS4 de luizgustavs), todos GPL-2.0, assim como este projeto ([LICENSE](port/LICENSE)). Áudio ATRAC9 via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9); fontes via [FreeType](https://freetype.org).

Este projeto não tem vínculo com a Sony Interactive Entertainment ou a Sucker Punch Productions. inFAMOUS é marca da Sony Interactive Entertainment. Nenhum código, arquivo ou arte do jogo é distribuído aqui. O ícone é uma arte original do projeto.

---

<a id="english"></a>

# inFAMOUS Second Son — native PC port

> **Playable, in development.** The game boots, reaches gameplay and gets through the first chapters, but performance is still unstable (20–30 FPS typical on an RTX 2060) and there are known graphics glitches. See the status below.

**inFAMOUS Second Son** (PS4, CUSA00223, base game 1.00 + update 1.07) running on PC without a CPU emulator: the game's original code runs natively on the processor, the PS4 system is reimplemented, and the GPU is translated to Vulkan. It uses the same core as the [The Last Guardian](https://github.com/HayatoG/tlg_pc) and [Gravity Rush 2](https://github.com/HayatoG/gr2_pc) ports.

> **No game files come with this project.** To play, you need your own copy, dumped from your own PS4.

By **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

The screenshots are at the top of this page.

## What's new

- **CPUs without F16C (Sandy Bridge, #51):** the game's 13 half-precision conversions (`VCVTPH2PS`/`VCVTPS2PH`) are now emulated at start, bit-exact with the CPU (rounding, denormals, Inf and NaN). The game used to stop with "13 sites use encodings the rewrite cannot emulate".
- **Mouse:** the mouse turns the camera (right stick) and also plays the **touchpad**. Left = R2, right = L2, middle = R3. **Hold Left Ctrl (or the X1 side button)** and the mouse becomes a finger on the touchpad: left touches/clicks (hold = absorb a power), dragging with the left slides (the "Open Door" swipe, the scanner), right = two fingers (lift the car off Reggie). The window captures the mouse; Esc releases it and a click captures it again. See [Mouse](#mouse-1).
- **Graffiti steps on screen:** the first time sensor mode turns on, a screen in the middle shows the steps (shake, spray, aim, leave) with your controller's buttons; "Got it" closes it. The Insert menu has a new **Controls** tab that shows it again and sets the **graffiti aiming speed** (25–200%, also `ISS_SENSOR_AIM`).
- **Easier graffiti (sensor mode):** sensor mode is now the graffiti's spray can: turning it on (L3+R3) holds the controller on its side, as the game asks ("Hold Wireless Controller Sideways"); **cross/A shakes**, **R2 sprays** and the **left stick aims** the cursor left/right and up/down (it used to move only up and down), slower with a small push, for tracing the stencil. On the keyboard, while T or G hold the controller sideways, the **arrow keys** aim.
- **Being tested: flickering GPU smoke and particles (#7, #50).** Shader recompiler fixes, partly from the native [Shadow of the Colossus](https://github.com/AjncSystem/ShadowOfTheColossus-PC) port:
  - shared memory (LDS) barriers in compute shaders of every workgroup size, including those that are not multiples of 64 (96, 192...): `ISS_LDS_SMALL` (under 64 threads), `ISS_LDS_MULTI` (over 64; on 32-lane GPUs the barrier covers the whole workgroup, because each 64-lane PS4 wave takes two subgroups), `ISS_LDS_READLANE`;
  - `ISS_LANE_DIVERGENCE`: branches that depend on `v_mbcnt`, the lane number or an atomic's returned value count as divergent, so no barrier lands inside a branch only one lane takes;
  - `S_WQM_B64`, which did nothing (`ISS_WQM`).
  - All on by default in inFAMOUS; `0` turns each one off, for comparisons. The log has one `shader switch` line per switch.
  - Experiment, off: `ISS_RFL_ALL=1` makes `ReadFirstLane` read the first lane of the whole 64-lane wave in every wide compute shader (not only those that use ballots).
  - The shader cache rebuilds itself for each combination.
- **Fixes from [shadPS4-Infamous-FixBuild](https://github.com/rayhlancaner-png/shadPS4-Infamous-FixBuild):**
  - **Delsin's glow while draining energy fixed:** stencil now honors both the test and the write values, which are separate on PS4.
  - **More FPS:** when the game reads GPU results, only the thread that asked waits, not the whole GPU (`ISS_DEFERRED_READBACK`, on by default), and work goes to the GPU in pieces (`ISS_SUBMIT_DRAWS`, default 1024).
  - **Fewer hitches when a new effect shows up:** compute shaders compile off the GPU thread (`ISS_COMPUTE_ASYNC_BUILD`), and pipeline creation is retried when the driver fails.
  - **VRAM:** when video memory runs short, the port frees old textures and tries again instead of closing. Huge uploads, such as loading a save, go in parts, and the driver may page memory out to RAM.
  - **Float atomics** fixed on GPUs without native support, such as NVIDIA.
- **Motion sensor:** the DualShock 4/DualSense gyro works as is. On controllers without one, a tap on L3+R3 (or Share on an Xbox Series) toggles "sensor mode", the graffiti's spray can: the controller is held on its side, cross/A shakes, R2 sprays and the left stick aims. On the keyboard, T/G turn it sideways (the arrow keys aim while they are held) and Y shakes. This is what gets you past the graffiti ("Hold Wireless Controller Sideways").
- **Sticks:** a 10% dead zone against drift (`ISS_STICK_DEADZONE`, also in the launcher), and the last controller used is the one that counts.
- **Touchpad without a touchpad:** hold View/Select (or Tab) and move the right stick (or the arrow keys) to swipe, as in "Open Door"; a quick tap still clicks.
- **Performance:** FPS no longer drops over time (it went from 60 to 6 in 2 minutes: shader variants were never reused), and repeated partial image transitions are skipped.
- **Precise GPU readbacks by default:** the energy-drain smoke, drones and other GPU-computed particles show up. The fast mode is still in the launcher ("GPU accuracy").
- **Automatic shader cache:** it lives in `user/cache/`, next to the saves (Linux and Windows; the old cache in `~/.local/share/shadPS4` or `user/user/` is moved over on the first start). The folder is keyed by the shader recompiler version, and the old cache is deleted on its own after an update. To rebuild everything, the launcher has a **Clear shader cache** button (or `./run_infamous.sh --clear-shader-cache`); it deletes only this game's compiled shaders, never saves or settings.

## Status

| Area | State |
|---|---|
| Boot, title, intro and gameplay | ✅ Works; tested up to "Go to Longhouse", with climbing, running, powers and cutscenes |
| Motion sensor (graffiti, motion prompts) | ✅ Real gyro, or simulated on any controller and the keyboard |
| Drain smoke, drones and GPU particles | ✅ With precise GPU readbacks (default) |
| HUD | ✅ Correct |
| Audio | ✅ Our own AudioOut + Ajm, no firmware file needed |
| Saves | ✅ The save is created and "Continue" works |
| Controller | ✅ DualSense, DualShock 4, Xbox and 8BitDo via SDL3 |
| Performance | 🔧 20–30 FPS typical on an RTX 2060, unstable; optimization ongoing |
| Stutter | 🔧 The first time each shader is compiled (cutscenes and new areas) |
| Graphics | 🔧 Some fog, water and light effects flicker |
| Linux | ✅ Tested (Nobara/Fedora 44) |
| Windows | 🧪 Automatic build, not yet tested in game |

![Performance over a 7-minute session walking through the city](docs/screenshots/desempenho.png)

<sub>FPS, worst frame and draws per frame every 5 s, from the port's log (`ISS_FRAME_STATS=1`), on an RTX 2060: median 27 FPS, above 30 FPS 44% of the time. The game has no frame cap. Made with `scripts/session_chart.py` (`0` = uncapped).</sub>

## Download

The [**latest release**](https://github.com/HayatoG/iss_pc/releases/latest) is built by GitHub Actions on every change; older ones stay under [Releases](https://github.com/HayatoG/iss_pc/releases) as history:

- **Linux x86-64** (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 or newer): `infamous-linux-x86_64.tar.gz`
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

**From the console firmware:** nothing. Audio uses our own AudioOut + Ajm; the game imports neither `libSceNgs2` nor any other PS4 system module.

The full list and the step-by-step guide, which also go in the notes of every Release, are in [`docs/ARQUIVOS_NECESSARIOS.md`](docs/ARQUIVOS_NECESSARIOS.md).

**PC:** a graphics card with Vulkan 1.3 (6 GB of VRAM recommended) and ~33 GB free.

## How to play

1. Extract the package.
2. Open **inFAMOUS Second Son**, pick the game folder and the language, and click **Play**. If it stutters too much, the "GPU accuracy" option has a fast mode (without GPU particles).
3. In game, **F10** toggles the FPS counter, and **Insert** (or R3 + L2 on a controller) opens the port's menu.
4. When the game asks you to turn or shake the controller and yours has no sensor: tap L3+R3 (or Share on an Xbox Series). The controller is then on its side; cross/A shakes, R2 sprays and the left stick aims. Tap again to leave. On the keyboard: T/G (with the arrow keys to aim) and Y. See [Motion sensor and touchpad](#motion-sensor-and-touchpad).

The full guide is in [`README-player.md`](port/packaging/README-player.md), which also ships inside the package.

**Experimental fixes:** the launcher's **Experimental fixes…** button turns the 12 fixes `TLG_BP01` to `TLG_BP12` (from other PS4 ports and shadPS4), the diagnostic switches (`TLG_WQM`, `TLG_LDS_*`, `TLG_BC_TINY`...) and the Insert menu options on and off, tagged "in game" or "restarts the game". Untouched, the defaults hold. Full list: [`docs/EXPERIMENTAL_FIXES.md`](docs/EXPERIMENTAL_FIXES.md).

## Mouse

The mouse works with or without a controller (its buttons add to the controller's). The game window captures the mouse while it has focus and the Insert menu is closed; **Esc releases it** (the cursor comes back) and **a click in the window captures it again** (that click is not a game button).

**Camera and buttons:**

| Mouse | In the game |
|---|---|
| Move | turns the camera (right stick) |
| Left button | R2 (use the power / shoot) |
| Right button | L2 (aim) |
| Middle button | R3 |
| Side buttons X1 / X2 and the wheel | free (see `ISS_KEY_MAP`); X1 is also a touchpad-mode key |
| Sensor on (sensor mode, T or G) | the mouse points the graffiti spray can instead of turning the camera |

**Touchpad mode:** hold **Left Ctrl** or the mouse's **X1 side button**. While the mode is on the camera does not turn: mouse motion moves a virtual finger over the touchpad (a small pad in the bottom-left corner of the screen shows where it is) and the buttons become the finger:

| Gesture (mouse in touchpad mode) | What the game sees | Where to use it |
|---|---|---|
| Just move | hovering finger (no touch): places the finger | before a gesture |
| Left, quick tap | touch + touchpad click | "press the touchpad" interactions |
| Left, hold still | touch + click held | absorbing/draining powers (smoke, neon...) |
| Left, drag more than 80 units | the click is released and the finger slides | "Open Door", hand scanner |
| Middle button (hold and move) | finger with no click | sliding without a click, if a gesture dislikes the click |
| Right | two fingers on both ends with the touchpad pressed | lifting the car off Reggie |

The finger starts in the middle of the touchpad and stays where you leave it. The keyboard shortcuts (Tab/Backspace, Tab + arrow keys) work as before.

**Environment variables** (`ISS_` and `TLG_` work the same; the `mouse_*` ones can also go in `tlg.ini`):

| Variable | Default | What it does |
|---|---|---|
| `ISS_MOUSE` | `1` | `0` turns the mouse off (the window no longer captures it) |
| `ISS_MOUSE_SENS` | `1.0` | camera sensitivity (0.05-10) |
| `ISS_MOUSE_INVERT_Y` | `0` | `1` inverts the Y axis |
| `ISS_MOUSE_SMOOTHING` | `0.5` | smoothing (0-0.95) |
| `ISS_MOUSE_ACCEL` | `0` | acceleration (0-2) |
| `ISS_MOUSE_DEADZONE` | `0.1` | anti-dead zone: small movements skip the game's dead zone (0-0.5) |
| `ISS_MOUSE_PAD` | `1` | `0` turns the mouse touchpad mode off |
| `ISS_MOUSE_PAD_KEY` | `Left Ctrl\|Mouse X1` | touchpad-mode key(s); SDL key names or `Mouse Left/Middle/Right/X1/X2`, separated by `\|` |
| `ISS_MOUSE_PAD_MODE` | `hold` | `toggle`: one press turns it on, another turns it off |
| `ISS_MOUSE_PAD_SENS` | `1.0` | finger speed (0.1-10) |
| `ISS_MOUSE_PAD_DRAG` | `80` | units (the touchpad is 1920 wide) of drag before the click becomes a swipe; `0` = never |
| `ISS_KEY_MAP` | — | remaps keys and mouse: `"r2=Mouse Left\|F,l2=Mouse Right\|R,r1=Mouse X2,l1=Wheel Down"`; several per button with `\|`, `none` removes all |
| `ISS_MOUSE_LOG` | `0` | `1` logs what the game gets from the mouse |

The Insert menu's **Controls** tab has the mouse camera settings.

### Where your saves live and how to update without losing them

By default saves and settings live in `user/`, next to the game. **Updating deletes nothing**, but if you extract the new zip somewhere else (or delete the old folder) the game opens without saves: they are still in the old folder, under `user/savedata`. To never go through that again, open the Qt launcher, go to **Saves & data** and pick a fixed folder outside the game (suggestion: `Documents\inFAMOUS-PC` on Windows, `~/.local/share/infamous-pc` on Linux); the launcher copies your saves there and keeps the choice in a per-user file (`%APPDATA%\inFAMOUS-PC\launcher.json` / `~/.config/infamous-pc/launcher.json`) that survives reinstalls. The same screen finds saves in other port folders, imports and exports `.zip`, and makes backups (also before every play session). The `ISS_USER_DIR` variable overrides everything.

## Motion sensor and touchpad

The game asks for the motion sensor and the touchpad in many scenes: graffiti, absorbing powers (smoke, neon...), opening doors and other interactions. On a **DualShock 4 or DualSense** the gyro and the touchpad work as is, with nothing to turn on. On other controllers and on the keyboard, the port simulates both.

**Sensor mode (turning it on and off):**
- **One tap on L3+R3 together** turns sensor mode on; another tap turns it off. It works on any controller. The controller's extra button works too: **Share** on an Xbox Series, **Capture** on a Switch Pro and the **microphone** button on a DualSense. On a DualShock 4 or DualSense, Share/Create does **not** toggle sensor mode: it is the touchpad click.
- A notice on screen confirms it: "Sensor mode ON (spray can): cross shakes, R2 sprays, left stick aims" or "Sensor mode off".
- While it is on, the controller is **on its side**, like a spray can (what the graffiti asks for), **cross/A shakes** and the **left stick aims**, pointing the can left/right and up/down (this moves the graffiti cursor; it stays where you let go; a small push is slow, for tracing the stencil; the right stick works too). R2 still sprays. The sticks and cross/A are hidden from the game, so Delsin neither walks nor jumps and the camera does not turn: **turn the mode off after the scene**. L3+R3 together never reaches the game either.
- While it is on, the simulated tilt replaces the real gyro.
- **Keyboard** (no mode needed, any time): hold **T** or **G** to turn the controller sideways (one side or the other) and **Y** to shake it.

**Touchpad on a controller without one:**
- **View/Select/Back** is the touchpad click (right side; with L1 held, the left side). Holding the button holds the touchpad.
- **Hold View/Select and move the right stick** to swipe a finger from the middle of the touchpad. A quick tap without moving still clicks.
- **Keyboard:** Tab (left side) and Backspace (right side) click; **hold Tab and use the arrow keys** to swipe.
- **Two fingers on both ends of the touchpad** (lifting the car off Reggie): **hold View/Select + R1**; on the keyboard, **hold Tab + Backspace**.

| In-game action | DualShock 4 / DualSense | Xbox / other controller | Keyboard |
|---|---|---|---|
| Absorb/drain a power (smoke, neon...) and "hold the touchpad" interactions | hold the touchpad | hold View/Select (leave the right stick alone, or it becomes a swipe) | hold Tab or Backspace (no arrow keys); mouse: Left Ctrl (or X1) + hold the left button still |
| "Press the touchpad" interactions | click the touchpad | tap View/Select | Tab or Backspace |
| Graffiti: turn the controller sideways | turn the controller | L3+R3 (sensor mode): it is on its side at once | hold T or G |
| Graffiti: shake the can | shake the controller | cross/A in sensor mode | Y |
| Graffiti: spray | R2, aiming with the controller | R2, aiming with the left stick in sensor mode | F (R2), aiming with the arrow keys while holding T or G |
| Press both ends of the touchpad (lifting the car off Reggie) | two fingers, one on each end | hold View/Select + R1 | hold Tab + Backspace; mouse: Left Ctrl (or X1) + right button |
| Touchpad swipe ("Open Door", hand scanner) | swipe a finger | hold View/Select + right stick in the asked direction | hold Tab + arrow keys; mouse: hold Left Ctrl (or X1), left button and drag |
| Back to normal after the graffiti | — | L3+R3 again ("Sensor mode off") | — |

**Launcher:** the **Controller** box has the **Stick dead zone** (0–40%, default 10%). Raise it if the character, the camera or the sensor-mode tilt moves on its own (stick drift).

**Environment variables:** `ISS_MOTION_BUTTON=<SDL button>` changes the sensor-mode button (default `misc1`; L3+R3 always works), and `ISS_MOTION=off` ignores the real gyro (the simulation still works).

**Intel CPUs:** the game's code uses SSE4A instructions (EXTRQ), which only AMD CPUs have. On Intel the port replaces them with an emulation at start (needs `iced-x86`, included in the packages). Older CPUs (Sandy and Ivy Bridge) also lack MOVBE, F16C, BMI1 or LZCNT, which are emulated the same way; AVX is still required. `ISS_ISA_REWRITE=sse4a` (or `f16c`, or a list such as `f16c,movbe`) forces the emulation on a CPU that has the instruction (testing), `ISS_ISA_REWRITE=1` forces every emulated set (MOVBE, BMI1, LZCNT, F16C, SSE4A) and `ISS_ISA_REWRITE=0` turns it off. Details: [port/docs/isa_rewrite.md](port/docs/isa_rewrite.md).

**Windows red-zone protection.** PS4 code keeps variables in the 128 bytes below `rsp` (the "red zone"), and Windows writes there on every exception (the port uses exceptions to track GPU memory). At start the port rewrites the memory instructions of the functions that use the red zone so they run with `rsp` 128 bytes lower (crash at `0x1cfaaf`, #29/#41). On by default on Windows; `ISS_RED_ZONE_REWRITE=0` turns it off and `ISS_RED_ZONE_REWRITE=1` turns it on on Linux (testing). Linux test: `TLG_CLOBBER_RED_ZONE=<bytes>` zeroes that many bytes below `rsp` on every exception, like Windows (`1` = 128). Details: [port/docs/red_zone.md](port/docs/red_zone.md).

**Frozen screen:** if the game shows no new frame for 10 s, the log (`out/last_run.log`) gets a `FREEZE: no frame for 10 s; threads:` block with every thread of the game, what it is waiting on (mutex, semaphore, event queue, file read, GPU...) and where it is in the code. The game keeps running, and the report only repeats after frames resume and stop again. Send that log with the report. `ISS_FREEZE_REPORT_SECONDS=<s>` changes the time (`0` turns it off).

**AMD cards on Windows (RX 580): tiny BC textures.** AMD's Windows driver (`amdvlk64.dll`) crashes right after the logos (`Fault: write access to 0 at amdvlk64.dll+0xebbbb`, #16/#31/#49) on the game's first BC-compressed 1D texture (512x1), whether it is created 1D or 2D. On AMD's driver the port decodes BC1–BC5 textures that are 1D or smaller than a 4x4 block on the CPU and gives the driver plain images (RGBA8, R8 or RG8, sRGB and snorm kept); the log line `GPU: tiny block-compressed textures ...` says which mode is on. `ISS_BC_TINY=0` turns it off and `ISS_BC_TINY=1` turns it on on any GPU (testing).

## Building from source

```bash
git clone --recursive https://github.com/HayatoG/iss_pc.git && cd iss_pc
cd port && ISS_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, FreeType, Boost, fmt, Zydis, glslang
cd .. && ./infamous_launcher.sh        # or ./run_infamous.sh from a terminal
```

On Windows, the build runs in MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). The workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) shows the full process on both platforms.

## How it works

| Layer | What it does | Based on |
|---|---|---|
| Loader | Loads the 1.07 `eboot.bin` and links the game's own modules (`libc`, `Fios2`) | [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) |
| Runtime | Reimplements the PS4 libraries (NpManager, Trophy, Http, PlayGo, SaveData, AppContent, AudioOut, Ajm...). inFAMOUS-specific: `port/src/runtime_infamous.c` | `port/src/` |
| Video | Translates Gnm commands and GCN shaders to Vulkan/SPIR-V | [shadPS4](https://github.com/shadps4-emu/shadPS4) video core |

## Next steps

What is left is in [`docs/ROADMAP.md`](docs/ROADMAP.md): performance (waits on GPU readbacks), an on-disk pipeline cache against the stutter, the flickering effects, the drone-drain glow and the game languages in the launcher.

## Credits and legal notice

Code base: [tlg_pc](https://github.com/HayatoG/tlg_pc), [gr2_pc](https://github.com/HayatoG/gr2_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) and [shadPS4](https://github.com/shadps4-emu/shadPS4) the [shadPS4-Infamous-FixBuild](https://github.com/rayhlancaner-png/shadPS4-Infamous-FixBuild) fork (Eye Of The Ruins/rayhlancaner-png, TOXIC-KID, 0xDeftones) and the native [ShadowOfTheColossus-PC](https://github.com/AjncSystem/ShadowOfTheColossus-PC) port (AjncSystem; with parts of Pink-shadPS4 by luizgustavs), all GPL-2.0, as is this project ([LICENSE](port/LICENSE)). ATRAC9 audio via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9); fonts via [FreeType](https://freetype.org).

This project is not affiliated with Sony Interactive Entertainment or Sucker Punch Productions. inFAMOUS is a trademark of Sony Interactive Entertainment. No game code, files or art are distributed here. The icon is original artwork made for this project.
