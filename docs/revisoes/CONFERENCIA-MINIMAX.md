# Conferência independente — AOD × PM2,5 em Goiás e no DF (pasta `jackeline`)

**Revisor:** MiniMax (conferência de 31/10/2026, sobre o pacote produzido por outra IA)
**Pasta conferida:** `<pasta>\jackeline`
**Regra respeitada:** nenhum arquivo existente foi alterado. Os scripts que dependem de
rede ou de Earth Engine **não** foram rodados. As conferências que exigiam execução foram
feitas numa **cópia isolada** em `<pasta>\jackeline`;
as mtimes dos arquivos originais foram conferidas depois e estão inalteradas.

---

## 0. Veredito em uma tela

| Item | Veredito |
|---|---|
| **As 4 correções de `CORRECOES.md` foram feitas?** | **3 sim, 1 parcialmente.** A nº 3 (afirmação forte demais) e a nº 4 (referências do Brasil) estão completas e corretas. A nº 1 (arquivos temporários) está resolvida de outra forma, mas legitimamente. A nº 2 (hora do ERA5 × satélite) **corrigiu o mecanismo e deixou os números e os rótulos de hora errados** — que é justamente o que ela pedia. |
| **Os números do `RELATORIO.md` batem com os dados?** | **Em grande parte sim.** 26 dos 31 números que conferi reproduzem exatamente. Quatro não batem (um deles é o AOD mínimo, que não existe em nenhum arquivo). |
| **Os testes passam?** | **Sim.** `5 testes, 0 falha(s)`, reproduzido aqui. `04_validacao.py` e `06_referencias.py` reexecutados: saídas **byte-idênticas** às entregues. |
| **Alguma conclusão é invalidada?** | **Não.** Nenhuma conclusão central do relatório cai. As conclusões do §4 sobrevivem a todas as reanálises que fiz. O que existe é **número que não reproduz do CSV entregue**, **rótulo de hora errado** e **controle que não testa o que diz testar**. |
| **O trabalho responde ao `CONTEXTO.md`?** | **Sim, e bem.** A pergunta "¿existe perfil vertical suficiente sobre GO/DF?" — que é a pergunta que pode mudar a tese — está respondida com rigor e é a parte mais forte do pacote. Faltam três coisas concretas (ver §6). |

**Veredito geral:** o trabalho é sólido, honesto e utilizável. Os problemas são de
**rastreabilidade e de rótulo**, não de conceito. Nada aqui exige refazer o pacote; exige
corrigir umas 10 linhas de texto e 2 linhas de código.

---

## 1. As correções de `CORRECOES.md` foram feitas de verdade?

### Correção 1 — Arquivos temporários na raiz → **FEITA (por outro caminho, válido)**

**Evidência.** A raiz contém apenas `AGENTS.md`, `CLAUDE.md`, `CONTEXTO.md`, `CORRECOES.md`,
`PEDIDO-CONFERENCIA.md`, `PEDIDO.md`, `README.md`, `REFERENCIAS.md`, `REGRAS-COMUNS.md`,
`RELATORIO.md` e as pastas `codigo/`, `dados/`, `figuras/`. Um `find` em toda a árvore por
`tmp_*`, `cmrtest*`, `*.tmp` **não devolve nada** — a afirmação do §"Correções de 31/10"
("Conferido agora com `find`: não há arquivo temporário em nenhum nível da pasta") é
literalmente verdadeira.

**O ponto que a correção sugeria (`dados/sondagens/`) não foi seguido, e está tudo bem:**
a correção era condicional ("*se* algum é fonte de número do relatório, mova para
`dados/sondagens/`"). O relatório argumenta (linhas 387–393) que nenhum temporário era fonte
de número, porque os códigos HTTP e os tamanhos de resposta vêm de
`dados/pm25_sondagens_http.csv`. **Conferi: é verdade.** O `pm25_sondagens_http.csv` contém
exatamente os 9 pares (fonte, URL, HTTP, bytes) que a seção 3 do relatório cita — OpenAQ v3
= 401, OpenAQ v2 = 410, MMA/SEMAD/Cimehgo/IBRAM = 200, Sensor.Community = 200 com 2 bytes.
Não há número órfão na seção 3.

**Nada a fazer.**

### Correção 2 — Hora do ERA5 × satélite → **PARCIALMENTE FEITA** ⚠️

**O mecanismo foi corrigido e está certo.** Verifiquei em `codigo/03_prototipo_gee.py`:
- linha 313: `aod["satelite"] = aod.satelite.replace({"T": "Terra", "A": "Aqua"})` — a
  propriedade `SATELLITE` do MCD19A2 é usada, como o `CLAUDE.md` pedia;
- linhas 275–277: o ERA5 entra por `hora_cheia` **de cada granulo**, com merge por
  `["ponto", "hora_cheia"]` — não há mais nenhuma média de horas;
- a tabela entregue tem uma linha por granulo, com `hora_utc` e `hora_local`;
- conferi que as horas cheias usadas no ERA5 são **UTC 12, 13, 14 para Terra** e **UTC 17,
  18 para Aqua** — ou seja, as duas horas nunca se misturam. O problema original está
  resolvido.

**Mas os rótulos de hora estão errados, e é exatamente isso que a correção pedia.** A
correção decía: "*deixe claro e coerente: qual hora do ERA5 entra quando há granulo de
Terra (~10h30) e de Aqua (~13h30) no mesmo dia*". O relatório e o `CLAUDE.md` responderam
com os mesmos rótulos de antes, sem conferir contra a tabela que entregaram.

| Fonte | O que diz | O que a tabela `prototipo_integrado.csv` realmente contém (`hora_local`) |
|---|---|---|
| `RELATORIO.md` l. 23, 175, 199, 201, 212, 398, 413 | Terra **~10h30**, Aqua **~13h30** | Terra **09:00–10:35**, média **09h48**; Aqua **13:55–15:20**, média **14h40** |
| `CLAUDE.md` l. 61 | Terra **10h30**, Aqua **13h30** (e BLH "1.120 m às 10h30" / "2.512 m às 13h30") | idem |
| `README.md` l. 64 | Terra **10h30**, Aqua **13h30** | idem |
| `figuras/prototipo_integrado.png`, legenda | "AOD MAIAC Terra (~10h30 local)" / "Aqua (~13h30 local)" | idem |

O erro do Aqua é de **mais de uma hora** (média 14h40 contra 13h30). E o ERA5 que entra
na prática são as horas **09–11 h locais** (Terra) e **14–15 h locais** (Aqua). Quem
reproduzir a association pegando ERA5 às 13h30 para o Aqua pega a hora errada.

O argumento **físico** do relatório sobrevive intacto — a camada limite da tarde é muito
mais alta que a da manhã, e isso é verdade e está bem ilustrado. O que está errado é o
**número de hora**, que é o que a correção nº 2 queria certo.

**O que fazer:** substituir "~10h30"/"~13h30" por "~09h45"/"~14h40" (ou, melhor, pelo
intervalo real: Terra 09:00–10:35, Aqua 13:55–15:20) em `RELATORIO.md`, `CLAUDE.md`,
`README.md` e na legenda da figura — e escrever "ERA5 na hora cheia mais próxima do
granulo (09–11 h local em Terra, 14–15 h local em Aqua)".

**Um segundo problema na mesma frase.** `RELATORIO.md` l. 418 afirma que a BLH de
1.120 m (Terra) e 2.512 m (Aqua) vêm de *"mesmos pontos e mesmos dias"*. **Não vêm:**
1.120 m é a média de **38 dias de Terra**, 2.512 m é a média de **35 dias de Aqua**, e só
**27 dias** são comuns aos dois. No par balanceado (os mesmos 27 dias) o contraste é
**1.197 m contra 2.668 m** — a conclusão é até mais forte do que a relatada, mas a
justificativa escrita está errada. (Detalhe: `CLAUDE.md` l. 61 repete a mesma ideia, com
"mesma janela e no mesmo ponto".)

### Correção 3 — Afirmação forte demais → **FEITA, e bem feita** ✅

**Evidência.** A frase "Se a camada limite não explica a coluna, o ajuste AOD/BLH só
adiciona ruído" **não existe mais** no `RELATORIO.md` — só aparece em `CORRECOES.md` (que é
o pedido) e na descrição do que mudou (l. 422–427). O texto novo (l. 216–220) diz:

