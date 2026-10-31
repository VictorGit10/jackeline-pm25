"""
Funções de divisão treino/teste e de verificação de vazamento.

Regra central: em dados espaço-temporais não se sorteiam linhas. O teste pode
ser separado por tempo (blocos contíguos de dias) ou por espaço (estações).
A verificação falha quando o teste compartilha com o treino aquilo que deveria
estar bloqueado: dias (se o bloqueio é temporal) ou estações (se é espacial).

Este módulo é usado por 04_validacao.py e testado por teste_validacao.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class VazamentoError(AssertionError):
    """Levantado quando treino e teste compartilham dia ou estação bloqueados."""


def checar_vazamento(
    treino: pd.DataFrame,
    teste: pd.DataFrame,
    col_estacao: str = "estacao",
    col_dia: str = "data",
    bloquear_dia: bool = True,
    bloquear_estacao: bool = False,
) -> bool:
    """Falha se o bloqueio pedido for violado (ou se houver linha repetida)."""
    if len(treino) == 0 or len(teste) == 0:
        raise VazamentoError("divisão vazia")

    pares_t = set(zip(treino[col_estacao].astype(str), treino[col_dia].astype(str)))
    pares_s = set(zip(teste[col_estacao].astype(str), teste[col_dia].astype(str)))
    comuns = pares_t & pares_s
    if comuns:
        raise VazamentoError(f"{len(comuns)} par(es) estação-dia repetidos, ex.: {sorted(comuns)[:2]}")

    if bloquear_dia:
        dias = set(pd.to_datetime(teste[col_dia]).astype(str)) & set(pd.to_datetime(treino[col_dia]).astype(str))
        if dias:
            raise VazamentoError(f"{len(dias)} dia(s) no treino e no teste, ex.: {sorted(dias)[:3]}")

    if bloquear_estacao:
        ests = set(teste[col_estacao].astype(str)) & set(treino[col_estacao].astype(str))
        if ests:
            raise VazamentoError(f"estação(ões) no treino e no teste: {sorted(ests)[:3]}")
    return True


def blocos_de_tempo(dias: pd.Series, n_blocos: int = 5) -> pd.Series:
    """Divide o período em n blocos contíguos (não sorteia dias)."""
    ordem = pd.Series(pd.to_datetime(dias).unique()).sort_values().reset_index(drop=True)
    if n_blocos > len(ordem):
        n_blocos = max(2, len(ordem) // 2)
    rotulos = pd.qcut(ordem.rank(method="first"), n_blocos, labels=False)
    mapa = dict(zip(ordem, rotulos))
    return pd.Series(pd.to_datetime(dias).map(mapa).values)


def dividir_por_bloco_de_tempo(df: pd.DataFrame, n_blocos: int = 5, col_dia: str = "data"):
    """Gera (treino, teste) com blocos contíguos; testa um bloco por vez."""
    rot = blocos_de_tempo(df[col_dia], n_blocos).values
    for b in sorted(set(rot)):
        yield df[rot != b], df[rot == b]


def dividir_por_estacao(df: pd.DataFrame, col_estacao: str = "estacao"):
    """Deixa uma estação inteira de fora por vez (validação espacial)."""
    for est in sorted(df[col_estacao].unique()):
        yield df[df[col_estacao] != est], df[df[col_estacao] == est]


def dividir_sorteando_linhas(df: pd.DataFrame, n_partes: int = 5, semente: int = 0):
    """O jeito ERRADO, só para medir o tamanho do problema."""
    rng = np.random.default_rng(semente)
    rot = rng.integers(0, n_partes, len(df))
    for k in range(n_partes):
        yield df[rot != k], df[rot == k]
