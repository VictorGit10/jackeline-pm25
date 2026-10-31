"""
03 - Protótipo de associação espacial e temporal no ponto Fercal (Earth Engine).

Por que Fercal: as duas estações de PM2,5 do DF (CRAS Fercal e Escola) ficam a
2-3 km uma da outra, em -15,5955/-47,8566, e a 21-23 km do centro de Brasília
(que era o ponto usado antes). Este script usa o ponto no MEIO das duas e um
raio de AOD de 10 km, de modo que as estações ficam dentro do disco.

Periodo: 19/09/2024 (primeiro registro de PM2,5 no MonitorAr) a 31/12/2025.
Terra e Aqua sao mantidos separados, cada um com o ERA5 da sua propria hora.

Saidas:
  dados/prototipo_integrado.csv          uma linha por granulo (ponto x dia x satelite)
  dados/prototipo_integrado_diario.csv   idem, agregado quando ha 2 granulos do mesmo satelite
  dados/pm25_fercal_horario.csv          serie horaria das duas estacoes
  dados/prototipo_controle.json          contagens de pixels, descarte da mascara, horarios

Metricas: pm25_hora (media na janela de +-1 h em torno da passagem, em hora local)
e pm25_dia (media do dia, com >=18 h e >=12 h validas).

Uso:  python codigo/03_prototipo_gee.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import DADOS, FIGURAS, RAIZ, salvar_csv  # noqa: E402

import matplotlib  # noqa: E402
import matplotlib.dates  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import ee  # noqa: E402

PROJETO = "SEU-PROJETO-EARTH-ENGINE"
INI, FIM = "2024-09-19", "2025-12-31"
PONTO = {"nome": "Fercal", "lat": -15.5955, "lon": -47.8566}
ESTACOES = {
    "fercal": {"nome": "Estação CRAS FERCAL", "lat": -15.601292, "lon": -47.870440},
    "escola": {"nome": "Estação Escola", "lat": -15.589824, "lon": -47.842796},
}
RAIO_AOD_M = 10_000
RAIO_FOCO_M = 100_000
JANELA_FOCO_DIAS = 3
PISO_N_PX = 20  # pixels validos minimos no disco de 10 km (justificado no relatorio)
ANO_ARQUIVOS = [2024, 2025]


# ---------------------------------------------------------------------------
# PM2,5: le os ZIPs do MonitorAr (2024 e 2025)
# ---------------------------------------------------------------------------
def pm25_horario() -> pd.DataFrame:
    linhas = []
    for ano in ANO_ARQUIVOS:
        zp = DADOS / f"monitorar_{ano}.zip"
        if not zp.exists():
            raise SystemExit(f"falta {zp.name}: rode antes o 02_estacoes_pm25.py")
        with zipfile.ZipFile(zp) as z:
            nome = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(nome) as f:
                txt = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
                for row in csv.DictReader(txt, delimiter=","):
                    if row["sg_uf"] != "DF":
                        continue
                    if "2,5" not in row["no_item_monitorado"]:
                        continue
                    try:
                        val = float(row["nu_concentracao"])
                    except (TypeError, ValueError):
                        continue
                    if not (0 <= val < 1000):
                        continue
                    linhas.append(
                        {
                            "estacao": row["no_estacao"],
                            "data_hora": row["dh_medicao"][:19],  # hora local (ver relatorio)
                            "pm25": val,
                        }
                    )
    df = pd.DataFrame(linhas)
    df["data_hora"] = pd.to_datetime(df["data_hora"])
    df["data"] = df["data_hora"].dt.normalize()
    df["hora"] = df["data_hora"].dt.hour
    h = df.groupby(["estacao", "data_hora"]).pm25.mean().reset_index()
    h["data"] = h["data_hora"].dt.normalize()
    h["hora"] = h["data_hora"].dt.hour
    h["apelido"] = np.where(h.estacao.str.contains("FERCA", case=False), "fercal",
                            np.where(h.estacao.str.contains("Escola", case=False), "escola", "outra"))
    salvar_csv(h, "pm25_fercal_horario.csv")

    # medias diarias com dois limiares de horas validas
    d = h.groupby(["data", "apelido"]).pm25.agg(["mean", "count"]).reset_index()
    d.columns = ["data", "apelido", "pm25", "n_horas"]
    largo = d.pivot_table(index="data", columns="apelido", values="pm25", aggfunc="mean")
    largo.columns = [f"pm25_{c}" for c in largo.columns]
    contagem = d.pivot_table(index="data", columns="apelido", values="n_horas", aggfunc="sum")
    contagem.columns = [f"n_horas_{c}" for c in contagem.columns]
    largo = largo.join(contagem).reset_index()
    # media entre estacoes: so se ambas tiverem o dia
    cols = [c for c in largo.columns if c.startswith("pm25_")]
    largo["pm25_media"] = largo[cols].mean(axis=1, skipna=True)
    largo["n_estacoes"] = largo[cols].notna().sum(axis=1)
    salvar_csv(largo.assign(data=lambda x: x.data.dt.strftime("%Y-%m-%d")),
               "pm25_fercal_diario.csv")
    return h, largo


def janela_pm(h: pd.DataFrame, data: pd.Timestamp, hora_local: int, meia: int = 1) -> float:
    """Media do PM2,5 em +-meia hora em torno da passagem (hora local)."""
    horas = [(hora_local + k) % 24 for k in range(-meia, meia + 1)]
    # se a janela cruza a meia-noite, usa o mesmo dia (aproximacao documentada)
    sub = h[(h.data == data) & (h.hora.isin(horas))]
    if len(sub) >= 2:
        return float(sub.pm25.mean())
    return np.nan


# ---------------------------------------------------------------------------
# Earth Engine
# ---------------------------------------------------------------------------
def mascara_qa(img):
    """Mascara de qualidade do AOD_QA do MAIAC (MCD19A2 v061).

    Layout oficial dos bits (catalogo do Earth Engine / guia do produto):
      0-2  nuvem (0 indefinido, 1 claro, 2 possivelmente nublado, 3 nublado,
           5 sombra, 6 ponto quente de fogo, 7 sedimento)
      3-4  terra/agua/neve/gelo
      5-7  adjacencia (0 normal)
      8-11 QA do AOD (0 melhor qualidade)
      12   brilho especular
      13-14 modelo de aerossol (1 = fumaca)
    """
    qa = img.select("AOD_QA")
    return (
        qa.bitwiseAnd(7).eq(1)
        .And(qa.rightShift(5).bitwiseAnd(7).eq(0))
        .And(qa.rightShift(8).bitwiseAnd(15).eq(0))
        .And(qa.rightShift(12).bitwiseAnd(1).eq(0))
    )


def estatisticas_granulo(img, buffers):
    aod = img.select("Optical_Depth_055")
    valido = aod.gt(0).And(aod.lt(5000))
    limpo = aod.updateMask(valido.And(mascara_qa(img)))
    cru = aod.updateMask(valido)
    n = limpo.mask().unmask(0).rename("n")
    nraw = cru.mask().unmask(0).rename("nraw")
    modelo = img.select("AOD_QA").rightShift(13).bitwiseAnd(3)
    fumaca = modelo.eq(1).And(limpo.mask()).unmask(0).rename("fumaca")
    stack = (limpo.rename("aod").addBands(cru.rename("aod_raw"))
             .addBands(n).addBands(nraw).addBands(fumaca))
    red = ee.Reducer.mean().combine(reducer2=ee.Reducer.sum(), sharedInputs=True)
    fc = stack.reduceRegions(collection=buffers, reducer=red, scale=1000, tileScale=4)
    return fc.map(lambda f: f.set({"t_ms": img.get("system:time_start"),
                                   "satelite": img.get("SATELLITE")}))


def tile_modis(lat, lon):
    return f"h{int((lon + 180) // 10):02d}v{int((90 - lat) // 10):02d}"


def blocos(ini: str, fim: str, dias: int = 25):
    a, b = pd.Timestamp(ini), pd.Timestamp(fim)
    while a < b:
        c = min(a + pd.Timedelta(days=dias), b)
        yield a.strftime("%Y-%m-%d"), c.strftime("%Y-%m-%d")
        a = c


def aod_nos_pontos(buffers, recortes, tile):
    partes = []
    for ini, fim in recortes:
        col = (ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
               .filterDate(ini, fim)
               .filter(ee.Filter.stringContains("system:index", tile)))
        got = col.map(lambda img: estatisticas_granulo(img, buffers)).flatten().getInfo()["features"]
        print(f"    AOD {ini}..{fim}: {len(got)} registros")
        partes.extend([f["properties"] for f in got])
    return partes


def era5_por_horas(ponto_ee, horas_ms, banda):
    col = ee.ImageCollection("ECMWF/ERA5/HOURLY").filter(ee.Filter.inList("system:time_start", horas_ms))
    def f(img):
        d = img.select(banda).reduceRegion(ee.Reducer.first(), ponto_ee, 10000, bestEffort=True)
        return ee.Feature(None, d).set({"t_ms": img.get("system:time_start")})
    return col.map(f)


def focos_por_dia(ponto_ee, ini, fim):
    col = ee.ImageCollection("FIRMS").filterDate(ini, fim)
    geo = ponto_ee.buffer(RAIO_FOCO_M, 1000)
    def f(img):
        fogo = img.select("T21").gt(300).And(img.select("confidence").gte(30))
        n = fogo.reduceRegion(ee.Reducer.sum(), geo, 1000, maxPixels=1e9, bestEffort=True)
        return ee.Feature(None, {"focos": n.get("T21"), "t_ms": img.get("system:time_start")})
    return col.map(f)


def horas_txt(x: float) -> str:
    """Converte 14.65 em '14:39'."""
    h = int(x)
    m = int(round((x - h) * 60))
    if m == 60:
        h, m = h + 1, 0
    return f"{h:02d}:{m:02d}"


def main():
    ee.Initialize(project=PROJETO)
    print("1) PM2,5 horario do DF (MonitorAr 2024+2025)")
    pm_h, pm_dia = pm25_horario()
    print(f"  {len(pm_h)} registros horarios; {pm_h.data.nunique()} dias; "
          f"estacoes: {sorted(pm_h.estacao.unique())}")

    print("2) AOD MAIAC (Terra e Aqua), ERA5 e FIRMS no ponto Fercal")
    buffers = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Point([PONTO["lon"], PONTO["lat"]]).buffer(RAIO_AOD_M, 500),
                   {"ponto": PONTO["nome"], "tile": tile_modis(PONTO["lat"], PONTO["lon"])})
    ])
    pt = ee.Geometry.Point([PONTO["lon"], PONTO["lat"]])
    recortes = list(blocos(INI, FIM))
    print(f"  recortes: {len(recortes)}")
    aod_partes = aod_nos_pontos(buffers, recortes, tile_modis(PONTO["lat"], PONTO["lon"]))

    aod = pd.DataFrame(aod_partes)
    for c in ("aod_sum", "aod_raw_sum", "n_sum", "nraw_sum", "fumaca_sum"):
        if c not in aod:
            aod[c] = 0.0
        aod[c] = pd.to_numeric(aod[c], errors="coerce").fillna(0.0)
    aod["n_px"] = aod.n_sum
    with np.errstate(divide="ignore", invalid="ignore"):
        aod["aod"] = np.where(aod.n_sum > 0, aod.aod_sum / aod.n_sum, np.nan) * 0.001
        aod["aod_sem_qa"] = np.where(aod.nraw_sum > 0, aod.aod_raw_sum / aod.nraw_sum, np.nan) * 0.001
        aod["frac_fumaca"] = np.where(aod.n_sum > 0, aod.fumaca_sum / aod.n_sum, np.nan)
    aod["data_hora_utc"] = pd.to_datetime(aod.t_ms, unit="ms", utc=True)
    aod["data"] = (aod.data_hora_utc.dt.tz_convert("America/Sao_Paulo")
                   .dt.normalize().dt.tz_localize(None))
    aod["satelite"] = aod.satelite.replace({"T": "Terra", "A": "Aqua"})
    n_bruto = len(aod)
    n_zero = int((aod.n_px <= 0).sum())

    # ERA5: horas unicas de cada recorte, fatiado igual ao AOD
    BANDAS = ["boundary_layer_height", "u_component_of_wind_10m", "v_component_of_wind_10m",
              "temperature_2m", "dewpoint_temperature_2m",
              "convective_available_potential_energy", "convective_inhibition"]
    met = []
    for ini, fim in recortes:
        sub = aod[(aod.data >= pd.Timestamp(ini)) & (aod.data < pd.Timestamp(fim))]
        horas = sorted({int(round(t / 3.6e6) * 3600000) for t in sub.t_ms})
        if not horas:
            continue
        got = era5_por_horas(pt, horas, BANDAS).getInfo()["features"]
        met.extend([f["properties"] for f in got])
        print(f"    ERA5 {ini}..{fim}: {len(got)} horas")
    met = pd.DataFrame(met)
    met["data_hora_utc"] = pd.to_datetime(met.t_ms, unit="ms", utc=True)
    met["hora_cheia"] = met.data_hora_utc.dt.tz_localize(None).dt.round("h")

    # FIRMS (soma de pixels de fogo por dia)
    fogo = []
    for ini, fim in recortes:
        got = focos_por_dia(pt, ini, fim).getInfo()["features"]
        fogo.extend([dict(f["properties"]) for f in got])
    fogo = pd.DataFrame(fogo)
    fogo["focos"] = pd.to_numeric(fogo.focos, errors="coerce").fillna(0)
    fogo["data"] = pd.to_datetime(fogo.t_ms, unit="ms", utc=True).dt.normalize().dt.tz_localize(None)
    print(f"    FIRMS: {len(fogo)} dias")

    # --- integra -----------------------------------------------------------
    aod["hora_cheia"] = aod.data_hora_utc.dt.tz_localize(None).dt.round("h")
    aod = aod.merge(met.drop(columns=["t_ms", "data_hora_utc"]), on="hora_cheia", how="left")

    aod["temp_c"] = aod.temperature_2m - 273.15
    aod["td_c"] = aod.dewpoint_temperature_2m - 273.15
    aod["deficit_orvalho"] = aod.temp_c - aod.td_c
    aod["vento"] = np.hypot(aod.u_component_of_wind_10m, aod.v_component_of_wind_10m)
    aod["ventilacao"] = aod.boundary_layer_height * aod.vento  # m2/s
    aod["umidade"] = 100 * np.exp(17.625 * aod.td_c / (243.04 + aod.td_c)) / np.exp(
        17.625 * aod.temp_c / (243.04 + aod.temp_c))
    aod["aod_km"] = aod.aod / (aod.boundary_layer_height / 1000.0)
    local = aod.data_hora_utc.dt.tz_convert("America/Sao_Paulo")
    aod["hora_local"] = local.dt.hour
    aod["hora_local_dec"] = local.dt.hour + local.dt.minute / 60.0

    fogo_d = fogo.groupby("data").focos.sum().sort_index()
    idx = pd.date_range(INI, FIM, freq="D")
    fogo_d = fogo_d.reindex(idx).fillna(0)
    fogo3 = pd.DataFrame({
        "data": idx,
        "focos_dia": fogo_d.values,
        "focos_3d": [fogo_d.loc[d - pd.Timedelta(days=2):d].sum() for d in idx],
    })

    # PM: janela horaria e media diaria (dois limiares)
    pm_h["data"] = pd.to_datetime(pm_h["data"]).dt.normalize()
    dia_cols = pm_dia.copy()
    dia_cols["data"] = pd.to_datetime(dia_cols["data"])
    pm18 = dia_cols[(dia_cols.n_horas_fercal.fillna(0) >= 18) | (dia_cols.n_horas_escola.fillna(0) >= 18)]
    pm12 = dia_cols[(dia_cols.n_horas_fercal.fillna(0) >= 12) | (dia_cols.n_horas_escola.fillna(0) >= 12)]

    aod["pm25_hora"] = [
        janela_pm(pm_h, d, int(h)) for d, h in zip(aod.data, aod.hora_local)
    ]
    aod = aod.merge(fogo3, on="data", how="left")
    aod = aod.merge(pm18[["data", "pm25_media"]].rename(columns={"pm25_media": "pm25_dia18"}),
                    on="data", how="left")
    aod = aod.merge(pm12[["data", "pm25_media"]].rename(columns={"pm25_media": "pm25_dia12"}),
                    on="data", how="left")
    aod = aod.merge(dia_cols[["data", "pm25_fercal", "pm25_escola"]], on="data", how="left")
    aod["pm25_dia"] = aod.pm25_dia18  # nome curto; o de 12 h fica como comparacao

    aod = aod.sort_values(["data", "satelite", "data_hora_utc"])
    aod["valido"] = (aod.n_px >= PISO_N_PX).astype(int)

    colunas = {
        "data": lambda d: d.data.dt.strftime("%Y-%m-%d"),
        "hora_utc": lambda d: d.data_hora_utc.dt.strftime("%H:%M"),
        "hora_local_txt": lambda d: d.data_hora_utc.dt.tz_convert("America/Sao_Paulo").dt.strftime("%H:%M"),
        "aod": lambda d: d.aod.round(4),
        "aod_km": lambda d: d.aod_km.round(4),
        "aod_sem_qa": lambda d: d.aod_sem_qa.round(4),
        "blh": lambda d: d.boundary_layer_height.round(0),
        "vento": lambda d: d.vento.round(2),
        "ventilacao": lambda d: d.ventilacao.round(0),
        "umidade": lambda d: d.umidade.round(1),
        "temp": lambda d: d.temp_c.round(2),
        "deficit_orvalho": lambda d: d.deficit_orvalho.round(2),
        "frac_fumaca": lambda d: d.frac_fumaca.round(3),
        "cape": lambda d: d.convective_available_potential_energy.round(0),
        "cin": lambda d: d.convective_inhibition.round(0),
        "pm25_hora": lambda d: d.pm25_hora.round(2),
        "pm25_dia18": lambda d: d.pm25_dia18.round(2),
        "pm25_dia12": lambda d: d.pm25_dia12.round(2),
        "pm25_fercal": lambda d: d.pm25_fercal.round(2),
        "pm25_escola": lambda d: d.pm25_escola.round(2),
    }
    detalhe = aod.assign(**colunas)[
        ["ponto", "data", "satelite", "hora_utc", "hora_local_txt", "aod", "aod_km", "aod_sem_qa",
         "n_px", "valido", "frac_fumaca", "blh", "vento", "ventilacao", "umidade", "temp",
         "deficit_orvalho", "cape", "cin", "focos_3d", "pm25_hora", "pm25_dia18", "pm25_dia12",
         "pm25_fercal", "pm25_escola"]
    ]
    salvar_csv(detalhe, "prototipo_integrado.csv")

    # diario: media dos granulos do mesmo satelite no dia (raramente >1)
    dia = (
        aod.groupby(["ponto", "data", "satelite"])
        .agg(hora_local=("hora_local", "mean"), aod=("aod", "mean"), aod_km=("aod_km", "mean"),
             aod_sem_qa=("aod_sem_qa", "mean"), n_px=("n_px", "sum"),
             n_granulos=("aod", "size"), frac_fumaca=("frac_fumaca", "mean"),
             blh=("boundary_layer_height", "mean"), vento=("vento", "mean"),
             ventilacao=("ventilacao", "mean"), umidade=("umidade", "mean"),
             temp=("temp_c", "mean"), deficit_orvalho=("deficit_orvalho", "mean"),
             cape=("convective_available_potential_energy", "mean"),
             cin=("convective_inhibition", "mean"),
             focos_3d=("focos_3d", "first"),
             pm25_hora=("pm25_hora", "mean"), pm25_dia18=("pm25_dia18", "first"),
             pm25_dia12=("pm25_dia12", "first"), pm25_fercal=("pm25_fercal", "first"),
             pm25_escola=("pm25_escola", "first"))
        .reset_index()
    )
    dia["valido"] = (dia.n_px >= PISO_N_PX).astype(int)
    dia = dia.sort_values(["data", "satelite"])
    salvar_csv(dia.assign(data=lambda d: d.data.dt.strftime("%Y-%m-%d")),
               "prototipo_integrado_diario.csv")

    # --- controle e numeros de rastreabilidade ----------------------------
    def estat(x):
        x = pd.Series(x).dropna()
        if x.empty:
            return {}
        return {"min": round(float(x.min()), 4), "mediana": round(float(x.median()), 2),
                "media": round(float(x.mean()), 3), "max": round(float(x.max()), 4)}

    controle = {
        "periodo": [INI, FIM],
        "ponto": PONTO,
        "piso_n_px": PISO_N_PX,
        "registros_granulo_ponto": int(n_bruto),
        "registros_com_zero_pixel": n_zero,
        "fracao_descartada_pela_mascara": round(n_zero / max(1, n_bruto), 3),
        "linhas_validas": int(len(dia)),
        "n_px": {
            "todos": estat(aod.n_px),
            "Terra": estat(aod[aod.satelite == "Terra"].n_px),
            "Aqua": estat(aod[aod.satelite == "Aqua"].n_px),
        },
        "aod": {s: estat(aod[aod.satelite == s].aod) for s in ("Terra", "Aqua")},
        "hora_local": {
            s: {
                "min": horas_txt(aod[aod.satelite == s].hora_local_dec.min()),
                "media": horas_txt(aod[aod.satelite == s].hora_local_dec.mean()),
                "max": horas_txt(aod[aod.satelite == s].hora_local_dec.max()),
            }
            for s in ("Terra", "Aqua")
        },
        "pm25": {
            "dias_com_pm25_horario": int(pm_h.data.nunique()),
            "dias_pm25_dia_18h": int(pm18.data.nunique()),
            "dias_pm25_dia_12h": int(pm12.data.nunique()),
            "primeiro_registro": str(pm_h.data_hora.min()),
            "ultimo_registro": str(pm_h.data_hora.max()),
        },
        "focos": "soma de pixels de fogo de 1 km do produto FIRMS NRT (nao e contagem de deteccoes)",
    }
    (DADOS / "prototipo_controle.json").write_text(
        json.dumps(controle, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- figura ----------------------------------------------------------
    fig = plt.figure(figsize=(12, 8.5))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 1], hspace=0.5, wspace=0.26)

    ax = fig.add_subplot(gs[0, :])
    for sat, cor, marc in [("Terra", "#2e6e4e", "^"), ("Aqua", "#1f4e79", "o")]:
        s2 = dia[dia.satelite == sat]
        ax.plot(s2.data, s2.aod, marc, ms=3.2, color=cor, alpha=0.75, label=f"AOD {sat}")
    ax.set_ylabel("AOD 550 nm")
    ax2 = ax.twinx()
    ax2.plot(dia.groupby("data").pm25_dia18.first().index,
             dia.groupby("data").pm25_dia18.first().values,
             "-", lw=1.0, color="#c0504d", alpha=0.8, label="PM2,5 diário (18 h)")
    ax2.set_ylabel("PM2,5 (µg m$^{-3}$)")
    ax.set_title("Fercal, 19/09/2024 a 31/12/2025: AOD de Terra e Aqua e PM2,5 das estações do DF")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[1, 0])
    m = dia[(dia.satelite == "Aqua") & dia.pm25_hora.notna() & (dia.n_px >= PISO_N_PX)]
    sc = ax.scatter(m.aod, m.pm25_hora, c=m.frac_fumaca, cmap="YlOrRd", s=22,
                    edgecolor="k", linewidth=0.25, vmin=0, vmax=1)
    ax.set_xlabel("AOD Aqua")
    ax.set_ylabel("PM2,5 na hora da passagem (µg m$^{-3}$)")
    ax.set_title("AOD × PM2,5 horário (Aqua), cor = fração de fumaça")
    ax.grid(alpha=0.3)
    plt.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)

    ax = fig.add_subplot(gs[1, 1])
    ax.scatter(m.aod_km, m.pm25_hora, c=m.frac_fumaca, cmap="YlOrRd", s=22,
               edgecolor="k", linewidth=0.25, vmin=0, vmax=1)
    ax.set_xlabel("AOD / BLH (km$^{-1}$, Aqua)")
    ax.set_ylabel("PM2,5 na hora da passagem (µg m$^{-3}$)")
    ax.set_title("AOD/BLH × PM2,5 horário (Aqua)")
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[2, 0])
    ax.plot(dia.groupby("data").focos_3d.first().index,
            dia.groupby("data").focos_3d.first().values, "-", color="#e08a3c", lw=1)
    ax.set_ylabel("pixels de fogo (3 d)")
    ax.set_title("Fogo no raio de 100 km (FIRMS NRT)")
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", labelsize=7, rotation=30)

    ax = fig.add_subplot(gs[2, 1])
    for sat, cor in [("Terra", "#2e6e4e"), ("Aqua", "#1f4e79")]:
        s2 = dia[(dia.satelite == sat) & (dia.n_px > 0)]
        ax.hist(s2.n_px, bins=np.arange(0, 330, 20), alpha=0.55, color=cor, label=sat)
    ax.axvline(PISO_N_PX, color="k", ls="--", lw=1, label=f"piso = {PISO_N_PX} px")
    ax.set_xlabel("pixels válidos no disco de 10 km")
    ax.set_ylabel("dias")
    ax.set_title("Quantos pixels entram na média")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.suptitle("Protótipo integrado no ponto Fercal (dentro do disco das duas estações)", fontsize=12)
    saida = FIGURAS / "prototipo_integrado.png"
    fig.savefig(saida, dpi=170, bbox_inches="tight")
    print(f"\nFigura: {saida.relative_to(RAIZ)}")
    print(f"Controle: {json.dumps({k: v for k, v in controle.items() if k in ('registros_granulo_ponto','registros_com_zero_pixel','fracao_descartada_pela_mascara','hora_local')}, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
