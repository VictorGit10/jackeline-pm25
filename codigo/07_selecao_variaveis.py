"""
07 - Seleção de variáveis da dinâmica vertical, sem vazamento.

Pergunta do formulário: quais variáveis ligadas à dinâmica vertical melhoram a
estimativa de PM2,5 a partir do AOD? Com ~1 ano e duas estações vizinhas, isto é
uma ILUSTRAÇÃO DE MÉTODO, não a seleção de variáveis da tese.

Protocolo (o ponto central):
  - validação por blocos de SEMANAS, com intervalo (gap) de 3 dias entre treino e
    teste, para que dias vizinhos não vazem de um lado para o outro;
  - a escolha do conjunto de variáveis é feita DENTRO de cada dobra (validação
    interna), nunca olhando o teste;
  - importância por permutação AGRUPADA: AOD e AOD/BLH são o mesmo grupo, para
    não premiar duas versões da mesma variável;
  - comparam-se quatro conjuntos: só AOD, AOD+vertical, AOD+meteorologia,
    AOD+vertical+meteorologia.

Uso:  python codigo/07_selecao_variaveis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import DADOS, FIGURAS, RAIZ, salvar_csv  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SEMENTE = 42
ALVO = "pm25_hora"
PISO_N_PX = 20

GRUPOS = {
    "AOD": ["aod", "aod_km"],
    "vertical": ["blh", "ventilacao", "frac_fumaca"],
    "meteorologia": ["vento", "umidade", "temp", "deficit_orvalho", "cape", "cin"],
}
MODELOS = {
    "só AOD": ["aod"],
    "AOD + vertical": ["aod", "aod_km", "blh", "ventilacao", "frac_fumaca"],
    "AOD + meteorologia": ["aod", "vento", "umidade", "temp", "deficit_orvalho", "cape", "cin"],
    "AOD + vertical + meteorologia": sum(GRUPOS.values(), []),
}


def carregar() -> pd.DataFrame:
    d = pd.read_csv(DADOS / "prototipo_integrado_diario.csv", parse_dates=["data"])
    d = d[d.aod.notna() & (d.n_px >= PISO_N_PX)].copy()
    d["aqua"] = (d.satelite == "Aqua").astype(int)
    for c in ["cape", "cin"]:
        if c not in d:
            d[c] = np.nan
    return d.dropna(subset=[ALVO]).sort_values("data").reset_index(drop=True)


def blocos_semanais(datas: pd.Series, n_blocos=6, gap_dias=3):
    """Rotula cada dia com um bloco semanal; devolve (rotulo, mascara_gap)."""
    inicio = datas.min().normalize()
    semana = ((datas - inicio).dt.days // 7).astype(int)
    # agrupa semanas em n_blocos contiguos
    n_semanas = semana.max() + 1
    rot = pd.qcut(semana.rank(method="first"), min(n_blocos, n_semanas), labels=False)
    return rot.astype(int)


def folds_blocos(d: pd.DataFrame, n_blocos=6, gap_dias=3):
    rot = blocos_semanais(d["data"], n_blocos)
    for b in sorted(rot.unique()):
        teste = d[rot == b]
        t0, t1 = teste.data.min(), teste.data.max()
        gap = (d.data >= t0 - pd.Timedelta(days=gap_dias)) & (d.data <= t1 + pd.Timedelta(days=gap_dias))
        treino = d[(rot != b) & ~gap]
        yield treino, teste


def modelo():
    return RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=SEMENTE, n_jobs=-1)


def avaliar_cv(d, preditores, folds):
    r2s = []
    for tr, te in folds:
        m = modelo().fit(tr[preditores], tr[ALVO])
        r2s.append(r2_score(te[ALVO], m.predict(te[preditores])))
    return np.array(r2s)


def escolher_dentro_do_treino(treino, candidatos, n_inner=3):
    """Seleção interna: escolhe o conjunto com melhor R2 na CV interna."""
    melhor, melhor_r2 = None, -np.inf
    for nome, preds in candidatos.items():
        r2 = np.nanmean(avaliar_cv(treino, preds, folds_blocos(treino, n_blocos=n_inner)))
        if r2 > melhor_r2:
            melhor, melhor_r2 = nome, r2
    return melhor, melhor_r2


def importancia_grupos(d, preditores, folds, n_rep=20):
    """ΔR² ao permutar cada grupo de variáveis, avaliado nas dobras externas."""
    grupos = {g: [c for c in cols if c in preditores] for g, cols in GRUPOS.items()}
    grupos = {g: c for g, c in grupos.items() if c}
    deltas = {g: [] for g in grupos}
    rng = np.random.default_rng(SEMENTE)
    for tr, te in folds:
        m = modelo().fit(tr[preditores], tr[ALVO])
        base = r2_score(te[ALVO], m.predict(te[preditores]))
        for g, cols in grupos.items():
            vals = []
            for _ in range(n_rep):
                t2 = te.copy()
                for c in cols:
                    t2[c] = rng.permutation(t2[c].values)
                vals.append(base - r2_score(te[ALVO], m.predict(t2[preditores])))
            deltas[g].append(float(np.mean(vals)))
    return {g: round(float(np.mean(v)), 4) for g, v in deltas.items()}


def main():
    d = carregar()
    print(f"{len(d)} dias-satelite com AOD (n_px >= {PISO_N_PX}) e PM2,5 horário")
    print(f"  Terra: {(d.satelite=='Terra').sum()}, Aqua: {(d.satelite=='Aqua').sum()}, "
          f"dias distintos: {d.data.nunique()}")
    print(f"  PM2,5: {d[ALVO].min():.1f} a {d[ALVO].max():.1f} µg/m3, mediana {d[ALVO].median():.1f}")

    folds = list(folds_blocos(d, n_blocos=6, gap_dias=3))
    print(f"  {len(folds)} dobras semanais com gap de 3 dias; "
          f"tamanhos de teste: {[len(t) for _, t in folds]}")

    linhas = []
    # baseline: prever a media do treino (R2 = 0 se o teste tivesse a mesma media)
    r2b = []
    for tr, te in folds:
        r2b.append(r2_score(te[ALVO], np.full(len(te), tr[ALVO].mean())))
    linhas.append({"modelo": "média do treino (baseline)", "r2_medio": round(float(np.nanmean(r2b)), 3),
                   "r2_por_dobra": "; ".join(f"{x:.2f}" for x in r2b), "n": len(d)})
    print(f"  {'média do treino (baseline)':32s} R2 = {np.nanmean(r2b):6.3f}")

    for nome, preds in MODELOS.items():
        r2 = avaliar_cv(d, preds, folds)
        linhas.append({"modelo": nome, "r2_medio": round(float(np.nanmean(r2)), 3),
                       "r2_por_dobra": "; ".join(f"{x:.2f}" for x in r2),
                       "n": len(d)})
        print(f"  {nome:32s} R2 = {np.nanmean(r2):6.3f}  {[round(x, 2) for x in r2]}")

    # seleção dentro de cada dobra (aninhada)
    escolhidos, r2_aninhado = [], []
    for tr, te in folds:
        nome, _ = escolher_dentro_do_treino(tr, MODELOS)
        m = modelo().fit(tr[MODELOS[nome]], tr[ALVO])
        r2_aninhado.append(r2_score(te[ALVO], m.predict(te[MODELOS[nome]])))
        escolhidos.append(nome)
    linhas.append({"modelo": "seleção interna (aninhada)", "r2_medio": round(float(np.nanmean(r2_aninhado)), 3),
                   "r2_por_dobra": "; ".join(f"{x:.2f}" for x in r2_aninhado),
                   "n": len(d), "escolhas": "; ".join(escolhidos)})
    print(f"  {'seleção interna (aninhada)':32s} R2 = {np.nanmean(r2_aninhado):6.3f}  "
          f"escolhas = {escolhidos}")

    imp = importancia_grupos(d, MODELOS["AOD + vertical + meteorologia"], folds)
    print("  importância por grupo (delta R2 ao permutar):", imp)

    # correlações de referência (posto), por satélite e alvo
    corr = []
    for sat in ["Aqua", "Terra"]:
        s = d[d.satelite == sat]
        for alvo in ["pm25_hora", "pm25_dia18"]:
            if alvo not in s or s[alvo].notna().sum() < 8:
                continue
            x = s.dropna(subset=[alvo])
            corr.append({
                "satelite": sat, "alvo": alvo, "n": len(x),
                "spearman_aod": round(float(x.aod.corr(x[alvo], method="spearman")), 3),
                "spearman_aod_blh": round(float(x.aod_km.corr(x[alvo], method="spearman")), 3),
            })
    for c in corr:
        print(f"  {c['satelite']:6s} {c['alvo']:12s} n={c['n']:3d}  AOD {c['spearman_aod']:+.2f}  "
              f"AOD/BLH {c['spearman_aod_blh']:+.2f}")

    salvar_csv(pd.DataFrame(linhas), "selecao_variaveis_modelos.csv")
    salvar_csv(pd.DataFrame(corr), "selecao_variaveis_correlacoes.csv")
    (DADOS / "selecao_variaveis_importancia.json").write_text(
        json.dumps({"importancia_grupos_delta_r2": imp, "escolhas_por_dobra": escolhidos,
                    "n": len(d), "alvo": ALVO}, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- figura ----------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.5, 1]})
    nomes = [l["modelo"] for l in linhas]
    vals = [l["r2_medio"] for l in linhas]
    cores = ["#999999", "#8fa6b8", "#1f4e79", "#2e6e4e", "#c0504d", "#e08a3c"]
    ax1.barh(nomes, vals, color=cores[: len(nomes)])
    for i, v in enumerate(vals):
        ax1.text(max(v, 0) + 0.01, i, f"{v:.2f}", va="center", fontsize=9)
    ax1.axvline(0, color="k", lw=0.8)
    ax1.axvline(linhas[0]["r2_medio"], color="#555555", ls="--", lw=1)
    ax1.set_xlabel("R² médio nas dobras semanais")
    ax1.set_title("Comparação de conjuntos de variáveis\n(alvo: PM2,5 na hora da passagem; tracejado = baseline)")
    ax1.grid(axis="x", alpha=0.3)
    ax1.tick_params(labelsize=8)

    gs = list(imp.keys())
    ax2.barh(gs, [imp[g] for g in gs], color="#1f4e79")
    ax2.axvline(0, color="k", lw=0.8)
    ax2.set_xlabel("ΔR² ao permutar o grupo")
    ax2.set_title("Importância por permutação agrupada\n(negativo = não ajuda)")
    ax2.grid(axis="x", alpha=0.3)
    ax2.tick_params(labelsize=8)

    fig.suptitle(f"Seleção de variáveis sem vazamento — Fercal, {len(d)} dias-satélite", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURAS / "selecao_variaveis.png", dpi=170, bbox_inches="tight")
    print(f"\nFigura: {(FIGURAS / 'selecao_variaveis.png').relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
