# AGENTS.md

O contexto completo deste projeto está em **[`CLAUDE.md`](CLAUDE.md)**. Leia aquele
arquivo primeiro; ele tem a descrição do problema, a origem de cada dado, a ordem dos
scripts e a lista de armadilhas.

Resumo de 30 segundos:

- `codigo/01` a `codigo/08` rodam nesta ordem (`python codigo/rodar_tudo.py` roda tudo).
- Dados brutos em `dados/*.zip` (MonitorAr); saídas em CSV/JSON em `dados/`; figuras em
  `figuras/`. O protótipo é de um ponto só (Fercal), de 09/2024 a 12/2025, com Terra e Aqua
  separados.
- Earth Engine já autenticado, projeto `SEU-PROJETO-EARTH-ENGINE`.
- Nada aqui faz login. O CALIOP não foi baixado (exige conta Earthdata) — o leitor HDF4
  está em `codigo/05_leitor_calipso.py` e tem autoteste.
- Os números do `RELATORIO.md` saem dos CSV em `dados/`; se mudar um script, rode de novo
  e confira as saídas antes de citar qualquer valor.
- Regra que não se negocia neste projeto: **validação por estação e por blocos de tempo,
  nunca sorteando linhas** (`codigo/validacao.py` e `codigo/teste_validacao.py`).
