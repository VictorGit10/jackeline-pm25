"""
06 - Confere as referências no Crossref e gera REFERENCIAS.md.

Regra do encontro: toda referência citada precisa ter o DOI conferido em
https://api.crossref.org/works/<doi> e o título precisa bater. Este script faz
exatamente isso: busca cada DOI, compara o título (similaridade de palavras) e
só escreve no arquivo o que passar. O que não passar sai e fica registrado no
console.

Uso:  python codigo/06_referencias.py
"""
from __future__ import annotations

import html
import re
import sys
import unicodedata
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import RAIZ  # noqa: E402

H = {"User-Agent": "estudo-aod-pm25-lapig-ufg/1.0 (verificacao de DOI; sem login)"}

# trabalhos com foco no Brasil (Cerrado, Amazonia ou algoritmos de AOD no pais)
DOIS_BRASIL = {
    "10.1016/j.atmosenv.2018.03.057",
    "10.1016/j.atmosenv.2023.120130",
    "10.3390/rs11192254",
    "10.5194/acp-19-9125-2019",
    "10.1038/nature19819",
    "10.5194/acp-24-8751-2024",
}

# (doi, título esperado, por que entra neste trabalho)
CANDIDATAS = [
    (
        "10.1021/es049352m",
        "Estimating Ground-Level PM2.5 in the Eastern United States Using Satellite Remote Sensing",
        "o artigo que fixou a ideia de estimar PM2,5 de superfície a partir de AOD orbital; ponto de partida conceitual.",
    ),
    (
        "10.1289/ehp.0901623",
        "Global Estimates of Ambient Fine Particulate Matter Concentrations from Satellite-Based Aerosol Optical Depth",
        "mostra o uso de razão AOD:PM2,5 e de perfis verticais para converter coluna em superfície, em escala global.",
    ),
    (
        "10.1016/j.rse.2013.08.032",
        "Estimating ground-level PM2.5 concentrations in the Southeastern United States using MAIAC AOD retrievals and a two-stage model",
        "exemplo de modelo em dois estágios com MAIAC, com filtros de qualidade de AOD; base para o desenho de validação.",
    ),
    (
        "10.1016/j.apr.2019.08.003",
        "Satellite AOD conversion into ground PM10, PM2.5 and PM1 over the Po valley (Milan, Italy) exploiting information on aerosol vertical profiles",
        "converte AOD em PM usando o perfil vertical observado, que é exatamente o ajuste que falta na proposta.",
    ),
    (
        "10.1016/j.atmosenv.2017.07.054",
        "An intercomparison of AOD-converted PM2.5 concentrations using different approaches for estimating aerosol vertical distribution",
        "compara formas de representar a distribuição vertical ao converter AOD em PM2,5; útil para escolher o método.",
    ),
    (
        "10.1016/j.atmosenv.2020.117329",
        "Aerosol vertical profile variations with seasons, air mass movements and local PM2.5 levels in three large Chinese cities",
        "liga perfil vertical medido (lidar) a PM2,5 local e a transporte de massa de ar, o mesmo problema dela em GO/DF.",
    ),
    (
        "10.1007/s40726-019-00124-5",
        "Interaction Between Planetary Boundary Layer and PM2.5 Pollution in Megacities in China: a Review",
        "revisão sobre camada limite e PM2,5: por que dividir o AOD pela altura da CL é a primeira aproximação (e onde falha).",
    ),
    (
        "10.1016/j.atmosenv.2018.03.057",
        "Development of non-linear models predicting daily fine particle concentrations using aerosol optical depth retrievals and ground-based measurements at a municipality in the Brazilian Amazon region",
        "estudo brasileiro (Amazônia) que estima PM2,5 diário a partir de AOD com medições de superfície: o precedente nacional mais próximo.",
    ),
    (
        "10.1016/j.atmosenv.2023.120130",
        "Evaluation and comparison of MODIS aerosol optical depth retrieval algorithms over Brazil",
        "compara algoritmos de AOD do MODIS no Brasil (inclui MAIAC); ajuda a justificar o produto e os filtros de qualidade.",
    ),
    (
        "10.3390/rs11192254",
        "Characterization and Trends of Fine Particulate Matter (PM2.5) Fire Emissions in the Brazilian Cerrado during 2002-2017",
        "série de PM2,5 de queimadas no Cerrado (o bioma de Goiás e do DF), com tendências por ano; referência direta para a área de estudo.",
    ),
    (
        "10.5194/acp-19-9125-2019",
        "Biomass burning aerosol over the Amazon: analysis of aircraft, surface and satellite observations using a global aerosol model",
        "junta observação de aeronave, superfície e satélite para separar a coluna do que chega ao solo no aerosol de queimada — o mesmo problema de representação vertical.",
    ),
    (
        "10.1038/nature19819",
        "Amazon boundary layer aerosol concentration sustained by vertical transport during rainfall",
        "mostra que o transporte vertical controla a concentração de aerossol na camada limite amazônica: argumento físico para não tratar a coluna como bem misturada.",
    ),
    (
        "10.5194/acp-24-8751-2024",
        "Vertically resolved aerosol variability at the Amazon Tall Tower Observatory under wet-season conditions",
        "perfil vertical de aerossol medido na Amazônia (ATTO), útil para comparar a estrutura vertical do Cerrado/Amazônia com o que o CALIOP vê.",
    ),
    (
        "10.5194/amt-11-5741-2018",
        "MODIS Collection 6 MAIAC algorithm",
        "documento do algoritmo MAIAC (MCD19A2), necessário para descrever corretamente a máscara de qualidade usada aqui.",
    ),
    (
        "10.1175/2010BAMS3009.1",
        "The CALIPSO Mission",
        "descrição da missão CALIPSO/CALIOP, de onde vêm os perfis verticais usados na correção.",
    ),
    (
        "10.5194/amt-17-5301-2024",
        "The EarthCARE lidar cloud and aerosol profile processor (A-PRO): the A-AER, A-EBD, A-TC, and A-ICE products",
        "define o produto de aerossol do ATLID (EarthCARE), o sucessor operacional do CALIOP para perfil vertical.",
    ),
]


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"<[^>]+>", " ", t)  # o Crossref devolve tags (<sub>2.5</sub>)
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def conferir(doi: str, titulo_esperado: str):
    r = requests.get(f"https://api.crossref.org/works/{doi}", headers=H, timeout=60)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    m = r.json()["message"]
    titulo = (m.get("title") or [""])[0]
    a, b = set(normalizar(titulo).split()), set(normalizar(titulo_esperado).split())
    jacc = len(a & b) / max(1, len(a | b))
    if jacc < 0.6:
        return None, f"título não bate (jaccard {jacc:.2f}): {titulo[:90]}"
    autores = ", ".join(
        f"{x.get('family', '')} {x.get('given', '')[:1]}." for x in (m.get("author") or [])[:3]
    )
    if len(m.get("author") or []) > 3:
        autores += " et al."
    ano = (m.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0]
    return {
        "doi": doi,
        "titulo": html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", titulo))).strip(),
        "autores": autores,
        "ano": ano,
        "revista": html.unescape((m.get("container-title") or [""])[0]),
        "jaccard": jacc,
    }, None


