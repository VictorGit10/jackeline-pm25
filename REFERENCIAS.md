# Referências conferidas

Todas as referências abaixo tiveram o DOI conferido em `https://api.crossref.org/works/<doi>`
pelo script `codigo/06_referencias.py`, que compara o título devolvido pelo Crossref com o título
esperado (similaridade de palavras >= 0,60) e monta este arquivo. O que não passou foi descartado.

Conferidas: 16 de 16 candidatas, das quais 6 com foco no Brasil (Cerrado, Amazônia ou AOD no país).

**1. Liu Y., Sarnat J., Kilaru V. et al. (2005).** Estimating Ground-Level PM2.5 in the Eastern United States Using Satellite Remote Sensing. *Environmental Science & Technology*.
DOI: [10.1021/es049352m](https://doi.org/10.1021/es049352m) — o artigo que fixou a ideia de estimar PM2,5 de superfície a partir de AOD orbital; ponto de partida conceitual.

**2. van Donkelaar A., Martin R., Brauer M. et al. (2010).** Global Estimates of Ambient Fine Particulate Matter Concentrations from Satellite-Based Aerosol Optical Depth: Development and Application. *Environmental Health Perspectives*.
DOI: [10.1289/ehp.0901623](https://doi.org/10.1289/ehp.0901623) — mostra o uso de razão AOD:PM2,5 e de perfis verticais para converter coluna em superfície, em escala global.

**3. Hu X., Waller L., Lyapustin A. et al. (2014).** Estimating ground-level PM2.5 concentrations in the Southeastern United States using MAIAC AOD retrievals and a two-stage model. *Remote Sensing of Environment*.
DOI: [10.1016/j.rse.2013.08.032](https://doi.org/10.1016/j.rse.2013.08.032) — exemplo de modelo em dois estágios com MAIAC, com filtros de qualidade de AOD; base para o desenho de validação.

**4. Ferrero L., Riccio A., Ferrini B. et al. (2019).** Satellite AOD conversion into ground PM10, PM2.5 and PM1 over the Po valley (Milan, Italy) exploiting information on aerosol vertical profiles, chemistry, hygroscopicity and meteorology. *Atmospheric Pollution Research*.
DOI: [10.1016/j.apr.2019.08.003](https://doi.org/10.1016/j.apr.2019.08.003) — converte AOD em PM usando o perfil vertical observado, que é exatamente o ajuste que falta na proposta.

**5. Su T., Li J., Li C. et al. (2017).** An intercomparison of AOD-converted PM2.5 concentrations using different approaches for estimating aerosol vertical distribution. *Atmospheric Environment*.
DOI: [10.1016/j.atmosenv.2017.07.054](https://doi.org/10.1016/j.atmosenv.2017.07.054) — compara formas de representar a distribuição vertical ao converter AOD em PM2,5; útil para escolher o método.

**6. Wang L., Lyu B., Bai Y. (2020).** Aerosol vertical profile variations with seasons, air mass movements and local PM2.5 levels in three large China cities. *Atmospheric Environment*.
DOI: [10.1016/j.atmosenv.2020.117329](https://doi.org/10.1016/j.atmosenv.2020.117329) — liga perfil vertical medido (lidar) a PM2,5 local e a transporte de massa de ar, o mesmo problema dela em GO/DF.

**7. Miao Y., Li J., Miao S. et al. (2019).** Interaction Between Planetary Boundary Layer and PM2.5 Pollution in Megacities in China: a Review. *Current Pollution Reports*.
DOI: [10.1007/s40726-019-00124-5](https://doi.org/10.1007/s40726-019-00124-5) — revisão sobre camada limite e PM2,5: por que dividir o AOD pela altura da CL é a primeira aproximação (e onde falha).

**8. Gonçalves K., Winkler M., Benchimol-Barbosa P. et al. (2018).** Development of non-linear models predicting daily fine particle concentrations using aerosol optical depth retrievals and ground-based measurements at a municipality in the Brazilian Amazon region. *Atmospheric Environment*.
DOI: [10.1016/j.atmosenv.2018.03.057](https://doi.org/10.1016/j.atmosenv.2018.03.057) — estudo brasileiro (Amazônia) que estima PM2,5 diário a partir de AOD com medições de superfície: o precedente nacional mais próximo.

**9. Rudke A., Martins J., Martins L. et al. (2023).** Evaluation and comparison of MODIS aerosol optical depth retrieval algorithms over Brazil. *Atmospheric Environment*.
DOI: [10.1016/j.atmosenv.2023.120130](https://doi.org/10.1016/j.atmosenv.2023.120130) — compara algoritmos de AOD do MODIS no Brasil (inclui MAIAC); ajuda a justificar o produto e os filtros de qualidade.

**10. Mataveli G., Silva M., França D. et al. (2019).** Characterization and Trends of Fine Particulate Matter (PM2.5) Fire Emissions in the Brazilian Cerrado during 2002–2017. *Remote Sensing*.
DOI: [10.3390/rs11192254](https://doi.org/10.3390/rs11192254) — série de PM2,5 de queimadas no Cerrado (o bioma de Goiás e do DF), com tendências por ano; referência direta para a área de estudo.

**11. Reddington C., Morgan W., Darbyshire E. et al. (2019).** Biomass burning aerosol over the Amazon: analysis of aircraft, surface and satellite observations using a global aerosol model. *Atmospheric Chemistry and Physics*.
DOI: [10.5194/acp-19-9125-2019](https://doi.org/10.5194/acp-19-9125-2019) — junta observação de aeronave, superfície e satélite para separar a coluna do que chega ao solo no aerosol de queimada — o mesmo problema de representação vertical.

**12. Wang J., Krejci R., Giangrande S. et al. (2016).** Amazon boundary layer aerosol concentration sustained by vertical transport during rainfall. *Nature*.
DOI: [10.1038/nature19819](https://doi.org/10.1038/nature19819) — mostra que o transporte vertical controla a concentração de aerossol na camada limite amazônica: argumento físico para não tratar a coluna como bem misturada.

**13. Franco M., Valiati R., Holanda B. et al. (2024).** Vertically resolved aerosol variability at the Amazon Tall Tower Observatory under wet-season conditions. *Atmospheric Chemistry and Physics*.
DOI: [10.5194/acp-24-8751-2024](https://doi.org/10.5194/acp-24-8751-2024) — perfil vertical de aerossol medido na Amazônia (ATTO), útil para comparar a estrutura vertical do Cerrado/Amazônia com o que o CALIOP vê.

**14. Lyapustin A., Wang Y., Korkin S. et al. (2018).** MODIS Collection 6 MAIAC algorithm. *Atmospheric Measurement Techniques*.
DOI: [10.5194/amt-11-5741-2018](https://doi.org/10.5194/amt-11-5741-2018) — documento do algoritmo MAIAC (MCD19A2), necessário para descrever corretamente a máscara de qualidade usada aqui.

**15. Winker D., Pelon J., Coakley J. et al. (2010).** The CALIPSO Mission. *Bulletin of the American Meteorological Society*.
DOI: [10.1175/2010BAMS3009.1](https://doi.org/10.1175/2010BAMS3009.1) — descrição da missão CALIPSO/CALIOP, de onde vêm os perfis verticais usados na correção.

**16. Donovan D., van Zadelhoff G., Wang P. (2024).** The EarthCARE lidar cloud and aerosol profile processor (A-PRO): the A-AER, A-EBD, A-TC, and A-ICE products. *Atmospheric Measurement Techniques*.
DOI: [10.5194/amt-17-5301-2024](https://doi.org/10.5194/amt-17-5301-2024) — define o produto de aerossol do ATLID (EarthCARE), o sucessor operacional do CALIOP para perfil vertical.
