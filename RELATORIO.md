# Relatório — AOD, perfil vertical e meteorologia para PM2,5 em Goiás e no DF

Encontro de 31/10/2026. Tudo o que está aqui foi executado nesta pasta; todo número
abaixo sai de um script indicado ao lado (tabela de origem no fim).

## Resumo em sete linhas

1. O CALIPSO **acabou em 01/08/2023**, mas o último granulo do produto de aerossol é de
   **30/06/2023** — o acervo fecha um mês antes do fim oficial (verificado no CMR).
2. O sucessor é o **ATLID, a bordo do EarthCARE**: dados de nível 1 públicos desde
   16/01/2025 e o produto de aerossol nível 2A (AER) com versões até **BD (2026)**, mas
   **acesso exige conta EO Sign In**.
3. Sobre Goiânia há **33 passagens/ano a ≤25 km** entre 2007 e 2018, **19,6 delas à noite**;
   sobre Brasília, 17/ano — mas **quase nenhuma à noite** (0,3/ano) nesse período. Depois de
   2019 o total cai (15 e 11/ano) e, em Brasília, a grade orbital se desloca.
4. Na **estação de queimadas (ago–out)**, Goiânia tem **72 passagens noturnas a ≤25 km em
   18 anos**; Brasília tem **8**. Ou seja: em Brasília o perfil vertical noturno, na
   época que interessa, praticamente não existe a 25 km.
5. **Goiás não tem série pública de PM2,5.** O MonitorAr (MMA) só passou a ter o DF: as
   duas estações entram em 14/08/2024 e o MP2,5 começa em 19/09/2024. Isso limita qualquer
   calibração em Goiânia com dado aberto.
6. O protótipo foi refeito no ponto **Fercal** (dentro do disco das duas estações de PM2,5),
   de 19/09/2024 a 31/12/2025, com Terra e Aqua separados: **166 pares dia-satélite** com AOD
   e PM2,5 horário. Aqua dá AOD × PM2,5 = **0,35** e Terra **0,27**; **dividir pela camada
   limite piora nos dois** (0,22 e 0,19). E a tentativa de selecionar variáveis com validação
   por semanas **não supera o baseline da média** — o que este n permite concluir é só que o
   método está pronto, não que há ranking de variáveis.
7. O desenho de validação está implementado e testado: separar **por estação** (estimar onde
   não há sensor, no mesmo dia) e por **blocos de tempo** (prever dias novos), com teste
   automático que falha se um dia/estação aparecer nos dois lados, e um teste específico para
   o caso do CATT-BRAMS como preditor.

---

## 1. Período do CALIOP/CALIPSO e o que veio depois

**Fim da missão.** NASA e CNES encerraram a missão científica do CALIPSO em **1º de agosto
de 2023**, por esgotamento do combustível (`https://www.earthdata.nasa.gov/news/official-end-calipso-science-mission`,
publicado em 02/08/2023; a página da missão em `https://science.nasa.gov/mission/calipso/`
repete a data).

**Último dado disponível.** O CMR tem duas versões do produto `CAL_LID_L2_05kmAPro`:
V4-51 e **V5-00 (a mais recente)**. A consulta ordenada por data (script `01`) devolve como
último granulo `CAL_LID_L2_05kmAPro-Standard-V5-00.2023-06-30T21-39-53ZD.hdf`, às
**2023-06-30T21:39:53Z**. O mesmo teste no nível 1B (`CAL_LID_L1`) dá o mesmo instante final:
**o acervo termina em 30/06/2023**, um mês antes do encerramento oficial. Vale registrar isso
no texto da tese — quem procurar julho de 2023 não vai achar nada.

**Sucessor: ATLID, no EarthCARE.** O EarthCARE (ESA/JAXA) foi lançado em maio de 2024. O
fluxo de dados de **nível 1** ficou público em **16/01/2025**
(`https://www.esa.int/Applications/Observing_the_Earth/FutureEO/EarthCARE/EarthCARE_goes_live_with_data_now_available_to_all`),
com a ressalva de que é preciso criar conta. Os produtos de **nível 2 de instrumento único**
começaram a sair em 2025: o catálogo da ESA lista o **"EarthCARE ATLID AER Level 2A"** com
versões até **BD (2026)**, cada versão com DOI próprio (BA `10.57780/eca-8f242db`,
BB `10.57780/eca-c456d02`, BC `10.57780/eca-ed27878`); `10.57780/eca-bd87949` é o DOI da
**coleção** "EarthCARE ESA L2 Products", não de uma versão. Catálogo em
`https://earth.esa.int/eogateway/catalog/earthcare-esa-l2-products`. O acesso é "aberto,
mas com EO Sign In": cadastro obrigatório, download pela ESA MAAP Explorer ou por STAC com
token. O algoritmo do produto está descrito no artigo de Donovan et al. (2024), conferido
em `REFERENCIAS.md`.

**O que isso significa para a proposta.** O ATLID é o substituto natural do CALIOP, mas é
uma série nova, com ~1,5 ano de dados (e nível 2A ainda em consolidação). Para uma tese que
precisa de climatologia de 10 anos, o CALIOP continua sendo a base; o ATLID entra como
comparação e como perspectiva.

---

## 2. Quantas passagens existem de verdade (CMR, 2006–2023)

Método (script `codigo/01_calipso_cmr.py`, sem login): para cada ponto e cada ano, busca no
CMR os granulos de `CAL_LID_L2_05kmAPro` V5-00 cuja trajetória entra numa caixa de ±1,5°;
calcula a distância do ponto à polilinha da trajetória (geometria `Lines` do UMM); conta as
passagens a ≤5, 25 e 50 km; separa dia e noite pelo sufixo do arquivo (`ZN`/`ZD`).

| Ponto | ≤5 km | ≤25 km | ≤50 km | fração noturna ≤25 km | fração noturna ≤50 km |
|---|---|---|---|---|---|
| Goiânia | 154 | **484** | 620 | **0,58** | 0,49 |
| Brasília | 9 | **259** | 589 | **0,13** | 0,48 |

