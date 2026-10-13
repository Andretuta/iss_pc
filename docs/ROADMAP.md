# inFAMOUS Second Son PC: roadmap

Port de inFAMOUS Second Son (Sucker Punch, PS4, CUSA00223, base 1.00 + update 1.07, SDK 4.00).
Repositório local, ainda sem GitHub. Criado em 13/10/2026.

O plano, o estado e as investigações ficam em `~/decomp/PORT_INFAMOUS.md`, fora do repositório,
junto da estrutura comum dos ports (`~/decomp/PADRAO_PORTS.md`). Quando o repositório for para o
GitHub, cada etapa vira uma issue e este arquivo passa a ter o plano completo.

## Onde estamos

| Área | Estado |
|---|---|
| Repositório (launcher, pacotes, docs, ícone) | ✅ Padronizado a partir do gr2_pc |
| `prepare.py` / `link_modules.py` (eboot, libc e Fios2 do 1.07) | ✅ |
| Imports que faltam (NpManager "A", PlayGo, Http, NetCtl, AppContent, Razor...) | ⏳ |
| Primeiro boot | ❌ Ainda não inicia |
| Vídeo (GPU), áudio, vídeos, saves | 📋 Planejado |

---

# inFAMOUS Second Son PC: roadmap (English)

Port of inFAMOUS Second Son (Sucker Punch, PS4, CUSA00223, base 1.00 + update 1.07, SDK 4.00).
Local repository, no GitHub yet. The plan, status and investigations live in
`~/decomp/PORT_INFAMOUS.md`, outside the repository. In development: **it does not boot yet**.
