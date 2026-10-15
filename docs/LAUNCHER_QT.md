# Novo launcher (Qt Quick) - fase 1

O novo launcher usa Qt Quick (PySide6) e segue a maquete aprovada: trilho de navegação à esquerda, tela **Início** com o botão **Jogar** e as telas **Correções** (BP01-BP12 e chaves A/B). Gráficos, Controles, Suporte e Atualizações aparecem como "Em breve". O launcher Tk (`infamous_launcher.py`) continua sendo o padrão e funciona como antes.

Ele **não reimplementa nada**: usa `infamous_run.py` (`prepare`, `launch`, `build_env`, `save_experimental`), `backports_table.py`, `shader_cache.py` e `tlg_vulkan.py`. O mesmo `settings.json` e o mesmo `tlg.ini` valem nos dois launchers.

## Como rodar

```bash
python3 -m venv .venv-qt
.venv-qt/bin/pip install -r port/launcher/qt/requirements.txt   # PySide6-Essentials >= 6.7
./infamous_launcher_qt.sh        # ou: python3 port/launcher/infamous_launcher_qt.py
```

No Windows: `py -m venv .venv-qt`, `.venv-qt\Scripts\pip install -r port\launcher\qt\requirements.txt` e `.venv-qt\Scripts\python port\launcher\infamous_launcher_qt.py`. Os argumentos `--play`, `--script` e `--clear-shader-cache` funcionam como no launcher Tk.

Sem PySide6 o ponto de entrada imprime como instalar e sai. As fontes (Big Shoulders Stencil Display e Barlow, licença OFL, arquivos `OFL-*.txt`) ficam em `port/launcher/qt/fonts/` e são carregadas na execução; sem elas, cai a fonte do sistema.

## O que a tela Início lê

| Item | De onde |
|---|---|
| GPU e Vulkan | `vulkaninfo --summary`, com o mesmo ambiente do jogo (`tlg_vulkan.configure`), numa thread |
| Pasta do jogo e versão | `infamous_run.check_game` (aceita só o update 1.07) |
| Perfil | `backports_table.changes`: Recomendado ou personalizado (N mudanças) |
| Cache de shaders | `infamous_run.shader_cache_size` |
| Controle | `/proc/bus/input/devices` (Linux; no Windows o chip diz que não há detecção) |
| Continuar | `param.bin`/`param.sfo` mais recente em `user/savedata` (SUBTITLE e DETAIL); sem save, o botão só diz "Iniciar o jogo" |
| Novidades | as 3 primeiras linhas de "Novidades" do `README.md` (ou texto fixo) |
| Arte do herói | `sce_sys/pic1.png` do dump do jogador, lido em tempo de execução; sem ele, o gradiente de neon e chuva desenhado em `qt/app.py`. Nada da Sony vai para o repositório |

## Estrutura

- `qt/qml/Launcher/Theme.qml`: todas as cores, tamanhos e ícones (um lugar só).
- `qt/logic.py`: lógica sem Qt (textos, chips, novidades, save, grupos de correções); coberta por `port/tests/test_qt_launcher.py`.
- `qt/backend.py`: o objeto que o QML usa (`Backend`).
- `qt/i18n/strings.json`: textos novos em pt-BR e en-US; textos que o Tk já tem (`exp_live`, `exp_recommended`...) são reaproveitados de `infamous_launcher.TEXT`.

## Capturas sem abrir o jogo

```bash
cd port/launcher
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software python3 -m qt.screenshots ../../shots
```

Usa dados de demonstração e uma pasta de configuração temporária; não toca nos seus saves nem no `settings.json`.
