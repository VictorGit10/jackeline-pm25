# CLAUDE.md — contexto para a IA que for continuar este trabalho

Leia este arquivo antes de mexer em qualquer coisa. Ele descreve o problema, os dados,
a ordem dos scripts e — o mais importante — as armadilhas que já custaram tempo.

## O problema

Uma pesquisadora que terminou o mestrado estimando PM2,5 em Goiás e no DF com MODIS,
CATT-BRAMS e aprendizado de máquina quer incorporar a **distribuição vertical dos
aerossóis**. A limitação do mestrado: usou só o primeiro nível atmosférico do modelo.
A tese propõe integrar MODIS (Terra/Aqua), perfis do CALIOP/CALIPSO, ERA5 e CATT-BRAMS.

Antes de modelar, a pergunta que pode mudar o projeto: **existe perfil vertical suficiente
sobre GO/DF?** Este pacote responde isso e entrega um protótipo executado de integração.

## Dados e de onde vêm

| Fonte | Como foi acessada | Observação |
|---|---|---|
| CALIOP `CAL_LID_L2_05kmAPro` | **só metadados** pela API pública do CMR (`cmr.earthdata.nasa.gov`, sem login) | os `.hdf` exigem conta Earthdata e **não** foram baixados |
| MonitorAr (MMA) | ZIPs anuais em `dados.mma.gov.br` (CKAN, aberto) | `dados/monitorar_20XX.zip`, CSV único por ano, ~800 MB descompactado |
| MCD19A2 (MAIAC) | Earth Engine, `MODIS/061/MCD19A2_GRANULES` | AOD 550 nm, 1 km, por granulo; Terra e Aqua separados (propriedade `SATELLITE`) |
| PM2,5 do DF | ZIPs do MonitorAr 2024 e 2025 | duas estações (Fercal e Escola), a 1,6 km do ponto Fercal |
| ERA5 | Earth Engine, `ECMWF/ERA5/HOURLY` | 1 imagem por hora, bandas nomeadas (`boundary_layer_height`, etc.) |
| FIRMS | Earth Engine, `FIRMS` | 1 imagem por dia, `T21` e `confidence` |
| IBRAM-DF / SEMAD-GO / OpenAQ | só sondagem HTTP | exigem login ou chave; ver `dados/pm25_sondagens_http.csv` |

## Ordem dos scripts

1. `codigo/comum.py` — utilitários (pontos, HTTP com retry, distância ponto-trajeto na
   esfera, saída de CSV/JSON). Não roda sozinho.
2. `codigo/01_calipso_cmr.py` — conta as passagens do CALIOP a ≤5/25/50 km de Goiânia e
   Brasília, por ano e mês, dia e noite. Gera `calipso_passagens_*.csv` e
   `calipso_controle.json`.
3. `codigo/02_estacoes_pm25.py` — baixa/ler os ZIPs do MonitorAr, lista estações com
   PM2,5 em GO/DF e sonda as outras fontes. Gera `pm25_*.csv`.
4. `codigo/03_prototipo_gee.py` — tabela ponto × dia (AOD, ERA5 na hora da passagem,
   focos em 3 dias, PM2,5 diário) e a figura. Gera `prototipo_integrado.csv`.
5. `codigo/04_validacao.py` + `codigo/validacao.py` — desenho de validação (blocos de
   tempo, por estação) e demonstração do vazamento por sorteio de linhas e por simulação
   usada como preditor. Gera `validacao_resultados.csv` e a figura.
6. `codigo/teste_validacao.py` — 5 testes; falham se o mesmo dia/estação aparecer em
   treino e teste.
7. `codigo/05_leitor_calipso.py` — leitor HDF4 do CALIOP (399 níveis, altitudes do SDS,
   DEM) + cálculo da fração do AOD dentro da camada limite. Autoteste com perfil topo-base.
8. `codigo/06_referencias.py` — confere os DOIs no Crossref e reescreve `REFERENCIAS.md`.
9. `codigo/07_selecao_variaveis.py` — compara conjuntos de variáveis com validação por
   semanas, seleção dentro da dobra e importância agrupada.
10. `codigo/08_checagens.py` — números de rastreabilidade em `dados/checagens.json`
    (custo da máscara, pixels, horários, controle de QA, dias comuns, distâncias).

## Armadilhas encontradas (não repita)

- **CMR, geometria do granulo CALIPSO:** vem como `Lines` com ~10 pontos por meia-órbita,
  não como polígono do swath. Dá para calcular a distância do ponto à trajetória, mas com
  erro de poucos km. Não confie em contagens a ≤5 km; 25 km é o piso seguro.
- **CMR, `spatial=circle(...)`** devolveu HTTP 500 para granulos. Use `bounding_box` e
  filtre a distância você mesmo.
- **CMR atrás de CloudFront**: requisição sem `User-Agent` volta 403. Sempre mande um UA.
- **Dia/noite do CALIOP:** vem no sufixo do nome do arquivo (`...ZN.hdf` = noite,
  `...ZD.hdf` = dia). Não há campo no UMM.