São 3.705 granulos na caixa (2.427 únicos, porque os dois pontos compartilham granulos),
todos 2006–2023. Recontando a partir do CSV (distâncias arredondadas a 2 casas), o total a
≤50 km de Goiânia dá 621 em vez de 620; a diferença de 1 é arredondamento, e o valor de
referência é o do JSON, com precisão plena. As frações noturnas por ponto e por raio saem de `codigo/08_checagens.py`
(`dados/checagens.json`) — a versão anterior da tabela repetia o valor agregado dos dois
pontos (0,49) nas duas linhas e escondia a diferença de 4,5× a ≤25 km, que é o achado.

**Por ano e por dia/noite (≤25 km)** — figura `figuras/calipso_passagens.png`, tabela
`dados/calipso_passagens_por_ano.csv`:

| Período | Goiânia | Brasília |
|---|---|---|
| média 2007–2018 | **33,4/ano** (19,6 à noite, 13,8 de dia) | **16,6/ano** (0,3 à noite, 16,2 de dia) |
| média 2019–2022 | 14,8/ano (8,2 à noite) | 11,0/ano (6,5 à noite) |
| 2023 (dados até 30/06) | 4 | 5 |

A assimetria entre os dois pontos é o achado mais importante desta seção. Em **Brasília, entre
2007 e 2018, praticamente não houve passagem noturna a ≤25 km** (0,3/ano): a grade orbital
deixava a trajetória noturna a mais de 25 km. Só depois de 2019, quando a órbita baixou e a
grade se deslocou, começam a aparecer noites (6,5/ano). Como o dado diurno do CALIOP tem
relação sinal/ruído baixa para aerossol, **em Brasília o perfil vertical utilizável é
escasso justamente nos anos de referência**.

A queda depois de 2019 acompanha a degradação da órbita (a altitude caiu e a grade de
trajetórias mudou de posição). Não é falha de busca: as passagens ficaram mais longe.
A razão entre Goiânia e Brasília a ≤5 km é de **17,2×** (154 contra 9).

**Estação de queimadas (ago–out)**, o número que mais importa — `dados/calipso_estacao_queimadas.csv`:

| Ponto | noite ≤25 km | dia ≤25 km | noite ≤50 km | dia ≤50 km |
|---|---|---|---|---|
| Goiânia | **72** (4/ano) | 54 | 79 | 78 |
| Brasília | **8** (0,4/ano) | 63 | 71 | 77 |

**Leitura prática.** Para Goiânia, dá para fazer estudo de caso noturno na estação de
queimadas (~4 noites por ano, 72 no total) e climatologia mensal com 2 a 3 perfis/mês. Para
Brasília, a 25 km quase não há noite em ago–out: ou se usa **50 km** (4/ano), ou o perfil
vira apenas contexto regional. **O CALIOP não sustenta um preditor diário por estação** — a
não ser que se aceite interpolar no tempo, o que é uma decisão metodológica dela.

**Por que a contagem não cresce com a área (e por que isso é bom sinal).** A órbita repete a
mesma grade de trajetórias a cada 16 dias: o que decide o número de passagens é o "encaixe"
do ponto na grade, não a área do círculo. Isso explica Goiânia ter 484 passagens a 25 km e
Brasília 259, e Goiânia ter 154 a 5 km contra 9 em Brasília. **Controles que confirmam que a
geometria está certa** (`dados/calipso_controle.json`):
- distância calculada por dois métodos independentes (projeção no grande círculo ×
  amostragem densa da polilinha): diferença máxima **1,19 km**, mediana **0,58 km**;
- intervalo mediano entre passagens do mesmo período do dia: **16,0 dias** nos quatro casos
  — exatamente a repetitividade orbital, o que só acontece se as passagens identificadas
  forem reais;
- contagem monotônica em 5 < 25 < 50 km, como esperado;
- as contagens a ≤5 km são o piso de confiança da geometria (a polilinha do CMR tem ~10
  pontos por meia-órbita), então **use 25 km como raio mínimo** em qualquer análise.

---

## 3. Estações de PM2,5 em Goiás e no DF

Tudo verificado por HTTP e por leitura dos arquivos (script `codigo/02_estacoes_pm25.py`;
`dados/pm25_fontes.csv`, `dados/pm25_sondagens_http.csv`).

| Fonte | UF | O que oferece | Período | Acesso | Situação |
|---|---|---|---|---|---|
| **MonitorAr (MMA)** | Brasil | CSV anual por estação, todos os poluentes | 2022–2025 | aberto, sem login | **GO: 0 estações. DF: 2 estações** (a partir de 14/08/2024) |
| SEMAD-GO / Cimehgo | GO | páginas e boletins de qualidade do ar | páginas paradas em 2021 | sem download | API do Cimehgo devolve só meteorologia (série vazia nas datas testadas) |
| IBRAM-DF (portal ONDA) | DF | camadas ArcGIS | — | **login ArcGIS** | não acessível sem conta |
| OpenAQ | Brasil | agregador, API v3 | — | **exige chave** | v3 = HTTP 401; v2 aposentada (HTTP 410) |
| Sensor.Community | GO/DF | sensores de baixo custo | tempo real | aberto | 0 sensores na caixa de Goiânia no momento da consulta |

**As duas estações do DF** (`dados/pm25_estacoes_monitorar_go_df.csv`):

| Estação | Registros 2024 (todos os poluentes) | Registros de MP2,5 em 2024 | 1º registro de MP2,5 | Registros de MP2,5 em 2025 | Poluentes |
|---|---|---|---|---|---|
| CRAS Fercal | 12.201 | **579** | 21/09/2024 | 2.585 | SO₂, NO₂, MP10, **MP2,5**, MP, CO, O₃ |
| Escola | 3.503 | **1.190** | 19/09/2024 | 2.322 | MP10, **MP2,5** |

As colunas de 2025 têm 32.772 e 7.675 registros **de todos os poluentes** (não de MP2,5); o
primeiro registro de qualquer poluente é 14/08/2024, mas o MP2,5 só começa em setembro.

Cobertura nacional do MonitorAr em 2025: 13 UFs, 4,9 milhões de registros horários — e
Goiás não está entre elas (`dados/monitorar_cobertura_por_uf.csv`). **Esse é o gargalo do
projeto**: sem PM2,5 em Goiás, qualquer modelo para o estado depende de (a) pedido formal à
SEMAD, (b) dados do CATT-BRAMS como referência, ou (c) campanha própria.

