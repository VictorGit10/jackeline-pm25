"""
08 - Checagens de rastreabilidade: todos os numeros "pequenos" do relatorio em
um lugar so, calculados a partir dos arquivos entregues.

Responde, com numero:
  - fracao noturna por ponto (a <=25 e <=50 km), que antes vinha "pooled";
  - AOD minimo e maximo por satelite (o 0,056 antigo nao existia);
  - custo da mascara de QA (registros com zero pixel) e distribuicao de n_px;
  - sensibilidade das correlacoes ao piso de pixels (0, 20, 50);
  - controle de QA correto: r(AOD sem QA, PM2,5) e o deslocamento de nivel;
  - Aqua x Terra nos dias comuns (pareado) e BLH nos dias comuns;
  - distancia das estacoes ao ponto de AOD;
  - numero de dobras de cada desenho de validacao.

Uso:  python codigo/08_checagens.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import DADOS, RAIZ  # noqa: E402


def r(x, y, met="spearman"):
    s = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(s) < 4:
        return None, len(s)
    return round(float(s.x.corr(s.y, method=met)), 3), len(s)


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return float(2 * 6371.0088 * np.arcsin(np.sqrt(a)))


def main():
    out = {}

    # --- CALIOP: fracao noturna por ponto ---------------------------------
    ev = pd.read_csv(DADOS / "calipso_passagens_eventos.csv")
    ctrl_cal = json.loads((DADOS / "calipso_controle.json").read_text(encoding="utf-8"))
    cal = {}
    for nome in ["Goiania", "Brasilia"]:
        s = ev[ev.ponto == nome]
        cal[nome] = {}
        for raio in (25, 50):
            dentro = s[s.dist_km <= raio]
            cal[nome][f"fracao_noturna_{raio}km"] = round(
                float((dentro.dia_noite == "noite").mean()), 3)
            cal[nome][f"n_{raio}km"] = int(len(dentro))
        # totais de referencia vêm do JSON (distancia com precisao plena)
        cal[nome]["n_5km"] = int(ctrl_cal["n_5km"][nome])
        cal[nome]["n_25km"] = int(ctrl_cal["n_25km"][nome])
        cal[nome]["n_50km"] = int(ctrl_cal["n_50km"][nome])
        cal[nome]["razao_5km_goiania_sobre_brasilia"] = None
    cal["razao_5km"] = round(
        len(ev[(ev.ponto == "Goiania") & (ev.dist_km <= 5)])
        / max(1, len(ev[(ev.ponto == "Brasilia") & (ev.dist_km <= 5)])), 1)
    out["calipso"] = cal

    # --- tabela do prototipo ----------------------------------------------
    d = pd.read_csv(DADOS / "prototipo_integrado_diario.csv", parse_dates=["data"])
    det = pd.read_csv(DADOS / "prototipo_integrado.csv")
    out["prototipo"] = {
        "linhas_granulo": int(len(det)),
        "linhas_diarias": int(len(d)),
        "aod": {s: {"min": round(float(d[d.satelite == s].aod.min()), 4),
                    "max": round(float(d[d.satelite == s].aod.max()), 4)}
                for s in ("Terra", "Aqua")},
        "n_px": {
            # so nas linhas com AOD (as de n_px=0 nao tem AOD e ficam fora)
            "mediana_todos_os_dias": {s: float(v[v.satelite == s].n_px.median())
                                      for s in ("Terra", "Aqua") for v in [d[d.aod.notna()]]},
            "mediana_dias_com_pm_hora": {s: float(d[(d.satelite == s) & d.aod.notna() & d.pm25_hora.notna()].n_px.median())
                                         for s in ("Terra", "Aqua")},
            "pct_abaixo_20": {s: round(float((d[(d.satelite == s) & d.aod.notna()].n_px < 20).mean()), 3)
                              for s in ("Terra", "Aqua")},
            "pct_abaixo_50": {s: round(float((d[(d.satelite == s) & d.aod.notna()].n_px < 50).mean()), 3)
                              for s in ("Terra", "Aqua")},
        },
    }
    ctrl = json.loads((DADOS / "prototipo_controle.json").read_text(encoding="utf-8"))
    out["prototipo"]["registros_zero_pixel"] = ctrl["registros_com_zero_pixel"]
    out["prototipo"]["fracao_descartada"] = ctrl["fracao_descartada_pela_mascara"]
    out["prototipo"]["hora_local"] = ctrl["hora_local"]

    # --- sensibilidade ao piso de pixels -----------------------------------
    linhas = []
    for piso in (0, 20, 50):
        for sat in ("Aqua", "Terra"):
            s = d[(d.satelite == sat) & (d.n_px >= piso) & d.pm25_hora.notna()]
            ra, na = r(s.aod, s.pm25_hora)
            rk, nk = r(s.aod_km, s.pm25_hora)
            linhas.append({"piso_n_px": piso, "satelite": sat, "n": na,
                           "r_aod_pm_hora": ra, "r_aodblh_pm_hora": rk})
    sens = pd.DataFrame(linhas)
    sens.to_csv(DADOS / "checagem_sensibilidade_n_px.csv", index=False)
    out["sensibilidade_n_px"] = linhas

    # --- controle de QA correto -------------------------------------------
    qa = []
    for sat in ("Aqua", "Terra"):
        s = d[(d.satelite == sat) & d.pm25_hora.notna() & (d.n_px >= 20)]
        ra, na = r(s.aod, s.pm25_hora)
        rb, nb = r(s.aod_sem_qa, s.pm25_hora)
        qa.append({"satelite": sat, "n": na, "r_aod_com_qa": ra, "r_aod_sem_qa": rb,
                   "deslocamento_nivel_pct": round(float(100 * (s.aod.mean() / s.aod_sem_qa.mean() - 1)), 2)})
    out["controle_qa"] = qa

    # --- Aqua x Terra pareado ---------------------------------------------
    a = d[(d.satelite == "Aqua") & (d.n_px >= 20)].set_index("data")
    t = d[(d.satelite == "Terra") & (d.n_px >= 20)].set_index("data")
    comuns = a.index.intersection(t.index)
    com_pm = [x for x in comuns if pd.notna(a.loc[x, "pm25_hora"]) and pd.notna(t.loc[x, "pm25_hora"])]
    pareado = {
        "dias_comuns_com_pm_hora": len(com_pm),
        "r_aqua": r(a.loc[com_pm, "aod"], a.loc[com_pm, "pm25_hora"])[0] if com_pm else None,
        "r_terra": r(t.loc[com_pm, "aod"], t.loc[com_pm, "pm25_hora"])[0] if com_pm else None,
    }
    # BLH: todos os dias vs dias comuns
    blh = {"todos": {"Aqua": round(float(a.blh.mean()), 0), "Terra": round(float(t.blh.mean()), 0)},
           "dias_comuns": {"Aqua": round(float(a.loc[comuns, "blh"].mean()), 0),
                           "Terra": round(float(t.loc[comuns, "blh"].mean()), 0)}}
    out["aqua_terra"] = {"pareado": pareado, "blh_m": blh,
                         "dias_aqua": int(len(a)), "dias_terra": int(len(t)),
                         "dias_comuns": int(len(comuns))}

    # --- relacoes com BLH (usadas na interpretacao da secao 4) -------------
    blh_rel = {"blh_aod": {}, "blh_pm_hora": {}, "blh_pm_dia18": {}}
    for sat in ("Aqua", "Terra"):
        s = d[(d.satelite == sat) & d.aod.notna() & (d.n_px >= 20)]
        blh_rel["blh_aod"][sat] = {"r": r(s.blh, s.aod)[0], "n": len(s)}
        s2 = s[s.pm25_hora.notna()]
        blh_rel["blh_pm_hora"][sat] = {"r": r(s2.blh, s2.pm25_hora)[0], "n": len(s2)}
        s3 = s[s.pm25_dia18.notna()]
        blh_rel["blh_pm_dia18"][sat] = {"r": r(s3.blh, s3.pm25_dia18)[0], "n": len(s3)}
    out["blh_relacoes"] = blh_rel

    # --- distancia das estacoes ao ponto ----------------------------------
    out["distancias_km"] = {
        "Fercal_CRAS_ao_ponto": round(haversine_km(-15.5955, -47.8566, -15.601292, -47.870440), 2),
        "Escola_ao_ponto": round(haversine_km(-15.5955, -47.8566, -15.589824, -47.842796), 2),
        "Fercal_CRAS_ao_centro_Brasilia": round(haversine_km(-15.7939, -47.8828, -15.601292, -47.870440), 2),
        "Escola_ao_centro_Brasilia": round(haversine_km(-15.7939, -47.8828, -15.589824, -47.842796), 2),
    }

    # --- dobras de cada desenho -------------------------------------------
    val = pd.read_csv(DADOS / "validacao_resultados.csv")
    out["validacao"] = {
        row["esquema"]: len([x for x in str(row["r2_por_fold"]).split(";") if x.strip()])
        for _, row in val.iterrows() if str(row["r2_por_fold"]).strip()
    }

    (DADOS / "checagens.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
