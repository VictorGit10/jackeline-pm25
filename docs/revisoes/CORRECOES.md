# Correções pedidas após a conferência (31/10/2026)

As regras de `REGRAS-COMUNS.md` continuam valendo. Ao terminar, acrescente ao `RELATORIO.md` uma seção **"Correções de 31/10"** com o que mudou.

## 1. Arquivos temporários na raiz
Há `cmrtest.json`, `tmp_*.html`, `tmp_*.json` e `tmp_probe.txt` soltos na raiz. Se algum é fonte de número do relatório, mova para `dados/sondagens/` e atualize o caminho no script e no relatório. Os que não servem para nada, apague. A raiz deve ficar só com os `.md` e as pastas.

## 2. Hora do ERA5 × satélite do AOD
O `03_prototipo_gee.py` faz a média diária dos granulos MAIAC de **Terra e Aqua** juntos (linha ~294), mas o relatório fala em "hora da passagem (~13h30)" e o ERA5 é pego na hora cheia mais próxima do granulo. Deixe claro e coerente:
- qual hora do ERA5 entra quando há granulo de Terra (~10h30) e de Aqua (~13h30) no mesmo dia;
- de preferência, guarde Terra e Aqua separados (com a hora de cada um) ou use só um satélite, e justifique.
Rode de novo e atualize os números da seção 4 que mudarem.

## 3. Afirmação forte demais
Na seção 4, "Se a camada limite não explica a coluna, o ajuste AOD/BLH só adiciona ruído" afirma mais do que n = 18 permite. Reescreva no tom do resto do relatório: com esses dados, o ajuste não melhorou, e há uma explicação possível (BLH quase independente do AOD nesta janela), não uma conclusão.

## 4. Referências do Brasil
O pedido sugeria trabalhos no Brasil e nenhuma das 12 referências é. Procure 2 a 4 trabalhos sobre AOD × PM2,5, aerossol de queimadas ou perfil vertical no Brasil (ou no Cerrado/Amazônia), confira o DOI no Crossref como as outras e acrescente ao `REFERENCIAS.md`. Se não achar com DOI conferido, diga isso em vez de forçar.
