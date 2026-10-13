# Gravity Rush 2 PC: roadmap

Plano de recursos do port de Gravity Rush 2 (CUSA03694), no mesmo nível do The Last Guardian e do God of War III.
Repositório local, ainda sem GitHub (privado quando for criado). Criado em 13/10/2026.

## Onde estamos

| Área | Estado |
|---|---|
| Boot, abertura com créditos e legendas | ✅ Roda a 30 FPS em 1080p (RTX 2060, Linux) |
| Imports do sistema | ✅ 863/863 cobertas (runtime_gr2*.c, NpToolkit offline, Json2, FreeType) |
| Áudio | 🔧 Audio3d em implementação (sem som hoje) |
| Menu, gameplay, saves | ⏳ Testando |
| Update 1.11 | ⏳ Falta dumpar o patch (falhou no Itemzflow) |

## Planejado

Cada item vira uma issue quando o repositório existir. A ordem é uma sugestão.

### 1. Jogar do início ao fim
- [ ] Menu inicial, novo jogo, gameplay e saves (autosave e carregar)
- [ ] Áudio completo (Audio3d + NGS2 nativo + AudioOut)
- [ ] Vídeos (AvPlayer), se o jogo usar fora dos créditos
- [ ] Trocar para o eboot 1.11 quando o patch for dumpado (refazer a análise no Ghidra e revisar endereços)
- [ ] Corrigir os bugs gráficos que aparecerem; o modo de readback preciso é o padrão

### 2. Launcher (igual ao do TLG)
- [ ] Launcher horizontal em Tkinter, **bilíngue (pt_BR e en_US)**, com arte lida do dump do usuário e ícone próprio
- [ ] **Idioma do jogo escolhido no launcher** (`TLG_LANGUAGE` → id de idioma do PS4; o GR2 tem legendas em vários idiomas)
- [ ] Pasta do jogo, módulos do console, modo de tela, VSync, orçamento de VRAM, overlay de FPS
- [ ] Logs por sessão e atalhos para as pastas de saves e logs
- [ ] Créditos com YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) e Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

### 3. Controles
- [ ] Controle (SDL3: DualSense, DualShock 4, Xbox, 8BitDo) — já funciona pelo runtime herdado
- [ ] **Teclado e mouse**: a câmera e a mira da gravidade no mouse; layout pensado para o GR2 (gravidade, queda, chute); remapeamento no launcher
- [ ] Giroscópio do DualSense/DS4 (o GR2 usa sensor de movimento para mirar)
- [ ] Touchpad (o GR2 usa gestos no touchpad)

### 4. Imagem e desempenho (como no TLG e no GoW3)
- [ ] **60 FPS e FPS livre** (achar a trava de 30 e o passo de tempo do motor)
- [ ] **Resolução interna** configurável (abaixo e acima de 1080p)
- [ ] **FSR 3/4 e DLSS** usando o TAA do próprio jogo (não o gancho do GoW3)
- [ ] Pós-processamento: AA (SMAA/FXAA), nitidez, cor
- [ ] Ligar e desligar efeitos (motion blur, DOF, granulação)
- [ ] Overlay de FPS (F10) e menu do port (Insert), bilíngues

### 5. Plataformas e distribuição
- [ ] **Linux**: pacote `.tar.gz` com as bibliotecas (glibc 2.39+); Flatpak para distros antigas
- [ ] **Windows**: build MSYS2 CLANG64, launcher congelado com PyInstaller, `.zip`
- [ ] **macOS (Apple Silicon)**: Rosetta 2 + MoltenVK, mesmo plano da issue #1 do TLG
- [ ] GitHub Actions com a Release nightly substituída a cada build (só quando o repositório for criado e o usuário liberar)
- [ ] Importar o jogo de fake PKG, além do dump da pasta (issue #9 do TLG)

## O que vem do TLG

As melhorias do TLG entram no GR2 por cherry-pick, pelo remote `tlg`:
- o launcher, o overlay e o empacotamento;
- a CI;
- as correções do núcleo de vídeo (readback preciso, scheduler, leituras completas).

As correções do GR2 que servem aos dois jogos voltam para o TLG, como a da captura de shader com página protegida.
