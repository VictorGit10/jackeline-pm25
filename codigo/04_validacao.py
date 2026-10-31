"""
04 - Dependencia indevida e desenho de validacao.

Duas perguntas, com respostas mecanicas:
  (a) se o PM2,5 simulado pelo CATT-BRAMS entra como preditor, o modelo pode estar
      copiando a simulacao? Como testar isso?
  (b) como validar sem sortear linhas (por estacao e por blocos de tempo)?

A demonstracao usa um conjunto SIMULADO com verdade conhecida (4 estacoes,
180 dias, sazonalidade de queimadas, autocorrelacao diaria e efeito de estacao).
Num caso simulado da para ver quanto cada desenho de validacao mente, porque a
resposta certa e conhecida. A mesma funcao de verificacao roda na tabela real do
prototipo (o teste automatizado esta em codigo/teste_validacao.py).

O que cada divisao responde (importante para a tese):
  - deixar uma ESTACAO de fora = "estimar onde nao ha estacao, no mesmo dia".
    E o uso real de um mapa de PM2,5: o modelo vai preencher lugares sem sensor.
    Aqui as variaveis de calendario (sen_ano, cos_ano) NAO atrapalham: todos os
    dias do teste estao representados no treino.
  - BLOCOS DE TEMPO = "prever dias novos". Aqui o calendario e uma faca de dois
    fios: ajuda enquanto o teste cai perto de um periodo parecido do treino, e
    vira extrapolacao quando o bloco e uma estacao inteira que nao aparece no
    treino. Por isso o R2 cai, e por isso a comparacao com/sem calendario e
    reportada.

ATENCAO: os numeros desta secao sao de dados simulados; servem para escolher o
desenho de validacao, nao para dizer nada sobre AOD e PM2,5 em Goias.

Uso:  python codigo/04_validacao.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import DADOS, FIGURAS, RAIZ, salvar_csv  # noqa: E402
from validacao import (  # noqa: E402
    VazamentoError,
    checar_vazamento,
    dividir_por_bloco_de_tempo,
    dividir_por_estacao,
    dividir_sorteando_linhas,
)

SEMENTE = 11


def simular(n_estacoes=4, dias=180, semente=SEMENTE) -> pd.DataFrame:
    """Gera dados com estrutura conhecida: PM2,5 = f(AOD, BLH) + estacao + dia."""
    rng = np.random.default_rng(semente)
    idx = pd.date_range("2024-06-01", periods=dias, freq="D")
    doy = idx.dayofyear.values
    sazonal = np.sin(2 * np.pi * (doy - 240) / 365.25)  # pico em setembro
    # sinal diario comum a todas as estacoes (sinotico) -> e isso que o sorteio vaza
    comum = rng.normal(0, 1, dias)
    comum = pd.Series(comum).rolling(3, min_periods=1).mean().values
    linhas = []
    for e in range(n_estacoes):
        fogo = np.clip(rng.poisson(20 * np.clip(sazonal, 0, None) + 2), 0, None)
        aod = np.clip(0.12 + 0.22 * np.clip(sazonal, 0, None) + 0.05 * comum
                      + 0.004 * fogo + rng.normal(0, 0.03, dias), 0.02, 1.5)
        blh = 1400 - 500 * np.clip(sazonal, 0, None) + 150 * comum + rng.normal(0, 80, dias)
        vento = np.clip(2 + rng.normal(0, 0.8, dias), 0.2, None)
        temp = 21 + 5 * np.clip(sazonal, 0, None) + rng.normal(0, 1, dias)
        umidade = np.clip(65 - 20 * np.clip(sazonal, 0, None) + rng.normal(0, 5, dias), 5, 100)
        efeito_est = rng.normal(0, 3)
        pm = np.clip(
            5 + 45 * (aod / (blh / 1500)) + 4 * comum + efeito_est + 0.02 * fogo
            + rng.normal(0, 1.5, dias),
            0.5, None,
        )
        for i in range(dias):
            linhas.append(
                {
                    "estacao": f"E{e}",
                    "data": idx[i],
                    "aod": aod[i],
                    "blh": blh[i],
                    "vento": vento[i],
                    "temp": temp[i],
                    "umidade": umidade[i],
                    "focos_3d": fogo[i],
                    # termos sazonais: pratica comum em modelos de PM2,5 e a
                    # porta de entrada do vazamento quando se sorteiam linhas
                    "sen_ano": float(np.sin(2 * np.pi * doy[i] / 365.25)),
                    "cos_ano": float(np.cos(2 * np.pi * doy[i] / 365.25)),
                    "pm25": pm[i],
                }
            )
    df = pd.DataFrame(linhas)
    # "PM2,5 simulado pelo CATT-BRAMS": dependente do estado real (como um modelo
    # fisico acoplado) -> correlaciona muito com o observado, sem ser copia exata
    df["pm_sim"] = df.pm25 + rng.normal(0, 1.4, len(df))
    return df.sort_values(["estacao", "data"]).reset_index(drop=True)


PREDITORES = ["aod", "blh", "vento", "temp", "umidade", "focos_3d", "sen_ano", "cos_ano"]


def avaliar(df, preditores, alvo="pm25", esquema="bloco"):
    if esquema == "bloco":
        folds, bloqueios = list(dividir_por_bloco_de_tempo(df, n_blocos=5)), dict(bloquear_dia=True)
    elif esquema == "estacao":
        folds, bloqueios = list(dividir_por_estacao(df)), dict(bloquear_dia=False, bloquear_estacao=True)
    else:
        folds, bloqueios = list(dividir_sorteando_linhas(df)), dict(bloquear_dia=False)

    r2s = []
    for treino, teste in folds:
        checar_vazamento(treino, teste, **bloqueios)
        m = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0)
        m.fit(treino[preditores], treino[alvo])
        r2s.append(r2_score(teste[alvo], m.predict(teste[preditores])))
    return r2s, float(np.mean(r2s))


def residuos(df, preditores, alvo="pm25", coluna="pm_sim"):
    partes = []
    for treino, teste in dividir_por_bloco_de_tempo(df, n_blocos=5):
        checar_vazamento(treino, teste, bloquear_dia=True)
        m = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0)
        m.fit(treino[preditores], treino[alvo])
        partes.append(pd.DataFrame({"r": teste[alvo].values - m.predict(teste[preditores]),
                                    "v": teste[coluna].values}))
    p = pd.concat(partes)
    return p.r.corr(p.v, method="spearman"), len(p)


def main():
    df = simular()
    print(f"Dados simulados: {df.estacao.nunique()} estacoes x {df.data.nunique()} dias "
          f"= {len(df)} linhas; PM2,5 de {df.pm25.min():.1f} a {df.pm25.max():.1f} ug/m3")

    print("\n1) O desenho de validacao muda o resultado")
    linhas = []
    for esquema, rotulo in [("bloco", "blocos de tempo"), ("estacao", "por estacao"),
                            ("sorteio", "sorteando linhas (errado)")]:
        r2s, media = avaliar(df, PREDITORES, esquema=esquema)
        linhas.append({"esquema": rotulo, "r2_medio": round(media, 3),
                       "r2_por_fold": "; ".join(f"{x:.2f}" for x in r2s)})
        print(f"  {rotulo:26s} R2 medio = {media:6.3f}   folds = {[round(x, 2) for x in r2s]}")

    print("\n1b) Papel das variaveis de calendario (sen_ano, cos_ano)")
    sem_cal = [c for c in PREDITORES if c not in ("sen_ano", "cos_ano")]
    for nome_esq, esq in [("blocos de tempo", "bloco"), ("por estacao", "estacao")]:
        r2_com, m_com = avaliar(df, PREDITORES, esquema=esq)
        r2_sem, m_sem = avaliar(df, sem_cal, esquema=esq)
        linhas.append({"esquema": f"{nome_esq}, com calendario", "r2_medio": round(m_com, 3),
                       "r2_por_fold": "; ".join(f"{x:.2f}" for x in r2_com), "n": len(df)})
        linhas.append({"esquema": f"{nome_esq}, sem calendario", "r2_medio": round(m_sem, 3),
                       "r2_por_fold": "; ".join(f"{x:.2f}" for x in r2_sem), "n": len(df)})
        print(f"  {nome_esq:18s} com calendario R2 = {m_com:6.3f} | sem = {m_sem:6.3f}")

    print("\n2) PM2,5 simulado (CATT-BRAMS) como preditor: o modelo copia a simulacao?")
    for nome, preds in [
        ("sem a simulacao", PREDITORES),
        ("com a simulacao", PREDITORES + ["pm_sim"]),
    ]:
        r2s, media = avaliar(df, preds, esquema="bloco")
        r, n = residuos(df, preds)
        linhas.append({"esquema": f"blocos de tempo, {nome}", "r2_medio": round(media, 3),
                       "r2_por_fold": "; ".join(f"{x:.2f}" for x in r2s)})
        print(f"  {nome:18s} R2 = {media:6.3f}   Spearman(residuo, simulacao) = {r:6.3f}")

    print("\n   Importancia das variaveis (modelo ajustado em tudo, so diagnostico):")
    for nome, preds in [("sem a simulacao", PREDITORES), ("com a simulacao", PREDITORES + ["pm_sim"])]:
        m = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0).fit(df[preds], df.pm25)
        imp = sorted(zip(preds, m.feature_importances_), key=lambda x: -x[1])[:3]
        texto = ", ".join(f"{k}={v:.2f}" for k, v in imp)
        print(f"   {nome:18s} {texto}")
        linhas.append({"esquema": f"importancia ({nome})", "r2_medio": "", "r2_por_fold": texto})

    print("\n3) A mesma verificacao na tabela real do prototipo (Brasilia, 2024)")
    real = pd.read_csv(DADOS / "prototipo_integrado_diario.csv", parse_dates=["data"])
    real = real[real.pm25_hora.notna() & real.aod.notna() & (real.n_px >= 20)]
    real["estacao"] = "Fercal"
    print(f"  {len(real)} pares dia-satelite ({real.data.nunique()} dias distintos), "
          f"de {real.data.min().date()} a {real.data.max().date()}")
    print(f"  por satelite: {real.satelite.value_counts().to_dict()}")
    print("  com 1 ponto e ~1,5 ano nao ha modelo defensavel (ver 07_selecao_variaveis.py):")
    print("  e por isso que a proxima etapa e juntar CALIOP + mais estacoes + mais anos.")
    for treino, teste in dividir_por_bloco_de_tempo(real, n_blocos=5):
        checar_vazamento(treino, teste, bloquear_dia=True)
    print("  ok: os 5 blocos de tempo da tabela real passam na verificacao")

    salvar_csv(pd.DataFrame(linhas), "validacao_resultados.csv")

    # --- figura ----------------------------------------------------------
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    rot = ["blocos\nde tempo", "por\nestacao", "sorteando\nlinhas"]
    valores = [linhas[0]["r2_medio"], linhas[1]["r2_medio"], linhas[2]["r2_medio"]]
    cores = ["#2e6e4e", "#1f4e79", "#c0504d"]
    ax1.bar(rot, valores, color=cores)
    for i, v in enumerate(valores):
        ax1.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=9)
    ax1.set_ylabel("R² médio (5 folds)")
    ax1.set_title("Mesmo modelo, três desenhos de validação\n(dados simulados com verdade conhecida)")
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_ylim(0, max(valores) * 1.15)

    ax2.scatter(df.pm25, df.pm_sim, s=6, alpha=0.4, color="#c0504d")
    lim = [0, df.pm25.max() * 1.05]
    ax2.plot(lim, lim, "k--", lw=1)
    ax2.set_xlabel("PM2,5 observado (µg m$^{-3}$)")
    ax2.set_ylabel("PM2,5 simulado (µg m$^{-3}$)")
    ax2.set_title("Simulação x observação: alta correlação não prova\nque a simulação pode entrar como preditor")
    ax2.grid(alpha=0.3)

    fig.suptitle("Vazamento por sorteio de linhas e por simulação usada como preditor", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURAS / "validacao_desenho.png", dpi=170, bbox_inches="tight")
    print(f"\nFigura: {(FIGURAS / 'validacao_desenho.png').relative_to(RAIZ)}")

    try:
        checar_vazamento(df.iloc[:10], df.iloc[:10])
        print("ERRO: o teste nao detectou vazamento obvio")
    except VazamentoError:
        print("Teste do proprio desenho: vazamento proposital detectado (ok)")


if __name__ == "__main__":
    main()