- **A órbita repete a cada 16 dias**: o número de passagens não cresce com a área, depende
  de quantas trajetórias da grade caem no raio. Por isso Goiânia tem **17,2×** mais passagens
  a ≤5 km que Brasília (154 contra 9). Intervalo mediano entre passagens do mesmo período do
  dia = 16 dias.
- **Terra × Aqua não se misturam.** A propriedade `SATELLITE` (`T`/`A`) diz qual é. No
  Fercal, a hora local do início do granulo vai de 08:00 a 10:40 em Terra (média 09:21) e de
  13:25 a 16:30 em Aqua (média 14:57), e a BLH média é 827 m contra 2.028 m. Misturar as duas
  cria uma BLH que não existe em nenhum horário.
- **A máscara de QA custa caro.** Na série de 15 meses ela descarta **67%** dos registros
  granulo×ponto. Em Aqua a mediana é de apenas 25 pixels válidos no disco de 10 km (46% dos
  registros têm menos de 20). Use piso `n_px >= 20` e reporte o custo, senão a comparação
  entre satélites fica injusta.
- **`MCD19A2_GRANULES.filterBounds()` não filtra nada** (as pegadas no GEE são globais):
  retorna o mundo inteiro. Filtre pelo tile no `system:index` (ex.: `h13v10`) com
  `ee.Filter.stringContains`. Recortes de 60 dias estouram `User memory limit exceeded` em
  `reduceRegions`; use 25 dias e `tileScale=4`.
- **CALIOP tem 399 níveis, não 583**, e vem do topo para o chão: 60 m de −0,5 a 20,2 km e
  180 m acima. As altitudes são **acima do mar**; a CL do ERA5 é **acima do solo** — subtraia
  `DEM_Height`. Use a SDS `Lidar_Data_Altitudes` (V5.00) ou o metadado `Lidar_Data_Altitude`.
- **Bits do `AOD_QA`** (layout oficial, está no docstring de `mascara_qa`): 0–2 nuvem
  (1 = claro, 0 = indefinido!), 3–4 terra/água, 5–7 adjacência, 8–11 QA do AOD (0 = melhor),
  12 glint, 13–14 modelo de aerossol (1 = fumaça). O erro clássico é filtrar `bits(0,3)==0`
  (indefinido) e ficar sem pixel nenhum.
- **`Image.reduceRegions()` não aceita `maxPixels` nem `bestEffort`** (só `reduceRegion`
  aceita). Use `tileScale`.
- **Reducer combinado**: `mean().combine(sum(), sharedInputs=True)` gera
  `band_mean`/`band_sum`; com `sharedInputs=False` ele exige exatamente 2 bandas.
- **Média de região vazia volta nula e a propriedade desaparece** da FeatureCollection.
  Solução usada aqui: pedir `sum` e `count` e dividir no pandas (por isso as bandas
  auxiliares `n`/`nraw`).
- **MonitorAr mudou o nome de coluna**: 2024 usa `st_situacao_item`, 2025 usa
  `st_situacao`. O CSV é UTF-8 com vírgula (não é `;`), ~800 MB por ano — leia direto do
  ZIP em streaming, não extraia.
- **Fuso do MonitorAr**: o `dh_medicao` não declara fuso. O ciclo diurno (mínimo às 15–16 h,
  máximo às 21–22 h) indica hora local; use assim e registre a suposição.
- **PM2,5 no DF só começa em setembro de 2024** (as estações entram no MonitorAr em
  agosto, mas o MP2,5 aparece depois). Em 2025 há o ano inteiro; para a estação de
  queimadas use 2025 se quiser mais dias.
- **Coordenadas das estações do DF mudam entre 2024 e 2025** no arquivo (2025 repete o
  centro de Brasília). Use as de 2024 para as duas estações.
- **OpenAQ v3 exige `X-API-Key`** (401) e a v2 foi aposentada (410). Não insista sem chave.
- **SEMAD-GO**: as páginas de qualidade do ar estão paradas em 2021; a API do Cimehgo
  (`intratempo.meioambiente.go.gov.br/api/...`) responde só meteorologia e devolveu série
  vazia nas datas testadas.

## Se for continuar

- Baixar o CALIOP com a conta dela (`earthaccess`), começar por **junho de 2023** (últimos
  dados que existem — o acervo termina em 30/06/2023, não em 01/08/2023) e por
  **2010/2015** (anos com mais passagens).
- Calcular `fracao_abl` por perfil (script 05) e entrar com ela no lugar do BLH: é o teste
  central da tese.
- Definir o satélite principal. Aqua é o mais próximo do pico da tarde, mas tem menos pixels
  válidos (mediana 25) e mais dias perdidos; Terra tem 265. A escolha é metodológica e precisa
  ser justificada com o piso de pixels e a cobertura.
- Ampliar a tabela para 2015–2025 e usar **validação por estação e por blocos de tempo**
  (script 04). Nunca sortear linhas.
- Se o CATT-BRAMS entrar, rodar sempre o par de modelos com/sem a simulação e reportar a
  importância da variável — se ela domina (>0,9), o modelo está copiando a simulação.