> *dividir o AOD pela altura da camada limite não melhorou a correlação em nenhum dos dois
> satélites (0,90 → 0,64 em Aqua; 0,44 → −0,22 em Terra). Uma explicação possível é que a
> CL e o AOD são quase independentes nesta janela (0,08 em Aqua); outra é que a CL sozinha
> não descreve onde o aerossol está. Com n = 12 e 15, as duas explicações seguem abertas —
> não é conclusão, é hipótese a testar com mais anos;*

O tom pedido ("não é conclusão, é hipótese") foi adotado, e as duas explicações possíveis
foram mantidas sem eleger uma. Também é justo que a seção 5(b) registre que a validação por
estação deu R² alto *"porque a função é a mesma em todas as estações"* e que em dados reais
isso deve cair.

**Ressalva (importante):** a explicação numérica *"a CL e o AOD são quase independentes
nesta janela (0,08 em Aqua)"* é **frágil** — ver §4, item 4. A reescrita de tom está
correta; o número que a sustenta precisa de ajuste.

### Correção 4 — Referências do Brasil → **FEITA, e acima do pedido** ✅

**Evidência.** `REFERENCIAS.md` tem 16 referências, e o cabeçalho diz "6 com foco no Brasil".
Conferi que o conjunto `DOIS_BRASIL` em `codigo/06_referencias.py` (l. 28–35) tem
**exatamente 6** DOIs, coerentes com o cabeçalho. Reexecutei `06_referencias.py`: **16 de 16
confirmadas no Crossref, e o `REFERENCIAS.md` regenerado é byte-idêntico ao entregue.**
Confirmei à mão dois DOIs direto na API do Crossref (`10.3390/rs11192254` e
`10.1038/nature19819`): título, autores, ano e revista batem exatamente.

**As 4 acrescentadas são do tipo pedido** e são todas do Brasil:
Mataveli et al. 2019 (PM2,5 de queimadas no Cerrado) · Reddington et al. 2019 (aerossol de
queimada na Amazônia) · Wang et al. 2016 (*Nature*, transporte vertical na camada limite
amazônica) · Franco et al. 2024 (perfil vertical no ATTO).

