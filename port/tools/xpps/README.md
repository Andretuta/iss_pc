# xpps: índice dos pacotes `.xpps`

Etapa 1 da compilação de shaders na primeira execução. Lê os pacotes KCAP (`.xpps`) do jogo do próprio jogador e grava num SQLite local tudo o que as etapas seguintes precisam: shaders, cabeçalhos Gnm, registros de pass, fetch shaders, efeitos, instâncias de material, objetos textura e malhas.

Só Python com a biblioteca padrão (sem numpy), igual no Windows e no Linux. **Nada do jogo entra no git nem sai da máquina:** o código só descreve a estrutura, e os testes geram KCAP sintético.

*English summary at the end.*

## Como rodar

A partir de `port/tools`:

```sh
python -m xpps.index build <pasta com .xpps> <saida.sqlite> [--jobs N] [--full] [--verify-footers] [--nice]
python -m xpps.index stats <saida.sqlite>
python -m xpps.index sha   <saida.sqlite>
```

- `build` imprime no stdout uma linha `PROGRESS index <n> <total>` por pacote (reaproveitado ou lido), para o launcher. O resto vai para o stderr.
- `--jobs`: processos em paralelo, cada um com um pacote por vez (padrão: até 4).
- **Incremental:** um pacote só é lido de novo quando muda a impressão digital (tamanho + mtime + SHA-256 dos primeiros e últimos 64 KiB). Pacotes que sumiram saem do índice. `--full` ignora o índice anterior.
- O índice é gravado em `<saida>.tmp` e renomeado no fim: se der erro no meio, o anterior continua valendo.
- `--verify-footers` também procura cada `OrbShdr` pela assinatura e confere a regra do início. Isso lê os pacotes inteiros, então só serve para conferência.
- `sha` dá o hash do conteúdo, que não depende dos ids dos arquivos, da hora do build nem do layout do SQLite. Duas varreduras dos mesmos arquivos dão o mesmo valor (também fica em `meta.content_sha`).

Testes: `cd port && python3 -m unittest discover -s tests -p 'test_xpps_index.py'`. O teste com o jogo real só roda se existir `game/CUSA00223/art/cache` (ou `ISS_GAME`).

## Como a leitura funciona

A varredura segue as **tabelas de ligação** (`KNLI`) do pacote em vez de adivinhar ponteiros: um campo só é tratado como ponteiro quando o loader o reloca. Por isso ela lê só as estruturas de CPU e o começo dos shaders, e não os 22 GB de texturas e vértices.

