"""
Roda toda a cadeia, na ordem do README, e confere que as saidas existem.

Uso:  python codigo/rodar_tudo.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASSOS = [
    "01_calipso_cmr.py",
    "02_estacoes_pm25.py",
    "03_prototipo_gee.py",
    "04_validacao.py",
    "teste_validacao.py",
    "05_leitor_calipso.py",
    "06_referencias.py",
    "07_selecao_variaveis.py",
    "08_checagens.py",
    "09_controle_hora_do_dia.py",
]
# cada passo demora; 03 usa o Earth Engine (~2-3 min) e 02 baixa ~90 MB de ZIPs
ESPERADAS = [
    "dados/calipso_passagens_por_ano.csv",
    "dados/calipso_passagens_por_mes.csv",
    "dados/pm25_fontes.csv",
    "dados/prototipo_integrado.csv",
    "dados/prototipo_integrado_diario.csv",
    "dados/checagens.json",
    "dados/selecao_variaveis_modelos.csv",
    "dados/validacao_resultados.csv",
    "figuras/calipso_passagens.png",
    "figuras/pm25_estacoes_fontes.png",
    "figuras/prototipo_integrado.png",
    "figuras/selecao_variaveis.png",
    "figuras/validacao_desenho.png",
    "REFERENCIAS.md",
]


def main():
    falhou = []
    for passo in PASSOS:
        print(f"\n=== {passo}")
        r = subprocess.run([sys.executable, str(RAIZ / "codigo" / passo)], cwd=RAIZ)
        if r.returncode != 0:
            falhou.append(passo)
    print("\n--- conferindo saidas")
    for f in ESPERADAS:
        p = RAIZ / f
        print(f"  {'ok ' if p.exists() else 'FALTA'} {f}")
        if not p.exists():
            falhou.append(f)
    print("\nfalhas:", falhou if falhou else "nenhuma")


if __name__ == "__main__":
    main()
