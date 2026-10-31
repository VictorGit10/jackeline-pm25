"""
Teste automatizado do desenho de validacao.

Roda sozinho (python codigo/teste_validacao.py) e tambem com pytest.
O ponto central: o teste precisa FALHAR quando o mesmo dia/estacao aparece em
treino e teste. Se ele passar no sorteio de linhas, ele nao serve para nada.

Uso:  python codigo/teste_validacao.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validacao import (  # noqa: E402
    VazamentoError,
    blocos_de_tempo,
    checar_vazamento,
    dividir_por_bloco_de_tempo,
    dividir_por_estacao,
    dividir_sorteando_linhas,
)


def dados_falsos(n_estacoes=6, dias=120, semente=0) -> pd.DataFrame:
    rng = np.random.default_rng(semente)
    dias_idx = pd.date_range("2024-01-01", periods=dias, freq="D")
    linhas = []
    for e in range(n_estacoes):
        for d in dias_idx:
            if rng.random() < 0.15:  # buracos, como dados reais
                continue
            linhas.append(
                {
                    "estacao": f"E{e}",
                    "data": d,
                    "pm25": 10 + 5 * np.sin(d.dayofyear / 30) + rng.normal(0, 2) + e,
                    "aod": 0.2 + 0.05 * e + rng.normal(0, 0.05),
                }
            )
    return pd.DataFrame(linhas)


def test_sem_vazamento_nos_blocos_de_tempo():
    df = dados_falsos()
    for treino, teste in dividir_por_bloco_de_tempo(df, n_blocos=5):
        assert checar_vazamento(treino, teste)
        # blocos sao contiguos: nenhum dia do teste no treino
        assert not set(teste.data).intersection(set(treino.data))


def test_sem_vazamento_por_estacao():
    df = dados_falsos()
    vistos = 0
    for treino, teste in dividir_por_estacao(df):
        assert checar_vazamento(treino, teste, bloquear_dia=False, bloquear_estacao=True)
        assert not set(teste.estacao).intersection(set(treino.estacao))
        vistos += 1
    assert vistos == df.estacao.nunique()


def test_sorteio_de_linhas_falha():
    """O teste tem que reprovar o sorteio: senao nao detecta nada."""
    df = dados_falsos()
    reprovou = 0
    for treino, teste in dividir_sorteando_linhas(df):
        try:
            checar_vazamento(treino, teste)
        except VazamentoError:
            reprovou += 1
    assert reprovou > 0, "o sorteio de linhas deveria ter sido reprovado"


def test_deteccao_de_um_dia_repetido():
    """Caso cirurgico: uma unica linha repetida tem que ser pega."""
    df = dados_falsos(n_estacoes=2, dias=10)
    treino, teste = df.iloc[:-1], df.iloc[-1:]
    teste_repetido = pd.concat([teste, treino.head(1)])
    try:
        checar_vazamento(treino, teste_repetido)
        raise AssertionError("nao detectou a linha repetida")
    except VazamentoError:
        pass


def test_blocos_sao_contiguos_e_cobrem_o_periodo():
    dias = pd.Series(pd.date_range("2024-01-01", periods=90, freq="D"))
    rot = blocos_de_tempo(dias, n_blocos=5).values
    # o rotulo tem que crescer com o tempo (blocos contiguos, nao sorteados)
    assert all(rot[i] <= rot[i + 1] for i in range(len(rot) - 1))
    assert len(set(rot)) == 5


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok      {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"  FALHOU  {nome}: {e}")
    print(f"\n{len([n for n in globals() if n.startswith('test_')])} testes, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)