def main():
    ok, recusadas = [], []
    for doi, titulo, porque in CANDIDATAS:
        meta, erro = conferir(doi, titulo)
        if meta is None:
            recusadas.append((doi, erro))
            print(f"  RECUSADA {doi}: {erro}")
        else:
            meta["porque"] = porque
            ok.append(meta)
            print(f"  ok {doi} ({meta['jaccard']:.2f}) {meta['titulo'][:70]}")

    linhas = [
        "# Referências conferidas",
        "",
        "Todas as referências abaixo tiveram o DOI conferido em `https://api.crossref.org/works/<doi>`",
        "pelo script `codigo/06_referencias.py`, que compara o título devolvido pelo Crossref com o título",
        "esperado (similaridade de palavras >= 0,60) e monta este arquivo. O que não passou foi descartado.",
        "",
        f"Conferidas: {len(ok)} de {len(CANDIDATAS)} candidatas, das quais "
        f"{sum(1 for m in ok if m['doi'] in DOIS_BRASIL)} com foco no Brasil (Cerrado, Amazônia ou AOD no país).",
        "",
    ]
    for i, m in enumerate(ok, 1):
        linhas.append(f"**{i}. {m['autores']} ({m['ano']}).** {m['titulo']}. *{m['revista']}*.")
        linhas.append(f"DOI: [{m['doi']}](https://doi.org/{m['doi']}) — {m['porque']}")
        linhas.append("")
    if recusadas:
        linhas += ["## Não conferidas (descartadas)", ""]
        linhas += [f"- `{d}`: {e}" for d, e in recusadas]
        linhas.append("")

    saida = RAIZ / "REFERENCIAS.md"
    saida.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\n{len(ok)} referências conferidas -> {saida.name}")
    if recusadas:
        print(f"{len(recusadas)} descartadas")


if __name__ == "__main__":
    main()