**Um mérito a registrar:** a premissa da própria `CORRECOES.md` ("nenhuma das 12
referências é [brasileira]") **estava errada** — `dados/log_06.txt` mostra que 2 das 12
originais já eram brasileiras (Gonçalves 2018, Amazônia; Rudke 2023, Brasil). A resposta
detectou isso. A redação do §"Correções de 31/10" l. 429–431 fica, porém, autocontraditória
("*a conferência estava certa em cobrar: das 12 originais, duas já eram brasileiras*") — dá
a impressão de que as duas coisas contradizem. Reescreva: "a conferência estava certa em
cobrar mais; note que 2 das 12 originais já eram brasileiras, e acrescentamos 4".

### Bônus — o bug da umidade (Magnus com Kelvin) → **FEITO e conferido** ✅

**Evidência.** `codigo/03_prototipo_gee.py` l. 283–291 converte explicitamente para °C antes
de aplicar Magnus (`exp(17.625·T/(243.04+T))`). A tabela entregue tem umidade entre
**8,4% e 80,3%**, média **29,2%** — exatamente o que o relatório afirma ("8% e 80%, média
29%") e coerente com a estação seca. A correção do bug está no código **e** no dado.

**Ressalva menor:** a frase "66,9% quando o correto é 18,3%" (l. 446–447) é um caso
específico que não é reproduzível a partir dos arquivos entregues (a tabela pré-correção não
foi arquivada). Não é um erro — é um número que não tem como ser conferido por quem lê.

---

## 2. Números do `RELATORIO.md` conferidos contra os dados

Método: recalculei cada número a partir dos CSV/JSON em `dados/`, e reexecutei
`04_validacao.py`, `05_leitor_calipso.py`, `06_referencias.py` e `teste_validacao.py` na
cópia isolada. Tabela completa: **26 de 31 números reproduzem exatamente.**

### 2.1 Confirmados (amostra — os 12 mais importantes)

| # | Número no relatório | Onde | Recalculei | |
|---|---|---|---|---|
| 1 | 484 passagens ≤25 km em Goiânia / 259 em Brasília | l. 74–76 | `calipso_controle.json` + `calipso_passagens_eventos.csv` | ✅ |
| 2 | 154 a ≤5 km / 9 em Brasília | l. 74–76 | idem | ✅ |
| 3 | 620 / 589 a ≤50 km | l. 74–76 | idem | ✅ |
| 4 | 3.705 granulos na caixa, 2.427 únicos | l. 78 | `calipso_granulos_brutos.csv` | ✅ |
| 5 | Média 2007–2018: Goiânia 33,4/ano (19,6 noite, 13,8 dia); Brasília 16,6 (0,3 noite, 16,2 dia) | l. 86 | `calipso_passagens_por_ano.csv` | ✅ |
| 6 | 2019–2022: 14,8/ano (8,2 noite) e 11,0/ano (6,5 noite) | l. 87 | idem | ✅ |
| 7 | 2023: 4 e 5 passagens | l. 88 | idem | ✅ |
| 8 | Queimadas: Goiânia 72 noturnas ≤25 km (4/ano), 54 diurnas, 79/78 a ≤50; Brasília 8 (0,4/ano), 63, 71/77 | l. 104–105 | `calipso_estacao_queimadas.csv` | ✅ |
| 9 | Erro de distância: máx 1,19 km, mediana 0,58 km | l. 118–119 | `calipso_controle.json` | ✅ |
| 10 | Intervalo mediano 16,0 dias nos 4 casos | l. 120–121 | idem — **e robusto**: sem o filtro (5–40 d) a mediana continua 16,0 | ✅ |
| 11 | 217 linhas; 35 Aqua / 38 Terra em Brasília, 36/36 Goiânia, 31/41 Porangatu | l. 164–165, 187–188 | `prototipo_integrado*.csv` | ✅ |
| 12 | AOD médio 0,232 / 0,243; BLH 2.512 / 1.120 m | l. 189 | idem | ✅ |
| 13 | Spearman 0,902 / 0,436 / 0,573 / 0,077 / 0,996 | l. 199–206 | `prototipo_correlacoes.csv` | ✅ |
| 14 | R² 0,612 / 0,941 / 0,948; diferença sorteio−blocos = 0,336 ("0,34") | l. 260–265 | `validacao_resultados.csv` + rerun | ✅ |
| 15 | R² 0,845 com a simulação; `pm_sim`=0,99, `aod`=0,00 | l. 253–254 | idem | ✅ |
| 16 | 13 UFs em 2025, 4.926.747 registros ("4,9 milhões") | l. 149 | `monitorar_cobertura_por_uf.csv` | ✅ |
| 17 | CRAS Fercal 12.201 (2024) / 32.772 (2025); Escola 3.503 / 7.675 | l. 146–147 | `pm25_estacoes_monitorar_go_df.csv` | ✅ |
| 18 | Umidade 8%–80%, média 29% | l. 450 | `prototipo_integrado.csv` | ✅ |
| 19 | 16 de 16 referências com DOI conferido | l. 442 | rerun de `06_referencias.py` | ✅ |
| 20 | 5 testes, 0 falha(s) | l. 278 | rerun de `teste_validacao.py` | ✅ |
| 21 | 27 pares dia-satélite, 18 dias distintos | l. 281 | rerun de `04_validacao.py` | ✅ |
| 22 | "o CALIPPO não sustenta um preditor diário por estação" | l. 110 | decorre de 8–16 (72 noturnas em 18 anos) | ✅ |
| 23 | Fin da missão em 01/08/2023, por esgotamento de combustível | l. 36–39 | **página da NASA lida diretamente**: *"agreed to end the CALIPSO science mission on August 1, 2023... Fuel reserves are now exhausted"* | ✅ |
| 24 | Último granulo em 30/06/2023T21:39:53Z | l. 42–45 | **consulta direta ao CMR**, `sort_key=-start_date`: o granulo mais recente é exatamente `CAL_LID_L2_05kmAPro-Standard-V5-00.2023-06-30T21-39-53ZD.hdf` | ✅ |
| 25 | "O mesmo teste no nível 1B dá o mesmo instante final" | l. 44–45 | **consulta direta ao CMR** em `CAL_LID_L1-Standard-V5-00`: último granulo = 2023-06-30T21:39:53Z | ✅ (mas ver §4, item 12) |
| 26 | EarthCARE nível 1 público desde 16/01/2025; ATLID AER L2A com BA/BB/BC; acesso exige EO Sign In | l. 48–56 | **páginas da ESA lidas**: notícia de 16/01/2025 ("put the first level data stream... online"); catálogo do L2 ("EO Sign In Authentication (Open)"; versões BC/BB/BA listadas; "Date of launch: 2024-05-28") | ✅ (ver ressalva de DOI em §4, item 11) |

**Confirmação extra que vale registrar:** a máscara de QA do MAIAC foi conferida contra o
catálogo oficial do Earth Engine (que eu li). O `docstring` de `mascara_qa` (l. 121–143)
está **exato**: bits 0–2 = máscara de nuvem (0 = indefinido, 1 = claro) — e o código usa
`bitwiseAnd(7).eq(1)`, evitando a armadilha clássica que o `CLAUDE.md` l. 69 registra; bits
5–7 = adjacência (0 = normal); bits 8–11 = QA do AOD (0 = melhor qualidade); bit 12 =
glint; bits 13–14 = modelo de aerossol (1 = fumaça, e o código usa
`rightShift(13).bitwiseAnd(3).eq(1)`). Nenhum erro de bit. É raro ver um docstring de bits
de QA confere certo contra o catálogo.

### 2.2 Os quatro que NÃO batem

| # | O que o relatório diz | O que os dados dizem | Gravidade |
|---|---|---|---|
| 27 | "AOD de **0,056** a 0,947" (l. 190) | Mínimo real = **0,043** (Brasília, 01/09, Aqua). **0,056 não é o mínimo de nenhuma coluna entregue** — nem em `prototipo_integrado.csv`, nem em `_diario.csv`, nem em `prototipo_aod_granulos.csv`. Parece resíduo de uma execução anterior à correção da umidade. | **menor** |
| 28 | Tabela §2: "fração noturna (≤50 km): Goiânia **0,49**, Brasília **0,49**" (l. 73–77) | O `calipso_controle.json` guarda **um único valor pooled** (0,4872, calculado sobre os dois pontos juntos — `codigo/01_calipso_cmr.py` l. 257). Por ponto: Goiânia **0,4944**, Brasília **0,4788**. Ou seja, a tabela repete o mesmo número pooled em duas linhas, e a célula de Brasília deveria ser 0,48. | **menor** (mas ver §4, item 10) |
| 29 | "≤25 km: 484 / 259" reproduz do CSV ✅, mas `n_50km` e `n_5km` do JSON (620 / 154) recalculados do CSV dão 621 / 155 | Diferença de 1 por causa do arredondamento de `dist_km` a 2 casas na escrita (linha 195). O JSON (precisão plena) está certo e é o que o relatório cita. | **menor** |
| 30 | §5: cabeçalho "**R² médio (5 folds)**" (l. 260) e eixo da figura `validacao_desenho.png` idem | A linha "deixando uma estação de fora" tem **4 folds** (são 4 estações). As outras duas linhas têm 5. O cabeçalho engana em uma das três linhas. | **menor** |

### 2.3 Afirmações externas que não consegui verificar

- "uns 8 minutos na primeira vez" para `rodar_tudo.py` (`README.md` l. 40) — os logs não
  têm timestamp. **Não verificado.**
- "as páginas [da SEMAD-GO] paradas em 2021" — a fonte registrada é
  `pm25_fontes.csv` ("atualizacao de 2021"), que é a avaliação do agente anterior, não
  algo que eu possa recalcular do HTTP. **Não verificado** (e o relatório não o apresenta
  como número medido).
- Tempo real de execução do script 03 contra o Earth Engine. **Não verificado** (não rodei
  EE, por instrução).

---

## 3. Testes automatizados

```
$ python codigo/teste_validacao.py
  ok      test_blocos_sao_contiguos_e_cobrem_o_periodo
  ok      test_deteccao_de_um_dia_repetido
  ok      test_sem_vazamento_nos_blocos_de_tempo
  ok      test_sem_vazamento_por_estacao
  ok      test_sorteio_de_linhas_falha
5 testes, 0 falha(s)
```

**Todos os 5 passam**, e conferi que são os 5 que o relatório promete (l. 271–277). O ponto
mais valuable é `test_sorteio_de_linhas_falha`: ele prova que o detector de vazamento
**reprova** o desenho errado — sem ele, o detector não provaria nada. Está bem feito.

Também reexecutei, na cópia isolada:

- `04_validacao.py` → `validacao_resultados.csv` e `validacao_desenho.png` **byte-idênticos**
  aos entregues. Determinismo total (semente fixa em `validacao.py`/`04_validacao.py`).
- `05_leitor_calipso.py` → `autoteste ok: integracao, fracao na camada limite, fumaca
  acima da CL e QC`. O autoteste cobre 4 casos com resposta conhecida, incluindo o caso
  "fumaça acima da CL ⇒ `fracao_abl` = 0" e "QC ruim não entra". Confere o que promete.
- `06_referencias.py` → `REFERENCIAS.md` **byte-idêntico**, 16/16 no Crossref.

**Um ponto que a seção 5 acertou e que vale dar crédito:** o §5(d) diz que, com 1 estação e
18 dias, "não há modelo defensável — e o relatório diz isso em vez de ajustar um modelo que
parece bom". É a postura certa, e o `04_validacao.py` de fato não ajusta modelo nenhum
nos dados reais: ele só roda a verificação de blocos sobre a tabela real. Muitos pacotes
teriam publicado um R² sobre 27 linhas. Este não.

**Uma fragilidade do teste de validação por blocos (importante, ver §4, item 9):**
`blocos_de_tempo` (`codigo/validacao.py` l. 51–58) usa `qcut` sobre o *rank* das datas, o
que produz 5 blocos de tamanho quase igual em **número de dias**. Um bloco de 36 dias
cobre ~10% da janela, e o modelo treina com o resto — incluindo **o futuro**. Para um
diagnóstico de *vazamento* isso é legítimo e é o que se quer. Mas se a validação por
blocos de tempo for usada como **estimativa de desempenho fora da amostra**, ela é
otimista por construção. O relatório não promete isso, então não é erro — mas é a
distinção que ela vai precisar fazer na tese.

---

## 4. Problemas de método

Ordenados por gravidade. Nenhum invalida uma conclusão; todos afetam a **reprodutibilidade**
ou a **interpretação** de resultados que a pesquisadora vai reaproveitar.

### 🔴 Importante 1 — As correlações AOD/BLH do relatório **não reproduzem** do CSV entregue

**Evidência.** `prototipo_correlacoes.csv` diz Aqua AOD/BLH = **0,643**, Terra = **−0,218**,
Terra+Aqua = **0,061** — e o relatório cita esses valores (l. 200, 202, 204). Mas o script
calcula as correlações sobre o dataframe **em memória** (`dia`, l. 417–436), enquanto o CSV
entregue é gravado com `aod_km` **arredondado a 2 casas** (l. 330 e l. 373). O valor em
questão (`AOD/BLH`) vive na faixa **0,08–0,15** — arredondar a 2 casas destrói a ordenação.
Em Brasília, os 12 dias de Aqua têm apenas **6 valores distintos** de `aod_km`.

Recalculando a partir de `prototipo_integrado_diario.csv` (que é o que a pesquisadora vai
reaproveitar):

| Par | Relatório / `prototipo_correlacoes.csv` | Recalculado do `prototipo_integrado_diario.csv` |
|---|---|---|
| Aqua AOD/BLH × PM2,5 | **0,643** | **0,492** |
| Terra AOD/BLH × PM2,5 | **−0,218** | **−0,180** |
| Terra+Aqua AOD/BLH × PM2,5 | **0,061** | **0,033** |
| Aqua AOD × PM2,5 | 0,902 | 0,902 ✅ (arredondar `aod` a 3 casas basta) |

Ou seja: **a metade "AOD × PM2,5" reproduz; a metade "AOD/BLH × PM2,5" — a que sustenta
o argumento central do §4 — não reproduz.** Uma diferença de 0,15 no número que o
relatório diz ser o resultado do ajuste vertical.

**Por que importa.** O `README.md` (l. 50) apresenta `prototipo_integrado.csv` como a
tabela a ser levada adiante. Quem pegar essa tabela e recalcular chega a 0,49, não 0,64, e
não tem como saber de onde veio a diferença.

**O que fazer (2 linhas).** Ou gravar `aod_km` com 4–5 casas decimais (não 2), ou gravar as
correlações **a partir do dataframe já arredondado**, para que a tabela e o resultado sejam
o mesmo objeto. Recomendo a primeira, mais `n_px` junto (ver item 2).

### 🔴 Importante 2 — `n_px` (quantos pixels entraram na média) nunca é reportado — e é o que decide se a comparação Aqua×Terra é justa

**Evidência.** `n_px` existe na tabela (`prototipo_integrado.csv`) e **não aparece nenhuma
vez** no `RELATORIO.md` nem no `README.md` (grep: 0 ocorrências). Ele é o número de pixels
de 1 km que passaram na máscara de QA dentro do disco de 10 km (≈314 pixels no total).

Em Brasília:

| | Terra | Aqua |
|---|---|---|
| mediana, todos os dias com AOD | 230 px (73% do disco) | **141 px (45%)** |
| mediana, **só nos dias que entram na correlação** | 223 px | **33 px (10%)** |
| % de linhas com n_px < 20 | 7,9% | **20%** |
| % de linhas com n_px < 50 | 13,2% | **40%** |

E a taxa de descarte: **299 dos 516 registros granulo×ponto (58%) têm `n_px` = 0** — a
máscara conservadora não produz *nenhum* pixel válido — e são silenciosamente removidos
pelo filtro `n_px > 0` (l. 312). O relatório diz que a máscara é "a mais conservadora"
(l. 321) mas **não quantifica** o custo: ela come 58% dos registros.

**Sensibilidade.** Recalculei as correlações de Brasília impondo um piso de pixels:

| Corte | Aqua r(AOD,PM2,5) | Aqua r(AOD/BLH,PM2,5) | Terra r(AOD,PM2,5) | Terra r(AOD/BLH,PM2,5) |
|---|---|---|---|---|
| nenhum (o do relatório) | 0,902 (n=12) | 0,643 (n=12) | 0,436 (n=15) | −0,218 (n=15) |
| n_px ≥ 20 | **0,964** (n=10) | **0,552** (n=10) | **0,600** (n=14) | **−0,108** (n=14) |
| n_px ≥ 50 | 1,000 (n=4) | 0,600 (n=4) | 0,758 (n=13) | −0,027 (n=13) |

O 0,44 de Terra vem muito em parte de **uma única linha**: 17/10, com `n_px` = 6 pixels
(volume minúsculo de amostra) e BLH = 348 m, o menor da janela. Tirá-la move
`r(AOD, PM2,5)` de 0,436 para 0,600. A **direção** da conclusão (Aqua > Terra; dividir por
BLH não ajuda) é robusta em todos os cortes — bom. Mas os **números** são muito sensíveis a
uma escolha de filtro que o relatório não documenta.

**O que fazer.** Reportar `n_px` em cada linha da tabela e no texto, citar o corte de
`n_px` usado, e dar a sensibilidade. E, para a decisão "Aqua como satélite principal" (que
o `README.md` l. 63–65 põe explicitamente como escolha dela), acrescentar que as amostras
dos dois satélites **não são comparáveis em qualidade** (Aqua: mediana de 33 px na
correlação; Terra: 223 px).

### 🔴 Importante 3 — A comparação Aqua × Terra é feita em **dias diferentes**

**Evidência.** Em Brasília, os dias com PM2,5 **e** AOD são 12 para Aqua e 15 para Terra —
com apenas **9 em comum**. Os 3 dias só-Aqua têm r = +1,000 (n=3); os 6 dias só-Terra
têm r = **+0,143** (n=6). O headline "Aqua dá 0,90 e Terra dá 0,44" (l. 23–24) compara,
portanto, **subconjuntos diferentes de dias**.

Pareado nos 9 dias comuns: **Aqua +0,933, Terra +0,617** — a direção se mantém, e a
diferença encolhe de 0,47 para 0,32. A conclusão não cai; a base da comparação, sim.

**O que fazer.** Uma frase: "nos 9 dias em que ambos têm AOD e PM2,5, Aqua dá +0,93 e
Terra +0,62".

### 🔴 Importante 4 — O "controle de QA" mostrado **não testa o que a frase diz**

**Evidência.** `RELATORIO.md` l. 221: "*a máscara de QA não está dirigindo o resultado*
(1,00 entre AOD com e sem filtro) — bom controle", e l. 322: "*o controle com/sem filtro
mostra que ela não muda a correlação*".

O número exibido é `r(AOD com QA, AOD sem QA) = 0,996` — a concordância de **ordem** entre
duas versões da **mesma** variável. Isso é quase tautológico: as duas colunas vêm dos
mesmos pixels, uma filtrada e outra não. **Não diz nada** sobre a correlação *com o
PM2,5*.

O controle que realmente responde à pergunta não está em lugar nenhum do pacote.
Recalculei:

| Brasília | r(AOD **com** QA, PM2,5) | r(AOD **sem** QA, PM2,5) |
|---|---|---|
| Aqua (n=12) | +0,902 | +0,895 |
| Terra (n=15) | +0,436 | **+0,386** |

**A conclusão sobrevive** (a máscara não muda a correlação de forma decisiva) — mas o
número que foi apresentado não a demonstrava, e `prototipo_correlacoes.csv` não tem a linha
que a demonstraria. Além disso, a máscara **desloca o nível** do AOD: média com QA é
**2,9% menor** em Brasília (Aqua −3,7%, Goiânia −1,5%, Porangatu −0,6%) — um viés
sistemático que uma correlação de posto, por construção, **não enxerga**.

**O que fazer.** Trocar o controle exibido por
`r(AOD sem QA, PM2,5) = 0,895 (Aqua) e 0,386 (Terra)` — o número que apoia a frase — e
acrescentar que a máscara introduz viés de nível de −1% a −4%, invisível ao teste de posto.

### 🔴 Importante 5 — A explicação "a CL e o AOD são quase independentes (0,08)" assenta em 12 dias

**Evidência.** O 0,08 vem da linha `Aqua | BLH | AOD | 0,077 | n=12` de
`prototipo_correlacoes.csv`. Esse n=12 é o subconjunto **com PM2,5** (o script filtra
`pm25.notna()` antes de calcular). Calculando sobre **todos** os dias com AOD em Brasília:

| | r(BLH, AOD) nos dias com PM2,5 (o que o relatório usa) | r(BLH, AOD) em **todos** os dias com AOD |
|---|---|---|
| Aqua | +0,077 (n=12) | **+0,307 (n=35)** |
| Terra | +0,179 (n=15) | **−0,084 (n=38)** |

Ou seja: na janela inteira a relação BLH–AOD em Aqua é **moderadamente positiva** (0,31),
não "quase independente". A frase "quase independentes **nesta janela**" (l. 218) é
sustentada por um recorte de 12 dias escolhido por uma variável de resposta.

**Por que importa.** Essa é uma das duas explicações que a correção nº 3 deixou para o
relatório. Ela é a que "justifica" o resultado nulo do ajuste vertical. Se a explicação se
 apoia num recorte não representativo da janela, o parágrafo fica mais frágil do que o
tom Moderate sugere.

**O que fazer.** Trocar por "nos 12 dias com PM2,5, r(BLH,AOD) = 0,08; em todos os 35 dias
com AOD é 0,31 — a dependência é real, o que sugere que o problema não é a
independência entre CL e AOD, e sim asample." Ou, mais honesto: **remover** a
"independência" da lista de explicações e dizer que a correção vertical precisa ser testada
com o perfil (que é o que o §4 propõe de qualquer forma).

### 🟡 Menor 6 — O IC 95% de bootstrap com n = 12 tem um artefato visível

**Evidência.** `codigo/03_prototipo_gee.py` l. 395–405 faz bootstrap **percentual** de
Spearman. Com n=12 e reamostragem com reposição, **5,9% das 2.000 reamostragens dão
r = 1,000 exato** (a mesma linha repetida). Daí o IC "0,56 a **1,00**" da tabela (l. 199) e
o "−1,00 a 1,00" da linha `Terra | AOD | PM2.5 Fercal` (n=6) no CSV. O relatório já
avisa que os ICs são largos (l. 209) e que "com 12 dias de Aqua, o 0,90 ainda pode ser
0,56" — a honestidade está lá — mas o "1,00" está impresso como se fosse um limite
interpretável, e o §8 chama o IC de "o antídoto" contra o exagero (l. 362).

**O que fazer.** Manter o IC, mas marcar que com n=12 o bootstrap de Spearman é degenerado
(o limite superior de 1,00 vem de reamostragens com a mesma linha repetida) e usar um
teste de permutação ou Fisher-z para o p-valor. Não é problema do resultado — é do
antídoto.

### 🟡 Menor 7 — "n = 18" (linha 203–204) rotula como "versão anterior" uma linha que é recalculada ao vivo

O script calcula `pool` (média diária de Terra+Aqua) **do zero** sobre os dados atuais
(l. 407–414). A tabela o chama de "*(média do dia, versão anterior)*", o que sugere um
arquivo antigo. Pior: o §"Correções de 31/10" (l. 418–420) fala de "**o número antigo
(0,22 para AOD/BLH)**" enquanto a tabela §4 mostra **0,06** para a mesma coisa — e −0,22 é o
valor **novo** de Terra. Três números diferentes ("antigo" 0,22; "versão anterior" 0,06;
novo −0,22) para quantidades que se sobrepõem, sem legenda que os separe.

**O que fazer.** Renomear a linha para "(média do dia, calculada para comparação)" e
distinguir explicitamente "número da versão anterior, que não está arquivado" de "valor
atual".

### 🟡 Menor 8 — O PM2,5 de Brasília está colado nas linhas de Goiânia e Porangatu

**Evidência.** `codigo/03_prototipo_gee.py` l. 318–322 monta `pm_dia` só com as estações do
DF e faz o merge **por data, sem chave de ponto**. Conferi: os valores de `pm25` de Goiânia
e Brasília são **idênticos** nos 46 pares de data comparáveis. As colunas `pm25_fercal` e
`pm25_escola` aparecem em **todos** os três pontos.

**Nenhuma conclusão publicada é afetada** — o relatório só correlaciona Brasília. Mas a
tabela entregue é o principal produto do pacote, e quem cruzar `pm25` por `ponto` vai
"descobrir" PM2,5 em Goiânia (que não existe). Como a pesquisadora quer exatamente
generalizar para Goiás, essa é uma armadilha cara.

**O que fazer.** Restringir o merge ao ponto de Brasília, ou adicionar uma coluna
`pm25_origem = "DF (BRASÍLIA)"` e preencher `NaN` fora de lá.

### 🟡 Menor 9 — As duas estações do DF estão a 21–23 km do ponto de AOD, e isso não é dito

**Evidência.** O ponto de AOD em Brasília é o centro da cidade (`codigo/comum.py` l. 26–30:
`-15.7939, -47.8828`), e o disco tem 10 km de raio. As estações do MonitorAr de 2024 estão
em `-15.601292, -47.870440` (CRAS Fercal) e `-15.589824, -47.842796` (Escola) — a
**21,5 km** e **23,1 km** do centro. Ou seja, **nenhuma das duas está dentro do disco de
AOD de 10 km.** (As coordenadas de 2025, que repetem o centro, ficariam a 5,3 km — e o
`CLAUDE.md` l. 85–86 manda usar as de 2024.)

O relatório nunca menciona essa separação espacial, e o §4 fala de "AOD × PM2,5 em
Brasília" como se fossem co-localizados.

**O que fazer.** Uma frase no §4 e no §7. É limitação real e vai aparecer em revisão.

### 🟡 Menor 10 — A tabela §2 mostra a fração noturna onde os dois pontos **parecem iguais**

A tabela (l. 73–77) traz "fração noturna (≤50 km)" = 0,49 / 0,49 — a **≤50 km**, onde
Brasília e Goiânia de fato se parecem. Mas o argumento da seção inteira é sobre **≤25 km**,
onde as frações noturnas são **0,58 (Goiânia) contra 0,13 (Brasília)** — uma diferença de
4,5× que a tabela não mostra. Quem só lê a tabela não vê o achado principal.

**O que fazer.** Trocar a coluna por "fração noturna a ≤25 km" ou acrescentar as duas.

### 🟡 Menor 11 — DOI do ATLID atribuído à versão errada, e a versão de 2026 já existe

O relatório diz (l. 53–54): "*versões BA, BB e BC, DOI de versão `10.57780/eca-bd87949`*".
O DOI resolve para a **coleção** "EarthCARE ESA L2 Products" **e** para a **versão AE**
do AER L2A; as versões BA, BB e BC têm DOIs próprios
(`10.57780/eca-8f242db`, `.../eca-c456d02`, `.../eca-ed27878`). E o catálogo já lista uma
versão **BD (2026)**, então "com versões de 2025" envelheceu.

### 🟡 Menor 12 — "CAL_LID_L1" sem versão, e sem script na pasta

`RELATORIO.md` l. 44–45 afirma que o nível 1B dá o mesmo instante final. **Conferi e é
verdade** (consultei o CMR). Mas: (a) não diz a versão (V5-00); (b) **nenhum script da
pasta testa o nível 1B** — `grep -rn "CAL_LID_L1" codigo/` não devolve nada —, então é um
número que a regra 2 das `REGRAS-COMUNS` ("todo número precisa ter saído de um script
desta pasta que você rodou") não consegue satisfazer; e (c) o Anexo "de onde saiu cada
número" não lista esse item.

### 🟡 Menor 13 — "4 blocos de AOD × 3 pontos" descreve 4 chamadas, não 12

`RELATORIO.md` l. 309–310: "*10 (4 blocos de AOD × 3 pontos, 3 de ERA5, 3 de FIRMS)*". O
total 10 **está certo** (4 chamadas de AOD, cada uma cobrindo os 3 pontos, + 3 + 3 — bate
com `dados/log_03.txt`). Mas a multiplicação "× 3 pontos" sugere 12 chamadas de AOD.

### 🟡 Menor 14 — `CLAUDE.md` diz "Goiânia tem 3× mais passagens a 5 km que Brasília"

`CLAUDE.md` l. 58–59. O número real é **17×** (154 contra 9). O "3×" não corresponde a
nenhum par do relatório (484/259 = 1,9×; 620/589 = 1,05×). Como o `CLAUDE.md` é o arquivo
que **a IA dela vai ler** para continuar o trabalho, um número errado ali propaga.

### 🟡 Menor 15 — "n_pm25" é uma coluna morta que sempre vale 0

`codigo/02_estacoes_pm25.py` l. 89 e l. 109 põem `"n_pm25": 0` com o comentário
`# preenchido abaixo` — e não preenchem abaixo. O `pm25_estacoes_monitorar_go_df.csv`
entregue tem `n_pm25 = 0` nas quatro linhas, ao lado de `mede_pm25_provavel = True`. Quem
abrir o arquivo lê "0 registros de MP2,5" numa estação que mede MP2,5.

### 🟡 Menor 16 — "Registros 2024: 12.201 / 3.503" na tabela §3 são de **todos os poluentes**

A tabela §3 (l. 144–147) tem colunas "Registros 2024" e "Registros 2025" ao lado de uma
coluna "Poluentes" que inclui MP2,5 — a leitura natural é "registros de MP2,5". São
registros de **todos os poluentes**: extraí do `monitorar_2024.zip` e os registros de MP2,5
são **579** (CRAS Fercal) e **1.190** (Escola). E o "Início 14/08/2024" é o primeiro
registro de **qualquer** poluente: a primeira MP2,5 do Fercal é 21/09/2024 e da Escola
19/09/2024.

### 🟡 Menor 17 — `n_50km`/`n_5km` no JSON × CSV: 1 de diferença por arredondamento

Ver §2.2, item 29.

### 🟡 Menor 18 — A coluna `focos` conta **pixels de fogo**, não detecções do FIRMS, e o produto é near-real-time

**Evidência.** No `codigo/03_prototipo_gee.py` l. 208–211, `fogo` é o booleano
`T21.gt(300).And(confidence.gte(30))` e o `reduceRegion` soma esses 0/1. O resultado é
uma **contagem ponderada por área de pixels de 1 km** (daí os valores fracionários: 0,141,
16,5, 963,7 — pixels cortados pela borda do buffer de 100 km). Confirmei que **não** é soma
de T21 em Kelvin: se fosse, o menor valor positivo seria ≥300 K; o menor observado é
0,141. Ou seja, o número está certo — "963 focos" = ~963 km² com detecção de fogo em 100 km
de raio em 3 dias, plausível no Cerrado em queima.

Dois detalhes, porém, não estão no relatório:

1. O catálogo do Earth Engine descreve a coleção `FIRMS` como o produto **near-real-time**
   da LANCE e diz, textualmente, que *"the data in the near-real-time dataset are **not
   considered to be of science quality**"*. O relatório usa `focos` como covariável sem
   essa ressalva. Para uma tese, citar a coleção NRT sem o aviso é uma fragilidade
   evitable: a alternativa é o produto de arquivo (MCD14/MYD14, science quality), que
   exige conta Earthdata — a mesma conta que ela já vai usar para o CALIOP.
2. A mesma página explica que **várias detecções que caem no mesmo pixel de 1 km são
   fundidas em um só pixel** (fica o de maior confiança). Portanto "focos" é contagem de
   *pixels*, não de *detecções*. A distinção importa ao comparar com contagens do FIRMS
   em CSV.

**O que fazer.** Uma ressalva no §4 ("pixels de fogo, produto NRT, não science quality")
e, se ela quiser citar contagens de fogo na tese, trocar pelo MCD14/MYD14 de arquivo.

### 🟡 Menor 19 — `frac_fumaca` é calculada, entra na tabela e nunca é citada — e é a variável mais relevante para a tese

**Evidência.** `codigo/03_prototipo_gee.py` l. 159 extrai os **bits 13–14 do `AOD_QA`**
(o "modelo de aerossol" do MAIAC — catálogo oficial: *"1: Smoke model"*) e calcula a
fração de pixels de fumaça na área, que vai para a coluna `frac_fumaca` da tabela
entregue. Conferi o catálogo do Earth Engine: a leitura dos bits está **correta**.

O relatório **não menciona `frac_fumaca` nenhuma vez** (grep: 0 ocorrências em
`RELATORIO.md` e `README.md`), e a figura também não a usa — a cor dos pontos no scatter
é `focos_3d`, e a legenda do painel do meio mostra só BLH.

Isso é uma lacuna de aproveitamento, não um erro: a fração de pixels identificados como
*fumaça* pelo MAIAC é, na teoria, exatamente o discriminante entre aerossol de queima e
fundo regional que a tese precisa — e ela **já está calculada e verificada** na tabela
entregue. Na janela do protótipo ela varia de 0 a 0,99, com 14 das 217 linhas acima de
0,30 (média 0,05), o que sugere que dá para separar dias de queimada de dias limpos.

**O que fazer.** Citar a variável no §4 e usá-la como terceiro eixo de cor no scatter
`AOD × PM2,5` (hoje é `focos_3d`), e transformá-la em covariável na próxima etapa. É uma
das poucas coisas que a tabela já tem e o texto não usa.



**O que está honesto, e acima do esperado:**

1. **O §5(b) não vende o próprio desenho de validação.** Os três desenhos ficam lado a
   lado, incluindo o errado (0,95) e o que dá 0,61, com a frase "a diferença de 0,34 entre
   blocos de tempo e sorteio é o 'otimismo' que o sorteio produz". É o resultado que
   convém ao leitor ver.
2. **O §5(d) recusa-se a ajustar modelo** com 1 estação e 18 dias, e diz isso na
   íntegra em vez de mostrar um R² apresentável. O `04_validacao.py` de fato não ajusta
   modelo algum nos dados reais.
3. **O §7 é uma lista de limites de verdade**, não decorativa: janela de 61 dias, erro de
   ~1 km da polilinha do CMR, escolha conservadora da máscara de QA, "o ajuste vertical
   testado é o mais grosseiro", "Terra e Aqua não foram combinados". E a §6 lista os
   erros que deram errado (CMR 500, CloudFront 403, `reduceRegion` com nula,
   `filterBounds` que não filtra, a máscara de QA invertida) com o conserto de cada um.
4. **O §7 (l. 330) é explícito:** "*A demonstração de vazamento usa dados simulados. Os
   números dela servem para escolher o desenho de validação, não para descrever Goiás.*" —
   exato. E o `04_validacao.py` tem o mesmo aviso no docstring (l. 15–16).
5. **O teste `test_sorteio_de_linhas_falha` existe** justamente para provar que o detector
   não é decorativo. A existência do controle é mais rara que a boa execução dele.
6. **A §"Correções de 31/10" registra o que mudou, inclusive o bug da umidade** que a
   própria IA.previous encontrou — e a correção está no código e no dado.
7. **A §3 registra as portas fechadas com honestidade**: OpenAQ 401 e 410, IBRAM exigindo
   login, Cimehgo devolvendo série vazia, Sensor.Community com 0 sensores. Confirmei os
   códigos HTTP no `pm25_sondagens_http.csv`.
8. **A §2 registra a assimetria que é contra a própria tese** (Brasília sem passagem
   noturna a ≤25 km) e a lê como limitação do dado, não como problema aHide.

**O que é exagero ou impreciso:**

| Onde | O que diz | Problema |
|---|---|---|
| l. 221 e l. 322 | "a máscara de QA não está dirigindo o resultado (1,00 entre AOD com e sem filtro) — bom controle" | O número exibido não testa a frase (item 4). A conclusão é verdadeira, mas precisa de outro número — e há viés de nível de −1% a −4% que o controle de posto não vê. |
| l. 218 | "a CL e o AOD são quase independentes nesta janela (0,08 em Aqua)" | O 0,08 é de 12 dias; na janela inteira é 0,31 (item 5). |
| l. 190 | "AOD de 0,056 a 0,947" | O mínimo é 0,043 (item 27). |
| l. 73–77 | "fração noturna 0,49 / 0,49" | É o valor pooled repetido; por ponto 0,49 e 0,48 (item 28). |
| l. 418 | "1.120 m e 2.512 m (mesmos pontos e mesmos dias)" | São dias diferentes (item da Correção 2). |
| l. 23, 175, 199, 201, 212, 398, 413 + `CLAUDE.md` 61 + `README.md` 64 + legenda da figura | "Terra ~10h30, Aqua ~13h30" | Os dados dizem ~09h45 e ~14h40. |
| l. 446–447 | "66,9% quando o correto é 18,3%" | Caso específico não arquivado; não conferível a partir do pacote. |
| l. 53–54 | "versões BA, BB e BC, DOI de versão 10.57780/eca-bd87949" | É o DOI da coleção e da versão AE (item 11). |
| l. 44–45 | "O mesmo teste no nível 1B (CAL_LID_L1) dá o mesmo instante final" | Verdade, mas sem script na pasta e sem versão (item 12). |
| l. 309–310 | "4 blocos de AOD × 3 pontos" | São 4 chamadas (item 13). |

**Nada no relatório afirma algo que não foi conferido** — o padrão de honestidade é alto.
As imprecisões acima são de **rótulo e de padronagem**, não de invenção.

**Uma coisa que o relatório esconde — não por má-fé, mas por omissão: o custo da máscara de
QA.** "A máscara de QA do MAIAC é uma escolha (a mais conservadora)" (l. 321) soa como
detalhe menor. Na prática ela **descarta 58% dos registros granulo×ponto** e faz a
correlação de Aqua descansar de uma mediana de **33 pixels**. Isso é informação que muda a
decisão "Aqua como satélite principal" que o `README.md` coloca na mão dela. O relatório
não a esconde de propósito — simplesmente não a mediu.

---

## 6. Utilidade para a pesquisadora

### O que o pacote responde do `CONTEXTO.md`

| Pedido | Situação |
|---|---|
| "desenvolver um procedimento computacional para integrar observações orbitais do MODIS, perfis verticais do CALIOP, ERA5 e CATT-BRAMS" | **Parcial, com a parte mais difícil feita.** MODIS + ERA5 + FIRMS: protótipo executado e entregue. CALIOP: viabilidade quantificada (que é a pergunta que pode matar a tese) + leitor HDF4 pronto, mas **nenhum arquivo real lido**. CATT-BRAMS: só o desenho do teste de dependência, sem dados (correto — a saída não é pública). |
| "compatibilizar dados com diferentes resoluções espaciais, temporais e verticais, preservando critérios de qualidade" | **Feito no eixo temporal** (o bug Terra×Aqua era exatamente isso) e **documentado** no eixo vertical (leitor + `fracao_abl`). |
| "seleção de variáveis relacionadas à dinâmica vertical" | **Não entregue.** Nenhum passo de seleção de variáveis; o pacote correlaciona o que tem. |
| "evitar dependências inadequadas entre preditores e variável-alvo" | **Entregue e é o segundo melhor item do pacote**: os três desenhos, o detector de vazamento com teste que reprova o desenho errado, e o teste de cópia com o CATT-BRAMS. |
| "base de dados consistente e reproduzível" | **Quase.** Falta a reprodutibilidade numérica do §4 (item 1) e o marcador de qualidade por linha (`n_px`, item 2). |
| "investigação sobre o papel da IA generativa na construção das rotinas" |respondida na §8 do relatório, com honestidade (o que a IA fez bem: ler documentação, achar armadilhas, escrever o teste, montar controles; o que não faz: decidir método, preencher lacuna de dado, garantir número). Adequada ao formato. |

### As três lacunas que mais pesam para a tese

1. **Não existe PM2,5 público em Goiás.** A §3 é definitiva e honesta. As três saídas
   (pedido formal à SEMAD, CATT-BRAMS como referência, campanha própria) são as
   corretas. **Falta uma coisa:** o pacote não testa se o **MonitorAr de 2025** (que ela
   tem, 31,8 MB, com 4.926.747 registros e DF presente) dá **cobertura melhor** que 2024
   para calibrar com mais dias. `pm25_estacoes_monitorar_go_df.csv` mostra a Escola com
   **7.675** registros em 2025 e o Fercal com **32.772** — e o `CLAUDE.md` l. 84 já lembra
   disso ("para a estação de queimadas use 2025 se quiser mais dias"). Só que 2025 traz as
   coordenadas repetindo o centro de Brasília, o que muda a geometria da associação. Vale
   um teste de 5 minutos: 2025 × raio maior, com a estação de queimadas.
2. **O teste central — fração do AOD na camada limite — nunca rodou com dado real.** O
   leitor (script 05) está pronto e autotestado, mas o `fracao_abl` é a variável que a
   tese precisa, e ela nunca foi calculada sobre um perfil do CALIOP. **Todo o resto da
   tese depende disso.** O passo a passo de download está no `README.md` l. 73–88.
3. **Falta um passo de validação *espacial* de verdade.** Com 1 estação do DF, o desenho
   "deixar uma estação de fora" (que o §5 desenha) **não pode ser executado** — não há
   segunda estação. E o DF tem 2 estações a 21–23 km do centro, que o §5 já mostra ser
   0,94 no simulador e 0,61 em blocos de tempo. Com 2 estações a 21 km e o disco de AOD
   a 10 km do centro, dá para montar um teste espacial real (ainda fraco, mas real) e
   medir quanto de R² "deixando a estação de fora" sobrevive sem dia compartilhado. É o
   teste que separa "o modelo generaliza" de "o dia seguinte generaliza".

### Roteiro mínimo que eu faria a seguir (≈2 h de trabalho, tudo local)

| # | Ação | Por quê | Onde |
|---|---|---|---|
| 1 | Gravar `aod_km` com 4+ casas decimais; recomputar as correlações do CSV entregue | Elimina a não-reprodutibilidade do §4 (item 1) | `03_prototipo_gee.py` l. 330, 373 |
| 2 | Reportar `n_px` em todas as linhas e citar o corte de pixels + a sensibilidade | Torna a comparação Aqua×Terra auditável (item 2) | `03_prototipo_gee.py` + §4 |
| 3 | Trocar os rótulos de hora por "Terra ~09h45, Aqua ~14h40" e corrigir "mesmos dias" → "27 dias comuns: 1.197 vs 2.668 m" | Fecha a Correção 2 (que é o pedido que está em aberto) | `RELATORIO.md` l. 23, 175, 199, 201, 212, 398, 413, 418; `CLAUDE.md` l. 61; `README.md` l. 64; legenda da figura |
| 4 | Trocar o controle de QA por `r(AOD sem QA, PM2,5)` e acrescentar o viés de nível | O controle passa a sustentar a frase (item 4) | `RELATORIO.md` l. 221, 322 |
| 5 | Restringir o PM2,5 ao ponto de Brasília (ou marcar a origem) | Remove a armadilha de "PM2,5 em Goiânia" (item 8) | `03_prototipo_gee.py` l. 318–322 |
| 6 | Rodar o leitor do CALIOP em **um** arquivo real (junho/2023 ou ago–out/2015) e reportar o `fracao_abl` mediano | É o teste central da tese, ainda não feito | `README.md` l. 73–88 |
| 7 | Corrigir "3× mais passagens a 5 km" → "17×" | O `CLAUDE.md` é lido pela IA dela (item 14) | `CLAUDE.md` l. 58–59 |
| 8 | Ajustes de texto menores (0,056→0,043; fração noturna por ponto; "5 folds" → "4 folds" na linha da estação; "versão anterior" → "recalculado para comparação"; DOI do ATLID; `n_pm25`; "Registros" → "registros (todos os poluentes)"; "focos" → "pixels de fogo (produto NRT)") | Higiene de rastreabilidade | vários |

---

## 7. O que eu não consegui verificar, e como você pode conferir

| Item | Como verificar |
|---|---|
| O script 01 inteiro (CMR, rede) | Não rodei — baixa metadados do CMR. Verifiquei as **saídas** recalculando tudo a partir de `dados/calipso_granulos_brutos.csv` e `calipso_passagens_eventos.csv`, e conferi o último granulo com uma consulta direta ao CMR. |
| O script 02 (baixa 92 MB do MMA) | Não rodei. Verifiquei as **saídas** reabrindo `monitorar_2024.zip` e contando MP2,5 por estação — foi assim que achei o problema das 579 vs 12.201. |
| O script 03 (Earth Engine) | Não rodei, por instrução. Verifiquei as **saídas** recalculando todas as correlações e resumos a partir dos CSV entregues, e conferi a máscara de QA contra o catálogo oficial do EE. |
| Tempo de execução de `rodar_tudo.py` | `dados/log_rodar_tudo.txt` não tem timestamp. Sem forma de verificar os "8 minutos". |
| Atraso real de órbita do CALIPSO depois de 2019 | A explicação do §2 (l. 97–98) é plausível e consistente com os dados do pacote (o número de granulos na caixa cai ~20% depois de 2019, o que é o que a grade deslocada produziria), mas **não há script na pasta que teste isso** e eu não consultei a fonte orbital. Afirmação apoiada, não demonstrada. |

---

## 8. Encaminhamento

**Sobre as correções:** 3 de 4 estão prontas. A nº 2 está **concluída no código e aberta no
texto** — e é justamente o texto que a correção pedia ("deixe claro e coerente: qual hora
do ERA5 entra"). Fechá-la custa ~30 minutos de edição em 4 arquivos.

**Sobre o pacote como um todo:** ele está **acima da média** no que costuma estar errado
nestes trabalhos — a parte difícil (contar de verdade quanto perfil vertical existe sobre
GO/DF) foi feita com controles geométricos reais, e o desenho de validação tem um teste
que reprova o desenho errado. As conclusões do §4 que sobrevivem a **todas** as reanálises
que fiz. Os problemas são de rastreabilidade e de rótulo, nenhum de conceito.

**A sequência que eu recomendo:** itens 1–5 da tabela do §6 (≈2 h, tudo local, sem rede),
depois **item 6** — baixar **um** arquivo do CALIOP e rodar o leitor. Enquanto o
`fracao_abl` não tiver sido calculado sobre um perfil real, a pergunta que a tese formula
("como a distribuição vertical entra na relação AOD–PM2,5") continua respondida apenas
pelos **meios**: o ajuste grosseiro AOD/BLH, que deu negativo. O `fracao_abl` é o
experimento que decide o resto.

---

*Conferência conduzida sobre a pasta `jackeline` em 31/10/2026. Nenhum arquivo da pasta
foi alterado; as execuções foram feitas em cópia isolada sob
`<pasta>\jackeline` e as mtimes originais foram
reconferidas ao final.*