**Atenção a duas armadilhas do arquivo** (documentadas em `CLAUDE.md`): o nome da coluna de
situação muda de 2024 (`st_situacao_item`) para 2025 (`st_situacao`), e as coordenadas das
estações do DF em 2025 vêm repetindo o centro de Brasília — use as de 2024.

---

## 4. Protótipo de associação no ponto Fercal (19/09/2024 a 31/12/2025)

O protótipo anterior usava o centro de Brasília, a **21,5–23,1 km** das duas estações de
PM2,5 — fora do disco de AOD. Agora ele usa o ponto **Fercal** (−15,5955/−47,8566), no meio
das duas estações (1,62 km da CRAS Fercal e 1,61 km da Escola), e um raio de **10 km**
(`codigo/03_prototipo_gee.py`). As estações ficam dentro do disco, e o cruzamento espacial
passa a ser defensável.

**Como cada variável entrou**
- **AOD MAIAC** (`MODIS/061/MCD19A2_GRANULES`, 550 nm, 1 km): média no disco de 10 km na
  hora do granulo. Máscara conservadora do `AOD_QA`: nuvem claro (bits 0–2 = 1), adjacência
  normal (5–7 = 0), QA do AOD "melhor qualidade" (8–11 = 0), sem glint (bit 12 = 0).
- **Terra e Aqua separados**: uma linha por granulo, com a propriedade `SATELLITE`, hora UTC
  e hora local. O ERA5 entra na hora cheia mais próxima **daquele granulo**. Nesta série,
  Terra vai de **08:00 a 10:40** local (média **09:21**) e Aqua de **13:25 a 16:30** (média
  **14:57**) — note que é a hora de **início do granulo**, não do cruzamento exato do ponto
  (o ponto é cruzado alguns minutos depois; a janela de PM de ±1 h absorve isso).
- **ERA5 horário**: altura da camada limite, vento 10 m, temperatura e ponto de orvalho
  (convertidos para °C; umidade por Magnus), **CAPE** e **CIN**.
- **Derivadas**: déficit do ponto de orvalho (T − Td) e coeficiente de ventilação
  (BLH × vento, m²/s).
- **O que foi procurado e não existe sem login**: altura da camada de mistura do
  CATT-BRAMS (saída não pública); temperatura em níveis de pressão para um gradiente local
  (o ERA5 horário no GEE só traz 500/850 hPa como campos sinóticos, não como perfil no
  ponto); e um índice de estabilidade observado por estação (nenhuma das duas publica
  perfil). Ficaram **BLH, AOD/BLH, `frac_fumaca`, vento, umidade, temperatura, déficit de
  orvalho, ventilação, CAPE e CIN**.
- **FIRMS**: soma de **pixels de fogo de 1 km** com `T21 > 300 K` e confiança ≥ 30%, num
  raio de 100 km, acumulados em 3 dias. É o produto **NRT** (near-real-time) da LANCE, que
  **não é considerado de qualidade científica** pelo próprio catálogo; serve para o
  exercício, e para a tese convém trocar pelo MCD14/MYD14 de arquivo (mesma conta Earthdata
  do CALIOP). O valor é contagem de pixels, **não** de detecções: várias detecções no mesmo
  pixel de 1 km são fundidas.
- **PM2,5**: série horária das duas estações. O fuso do `dh_medicao` não está declarado no
  dicionário do MMA; o ciclo diurno observado (mínimo às 15–16 h, máximo às 21–22 h) é
  consistente com **hora local**, e é assim que os dados foram usados. Duas métricas:
  `pm25_hora` (média em ±1 h em torno da passagem) e `pm25_dia18`/`pm25_dia12` (média do
  dia com ≥18 h e com ≥12 h válidas).

**Cobertura (é o número que mais importa aqui)**
- 1.315 registros granulo × ponto; **884 (67,2%) não têm nenhum pixel válido** depois da
  máscara de QA. A máscara é conservadora e, na série de 15 meses, custa dois terços dos
  registros — muito mais do que na janela curta de 2024.
- Só **431** registros têm AOD; **306** passam o piso de **20 pixels** (Terra 196, Aqua 110).
- PM2,5 horário existe em **355 dias**; com ≥18 h, **134 dias**; com ≥12 h, **243 dias**.
- Cruzando AOD (piso 20) com PM horário: **166 pares dia-satélite** (Terra 108, Aqua 58),
  em **131 dias distintos**.

**Piso de pixels: por que 20.** O disco de 10 km tem ~314 pixels de 1 km. A mediana de
pixels válidos é **265 em Terra** e apenas **25 em Aqua** (33 nos dias com PM). Sem piso,
um "AOD" pode ser a média de 1–3 pixels. Com piso 20 (~6% do disco), ficam 306 registros e
o AOD deixa de depender de amostras minúsculas. A sensibilidade:

| Piso | Aqua: AOD × PM2,5 | Aqua: AOD/BLH × PM2,5 | Terra: AOD × PM2,5 | Terra: AOD/BLH × PM2,5 |
|---|---|---|---|---|
| nenhum | 0,280 (n=106) | 0,174 | 0,271 (n=120) | 0,188 |
| **≥20 (adotado)** | **0,353** (n=58) | **0,217** | **0,271** (n=108) | **0,194** |
| ≥50 | 0,321 (n=42) | 0,158 | 0,295 (n=103) | 0,200 |

A direção não muda com o piso; o valor de Aqua oscila 0,28–0,35 — a incerteza amostral é
maior que o efeito do filtro. Mas a comparação entre satélites **não é de qualidade igual**:
Aqua tem mediana de 25–33 pixels e 47% dos registros abaixo de 20 px; Terra tem 265–295 px
e 13% abaixo de 20 px.

**Correlações (Spearman), alvo PM2,5 na hora da passagem, piso 20**
— `dados/selecao_variaveis_correlacoes.csv`:

