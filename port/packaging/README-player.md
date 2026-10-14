# inFAMOUS Second Son — port para PC / PC port

Por HayatoG · YouTube: [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord: [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g) · Código: [github.com/HayatoG/infamous_pc](https://github.com/HayatoG/infamous_pc)

**Nenhum arquivo do jogo vem neste pacote.** Você precisa da sua própria cópia de inFAMOUS Second Son para PS4. / **No game files are included.** You need your own copy of inFAMOUS Second Son for PS4.

Versão de desenvolvimento: **o jogo ainda não inicia.** / Development build: **the game does not boot yet.**

---

## Português

### Arquivos do jogo necessários

Tudo vem do **seu** PS4 (GoldHEN + Itemzflow). Nada disso vai no download. Use **inFAMOUS Second Son CUSA00223 (EUA), jogo base 1.00 com o update 1.07**, montado numa pasta só, com o jogo base e o update por cima. São ~33 GB.

| Arquivo | Vem de | Para quê |
|---|---|---|
| `eboot.bin` | update 1.07 | o código do jogo (tem que ser o do 1.07) |
| `sce_module/libc.prx`, `sce_module/libSceFios2.prx` | update 1.07 | bibliotecas do próprio jogo |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic1.png`) | jogo base (+ `param.sfo` do update) | metadados, instalação e a arte do launcher |
| `art/` (`cache/`, `movies/`, `ui/`) | base + update | conteúdo do jogo |
| `playgo.pgm`, `sce_discmap.plt`, `sce_discmap_patch.plt` | base + update | mapa de arquivos e instalação |

**Do firmware do console:** nada. A pasta `system_lib/` fica vazia.

**Como montar a pasta:**
1. No Itemzflow, faça o dump do jogo (`CUSA00223`) e do update (`CUSA00223-patch`) para um pendrive exFAT.
2. No PC, copie a pasta do jogo base e depois copie o conteúdo do update **por cima**, substituindo os arquivos.
3. O `param.sfo` da versão 1.07 fica no PS4 em `/system_data/priv/appmeta/CUSA00223/param.sfo`: copie para o `sce_sys/` da pasta montada.

**PC:** Windows 10 (1903+)/11 64 bits ou Linux x86-64 (glibc 2.39+), placa de vídeo com Vulkan 1.3 (6 GB de VRAM recomendados).

### Como jogar

1. Extraia o pacote numa pasta qualquer (no Windows, fora do .zip).
2. Abra **inFAMOUS Second Son** (`inFAMOUS Second Son.exe` no Windows). No Windows, se aparecer "O Windows protegeu o computador", clique em *Mais informações* e depois em *Executar assim mesmo*. O programa não é assinado digitalmente.
3. Em **Pasta do jogo**, escolha a pasta que tem o `eboot.bin`. Escolha o idioma e clique em **Jogar**.

No Linux, `./install_desktop.sh` adiciona o jogo ao menu de aplicativos.

### Durante o jogo
- **F10**: contador de FPS · **Insert** (ou R3 + L2): menu do port
- Controles de PS4/PS5, Xbox e 8BitDo via SDL3, por USB ou Bluetooth.

### Sensor de movimento e touchpad
Para o grafite, absorver poderes (fumaça, neon...), abrir portas e outras cenas de sensor ou touchpad. No DualShock 4/DualSense, o giroscópio e o touchpad funcionam direto.
- **Modo sensor:** um toque em **L3+R3** juntos liga, outro toque desliga (ou Share no Xbox Series, Capture no Switch Pro, microfone no DualSense). Ligado, ele é a lata de spray do grafite: o controle fica **de lado**, **X/A sacode**, **R2 pinta** e o **analógico esquerdo mira** (o cursor do grafite); o Delsin não anda nem pula, então desligue depois da cena. Um aviso na tela mostra o estado.
- **Touchpad:** **View/Select** clica (segurar = segurar o touchpad, para absorver poderes); **segure View/Select + analógico direito** para deslizar (porta "Open Door", scanner de mão).
- **Teclado:** **T/G** viram o controle de lado (enquanto seguram, as **setas** miram), **Y** sacode, **F** é o R2 (pintar); **Tab/Backspace** clicam o touchpad, **Tab + setas** deslizam.
- **Launcher:** "Zona morta dos analógicos" (padrão 10%), se algo se mexer sozinho.

### Problemas
- **Não abre ou fecha sozinho**: é o esperado nesta fase. Mande o `out/last_run.log` no [Discord](https://discord.gg/UMkdMYZh9g) ou numa [issue](https://github.com/HayatoG/infamous_pc/issues) se quiser ajudar.
- **Tela congelada (o jogo para, a janela continua aberta)**: depois de 10 s sem quadro novo, o `out/last_run.log` recebe um bloco `FREEZE:` com o que cada thread está esperando. Feche o jogo e mande esse log. `ISS_FREEZE_REPORT_SECONDS` muda o tempo (`0` desliga).

---

## English

### Required game files

Everything comes from **your own** PS4 (GoldHEN + Itemzflow). None of it is in the download. Use **inFAMOUS Second Son CUSA00223 (US), base game 1.00 with update 1.07**, merged into one folder, with the base game and the update on top. About 33 GB.

| File | From | Purpose |
|---|---|---|
| `eboot.bin` | update 1.07 | the game code (must be the 1.07 one) |
| `sce_module/libc.prx`, `sce_module/libSceFios2.prx` | update 1.07 | the game's own libraries |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic1.png`) | base game (+ the update's `param.sfo`) | metadata, install info and the launcher art |
| `art/` (`cache/`, `movies/`, `ui/`) | base + update | game content |
| `playgo.pgm`, `sce_discmap.plt`, `sce_discmap_patch.plt` | base + update | file map and install info |

**From the console firmware:** nothing. The `system_lib/` folder stays empty.

**How to build the folder:**
1. In Itemzflow, dump the game (`CUSA00223`) and the update (`CUSA00223-patch`) to an exFAT USB drive.
2. On the PC, copy the base game folder, then copy the update's contents **over it**, replacing files.
3. The 1.07 `param.sfo` is at `/system_data/priv/appmeta/CUSA00223/param.sfo` on the PS4: copy it into the merged folder's `sce_sys/`.

**PC:** 64-bit Windows 10 (1903+)/11 or x86-64 Linux (glibc 2.39+), a graphics card with Vulkan 1.3 (6 GB of VRAM recommended).

### How to play

1. Extract the package anywhere (on Windows, outside the .zip).
2. Open **inFAMOUS Second Son** (`inFAMOUS Second Son.exe` on Windows). On Windows, if "Windows protected your PC" appears, click *More info*, then *Run anyway*. The program is not digitally signed.
3. Under **Game folder**, choose the folder that has `eboot.bin`. Pick the language and click **Play**.

On Linux, `./install_desktop.sh` adds the game to the applications menu.

### While playing
- **F10**: FPS counter · **Insert** (or R3 + L2): the port's menu
- PS4/PS5, Xbox and 8BitDo controllers via SDL3, over USB or Bluetooth.

### Motion sensor and touchpad
For the graffiti, absorbing powers (smoke, neon...), opening doors and other sensor or touchpad scenes. On a DualShock 4/DualSense, the gyro and the touchpad work as is.
- **Sensor mode:** one tap on **L3+R3** together turns it on, another turns it off (or Share on an Xbox Series, Capture on a Switch Pro, the microphone button on a DualSense). While on, it is the graffiti's spray can: the controller is **on its side**, **cross/A shakes**, **R2 sprays** and the **left stick aims** (the graffiti cursor); Delsin neither walks nor jumps, so turn it off after the scene. A notice on screen shows the state.
- **Touchpad:** **View/Select** clicks (hold = hold the touchpad, to absorb powers); **hold View/Select + right stick** to swipe ("Open Door", hand scanner).
- **Keyboard:** **T/G** turn the controller sideways (while held, the **arrow keys** aim), **Y** shakes, **F** is R2 (spray); **Tab/Backspace** click the touchpad, **Tab + arrow keys** swipe.
- **Launcher:** "Stick dead zone" (default 10%), if something moves on its own.

### Problems
- **Does not start or closes by itself**: expected at this stage. Send `out/last_run.log` on [Discord](https://discord.gg/UMkdMYZh9g) or in an [issue](https://github.com/HayatoG/infamous_pc/issues) if you want to help.
- **Frozen screen (the game stops, the window stays open)**: after 10 s without a new frame, `out/last_run.log` gets a `FREEZE:` block with what each thread is waiting on. Close the game and send that log. `ISS_FREEZE_REPORT_SECONDS` changes the time (`0` turns it off).

---

This project is not affiliated with Sony Interactive Entertainment or Sucker Punch Productions. inFAMOUS is a trademark of Sony Interactive Entertainment. / Este projeto não tem vínculo com a Sony Interactive Entertainment ou a Sucker Punch Productions.
