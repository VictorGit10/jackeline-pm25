"""
Controle: o AOD/BLH "melhora" a relacao com o PM2,5 da hora, ou so carrega a hora do dia?

Hipotese levantada numa revisao: empilhando Terra (manha) e Aqua (tarde) e comparando com o
PM2,5 na hora da passagem (pm25_hora), dividir o AOD pela altura da camada limite deveria
ajudar, porque a tarde tem camada limite mais alta e PM2,5 mais baixo.

O controle e uma variavel que so diz "manha ou tarde" (1 = Terra). Se ela sozinha correlaciona
tanto quanto o AOD/BLH, o ganho do empilhamento vem do ciclo diurno, nao do aerossol.

So le dados/prototipo_integrado_diario.csv (sem rede), a mesma tabela de 07_selecao_variaveis.py. Mesmo piso de qualidade do relatorio: n_px >= 20.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import RAIZ  # noqa: E402

PISO_NPX = 20


def spearman(a, b):
    return round(float(a.corr(b, method="spearman")), 3)


def main():
    d = pd.read_csv(RAIZ / "dados" / "prototipo_integrado_diario.csv")
    d = d[(d.ponto == "Fercal") & (d.n_px >= PISO_NPX) & d.aod.notna()].dropna(subset=["aod", "aod_km", "pm25_hora"])
    d["manha"] = (d.satelite == "Terra").astype(int)

    linhas = []
    print(f"Terra + Aqua empilhados, alvo pm25_hora, n = {len(d)}")
    for nome, col in [("AOD", "aod"), ("AOD/BLH", "aod_km"), ("BLH", "blh"), ("manha (1 = Terra)", "manha")]:
        r = spearman(d[col], d.pm25_hora)
        print(f"  {nome:20s} {r:+.3f}")
        linhas.append({"conjunto": "empilhado", "variavel": nome, "n": len(d), "spearman": r})
    print("Dentro de cada satelite (sem a diferenca manha x tarde):")
    for sat, g in d.groupby("satelite"):
        ra, rk = spearman(g.aod, g.pm25_hora), spearman(g.aod_km, g.pm25_hora)
        print(f"  {sat:6s} n={len(g):3d}  AOD {ra:+.3f}  AOD/BLH {rk:+.3f}")
        linhas += [{"conjunto": sat, "variavel": "AOD", "n": len(g), "spearman": ra},
                   {"conjunto": sat, "variavel": "AOD/BLH", "n": len(g), "spearman": rk}]
    pd.DataFrame(linhas).to_csv(RAIZ / "dados" / "controle_hora_do_dia.csv", index=False)
    print("salvo dados/controle_hora_do_dia.csv")


if __name__ == "__main__":
    main()