| Satélite | n | AOD × PM2,5 | AOD/BLH × PM2,5 |
|---|---|---|---|
| Aqua | 58 | **0,35** | 0,22 |
| Terra | 108 | **0,27** | 0,19 |

Alvo diário (`pm25_dia18`), que tem menos ruído: Aqua 0,23 (n=37) contra 0,11 do AOD/BLH;
Terra **0,46** (n=70) contra 0,39.

**Como interpretar (sem exagerar).**
1. **Dividir o AOD pela altura da camada limite não ajudou** em nenhum dos dois satélites,
   nem no alvo horário nem no diário. A correlação cai de 0,35→0,22 (Aqua) e 0,27→0,19
   (Terra).
2. **A explicação simples não é "BLH e AOD são independentes".** Na janela inteira, BLH e
   AOD andam **juntos** (Aqua +0,33, n=110; Terra +0,30, n=196 — `dados/checagens.json`). E BLH não se comporta como
   diluidor: em Aqua ele acompanha o PM2,5 (+0,39 no alvo horário, +0,52 no diário); em Terra
   quase não acompanha (+0,05 e +0,12). Ao longo do ano, o sinal de BLH é dominado pelo ciclo
   sazonal — camada alta na seca, com mais fogo e mais PM —, então dividir por ele remove
   parte do sinal sazonal, e não a diluição de curto prazo que a correção pretendia.
3. **Terra × Aqua em dias diferentes.** Aqua tem 110 dias válidos e Terra 196, com **80
   dias comuns**. Nos **35 dias comuns com PM horário**, Aqua dá 0,22 e Terra 0,09 — a
   diferença entre 0,35 e 0,27 vem, em boa parte, de amostras diferentes. A comparação
   honesta é a pareada, e nela os dois são fracos.
4. **O controle de QA que vale.** O número anterior (r entre AOD com e sem filtro = 0,996)
   comparava a variável com ela mesma. O controle correto: r(AOD **sem** QA, PM2,5) = 0,322
   em Aqua e 0,268 em Terra, contra 0,353 e 0,271 com QA. A conclusão sobrevive (a máscara
   não muda a correlação de forma decisiva), mas a máscara **desloca o nível**: o AOD médio
   com QA é **6,0% menor** em Aqua e **2,0% menor** em Terra. Esse viés de nível não aparece
   em correlação de posto.

**Seleção de variáveis (`codigo/07_selecao_variaveis.py`).** Com 166 pares, foram comparados
quatro conjuntos de preditores (só AOD; AOD + vertical; AOD + meteorologia; AOD + vertical +
meteorologia), com validação por **blocos de semanas** e intervalo de 3 dias entre treino e
teste, seleção **dentro de cada dobra** e importância por permutação **agrupada** (AOD e
AOD/BLH no mesmo grupo). Resultado:

| Modelo | R² médio (6 dobras) |
|---|---|
| média do treino (baseline) | **−0,303** |
| só AOD | −0,814 |
| AOD + vertical | −0,647 |
| AOD + meteorologia | −0,899 |
| AOD + vertical + meteorologia | −0,413 |
| seleção interna (aninhada) | −0,413 |

Figura: `figuras/selecao_variaveis.png`.

**Nenhum modelo superou o baseline de prever a média do treino.** A primeira dobra
(set/out de 2024, estação de queimadas) é extrapolada e sozinha derruba a média. A
importância agrupada (ΔR² ao permutar) é maior para o grupo vertical (0,468) e meteorologia
(0,325) do que para AOD (0,244), mas isso descreve o ajuste, não um ganho preditivo. A
seleção interna escolheu o conjunto completo em todas as dobras — e ainda assim perdeu do
baseline. **Com um ponto e ~1,5 ano, este exercício ilustra o protocolo; não estabelece
ranking de variáveis.** Para a tese, a seleção precisa de mais estações e mais anos, e de
preferência de um alvo espacialmente distribuído.

**Como o CALIOP entraria para conferir o ajuste.** Para cada passagem noturna a ≤25 km
(72 em Goiânia em ago–out), o script `05_leitor_calipso.py` calcula, perfil a perfil, com
a grade de **399 níveis** do produto (60 m até 20,2 km, 180 m acima) e altitude **acima do
solo** (altitude do arquivo menos `DEM_Height`): `AOD_total`, `AOD_abl` (abaixo do BLH do
ERA5 daquela hora) e `fracao_abl = AOD_abl / AOD_total`. A correção testável é
`AOD_corrigido = AOD × fracao_abl`, comparada com a versão por BLH. O leitor está escrito e
com autoteste (perfil topo-base, terreno a 1,17 km, fração 0,75 conferida à mão); **não foi
rodado em arquivo real** porque o download exige conta Earthdata.

---

## 5. Dependência indevida e validação

Script `codigo/04_validacao.py`; funções em `codigo/validacao.py`; testes em
`codigo/teste_validacao.py` (5 testes, todos passando).

**a) O CATT-BRAMS como preditor.** Se o PM2,5 simulado entra como variável de entrada, o
modelo pode estar apenas reproduzindo a simulação. O teste implementado tem três partes:
1. ajustar **com** e **sem** a variável e comparar o R² da validação (não do treino);
2. olhar a **importância** da variável: se ela domina (>0,9) e as outras caem a zero, o
   modelo está copiando;
3. correlacionar o **resíduo** com a simulação: resíduo correlacionado indica que a
   variável carrega informação do alvo que o resto não carrega.

Resultado na demonstração (dados **simulados**, 4 estações × 180 dias, com verdade
conhecida): R² 0,61 sem a simulação e 0,85 com ela; e a importância vai para
**pm_sim = 0,99**, com AOD caindo para 0,00 (`dados/validacao_resultados.csv`). Esse é o
padrão de "cópia": a variável não agrega física, ela substitui o alvo.

**b) As duas divisões respondem perguntas diferentes — e isso decide o desenho da tese.**
- **Deixar uma estação de fora** responde: *"consigo estimar PM2,5 onde não há estação, no
  mesmo dia?"* É o uso real de um mapa de PM2,5. Todos os dias do teste estão representados
  no treino (por outras estações), então o modelo interpola no espaço.
