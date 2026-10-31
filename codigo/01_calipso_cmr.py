"""
01 - CALIOP/CALIPSO: quanto perfil vertical existe de verdade sobre GO e o DF.

Fonte: busca publica do NASA CMR (Common Metadata Repository). NAO exige login.
Produto: CAL_LID_L2_05kmAPro (aerosol profile, 5 km), versao mais recente.

O que o script faz
1. Descobre no CMR a versao mais recente do produto e o ultimo granulo existente
   (evidencia do fim da serie; a NASA anunciou o fim da missao em 01/08/2023).
2. Para cada ponto (Goiania, Brasilia) e cada ano, busca os granulos cuja
   trajetoria passa na caixa de +-1,5 grau e calcula a distancia real do ponto
   a polilinha da trajetoria (geometria "Lines" do UMM).
3. Conta passagens a <=5, 25 e 50 km, por ano e por mes, dia e noite.
   Dia/noite vem do sufixo do nome do arquivo (ZN = noite, ZD = dia), que reflete
   o horario local da orbita heliossincrona (~13h30 dia / ~01h30 noite).
4. Controles:
   - distancia analitica x distancia por amostragem densa (implementacao
     independente, nos 20 granulos mais proximos);
   - contagem esperada pela repetitividade orbital de 16 dias / 233 orbitas;
   - caixa de 5 km (deve ser bem menor que 25 km).
5. Grava CSV, tabelas agregadas e figura.

Uso:  python codigo/01_calipso_cmr.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (  # noqa: E402
    FIGURAS,
    RAIZ,
    SITES,
    cmr_paginas,
    distancia_por_amostragem_km,
    distancia_ponto_trajeto_km,
    get_json,
    salvar_csv,
    salvar_json,
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PRODUTO = "CAL_LID_L2_05kmAPro"
ANO_INI, ANO_FIM = 2006, 2023
RAIOS = [5, 25, 50]
PONTOS = ["Goiania", "Brasilia"]


# ---------------------------------------------------------------------------
# 1. Colecao mais recente e ultimo granulo
# ---------------------------------------------------------------------------
def descobrir_colecao():
    d = get_json(
        "https://cmr.earthdata.nasa.gov/search/collections.json",
        {"keyword": "CALIPSO Lidar Level 2 Aerosol Profile", "page_size": 50},
    )
    cands = [e for e in d["feed"]["entry"] if e["short_name"].startswith(PRODUTO)]
    cands.sort(key=lambda e: e["version_id"])
    escolhida = cands[-1]
    print(f"Colecao: {escolhida['short_name']} versao {escolhida['version_id']} ({escolhida['id']})")
    print("Versoes disponiveis:", [c["version_id"] for c in cands])

    ult = get_json(
        "https://cmr.earthdata.nasa.gov/search/granules.umm_json",
        {
            "collection_concept_id": escolhida["id"],
            "temporal": "2023-05-01T00:00:00Z,2024-01-01T00:00:00Z",
            "page_size": 5,
            "sort_key": "-start_date",
        },
    )
    ultima = ult["items"][0]["umm"]
    ultima_data = ultima["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
    print(f"Ultimo granulo da serie: {ultima_data}  ({ultima['GranuleUR']})")
    return escolhida["id"], escolhida["version_id"], ultima_data


# ---------------------------------------------------------------------------
# 2. Busca por ponto e ano
# ---------------------------------------------------------------------------
def buscar_granulos(cid: str, lat: float, lon: float, ano: int, meia_caixa: float = 1.5):
    """Devolve (lista de registros, dict granulo_ur -> polilinha)."""
    caixa = f"{lon - meia_caixa},{lat - meia_caixa},{lon + meia_caixa},{lat + meia_caixa}"
    itens = cmr_paginas(
        "granules.umm_json",
        {
            "collection_concept_id": cid,
            "bounding_box": caixa,
            "temporal": f"{ano}-01-01T00:00:00Z,{ano + 1}-01-01T00:00:00Z",
        },
    )
    registros, trajetos = [], {}
    for it in itens:
        u = it["umm"]
        ur = u["GranuleUR"]
        geo = u["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]
        linhas = geo.get("Lines") or []
        if not linhas:
            continue
        pts = max((ln["Points"] for ln in linhas), key=len)
        lats = [p["Latitude"] for p in pts]
        lons = [p["Longitude"] for p in pts]
        dist = distancia_ponto_trajeto_km(lat, lon, lats, lons)
        t0 = datetime.fromisoformat(
            u["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"].replace("Z", "+00:00")
        )
        registros.append(
            {
                "ponto": "",
                "granulo": ur,
                "inicio_utc": t0,
                "dia_noite": "noite" if ur[:-4].endswith("ZN") else "dia",
                "dist_km": dist,
            }
        )
        trajetos[ur] = (lats, lons)
    return registros, trajetos


def deduplicar_eventos(df: pd.DataFrame, janela_min: int = 40) -> pd.DataFrame:
    """Um mesmo sobrevoo pode aparecer em dois granulos vizinhos; conta uma vez."""
    if df.empty:
        return df
    df = df.sort_values("inicio_utc").reset_index(drop=True)
    eventos, ultimo = [], None
    n = 0
    for t in df["inicio_utc"]:
        if ultimo is None or (t - ultimo) > timedelta(minutes=janela_min):
            n += 1
        eventos.append(n)
        ultimo = t
    df["evento"] = eventos
    return df


def main():
    cid, versao, ultima_data = descobrir_colecao()
    print(f"\nBuscando granulos por ponto e ano (caixa de +-1,5 grau)...")

    registros, trajetos = [], {}
    for nome in PONTOS:
        s = SITES[nome]
        for ano in range(ANO_INI, ANO_FIM + 1):
            lote, tr = buscar_granulos(cid, s["lat"], s["lon"], ano)
            for r in lote:
                r["ponto"] = nome
            registros.extend(lote)
            trajetos.update(tr)
            print(f"  {nome} {ano}: {len(lote)} granulos", file=sys.stderr)

    bruto = pd.DataFrame(registros)
    bruto["inicio_utc"] = pd.to_datetime(bruto["inicio_utc"], utc=True)

    ev = pd.concat(
        [deduplicar_eventos(bruto[bruto.ponto == n].copy()) for n in PONTOS],
        ignore_index=True,
    ).sort_values(["ponto", "inicio_utc"])
    for r in RAIOS:
        ev[f"ate_{r}km"] = ev["dist_km"] <= r
    for r in (25, 50):
        for dn in ("dia", "noite"):
            ev[f"{dn}_{r}"] = ev[f"ate_{r}km"] & (ev["dia_noite"] == dn)
    ev["mes"] = ev["inicio_utc"].dt.month
    ev["ano"] = ev["inicio_utc"].dt.year

    # --- controle de geometria: analitica x amostragem densa ----------------
    difs = []
    for _, r in ev.nsmallest(20, "dist_km").iterrows():
        lats, lons = trajetos[r["granulo"]]
        s = SITES[r["ponto"]]
        d2 = distancia_por_amostragem_km(s["lat"], s["lon"], lats, lons, n_por_segmento=4000)
        difs.append(abs(d2 - r["dist_km"]))

    # --- CSV por granulo e por evento --------------------------------------
    salvar_csv(
        bruto.assign(
            inicio_utc=bruto["inicio_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            dist_km=bruto["dist_km"].round(2),
        )[["ponto", "granulo", "inicio_utc", "dia_noite", "dist_km"]],
        "calipso_granulos_brutos.csv",
    )
    salvar_csv(
        ev.assign(
            inicio_utc=ev["inicio_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            dist_km=ev["dist_km"].round(2),
        )[["ponto", "granulo", "inicio_utc", "dia_noite", "dist_km", "evento"]],
        "calipso_passagens_eventos.csv",
    )

    # --- agregados ---------------------------------------------------------
    linhas = []
    for nome in PONTOS:
        sub = ev[ev.ponto == nome]
        for ano in range(ANO_INI, ANO_FIM + 1):
            s2 = sub[sub.ano == ano]
            for r in RAIOS:
                dentro = s2[f"ate_{r}km"]
                linhas.append(
                    {
                        "ponto": nome,
                        "ano": ano,
                        "raio_km": r,
                        "n_noite": int((dentro & (s2.dia_noite == "noite")).sum()),
                        "n_dia": int((dentro & (s2.dia_noite == "dia")).sum()),
                        "n_total": int(dentro.sum()),
                    }
                )
    anual = pd.DataFrame(linhas)
    salvar_csv(anual, "calipso_passagens_por_ano.csv")

    mensal = (
        ev.groupby(["ponto", "mes"])
        .agg(
            ate_5km=("ate_5km", "sum"),
            ate_25km=("ate_25km", "sum"),
            ate_50km=("ate_50km", "sum"),
            noite_25=("noite_25", "sum"),
            dia_25=("dia_25", "sum"),
            noite_50=("noite_50", "sum"),
            dia_50=("dia_50", "sum"),
            n_eventos=("evento", "size"),
        )
        .reset_index()
    )
    salvar_csv(mensal, "calipso_passagens_por_mes.csv")

    queima = (
        ev[ev.mes.isin([8, 9, 10])]
        .groupby(["ponto", "dia_noite"])
        .agg(ate_25km=("ate_25km", "sum"), ate_50km=("ate_50km", "sum"), n_eventos=("evento", "size"))
        .reset_index()
    )
    salvar_csv(queima, "calipso_estacao_queimadas.csv")

    # --- controles --------------------------------------------------------
    controle = {
        "produto": PRODUTO,
        "versao": versao,
        "collection_concept_id": cid,
        "ultimo_granulo_utc": ultima_data,
        "anos": [ANO_INI, ANO_FIM],
        "n_granulos_na_caixa": int(len(bruto)),
        "n_eventos_deduplicados": int(len(ev)),
        "n_eventos_por_ponto": {k: int(v) for k, v in ev.groupby("ponto").size().items()},
        "n_5km": {k: int(v) for k, v in ev.groupby("ponto")["ate_5km"].sum().items()},
        "n_25km": {k: int(v) for k, v in ev.groupby("ponto")["ate_25km"].sum().items()},
        "n_50km": {k: int(v) for k, v in ev.groupby("ponto")["ate_50km"].sum().items()},
        "fracao_noite_50km": float((ev[ev.ate_50km].dia_noite == "noite").mean()),
        "fracao_noite_25km": float((ev[ev.ate_25km].dia_noite == "noite").mean()),
        "controle_distancia_km_max_abs": float(max(difs)),
        "controle_distancia_km_mediana_abs": float(np.median(difs)),
    }
    # A orbita repete a mesma grade de trajetorias a cada 16 dias (233 orbitas).
    # Logo, o numero de passagens NAO cresce como area: depende de quantas
    # trajetorias da grade caem dentro do raio, e isso fica fixo por anos.
    esperado = {}
    for nome in PONTOS:
        s = SITES[nome]
        esp = 360 / 233 * 111.32 * np.cos(np.radians(abs(s["lat"])))
        esperado[f"{nome}_espacamento_grade_km"] = round(float(esp), 1)
        # media esperada se o ponto fosse sorteado ao acaso: 2 direcoes x 2r/espacamento
        for r in (25, 50):
            esperado[f"{nome}_media_por_ano_se_aleatorio_{r}km"] = round(
                float(2 * (2 * r) / esp * 365.25 / 16), 1
            )
    controle["grade_orbital"] = esperado

    # Diagnostico da repetitividade: intervalos entre passagens do mesmo periodo
    # do dia devem rondar 16 dias (uma volta da grade).
    intervalos = {}
    for nome in PONTOS:
        sub = ev[(ev.ponto == nome) & ev.ate_50km]
        for dn in ("noite", "dia"):
            t = sub[sub.dia_noite == dn]["inicio_utc"].sort_values()
            if len(t) > 3:
                g = t.diff().dt.total_seconds().div(86400).dropna()
                g = g[(g > 5) & (g < 40)]
                intervalos[f"{nome}_{dn}_dias_mediana"] = round(float(g.median()), 1)
    controle["intervalo_entre_passagens_dias"] = intervalos
    salvar_json(controle, "calipso_controle.json")

    print("\nRESUMO (eventos deduplicados, 2006-2023):")
    for nome in PONTOS:
        n5 = int(ev[(ev.ponto == nome) & ev.ate_5km].shape[0])
        n25 = int(ev[(ev.ponto == nome) & ev.ate_25km].shape[0])
        n50 = int(ev[(ev.ponto == nome) & ev.ate_50km].shape[0])
        print(f"  {nome}: <=5 km={n5}  <=25 km={n25}  <=50 km={n50}")
    print(f"  fracao noturna (<=50 km): {controle['fracao_noite_50km']:.2f}")
    print(f"  erro maximo entre as duas implementacoes de distancia: {max(difs):.3f} km")
    print(f"  grade orbital: {esperado}")
    print(f"  intervalo mediano entre passagens (dias): {intervalos}")

    # --- figura -----------------------------------------------------------
    fig = plt.figure(figsize=(11.5, 8.8))
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.26)
    cores = {"Goiania": "#1f4e79", "Brasilia": "#c0504d"}

    ax = fig.add_subplot(gs[0, :])
    largura = 0.42
    for i, nome in enumerate(PONTOS):
        sub = anual[(anual.ponto == nome) & (anual.raio_km == 25)]
        x = sub["ano"] + (i - 0.5) * largura * 1.05
        ax.bar(x, sub["n_noite"], width=largura, color=cores[nome], label=f"{nome} - noite")
        ax.bar(x, sub["n_dia"], width=largura, bottom=sub["n_noite"], color=cores[nome],
               alpha=0.35, label=f"{nome} - dia")
    ax.set_xticks(range(ANO_INI, ANO_FIM + 1))
    ax.set_xticklabels(range(ANO_INI, ANO_FIM + 1), rotation=45, fontsize=8)
    ax.set_xlabel("ano")
    ax.set_ylabel("passagens a <=25 km")
    ax.set_title("Passagens do CALIOP a ate 25 km, por ano e por periodo do dia")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(axis="y", alpha=0.3)

    ax = fig.add_subplot(gs[1, 0])
    meses = np.arange(1, 13)
    for nome in PONTOS:
        for r, ls in [(25, "-"), (50, "--")]:
            sub = mensal[mensal.ponto == nome].set_index("mes").reindex(meses)[f"ate_{r}km"].fillna(0)
            ax.plot(meses, sub / 18, marker="o", ms=3, ls=ls, color=cores[nome],
                    label=f"{nome} <= {r} km")
    ax.axvspan(7.5, 10.5, color="orange", alpha=0.15)
    ax.set_xticks(meses)
    ax.set_xlabel("mes")
    ax.set_ylabel("passagens no mes (media 2006-2023)")
    ax.set_title("Sazonalidade (faixa laranja = ago-out, queimadas)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_ylim(bottom=0)

    ax = fig.add_subplot(gs[1, 1])
    for nome in PONTOS:
        sub = mensal[mensal.ponto == nome].set_index("mes").reindex(meses)
        ax.plot(meses, sub["noite_50"].fillna(0) / 18, marker="o", ms=3, color=cores[nome],
                label=f"{nome} - noite")
        ax.plot(meses, sub["dia_50"].fillna(0) / 18, marker="s", ms=3, color=cores[nome],
                ls=":", alpha=0.7, label=f"{nome} - dia")
    ax.axvspan(7.5, 10.5, color="orange", alpha=0.15)
    ax.set_xticks(meses)
    ax.set_xlabel("mes")
    ax.set_ylabel("passagens no mes a <=50 km (media)")
    ax.set_title("Dia x noite (o perfil noturno e o de melhor qualidade)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_ylim(bottom=0)

    fig.suptitle("CALIOP sobre Goias e o Distrito Federal: quantas passagens existem de fato (2006-2023)", fontsize=12)
    saida = FIGURAS / "calipso_passagens.png"
    fig.savefig(saida, dpi=170, bbox_inches="tight")
    print(f"\nFigura: {saida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
