# Segunda rodada de correções (31/10/2026)

As regras de `REGRAS-COMUNS.md` continuam valendo (Earth Engine liberado no projeto `SEU-PROJETO-EARTH-ENGINE`; sem login em mais nada). Foram achados problemas por duas conferências independentes (`CONFERENCIA-MINIMAX.md` e uma análise de outra IA), confirmados no código. Critério: **servir ao que a pesquisadora pediu no `CONTEXTO.md`** — fluxo em Python para integrar MODIS Terra/Aqua, CALIOP, ERA5 e CATT-BRAMS; compatibilizar resoluções preservando física e critérios de qualidade; **associação espaço-temporal e seleção de variáveis da dinâmica vertical, evitando dependências inadequadas entre preditores e PM2,5**; base consistente e reproduzível.

Ao terminar, acrescente ao `RELATORIO.md` uma seção **"Correções de 31/10 (2ª rodada)"** e atualize README, CLAUDE.md/AGENTS.md e figuras. Rode `teste_validacao.py` e o `autoteste` do leitor no fim.

## 1. Leitor do CALIOP quebra com arquivo real (crítico)
`05_leitor_calipso.py`:
- `NIVEL_ALTURA_PADRAO_KM = np.arange(-0.5, 20.0, 0.06)` dá 342 níveis crescentes (o comentário fala em 583). O `CAL_LID_L2_05kmAPro` tem **399 níveis, do topo (~30,1 km) para o chão (−0,5 km)**, 60 m abaixo de ~20,2 km e 180 m acima. Confira na documentação oficial do produto (Data Products Catalog / descrição do Level 2 da NASA; cite a página) e use a altitude que vem no próprio arquivo quando existir (metadado `Lidar_Data_Altitudes`), com a grade fixa só como reserva.
- As altitudes do CALIOP são acima do nível do mar; a camada limite do ERA5 é acima do solo. Use `DEM_Height` (já lido e não usado) para converter: altura acima do solo = altitude − DEM.
- O `autoteste` deve ter um perfil em ordem topo-base com terreno a 1,17 km (Brasília) e conferir a fração na camada limite contra uma conta feita à mão.

## 2. PM2,5 de Brasília colado em Goiânia e Porangatu
`03_prototipo_gee.py` (~linha 322) cruza o PM2,5 só pela data. Cruze por ponto e data: só o ponto das estações (Fercal, ver item 5) tem PM2,5; as outras linhas ficam vazias.

## 3. Rastreabilidade da tabela
- Grave `aod_km` com 4 casas (hoje 2, o que impede reproduzir a correlação a partir da coluna).
- Informe `n_px` (pixels válidos no disco de 10 km), quantos registros a máscara descarta (hoje 58% ficam com zero pixel) e a sensibilidade das correlações a um piso `n_px ≥ 20` e `≥ 50`. Escolha um piso e justifique.
- `n_pm25`, se é sempre 0, remova. `focos`: diga que conta pixels de fogo do FIRMS NRT.

## 4. Textos com número ou rótulo errado
- Horários reais da tabela: Terra 09:00–10:35 local (média ~09h48), Aqua 13:55–15:25 (média ~14h40), e a hora do ERA5 que entra em cada um. Corrija relatório, README, CLAUDE.md e a legenda da figura.
- BLH 1.120 × 2.512 m não é "mesmos dias": são 38 e 35 dias; nos 27 comuns, 1.197 × 2.668 m.
- Aqua × Terra: diga que usam dias diferentes e dê o pareado nos 9 dias comuns (Aqua 0,93, Terra 0,62).
- Controle de QA: o 0,996 compara o AOD com ele mesmo. Use r(AOD sem QA, PM2,5): 0,895 Aqua, 0,386 Terra; e o deslocamento de nível médio que a máscara causa.
- "BLH e AOD quase independentes (0,08)" vale só nos 12 dias com PM2,5; em todos os 35 dias de Aqua é 0,31. Reescreva.
- Demais itens menores do `CONFERENCIA-MINIMAX.md` (AOD mínimo 0,056 que não existe, fração noturna por ponto, "5 folds" onde são 4, "3×" no CLAUDE.md, registros de todos os poluentes, distância das estações ao ponto, DOI/versão do ATLID).

