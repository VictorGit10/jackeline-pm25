"""Utilitarios compartilhados pelos scripts desta pasta.

Nada aqui faz login nem usa credencial. HTTP com User-Agent identificavel
(o CMR atras de CloudFront recusa requisicoes sem User-Agent).
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import requests

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
FIGURAS = RAIZ / "figuras"
for _d in (DADOS, FIGURAS):
    _d.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Pontos de estudo (graus decimais, WGS84). Coordenadas de centro de cidade,
# nao de estacao: servem para a geometria orbital e para amostrar o satelite.
# ---------------------------------------------------------------------------
SITES = {
    "Goiania": {"lon": -49.2536, "lat": -16.6869},
    "Brasilia": {"lon": -47.8828, "lat": -15.7939},
    "Porangatu": {"lon": -49.1486, "lat": -13.4403},  # norte de GO, mais fogo
}

UA = "estudo-aod-pm25-lapig-ufg/1.0 (script academico; sem login)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def get_json(url: str, params: dict | None = None, tentativas: int = 4, timeout: int = 120):
    """GET com novas tentativas e espera crescente (CMR as vezes devolve 500)."""
    ultimo = None
    for i in range(tentativas):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            ultimo = RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        except (requests.RequestException, ValueError) as e:  # inclui timeout/JSON invalido
            ultimo = e
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"falhou {url} {params}: {ultimo}")


def cmr_paginas(caminho: str, params: dict, page_size: int = 2000):
    """Percorre todas as paginas de uma busca do CMR e devolve a lista de itens."""
    itens, pagina = [], 1
    while True:
        p = dict(params, page_size=page_size, page_num=pagina)
        d = get_json(f"https://cmr.earthdata.nasa.gov/search/{caminho}", p)
        lote = d.get("items", d.get("feed", {}).get("entry", []))
        itens.extend(lote)
        if len(lote) < page_size:
            return itens
        pagina += 1


# ---------------------------------------------------------------------------
# Geometria na esfera
# ---------------------------------------------------------------------------
R_TERRA_KM = 6371.0088


def latlon_para_xyz(lat, lon):
    lat, lon = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


def distancia_ponto_trajeto_km(lat0, lon0, lats, lons):
    """Distancia minima (km) de um ponto a uma polilinha sobre a esfera.

    Projecao do ponto no plano do grande circulo de cada segmento, com
    verificacao de que a projecao cai dentro do arco; senao, usa o vertice.
    """
    c = latlon_para_xyz(lat0, lon0)
    a = latlon_para_xyz(np.asarray(lats), np.asarray(lons))
    melhor = 9e9
    for i in range(len(a) - 1):
        p1, p2 = a[i], a[i + 1]
        n = np.cross(p1, p2)
        norma = np.linalg.norm(n)
        if norma < 1e-12:  # segmento degenerado
            d = math.acos(min(1.0, max(-1.0, float(np.dot(c, p1)))))
            melhor = min(melhor, d * R_TERRA_KM)
            continue
        n = n / norma
        q = c - np.dot(c, n) * n  # projecao de c no plano do grande circulo
        nq = np.linalg.norm(q)
        q = q / nq if nq > 1e-9 else p1
        # q esta no arco p1->p2?
        dentro = (
            np.dot(np.cross(p1, q), n) >= 0 and np.dot(np.cross(q, p2), n) >= 0
        )
        alvo = q if dentro else (p1 if np.dot(c, p1) >= np.dot(c, p2) else p2)
        d = math.acos(min(1.0, max(-1.0, float(np.dot(c, alvo)))))
        melhor = min(melhor, d * R_TERRA_KM)
    return melhor


def distancia_por_amostragem_km(lat0, lon0, lats, lons, n_por_segmento=400):
    """Implementacao independente (forca bruta) para controle numerico."""
    c = latlon_para_xyz(lat0, lon0)
    lats, lons = np.asarray(lats, float), np.asarray(lons, float)
    melhor = 9e9
    for i in range(len(lats) - 1):
        t = np.linspace(0, 1, n_por_segmento)
        la = lats[i] + t * (lats[i + 1] - lats[i])
        lo = lons[i] + t * (lons[i + 1] - lons[i])
        p = latlon_para_xyz(la, lo)
        cosang = np.clip(p @ c, -1, 1)
        melhor = min(melhor, float(np.min(np.arccos(cosang))) * R_TERRA_KM)
    return melhor


def salvar_csv(df, nome: str, **kw):
    caminho = DADOS / nome
    df.to_csv(caminho, index=False, encoding="utf-8", **kw)
    print(f"  -> {caminho.relative_to(RAIZ)}  ({len(df)} linhas)")
    return caminho


def salvar_json(obj, nome: str):
    caminho = DADOS / nome
    caminho.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {caminho.relative_to(RAIZ)}")
    return caminho