| Módulo | O que lê |
|---|---|
| `kcap.py` | cabeçalho (0x98 B), seções, itens (`tipo << 16 \| alinhamento`) e BSS (itens que passam do fim dos dados) |
| `knli.py` | todas as tabelas `KNLI` (inclusive várias por pacote); relocações por tipo (0 ponteiro de CPU, 2 V#, 3 ponteiro de GPU, 4 endereço de GPU em registrador/T#); `CID` (local → classe); `XLNK` (imports: hash de 16 B → slot); tabela de exports (hash → offset) |
| `gnm.py` | rodapé `OrbShdr`; **início do código = rodapé − 8·(code[1]+1) com code[0] = 0xBEEB03FF**; cabeçalhos VS/PS/CS; InputUsageSlots (VS+0x28, PS+0x3C, CS+0x2C; 4 B `{usageType, apiSlot, startRegister, flags}`); `m_shaderSize`; tamanho do fetch até o `s_setpc_b64` |
| `scan.py` | as entidades abaixo, com os critérios descritos no próprio arquivo |
| `index.py` | SQLite, incremental, resolução dos imports, hash do conteúdo, CLI |

**Base única do registro de pass (0xB8 B):** +0x00 hash de classe, +0x20 início do objeto (entrada CID), +0x28 id do pass, +0x30 fetch, +0x38 VS, +0x40 PS, +0x48/+0x50 IRO do VS/PS (0x138 B), +0x58 lista de bytes, +0x68/+0x78/+0x88/+0x98 pares `{estágio, slot}`, +0xA8 lista de u32.

## Formato do índice (esquema 1)

Offsets relativos aos dados do pacote (`doff` do KCAP). Valores u64 (hashes, classes) ficam como int64 com sinal; hashes de 16 B e estruturas cruas ficam como BLOB.

| Tabela | Conteúdo |
|---|---|
| `schema_version` | versão do esquema (1) |
| `meta` | raiz, contagens, tempo, `content_sha`, resultado da resolução dos imports |
| `files` | `id, path` (com `/`), `size, mtime_ns, fp`, cabeçalho KCAP e estatísticas da varredura (JSON) |
| `shader_occ` | uma linha por cabeçalho Gnm: `hdr_off, code_off, size` (código + rodapé), `stage, hash, footer_off` |
| `shader_hdr` | cabeçalho de cada ocorrência: `common`, `regs` (+0x10 até os slots), `slots`, `semantics` |
| `shaders` | uma linha por hash (primeira ocorrência na ordem dos caminhos), `n_occ`, `n_variants`, `n_hdr_variants` |
| `passes` | `class_hash, cid_class, pass_id, vs, ps, vs_hdr, ps_hdr, fetch_off, fetch_size, iro_vs, iro_ps, list58, list68, list78, smp_pairs` (+0x88), `tex_pairs` (+0x98), `ids_a8` |
| `effects` | `passes_off, n_passes, nmat_tex` (+0x2C), `slot_map` (+0x68), listas +0x90/+0xA0/+0xB0, `smp_desc` (+0xC0), `tex_desc` (+0xD0), `matmap` (+0xE0), `matsmp` (+0xF0) |
| `matinst` | `kind` (`local`, `import`, `unlinked`), `name_hash` (+0x18), efeito (`effect_file/off` ou `effect_import`), `block_off`, `cb_vsharp`, `n_tex`, `tex_hashes`, `tex_list` |
| `textures` | `cid_class, hash` (+0x38), `tsharp` (32 B em +0x18), `fmtword` (+0x40) |
| `meshes` | `matinst_off` (ou `matinst_import`), `n_vsharps`, `vsharps` |
| `imports`, `exports` | tabelas de ligação entre pacotes |
| `footer_check` | só com `--verify-footers`: rodapés achados pela assinatura e quantos têm exatamente um início |

## O que foi medido (CUSA00223 1.07, 1.587 pacotes, 16/10/2026)

| Item | Medido | Esperado / referência |
|---|---|---|
| Shaders únicos | 10.374 (1.986 PS, 339 VS, 8.049 CS) | 10.374 (1.986 / 339 / 8.049) |
| Inícios de código | 314.869; `--verify-footers`: 314.869 rodapés, todos com exatamente um início | 314.869 |
| Registros de pass (VS e PS) | 138.900 (nenhum só com VS) | 138.900 |
| Pares (VS, PS) distintos | 2.195; os 879 pares dos 1.381 `.key` gráficos do cache de referência estão todos no índice | 2.195; 879/879 |
| Cabeçalhos com mais de uma versão por hash | 0 | 0 |
| Efeitos | 22.518 = todos os itens de tipo 0xB (o efeito fica no item + 0x10) | 22.520 (não confirmado) |
| Instâncias de material | 33.125 locais + 52.273 importadas (51.542 resolvem para um efeito, com o mesmo número de texturas) + 12.209 ligadas pelo jogo em tempo de execução | 141.180 = 33.110 + 108.070 (não confirmado) |
| Objetos textura | 119.582, com 9.177 hashes de nome | 180.936 (errado); assinatura 120.522 |
| Malhas | 210.244; 182.858 com efeito resolvido (80.339 local + 102.519 importado) | 178.505 (não confirmado) |
| Tempo | 44 s com o cache de páginas frio (SSD SATA), 14 s quente, 8 s sem mudanças | ≤ 120 s frio |
| Determinismo | duas varreduras completas e uma incremental: mesmo `content_sha` | igual |
| Recursos | 4 processos, ~400 MB de RSS somados; índice de 296 MiB | RAM ≤ 1,5 GB |

Por que os números não confirmados diferem:
- **Objetos textura:** a assinatura antiga (byte 0xFF em T#+0x2b, tipo de imagem) acha 940 objetos a mais. Nenhum deles tem relocação nos 0x48 bytes do objeto, e 933 estão dentro de itens de memória de GPU (dados de textura e vértices), então são falsos positivos. O índice exige a relocação do endereço do T#.
- **Instâncias de material:** em 12.209 casos o campo do efeito é nulo e não há import (o pacote nem tem `XLNK`); entram como `unlinked` só quando uma malha aponta para elas. 731 "imports" resolvem para algo que não é efeito e ficam com o efeito vazio. O 108.070 antigo não pôde ser refeito.
- **Malhas:** 210.244 é o total com V# relocados; a contagem antiga só considerava as cadeias com efeito resolvido e procurava os imports só na primeira tabela `KNLI`.
- **Efeitos:** a contagem estrutural bate com os 22.518 itens de tipo 0xB; os 2 a mais da conta antiga não foram achados.

## Etapas 2 e 3: jobs de pré-compilação (v1)

`jobs.py` gera, a partir do índice e dos `.xpps` do próprio jogador, o arquivo de jobs que o pré-compilador do port lê (`ISSPJOB1`, formato em `vk_precompile.h` e `jobfile.py`). `jobs_eval.py` mede o gerador contra uma captura de desenvolvimento (`TLG_PRECOMPILE_CAPTURE`); o produto nunca lê captura.

```sh
python -m xpps.jobs_eval infer <captura> <indice.sqlite> <tabelas.json>   # tabelas INFERIDAS (só enums)
python -m xpps.jobs <indice.sqlite> <tabelas.json> <saida.jobs> [--compute-wide]
python -m xpps.jobs_eval rules <captura> <indice.sqlite>                  # quanto cada regra explica
python -m xpps.jobs_eval eval  <captura> <indice.sqlite> <tabelas.json> --cv 5
```

| Módulo | O que faz |
|---|---|
| `jobfile.py` | lê e grava o formato `ISSPJOB1` |
| `signature.py` | `signature(registro)`: só o que muda a `GraphicsPipelineKey` e a `StageSpecialization` (cada campo com o arquivo:linha do port) |
| `engine_tables.py` | regras e tabelas do motor, cada uma marcada `EBOOT` (função do eboot) ou `INFERRED` (vira tarefa de RE) |
| `gcn_mem.py` | acessos a buffer no código GCN (stride e escrita de um V#) |
| `jobs.py` | o gerador |
| `jobs_eval.py` | `infer`, `rules`, `eval` |

**Assinatura.** Partes: `vs`, `ps`, `cs` (hash), `vs_rt`, `ps_rt`, `cs_rt` (RuntimeInfo comparado), `ps_in`, `rt`, `depth`, `raster`, `vs_res`, `ps_res`, `cs_res` (um sharp projetado por InputUsageSlot em `flat[startRegister]`, mais os quadros de user data sem slot) e `fetch`. Endereços e tamanhos saem. Na captura de 150 s ela separa 613 dos 614 pipelines gráficos e os 413 de compute que o port montou. Fica de fora: motion vectors, sgprs de draw indireto, `vertex_buffer_formats` (só sem input dinâmico), `start` e `mtype`/`add_tid_enable` (mudam o SPIR-V, mas não a chave: REVISAO B12).

**De onde vem cada parte** (`rules`, captura de 150 s em Seattle, 614 gráficos e 413 compute):

| Parte | Regra | Explica |
|---|---|---|
| RSRC1/2, formatos de export, PS_INPUT_ENA/ADDR, IN_CONTROL, BARYC, CB_SHADER_MASK, VS_OUT_* | cabeçalho Gnm | 614/614 cada |
| DB_SHADER_CONTROL | cabeçalho + regra de carga (EBOOT, FUN_014468e0) | 614/614 (cru: 503) |
| SPI_PS_INPUT_CNTL | semânticas de export do VS × entrada do PS | 614/614 |
| RSRC1/2, NUM_THREAD do compute | cabeçalho Gnm | 413/413 |
| T# de material do PS | efeito + instância + troca sRGB (EBOOT) | 3.027/3.027 (sem a troca: 2.959) |
| S# do efeito | `smp_desc` pelos pares do pass (EBOOT) | 938/938 |
| CB | V# canônico | 1.983/1.983 gráficos, 1.348/1.348 compute |
| V# do fetch | malha da instância de material | 485/545; 52 sem malha ligada ao efeito |
| estado RT/depth/raster | (pass id, COL_FORMAT) → perfis INFERIDOS de outros pares | 584/614 |
| V# do motor (VS/PS) e T# do motor | perfis INFERIDOS no mesmo api slot de outros pares | 2.341/2.352, 248/250, 676/687 |
| compute | modelo do `re_compute` (tabela de slots, stride da definição de partícula, V# anterior nulo/ligado) | ver abaixo |

**Medido (CV de 5 dobras por par/programa: as tabelas inferidas nunca viram o par avaliado).** Gráficos: 85,0% (521/613) com 4,4 registros gerados por necessário; faltas por parte: `rt` 47, `fetch` 26, `ps_res` 22, `vs_res` 22, `depth` 10. Compute: 83,1% com 1,2× (modo `--compute-wide`: 87,2% com 1,9×); as 17 especializações dos 13 CS do motor (imagens) nunca acertam. Jogo inteiro: 7.754 registros gráficos + 13.486 de compute = 21.240 (86 MB), 87 s e 323 MB de RSS.

**Limites.** A medição vale para uma rota de 150 s. As tabelas INFERIDAS saem de uma captura e não vão para o git: o produto ainda depende delas até o RE do eboot as substituir (estado por render slot e V# do motor). A assinatura é um modelo em Python do código C++; o teste final é no jogo.

---

## English summary

`xpps` builds a local SQLite index of the game's KCAP packages for the first-run shader precompiler (stage 1). It follows the packages' relocation tables instead of guessing pointers, so it only reads CPU structures and shader heads. Stdlib only.

- Run from `port/tools`: `python -m xpps.index build <dir> <out.sqlite> [--jobs N]`; progress lines `PROGRESS index <n> <total>` on stdout. Incremental by fingerprint (size + mtime + SHA-256 of the first/last 64 KiB); `sha` prints a content hash that is stable across builds.
- Code start rule: start = footer − 8·(code[1]+1), code[0] = 0xBEEB03FF (the footer's length field is not the code size).
- Measured on the game: 10,374 unique shaders, 314,869 code starts, 138,900 pass records, 2,195 VS/PS pairs (879/879 of the reference cache), 22,518 effects, 119,582 texture objects, 210,244 meshes; 44 s cold, 14 s warm.
- Tests: `python3 -m unittest discover -s tests -p 'test_xpps_index.py'` (synthetic KCAP; the real-game test is skipped without the game folder).
- Stages 2-3 (`jobs.py`, `jobs_eval.py`, `signature.py`): job builder v1 from the index; the signature keeps only what changes the pipeline key and the stage specialization. Cross-validated against a 150 s capture: 85.0% of graphics pipelines (4.4 records per needed one), 83.1% of compute (1.2x; 87.2% with `--compute-wide`); 21,240 records for the whole game in 87 s. The INFERRED tables come from a capture and stay off git.