## 5. Compatibilização espacial e temporal com as estações (achado novo, conferido)
- **Espaço:** as duas estações de PM2,5 (CRAS Fercal −15,6013/−47,8704 e Escola −15,5898/−47,8428, coordenadas do arquivo de 2024) ficam a **21,5 e 23,1 km** do ponto "Brasilia" (Plano Piloto), fora do disco de 10 km do AOD. Acrescente o ponto **Fercal** (meio das duas, ~−15,5955/−47,8566) e use-o para tudo o que envolve PM2,5. No arquivo de 2025 o IBRAM trocou as duas coordenadas por um ponto genérico (−15,7797/−47,9297): registre e use as de 2024.
- **Tempo:** o AOD e o ERA5 são da hora da passagem, mas o PM2,5 comparado é a média de 24 h. Em `pm25_df_horario_2024.csv` a média é ~12 µg/m³ às 9–10 h e ~5,7 às 14–15 h (a camada limite sobe e dilui). Grave as duas versões: `pm25_hora` (média na janela de ±1 h da passagem, na hora local) e `pm25_dia` (com `n_horas ≥ 18` e também `≥ 12`, informando quantos dias cada uma deixa). Compare AOD e AOD/BLH contra as duas. Hipótese a testar, não conclusão: contra o PM2,5 da hora, AOD/BLH deve ajudar (empilhando Terra e Aqua), coerente com a física.
- Confira o fuso dos dados do MonitorAr (hora local ou UTC) antes de montar a janela.

## 6. Seleção de variáveis da dinâmica vertical (pedido do formulário que não foi atendido)
Com 12–15 dias com PM2,5 não dá para selecionar nada. Amplie o protótipo **só para o ponto Fercal** de **19/09/2024** (primeiro registro de PM2,5; entre 14/08 e 18/09 as estações só mediram outros poluentes) **até o último dia disponível** em `monitorar_2025.zip` (já baixado), Terra e Aqua separados, mesmo método e mesmo piso de `n_px`.
- O `03_prototipo_gee.py` lê só o ZIP de 2024 e faz um `.getInfo()` único para ERA5 e focos: fatie por trimestre, como já faz no AOD. Se o ERA5 no Earth Engine não cobrir 2025 inteiro, use o Open-Meteo sem chave (`hourly=boundary_layer_height,...`, `models=era5`) e registre.
- Variáveis derivadas sem custo de download: déficit do ponto de orvalho (temperatura − ponto de orvalho) e coeficiente de ventilação (BLH × vento).
- Candidatos que representam a dinâmica vertical e existem sem login: BLH, AOD/BLH, `frac_fumaca` (fumaça no QA do MAIAC), vento, umidade, temperatura, e, se houver no catálogo do Earth Engine ou no Open-Meteo sem chave, algum indicador de estabilidade (ex.: diferença de temperatura entre níveis, CAPE/CIN). Liste o que procurou e não achou.
- Protocolo de seleção **sem vazamento**: validação por blocos de tempo (blocos de semanas, com intervalo entre treino e teste), seleção feita **dentro** de cada dobra (nunca com todos os dados), importância por permutação agrupando variáveis correlacionadas (AOD e AOD/BLH no mesmo grupo). Compare um modelo só com AOD × AOD + variáveis verticais.
- Diga com todas as letras o que esse n permite concluir (duas estações, um lugar, ~1 ano) e que o resultado é ilustração do método, não a seleção da tese.
- Tamanho total dentro de 1 GB; tabela final pequena em `dados/`.

## 7. Validação por estação × por tempo
Explique qual pergunta cada divisão responde: estação de fora = estimar onde não há estação, no mesmo dia (é o uso de um mapa de PM2,5); blocos de tempo = dias novos. Explique o papel das variáveis de calendário (`sen_ano`, `cos_ano`) em cada uma e mostre o R² com e sem elas no simulador.

## Não mexa
Contagem do CALIOP (01), fontes de PM2,5 (02), referências (só ajustar o ATLID).