- **Blocos de tempo** respondem: *"consigo prever dias novos?"* É o uso de previsão/série
  temporal. Aqui o modelo precisa extrapolar no tempo, e é o teste mais duro.

O mesmo modelo, nos três desenhos (simulador com verdade conhecida):

| Desenho | R² médio | dobras |
|---|---|---|
| blocos contíguos de tempo | **0,61** | 5 |
| deixando uma estação de fora | 0,94 | **4** (são 4 estações) |
| sorteando linhas (errado) | **0,95** | 5 |

A diferença de 0,34 entre blocos de tempo e sorteio é o "otimismo" que o sorteio produz: o
modelo vê dias vizinhos no treino e no teste. A validação por estação também deu alto porque,
nesse simulador, a função é a mesma em todas as estações; em dados reais, com gradiente
urbano/rural, ela deve cair — e é por isso que as duas validações são necessárias.

**c) O papel das variáveis de calendário (`sen_ano`, `cos_ano`).** Elas não carregam física:
codificam a época do ano. Na validação **por estação**, são seguras (o mesmo período existe
no treino). Na validação **por blocos de tempo**, são uma faca de dois fios: ajudam a
interpolar dentro do período coberto pelo treino e viram extrapolação quando o bloco de teste
é uma estação inteira ausente. No simulador, com e sem elas:

| Desenho | com calendário | sem calendário |
|---|---|---|
| blocos de tempo | 0,612 | **0,621** |
| por estação | **0,941** | 0,940 |

Ou seja: neste simulador o calendário não é a fonte do vazamento (o AOD já carrega o sinal
sazonal). O que infla o sorteio é a vizinhança temporal — por isso o teste honesto é o bloco
de tempo, com ou sem calendário.

**d) O teste que falha.** `codigo/teste_validacao.py` verifica:
- nenhum par (estação, dia) em treino e teste;
- em blocos de tempo, nenhum dia compartilhado;
- na validação por estação, nenhuma estação compartilhada;
- **o sorteio de linhas é reprovado** (se o teste aprovasse o sorteio, ele não serviria);
- os blocos são contíguos e cobrem o período.

Rodando: `5 testes, 0 falha(s)`.

**e) Na tabela real.** Os 5 blocos de tempo da série do Fercal (166 pares dia-satélite, 131
dias) passam na verificação. E o exercício de seleção de variáveis (`07_selecao_variaveis.py`,
seção 4) mostra o que acontece quando se tenta ir além: com um ponto e ~1,5 ano, nenhum
modelo supera o baseline da média do treino. O relatório diz isso em vez de ajustar um modelo
que parece bom.

---

## 6. O que não foi possível, e por quê

| O que | Por que | O que ficou no lugar |
|---|---|---|
| Baixar os arquivos `.hdf` do CALIOP | exigem conta Earthdata (a regra do encontro proíbe criar conta/login) | leitor HDF4 pronto e testado com perfil sintético; passo a passo no docstring |
| Dados do EarthCARE/ATLID | exigem conta EO Sign In | produto, versão, nível e DOI registrados; sem download |
| PM2,5 de Goiás | não existe em base aberta (MonitorAr não cobre GO; SEMAD sem download; IBRAM/OpenAQ exigem login/chave) | tabela de fontes com o que cada uma exigiria |
| CATT-BRAMS | saída do modelo não é pública; roda em ambiente próprio | desenho de teste do viés de "copiar a simulação", com demonstração |
| Série longa de PM2,5 no DF | o MP2,5 começa em 19/09/2024 (o cadastro das estações é de 14/08) | protótipo de 19/09/2024 a 31/12/2025, com 166 pares AOD–PM horário |
| Rodar o leitor do CALIOP em perfil real | mesma conta Earthdata | autoteste com perfil topo-base, terreno de Brasília e fração conferida à mão |

**Tentativas que deram erro e como foram tratadas** (registro honesto):
- `spatial=circle(...)` no CMR devolveu **HTTP 500** → troquei por `bounding_box` + filtro
  de distância próprio.
- CMR atrás de CloudFront devolveu **403** sem `User-Agent` → passei a mandar UA
  identificável em todas as requisições.
- `reduceRegion` com reducer combinado: a média de região vazia volta nula e a propriedade
  desaparece da coleção → passei a pedir soma e contagem e dividir no pandas.
- `MCD19A2_GRANULES.filterBounds()` não filtra (pegada global no GEE) → filtro pelo tile do
  `system:index` (`h13v10`) e recortes de 25 dias; com 60 dias o servidor estourou o limite
  de memória (`User memory limit exceeded`).
- Primeira máscara de QA estava errada (usei `bits 0-2 = 0` como "claro", mas 0 é
  *indefinido*; 1 é claro) → corrigida com o layout oficial do catálogo do Earth Engine;
  sem isso, **nenhum** pixel passava no filtro.

**Chamadas pesadas ao Earth Engine:** 20 recortes de AOD, 20 de ERA5 e 20 de FIRMS (60 no
total), cada um cobrindo 25 dias e um único ponto de 10 km. É pequeno em área, mas são mais
chamadas que antes porque a série passou de 2 meses para 15 meses.

---

## 7. Limites deste trabalho

- A janela do protótipo é de **15 meses** (19/09/2024 a 31/12/2025), num único ponto; o
  número de pares com AOD e PM2,5 horário é **166** (108 Terra, 58 Aqua). Nada aqui é
  resultado científico sobre a relação AOD–PM2,5; é prova de que o fluxo roda.
- A distância ponto–trajetória usa a polilinha do CMR (~10 pontos por meia-órbita): erro de
  ordem de 1 km, adequado a 25/50 km, **não** adequado a 5 km.
- A máscara de QA do MAIAC é uma escolha (a mais conservadora) e **custa 67% dos registros**
  na série longa. O controle correto — r(AOD sem QA, PM2,5) — mostra que a correlação muda
  pouco (0,353 → 0,322 em Aqua; 0,271 → 0,268 em Terra), mas a máscara **rebaixa o nível** do
  AOD em 6,0% (Aqua) e 2,0% (Terra), viés que um teste de posto não vê.
- O "ajuste vertical" testado é o mais grosseiro (AOD/BLH). O teste correto — fração do AOD
  na camada limite — depende do CALIOP e não foi executado.
