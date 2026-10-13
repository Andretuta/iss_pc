# Port para macOS em Apple Silicon (ARM)

**Status:** plano futuro, ainda não iniciado.

## Contexto
O port roda o `eboot.bin` original (x86-64) diretamente na CPU, com um runtime que substitui as
bibliotecas do PS4 e tradução de GPU para Vulkan. No Mac com chip Apple (ARM64), o código x86-64
do jogo teria de rodar sob **Rosetta 2**, e o Vulkan teria de passar pelo **MoltenVK** (Vulkan → Metal).

## O que precisa ser verificado ou feito
- [ ] **Rosetta 2 e AVX:** o eboot usa instruções AVX (por exemplo, `vpslldq`). Confirmar a partir de qual
      versão do macOS o Rosetta traduz AVX/AVX2 e se cobre tudo o que o jogo usa.
- [ ] **TLS / `gs`:** o loader troca `mov rax, fs:[0]` por `gs:` para o TLS do jogo. No macOS x86-64
      (Rosetta), o `gs` pertence ao sistema, então é preciso outro esquema de TLS. É o ponto mais difícil.
- [ ] **Memória:** mapeamentos em endereços fixos (região de 0x10_0000_0000+, o tess ring em
      0x7f0000000, o memfd de memória direta) usando as APIs Mach (`mach_vm_allocate`/`vm_remap`).
- [ ] **Sinais e exceções:** o rastreamento de páginas da GPU depende de SIGSEGV com contexto x86. Validar
      sob Rosetta, ou usar exception ports Mach.
- [ ] **GPU:** MoltenVK. Verificar as extensões que o núcleo do shadPS4 exige; o shadPS4 já tem build
      para macOS como referência.
- [ ] **Páginas de 16 KB:** o Apple Silicon usa páginas de 16 KB, como o PS4, o que é favorável. Revisar as
      suposições de 4 KB no runtime (`touch_for_write`, rastreamento de páginas).
- [ ] **Áudio/entrada:** SDL3 (já usado) cobre CoreAudio e controles no macOS.

## Estimativa
Semanas a meses, conforme o suporte do Rosetta a AVX e a solução para o TLS. Depende de alguém com um
Mac Apple Silicon para testar.
