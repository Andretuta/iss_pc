# Releases — publicação manual / manual publishing

## Português

PRs e pushes na `main` compilam os pacotes Linux e Windows e executam os testes do launcher. Aprovar ou mesclar um PR não publica release. Tags também não disparam publicação.

Para publicar as mudanças acumuladas:

1. Mescle os PRs revisados, confira o CI e teste o conjunto desejado.
2. No GitHub, abra **Actions → Build → Run workflow**.
3. Escolha a branch **main**, marque **Publicar release / Publish release** e execute.
4. Após os builds e testes dos dois sistemas passarem, o workflow publica `vAAAA.MM.DD-<commit>` e atualiza `latest`.

Pelo terminal:

```sh
gh workflow run build.yml --repo HayatoG/iss_pc --ref main -f publish_release=true
```

A opção vem desmarcada: uma execução manual sem ela apenas compila e testa. Em outra branch, o job de publicação é ignorado. Cada publicação inclui a `main` no commit fixado ao iniciar a execução; merges posteriores ficam para o próximo pacote. As notas bilíngues reúnem os PRs desde a release anterior, com créditos das issues. Não há quantidade mínima de PRs.

Falhas nos builds, testes ou geração de notas impedem a publicação. Os pacotes são enviados primeiro para um rascunho, depois publicados. Um rascunho deixado por uma falha deve ser inspecionado antes de tentar novamente. Releases anteriores e histórico dos checks são preservados; artifacts de teste expiram após 3 dias. Uma reexecução que encontra a mesma tag já publicada não envia novo anúncio ao Discord.

## English

PRs and pushes to `main` build Linux and Windows packages and smoke-test the launcher. Approvals, merges and tag pushes do not publish releases.

To publish accumulated changes, review and merge the PRs, verify CI and test the combined changes. Open **Actions → Build → Run workflow**, select **main**, enable **Publicar release / Publish release**, and run. Alternatively, use the command above. Both platform jobs must pass before `vYYYY.MM.DD-<commit>` is published as `latest`.

Publishing defaults to off. A manual run without it only builds and tests; publication is skipped on other branches. The release includes `main` at the commit captured when the run starts. Later merges belong to the next release. Bilingual notes collect PRs since the previous release and credit issue reporters. There is no minimum PR count.

Build, test or note-generation failures prevent publication. Packages are uploaded to a draft before publication; inspect any draft left by a failed attempt before retrying. Existing releases and check history are preserved; test artifacts expire after 3 days. Re-running a tag already published does not send another Discord announcement.