- Terra e Aqua não foram combinados: isso reduz o n de cada correlação, mas evita misturar
  duas horas e duas camadas limite diferentes. Combinar só faz sentido com um critério
  explícito (por exemplo, usar Aqua como satélite principal e Terra como verificação), que é
  decisão da pesquisadora.
- A demonstração de vazamento usa dados simulados. Os números dela servem para escolher o
  desenho de validação, não para descrever Goiás.
- A seleção de variáveis tem 166 pares e **nenhum modelo superou o baseline** da média do
  treino; o resultado ilustra o protocolo, não estabelece ranking.
- O PM2,5 do MonitorAr é dado bruto (o próprio MMA avisa que pode conter falhas e não passou
  por validação técnica); e o fuso do campo `dh_medicao` não está declarado — usei hora local
  por evidência do ciclo diurno.
- O FIRMS usado é o produto **NRT**, que o catálogo do Earth Engine diz não ser de qualidade
  científica; a contagem é de pixels de 1 km, não de detecções.

---

## 8. Onde a IA generativa ajudou e onde não ajuda

**Ajudou, e muito:**
- **Ler a documentação e transformar em código.** O layout dos bits do `AOD_QA`, a
  geometria `Lines` do CMR, os nomes de banda do ERA5 horário: coisas chatas de garimpar e
  que a IA resolveu em minutos, com a fonte conferida depois.
- **Encontrar as armadilhas por tentativa e erro.** `filterBounds` que não filtra, média de
  região vazia que desaparece, coluna que muda de nome entre anos do MonitorAr — cada uma
  custou um erro e virou uma linha no `CLAUDE.md`. É o tipo de conhecimento que não está em
  artigo.
- **Escrever o teste que falta nos artigos.** A validação por blocos de tempo e por estação
  é padrão na literatura, mas raramente vem com teste automatizado; aqui o teste reprova o
  sorteio de linhas, o que é a prova de que ele detecta algo.
- **Fazer o controle.** Comparar duas implementações de distância, rodar com e sem filtro de
  QA, comparar com a repetitividade orbital de 16 dias: a IA propôs e executou os controles
  que mostram se o número é artefato.

**Não ajuda, e pode atrapalhar:**
- **Decidir o que é fisicamente defensável.** Se o PM2,5 do CATT-BRAMS pode ou não entrar
  como preditor, qual raio de associação faz sentido em queimadas, se vale interpolar o
  perfil do CALIOP no tempo — isso é dela. A IA mostra o teste, não escolhe.
- **Escolher o método de correção vertical.** "Dividir por BLH" é o mais simples e aqui não
  funcionou; dizer se a fração na camada limite é a resposta certa exige julgamento
  científico sobre o regime de aerossol de Goiás, que os dados deste protótipo não têm.
- **Preencher lacuna de dado.** Não há PM2,5 público em Goiás. Nenhuma IA resolve isso;
  resolve pedido formal à SEMAD, parceria ou campanha.
- **Garantir número.** Toda inferência com 166 pares de um único ponto é frágil; a IA tende a
  escrever frases confiantes. O intervalo de confiança e o baseline da média foram o
  antídoto — e existem porque o número sozinho enganaria.

---

## Anexo — de onde saiu cada número

| Número | Script | Arquivo |
|---|---|---|
| versões do produto, último granulo 30/06/2023 | `01_calipso_cmr.py` | `dados/calipso_controle.json` |
| passagens por ano/mês, dia/noite, 5/25/50 km | `01_calipso_cmr.py` | `calipso_passagens_por_ano.csv`, `_por_mes.csv`, `_eventos.csv`, `calipso_estacao_queimadas.csv` |
| controle de distância (1,19 km / 0,58 km), intervalo de 16 dias | `01_calipso_cmr.py` | `calipso_controle.json` |
| estações de PM2,5, cobertura por UF, sondagens HTTP | `02_estacoes_pm25.py` | `pm25_estacoes_monitorar_go_df.csv`, `monitorar_cobertura_por_uf.csv`, `pm25_fontes.csv`, `pm25_sondagens_http.csv` |
| 1.315 registros granulo × ponto (931 dias-satélite), AOD, BLH, focos, PM horário/diário | `03_prototipo_gee.py` | `prototipo_integrado.csv`, `prototipo_integrado_diario.csv` |
| Spearman por satélite (alvo horário e diário) | `07_selecao_variaveis.py` | `selecao_variaveis_correlacoes.csv` |
| custo da máscara (67%), pixels válidos, horários reais, QA sem filtro, pares comuns, relações com BLH, distâncias | `08_checagens.py` | `checagens.json`, `checagem_sensibilidade_n_px.csv` |
| R² dos conjuntos de variáveis, seleção aninhada, importância por grupo | `07_selecao_variaveis.py` | `selecao_variaveis_modelos.csv`, `selecao_variaveis_importancia.json` |
| R² por desenho de validação, importância da simulação | `04_validacao.py` | `validacao_resultados.csv` |
| 5 testes do desenho | `teste_validacao.py` | saída no console |
| DOIs conferidos | `06_referencias.py` | `REFERENCIAS.md` |

---

## Correções de 31/10

Seção pedida na conferência (`docs/revisoes/CORRECOES.md`). O que mudou, item por item:

**1. Arquivos temporários na raiz.** Os `cmrtest.json`, `tmp_*.html`, `tmp_*.json` e
`tmp_probe.txt` criados durante as sondagens foram apagados ao final da execução; se a
conferência os viu, foi um estado intermediário do trabalho. Conferi de novo agora: a raiz
tem só os `.md` e as pastas `codigo/`, `dados/`, `figuras/`. Nenhum deles era fonte de número: os códigos HTTP e os tamanhos de resposta
que aparecem na seção 3 vêm de `dados/pm25_sondagens_http.csv`, gerado por
`codigo/02_estacoes_pm25.py`. Conferido agora com `find`: não há arquivo temporário em
nenhum nível da pasta.

