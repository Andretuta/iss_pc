# Bug: linhas pretas esticadas perto dos personagens (Gravity Rush 2)

Investigação de 13/10/2026. Status: **causa localizada, correção pendente**.

## Sintoma

Linhas pretas finas e retas cruzam a tela em todas as direções, por cima das esferas, dos personagens e da cesta da nave. Elas aparecem quando a câmera está perto de personagens e objetos, somem de longe e acontecem em vários cenários. O usuário reportou com prints (`~/Imagens/Capturas de tela/Captura de tela de 2026-10-13 10-25-39.png` e `10-30`).

## O que foi provado

1. Com `TLG_PIPELINE_LOG=1`, o jogo monta cerca de 200 pipelines gráficos. Só dois usam **`AdjTriangleList`** (prim=12, triângulos com adjacência), e os dois têm **geometry shader**:
   - pixel shader `0x311329a294e`;
   - vertex/export shader `0x87bedbd58eb` e `0x87bedbd58ea`;
   - geometry shader `0x22b3a4fca5a`;
   - 1 alvo de cor, profundidade D32.
2. Com `TLG_SKIP_ADJACENCY=1`, que pula só esses desenhos, a mesma cena da cesta sai **sem nenhuma linha**. O usuário confirmou na tela: "os riscos sumiram".

**Conclusão:** as linhas vêm do **contorno estilo quadrinho** que o GR2 desenha com um geometry shader. O GS lê os triângulos vizinhos para achar as bordas da silhueta e emite os traços. A tradução desse caminho no núcleo do shadPS4 gera traços ligando vértices errados. O contorno só é desenhado em objetos próximos, e por isso as linhas também só aparecem de perto.

## Onde atacar (ordem sugerida)

No PS4, o GS roda em três partes. O **ES** (o vertex shader) grava os vértices no anel ES→GS, o **GS** lê dali e grava no anel GS→VS, e um **copy shader** (VS) emite a saída final. O shadPS4 junta tudo num geometry shader Vulkan. Os pontos prováveis do erro:

1. **Corte dos strips de saída** (suspeito nº 1). O contorno sai como line strip ou como triangle strip fino. Conferir se `VGT_GS_OUT_PRIM_TYPE` vira o `OutputPrimitive` certo no SPIR-V e se o `EmitVertex`/`EndPrimitive` (o `s_sendmsg` GS_EMIT/GS_CUT do GCN) cortam os strips nos lugares certos. Um corte perdido liga o fim de um traço ao começo do próximo e gera exatamente linhas longas atravessando a tela.
2. **Leitura do anel ES→GS com 6 vértices.** Com adjacência, o GS recebe 6 vértices por primitiva. Conferir no `shader_recompiler/` (frontend do GS, `runtime_info.h` `gs.*`) se o deslocamento por vértice (`VGT_ESGS_RING_ITEMSIZE`, `VGT_GS_VERT_ITEMSIZE`) e o índice 0..5 batem com `gl_in[0..5]`.
3. **Ordem dos vértices com adjacência.** No Vulkan, `eTriangleListWithAdjacency` usa 0, 2 e 4 como triângulo e 1, 3 e 5 como vizinhos. Confirmar que o GCN usa a mesma ordem e que o caminho de índices (`liverpool_to_vk.cpp`, `AdjTriangleList`) não converte o index buffer como se fosse uma lista simples.
4. **Copy shader e stride do anel GS→VS** (`gs.vs_copy`, offsets por atributo, `VGT_GS_MAX_VERT_OUT`).
5. **Comparar com o shadPS4 upstream:** procurar correções de geometry shader com adjacência e de corte de strip ("gs cut", "adjacency", "EmitVertex") em issues e commits e portar.

## Ferramentas prontas (branch `feat/gameplay-tests` do gr2_pc)

- `TLG_PIPELINE_LOG=1`: lista cada pipeline criado, com primitiva, alvos, formatos de vértice e hashes (`vk_graphics_pipeline.cpp`).
- `TLG_SKIP_ADJACENCY=1`: pula os desenhos com adjacência (`vk_rasterizer.cpp`). Também serve de **contorno provisório**.
- Dump dos shaders: o `DumpShader` do pipeline cache grava `.bin`/`.spv` com o dump de shaders ligado. Pegar o GS `0x22b3a4fca5a` e o ES `0x87bedbd58eb` e comparar o GCN com o SPIR-V gerado (`spirv-dis`).
- `scripts/gr2_run.sh <s> <pasta_capturas> <roteiro>`: reproduz a cena (Continue → cesta da nave) com capturas em segundos fixos.

## Contorno provisório

Se o reparo demorar, expor `TLG_SKIP_ADJACENCY` como opção no launcher do GR2: "Desligar contorno do GS (corrige linhas pretas)". A imagem fica limpa, mas perde parte do traço de quadrinho.

## E o TLG?

O TLG não usou pipelines com adjacência nas sessões testadas. Quando o GS for corrigido, a correção vai para o núcleo comum dos dois repositórios.
