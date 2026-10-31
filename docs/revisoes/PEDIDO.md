# Pedido — integrar AOD, perfil vertical e meteorologia para PM2,5 em Goiás e DF: viabilidade e protótipo

Leia antes `REGRAS-COMUNS.md` e `CONTEXTO.md` (os dois estão nesta pasta).

## O que queremos
Ajudar a pesquisadora a montar o fluxo em Python de integração dos dados, começando pelo que pode **inviabilizar ou mudar a proposta**: quanto dado de perfil vertical existe de fato sobre Goiás e o DF. Depois, um protótipo pequeno e executado de associação espacial e temporal, e um desenho de validação que evite dependência indevida entre preditores e PM2,5.

## Passos
1. **Período do CALIOP/CALIPSO.** Confirme em fonte oficial da NASA quando a missão terminou e qual o último dado disponível. Confirme também o que existe como sucessor (ex.: lidar ATLID do EarthCARE): desde quando, nível de processamento e acesso. Cite as páginas.
2. **Quantas passagens existem de verdade.** Use a busca pública do NASA CMR (`https://cmr.earthdata.nasa.gov/search/`, não exige login) para contar os granulos do produto de perfil de aerossol do CALIOP (ex.: `CAL_LID_L2_05kmAPro`, versão mais recente) cuja trajetória passa a até 25 km e 50 km de Goiânia e de Brasília, **por ano e por mês**, com destaque para a estação de queimadas (ago–out). Separe dia e noite se possível. Gere tabela e figura. Esse número diz se dá para usar o CALIOP ponto a ponto ou só como climatologia regional.
3. **Estações de PM2,5.** Levante quais estações de PM2,5 existem em Goiás e no DF com dado público (órgãos estaduais, IBRAM-DF, OpenAQ etc.), o período e a forma de acesso. Se exigir chave ou cadastro, só registre.
4. **Protótipo de associação (com dados abertos, pelo Earth Engine).** Para 2 a 3 pontos (Goiânia, Brasília e mais um), num período curto que inclua uma estação de queimadas:
   - AOD do MODIS MAIAC (MCD19A2), com os filtros de qualidade documentados, em raio fixo ao redor do ponto e na hora da passagem;
   - ERA5 horário (ou ERA5-Land quando fizer sentido) na hora mais próxima da passagem: **altura da camada limite**, vento, umidade, temperatura;
   - focos de queimada (ex.: FIRMS no Earth Engine) num raio e numa janela de dias antes.
   Monte a tabela integrada (ponto × dia) e uma figura. Mostre o efeito de dividir o AOD pela altura da camada limite como a forma mais simples de representar a dimensão vertical, e explique como o CALIOP (onde houver passagem) entraria para conferir esse ajuste.
   - Para o CALIOP, deixe pronto um leitor (HDF4) documentado, mas **não baixe** se exigir login do Earthdata: registre o passo a passo que ela faria com a conta dela.
5. **Dependência indevida e validação.** Escreva e explique o desenho:
   - se o PM2,5 simulado pelo CATT-BRAMS entrar como preditor, o modelo pode estar copiando a simulação; mostre como testar isso (com e sem a variável);
   - validação cruzada **por estação** e **por blocos de tempo**, nunca sorteando linhas;
   - escreva um teste automatizado que falha se um mesmo dia/estação aparecer em treino e teste.
6. **Referências.** 8 a 12 trabalhos sobre AOD × PM2,5 com correção vertical (camada limite, CALIOP), de preferência com algum no Brasil, com DOI conferido.

## Entregas
As de `REGRAS-COMUNS.md`, mais: tabela e figura das passagens do CALIOP, a tabela integrada do protótipo (CSV pequeno) e a figura dela.
