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

## Saves e dados

Entrada **Saves e dados** no trilho (destaque verde). O problema que resolve: com os dados em `<pasta do port>/user`, quem atualiza extraindo o zip em outra pasta (ou dentro da antiga, ou apagando a antiga) abre o jogo sem saves e acha que a atualização os apagou. A atualização nunca apaga nada (o zip não traz `user/`), mas os saves ficaram na pasta antiga.

**Pasta de dados** (`infamous_run.user_dir()`, regras em `launcher/userdata.py`), nesta ordem:

1. variável de ambiente `ISS_USER_DIR` (`TLG_USER_DIR` ainda vale);
2. arquivo-ponteiro por usuário, **fora** da pasta do jogo: Windows `%APPDATA%\inFAMOUS-PC\launcher.json`, Linux `$XDG_CONFIG_HOME/infamous-pc/launcher.json` (chaves `user_dir`, `backup_extra_dir`, `backup_keep`);
3. `<pasta do port>/user` (modo portátil, como sempre foi).

O mesmo valor vai para `--user`, `ISS_CONFIG` (`tlg.ini`), `TLG_GPU_USER_DIR`/cache de shaders, backups e lista de saves, nos launchers Qt e Tk e em `run.py`. Sugestões estáveis: `Documentos\inFAMOUS-PC` (Windows) e `~/.local/share/infamous-pc` (Linux).

**Mudar a pasta** copia, nunca move: se a antiga tem saves e a nova está vazia, o launcher pergunta "Copiar os saves e configurações para a nova pasta?" (saves, backups e `tlg.ini`; o cache de shaders é refeito). Confere espaço, copia para um nome temporário e renomeia; nada é apagado da pasta antiga. Com `ISS_USER_DIR` definida a escolha fica travada na tela.

**Saves de outras instalações:** uma varredura limitada (profundidade, número de pastas e 8 s) em Downloads, Área de Trabalho, Documentos, home, `C:\Games`, `D:\`..., pastas irmãs e pais da atual, incluindo pasta-dentro-de-pasta (`infamous-windows-x86_64\infamous-windows-x86_64\user`). Mostra "Encontramos saves em ... Importar?" na tela e um aviso no Início quando a pasta atual não tem saves.

**Lista de saves:** um cartão por slot (`infamousssAuto0/1`, `infamousssUser0..N`) com o título de `param.bin` (subtítulo: capítulo, karma, %), data, tamanho e a miniatura `icon0.png` do próprio save (lida na hora; nada é copiado para o repositório). Ações: exportar `.zip`, duplicar (para o próximo `infamousssUserN`), excluir. Barra superior: **Fazer backup agora** (todos os saves), importar `.zip`, exportar tudo.

**Backups:** lista de `savedata_backups` (data, quantidade de saves, tamanho) com **Restaurar**; manter os últimos N (padrão 10) e **pasta extra de backup** (outro disco) que recebe uma cópia de cada backup. Um backup é feito antes de toda partida (pulado se nada mudou desde o último).

**Segurança** (`launcher/savemanager.py`, testes em `test_savemanager.py`, `test_userdata.py`, `test_qt_saves.py`):

- toda operação que pode substituir ou apagar um save passa por `guarded()`/`backup_now()`: o jogo não pode estar rodando (processo `tlg-probe`), o backup de segurança é feito antes (e copiado para a pasta extra); se o backup falhar, nada muda;
- copiar para temporário e renomear; troca de slot com desfazer em caso de erro; restauração troca por renomeações;
- `.zip` validado antes de escrever qualquer byte: estrutura `savedata/<usuario>/CUSA00223/<slot>[.sce_sys]/...` (até 2 pastas de embrulho), recusa total de `../`, caminho absoluto, `C:`, links e tamanhos absurdos (5000 arquivos / 1 GiB); nunca sobrescreve sem perguntar (a tela lista "novo" e "substitui seu ... por ...");
- erros (permissão, disco cheio) viram mensagens claras em pt-BR/en-US; com o jogo aberto as ações que escrevem em `savedata` ficam desativadas.

Formato do `param.bin` lido: `title[128]`, `subtitle[128]`, `detail[1024]`, tempo de 64 bits em `0x508` (também lê PSF `param.sfo`).

## Suporte e Atualizações

**Suporte** (ciano) tem três blocos. *Problemas conhecidos para a sua GPU*: tabela local em `qt/data/known_issues.json` (GPU/fabricante/driver/SO/VRAM e o que fazer; as que casam com a GPU detectada ficam no topo, as outras atrás de um botão). *Relatar um problema*, em 3 passos: (1) coleta local: GPU, driver e VRAM (`vulkaninfo`, com o mesmo ambiente do jogo), SO, CPU com SSE4A/AVX2/F16C (`/proc/cpuinfo`; no Windows a sonda `tlg-probe --cpu-features`), RAM, versão do port (arquivo `VERSION` do pacote, ou o commit da linha `Build:` do último log), jogo (TITLE_ID e APP_VER do `param.sfo`); (2) log: lista `out/logs/run-*.log` (o mais recente vem marcado), mostra o resumo (`Build:`, bloco `Config:`, `Fault:`/`STOP:`/`FREEZE:` e FPS médio) e faz a cópia **redigida**; (3) saída: *Copiar relatório* (markdown), *Salvar .zip* (relatório + log redigido) e *Abrir issue no GitHub* (`webbrowser.open` em `.../issues/new?title=&body=`; corpo acima de 6000 caracteres, ou URL acima de 7500, leva só o resumo e pede para anexar o .zip). Links: Discord, YouTube, GitHub e a pasta de logs.

Redação (`qt/report.py`): o nome em `C:\Users\<nome>`, `/home/<nome>`, `/Users`, `/var/home`, `/run/media` e `/media` vira `<user>`, mais o login/home/hostname desta máquina onde aparecerem soltos; o resto do texto fica igual. O relatório e o log são conferidos de novo antes de gravar o .zip (`leftover_home_paths`): se sobrar caminho pessoal, nada é gravado. **Nenhuma chamada de rede** e nada é enviado sem o clique do jogador.

**Atualizações** (amarelo): versão instalada, *Verificar atualizações* (um único GET HTTPS em `api.github.com/repos/HayatoG/iss_pc/releases/latest`, timeout de 10 s, só o `User-Agent` `iss_pc-launcher/<versão>`; sem dados do jogador), notas da release no idioma da interface (o corpo que o CI gera tem `## Novidades` e `## What's new`; blocos `<!-- notes:pt-BR -->` também são lidos) e *Baixar*, que só abre a página da release. Nada é baixado nem instalado. *Verificar ao abrir* fica **desligado** por padrão (`check_updates_on_open` no `settings.json`). O ponto amarelo do trilho aparece só quando a última versão conhecida (`update_seen` no settings) é mais nova que a instalada. Erros de rede viram mensagens simples (sem internet, demora, limite do GitHub, resposta estranha).

Versão: o pacote agora leva um arquivo `VERSION` com o nome da release (`vAAAA.MM.DD-<commit>`, escrito por `packaging/*/package.sh` quando `GITHUB_SHA` existe). Sem ele, só o commit do `Build:` do log é conhecido e a comparação diz "é outra versão" em vez de "mais nova". Testes: `port/tests/test_qt_support.py` (sem rede: o GET usa um `opener` de teste).

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