**2. Hora do ERA5 × satélite do AOD (mudança de método).** Antes, o script 03 calculava um
AOD por dia fazendo a média dos granulos de Terra e Aqua e usava a média das duas horas do
ERA5. Isso
estava errado por dois motivos: (a) as passagens daquela janela acontecem de 09:00 a 10:35
(Terra) e de 13:55 a 15:25 (Aqua), e a camada limite cresce entre elas; (b) a média diária
criava uma BLH que não existe em nenhum horário. O que o script faz agora:
- guarda uma linha por **granulo**, com a propriedade `SATELLITE` (`T`/`A`), a hora UTC e a
  hora local;
- pega o ERA5 na hora cheia mais próxima **daquele granulo**;
- gera `dados/prototipo_integrado.csv` (ponto × dia × satélite, uma linha por granulo) e
  `dados/prototipo_integrado_diario.csv` (ponto × dia × satélite);
- a média dos dois satélites no dia ficou só como **variante de comparação** nas correlações,
  para mostrar o tamanho do efeito de misturar.

Números que mudaram (Brasília, média das duas estações; na ocasião em
`dados/prototipo_correlacoes.csv`, arquivo substituído depois pela série do Fercal):

| | AOD × PM2,5 | AOD/BLH × PM2,5 | n |
|---|---|---|---|
| Aqua (13:55–15:25) | **0,90** (IC 0,56–1,00) | **0,64** (IC 0,07–0,94) | 12 |
| Terra (09:00–10:35) | **0,44** (IC −0,16–0,88) | **−0,22** (IC −0,73–0,37) | 15 |
| Terra+Aqua (média do dia) | 0,57 (IC 0,00–0,96) | 0,06 (IC −0,42–0,53) | 18 |

E a razão física do problema: BLH médio na passagem de **Terra = 1.120 m** e de
**Aqua = 2.512 m**. Esses dois números são de **dias diferentes** (38 dias de Terra e 35 de
Aqua); nos 27 dias comuns o contraste é 1.197 m × 2.668 m — a conclusão é a mesma, e a
justificativa correta é essa. O número antigo (0,22 para AOD/BLH) era um artefato de misturar
as duas horas; o novo (0,64 em Aqua, −0,22 em Terra) continua sem mostrar ganho do ajuste,
mas agora com a hora certa em cada linha.

**3. Afirmação forte demais.** A frase "Se a camada limite não explica a coluna, o ajuste
AOD/BLH só adiciona ruído" foi reescrita na seção 4. Agora o texto diz o que os dados
mostram (o ajuste **não melhorou** a correlação em nenhum dos dois satélites), oferece duas
explicações **possíveis** (BLH quase independente do AOD nesta janela; CL sozinha não
descreve onde o aerossol está) e registra que, com n = 12 e 15, as duas seguem em aberto.
Nenhuma conclusão sobre o método é tirada desta janela.

**4. Referências do Brasil.** A conferência estava certa em cobrar: das 12 originais, duas
já eram brasileiras — Gonçalves et al. (2018), AOD → PM2,5 na Amazônia, e Rudke et al.
(2023), algoritmos de AOD sobre o Brasil —, mas faltavam o Cerrado (a área de estudo) e o
perfil vertical. Foram acrescentadas **quatro**, todas com DOI conferido no
Crossref pelo mesmo script:
- Mataveli et al. (2019), PM2,5 de queimadas no Cerrado (2002–2017);
- Reddington et al. (2019), aerossol de queimada na Amazônia com observação de aeronave,
  superfície e satélite;
- Wang et al. (2016, *Nature*), transporte vertical sustentando o aerossol da camada limite
  amazônica;
- Franco et al. (2024), perfil vertical de aerossol no ATTO (Amazônia).

`REFERENCIAS.md` passou de 12 para **16 referências**, 6 com foco no Brasil, todas
verificadas (`16 de 16 candidatas`).

**Bug adicional encontrado ao conferir (corrigido).** Ao abrir a tabela para a conferência,
a umidade relativa apareceu com valores implausíveis (66% num dia de 30 °C e ar seco). O
cálculo usava a fórmula de Magnus com temperatura em **Kelvin**, mas a fórmula vale para
graus Celsius: no caso testado dava 66,9% quando o correto é 18,3%. Corrigido no script 03
(conversão explícita de T e Td para °C, coluna `temp` agora em °C). As correlações não usam
umidade, então nenhum número das seções 4 e 5 mudou; a tabela em `dados/` foi regerada com
umidade entre 8% e 80% (média 29%), coerente com a estação seca.

**O que foi rodado de novo:** `03_prototipo_gee.py` (três vezes: separação dos satélites,
filtro de n ≥ 6 nas correlações e correção da umidade), `04_validacao.py` (passou a ler a tabela diária por satélite),
`teste_validacao.py` (5 testes, 0 falhas) e `06_referencias.py`. No fechamento, o
`codigo/rodar_tudo.py` rodou a cadeia inteira sem falhas e todas as saídas esperadas existem.
A figura `figuras/prototipo_integrado.png` foi refeita: Terra e Aqua aparecem em marcadores
separados, e o painel do meio mostra o BLH da hora de Aqua.

---

## Correções de 31/10 (2ª rodada)

Seção pedida em `docs/revisoes/CORRECOES-2.md`, que consolida a `docs/revisoes/CONFERENCIA-MINIMAX.md` e uma segunda
análise. Tudo abaixo foi executado e as saídas foram conferidas.

**1. Leitor do CALIOP (crítico) — corrigido e autotestado.** A grade anterior tinha 342
níveis crescentes de −0,5 a 20 km e ignorava o terreno. Agora:
- a grade tem **399 níveis**, do topo para o chão, com **60 m até 20,2 km e 180 m acima**,
  conforme o *CALIPSO Lidar Level 2 Profile Data Description Document, Version 5.00* (ASDC,
  `cal_lid_l2_pro_v5-00_desc_qs.pdf`);
- as altitudes vêm da SDS **`Lidar_Data_Altitudes`** (V5.00) ou do metadado
  `Lidar_Data_Altitude` (versões anteriores); a grade fixa é só reserva;
- a altitude usada no cálculo é **acima do solo**: altitude do arquivo menos `DEM_Height`;
- o autoteste usa perfil em ordem topo-base com terreno a **1,17 km** (Brasília) e confere a
  fração do AOD na CL contra a conta à mão: **0,75** (e 0,15 se o DEM for esquecido) — é o
  erro que o teste protege.

**2. PM2,5 colado em Goiânia/Porangatu — resolvido pela mudança de desenho.** O protótipo
agora tem **um ponto só (Fercal)**, dentro do disco de AOD das duas estações, então o
cruzamento por data é também por ponto. A tabela antiga de 3 pontos foi substituída.

**3. Rastreabilidade.** (`08_checagens.py` → `dados/checagens.json`)
- `aod_km` agora é gravado com **4 casas**; a correlação reproduz do CSV.
- `n_px` aparece na tabela e no texto: mediana de **265 px** em Terra e **25 px** em Aqua;
  nos dias com PM, 295 e 33. Abaixo de 20 px: **12,9%** (Terra) e **46,6%** (Aqua).
- A máscara de QA descarta **884 de 1.315 registros (67,2%)** — o custo está medido.
- Piso adotado: **n_px ≥ 20**, com sensibilidade em 0/20/50 (seção 4). A direção não muda;
  Aqua oscila 0,28–0,35, mais que o efeito do filtro.
- `n_pm25` (sempre 0) foi removido de `02_estacoes_pm25.py` e do CSV de estações.
- `focos` está documentado como **pixels de fogo de 1 km do FIRMS NRT**, não detecções.

**4. Textos e rótulos.** Horários reais desta série: **Terra 08:00–10:40 (média 09:21)** e
**Aqua 13:25–16:30 (média 14:57)**, com o ERA5 na hora cheia mais próxima de cada granulo.
Corrigido em RELATORIO, README, CLAUDE e figura. Também: AOD mínimo por satélite
(0,0031 Terra / 0,0045 Aqua, não 0,056); fração noturna **por ponto** (0,58 Goiânia × 0,13
Brasília a ≤25 km); "5 folds" → **4** na linha da validação por estação; "3×" → **17,2×** no
CLAUDE; registros do MonitorAr identificados como "de todos os poluentes", com as contagens
de MP2,5 (579/1.190 em 2024); distância das estações ao ponto (1,62/1,61 km; 21,5/23,1 km do
centro de Brasília); DOI do ATLID separado por versão (BA/BB/BC) do DOI da coleção, com a
versão **BD (2026)** registrada.

**5. Compatibilização espaço-temporal (achado novo).** Ponto **Fercal** no meio das duas
estações; PM em duas métricas: `pm25_hora` (média em ±1 h da passagem) e `pm25_dia18`/
`pm25_dia12`. A série diária tem **134 dias** com ≥18 h e **243** com ≥12 h; a horária cobre
**355 dias**. O fuso do `dh_medicao` não é declarado no dicionário do MMA; o ciclo diurno
(mínimo às 15–16 h, máximo às 21–22 h) indica **hora local**, e é assim que foi usado.

**6. Seleção de variáveis (pedido do formulário).** `07_selecao_variaveis.py`: 166 pares,
blocos semanais com gap de 3 dias, seleção **dentro de cada dobra**, importância por
permutação **agrupada**. Resultado honesto: **nenhum conjunto superou o baseline da média do
treino** (baseline −0,303; melhor modelo −0,413). Aqua × Terra em dias pareados: 0,22 × 0,09
nos 35 dias comuns. Isto ilustra o protocolo; não é a seleção da tese.

**7. Validação por estação × por tempo.** Seção 5(b) reescrita: estação de fora = estimar
onde não há sensor no mesmo dia (mapa); blocos de tempo = prever dias novos. O papel do
calendário foi medido com e sem `sen_ano`/`cos_ano` (0,612 vs 0,621 em blocos; 0,941 vs 0,940
por estação) — neste simulador ele não é a fonte do vazamento.

**Bugs e surpresas do caminho.** (a) com recortes de 60 dias o Earth Engine estourou
`User memory limit exceeded`; passou com 25 dias e `tileScale=4`. (b) A primeira tentativa de
fazer o merge horário usou a data UTC; troquei para data local. (c) A tabela longa mostrou
que a relação BLH–AOD é **positiva** (0,33 Aqua, 0,30 Terra), o oposto do que a hipótese de
diluição sugere — mais um motivo para não vender o AOD/BLH como correção.

**O que não foi possível.** Rodar o leitor em arquivo real do CALIOP (exige conta Earthdata);
usar o PM2,5 simulado do CATT-BRAMS (saída não pública); validar espacialmente com mais de
duas estações (não existem no DF/GO em base aberta); e obter um modelo com desempenho
positivo — com um ponto e 15 meses, o baseline vence.

## Controle adicional: AOD/BLH × hora do dia (31/10, conferência do Claude)

Uma revisão sugeriu que, comparando com o PM2,5 **na hora da passagem** (`pm25_hora`) e empilhando Terra (manhã) e Aqua (tarde), dividir o AOD pela camada limite ajudaria, como a física prevê. Os números confirmam a primeira parte: empilhado (166 pares dia-satélite da tabela diária, `n_px ≥ 20`, a mesma de `07_selecao_variaveis.py`), o Spearman com `pm25_hora` sobe de **+0,27** (AOD) para **+0,46** (AOD/BLH).

O controle desmonta a leitura física: uma variável que só diz "manhã ou tarde" (1 = Terra) dá **+0,60** sozinha, mais que o AOD/BLH. Dentro de cada satélite, onde a diferença manhã × tarde some, o AOD/BLH fica **pior** que o AOD (Aqua +0,35 → +0,22; Terra +0,27 → +0,19). O ganho do empilhamento vem do ciclo diurno do PM2,5 (mais alto de manhã, mais baixo à tarde), que a BLH carrega, e não de uma melhor representação do aerossol na camada limite. Dentro de cada satélite o AOD continua correlacionando com o PM2,5 (0,27 a 0,35): ele só não explica mais do que a hora do dia.

Fonte: `codigo/09_controle_hora_do_dia.py` → `dados/controle_hora_do_dia.csv`. Lição para o fluxo: toda variável vertical candidata precisa ser testada contra um controle de "hora do dia" ou "estação do ano" antes de ser lida como efeito físico.
