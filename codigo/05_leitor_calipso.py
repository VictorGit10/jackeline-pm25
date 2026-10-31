"""
05 - Leitor de perfis verticais do CALIOP (arquivos HDF4 do CAL_LID_L2_05kmAPro).

NAO baixa nada: os arquivos exigem conta Earthdata (login), o que este trabalho
nao faz. O que este script entrega:
  1. o caminho documentado para ela baixar os arquivos;
  2. a leitura dos campos que interessam e o calculo do que a tese precisa:
     que fracao do AOD da coluna esta DENTRO da camada limite;
  3. um autoteste com dados falsos, em ordem topo-base, que roda aqui e confere
     a conta contra um resultado feito a mao.

Geometria vertical (fonte oficial)
----------------------------------
"CALIPSO Lidar Level 2 Profile Data Description Document, Version 5.00" (ASDC,
https://asdc.larc.nasa.gov/documents/calipso/quality_summaries/cal_lid_l2_pro_v5-00_desc_qs.pdf):
  - os produtos de perfil tem 399 niveis verticais;
  - 60 m de -0,5 km a 20,2 km e 180 m acima disso, ate 30 km;
  - as altitudes sao o ponto medio de cada nivel e sao ACIMA DO NIVEL DO MAR;
  - o vetor vem na SDS `Lidar_Data_Altitudes` (399 x 1) na V5.00; nas versoes
    anteriores o mesmo vetor fica no metadado, com o nome `Lidar_Data_Altitude`.
Por isso o leitor usa, nesta ordem: a SDS, o metadado, e so entao uma grade fixa
de reserva.

Altitude acima do solo x acima do mar
-------------------------------------
A camada limite do ERA5 e acima do solo; o perfil do CALIOP e acima do mar.
A conversao usa o `DEM_Height` de cada perfil: altura_agl = altitude_asl - DEM.
Sem isso, num ponto a 1,17 km de altitude (Brasilia) a fracao na CL sai errada
por um fator grande.

O calculo central, por perfil (cada perfil do produto 5 km e uma coluna vertical):
    AOD_total   = soma(extincao_532 * espessura_do_nivel)             [coluna toda]
    AOD_ABL     = a mesma soma, so nos niveis com altura_agl <= BLH    [camada limite]
    fracao_ABL  = AOD_ABL / AOD_total
Se fracao_ABL ~ 1, o AOD da coluna representa bem o PM2,5 de superficie.
Se for ~0.4, boa parte do AOD esta acima da camada limite e dividir por BLH
nao resolve: e preciso o perfil.

Como baixar (com a conta dela)
------------------------------
    pip install earthaccess pyhdf
    python -c "import earthaccess; earthaccess.login()"   # abre o navegador
    # depois: earthaccess.search_data(short_name='CAL_LID_L2_05kmAPro',
    #                                 version='V5-00', bounding_box=(...), temporal=(...))
    # e earthaccess.download(resultados, 'dados/calipso')
Alternativa: Earthdata Search (https://search.earthdata.nasa.gov) -> produto
CAL_LID_L2_05kmAPro -> recorte por caixa -> download dos .hdf.

Campos usados (nomes exatos do arquivo HDF4, grupo principal):
    Latitude, Longitude            (graus)
    Profile_Time                   (segundos desde 1993-01-01, TAI)
    Extinction_532                 (km^-1, matriz perfil x nivel)
    ExtinctionQC_532               (-1 sem valor, 0/1 confiavel, 2 baixa confianca)
    Aerosol_Optical_Depth_532      (AOD por perfil)
    DEM_Height                     (km, altitude do solo)
    Tropopause_Height              (km)
    Feature_Classification_Flags   (bits: tipo de aerossol por nivel)
    Lidar_Data_Altitudes           (km acima do mar, 399 x 1; V5.00)

Uso:
    python codigo/05_leitor_calipso.py                 # roda o autoteste
    python codigo/05_leitor_calipso.py arquivo.hdf     # le um arquivo baixado
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import RAIZ, SITES, salvar_csv  # noqa: E402

FILL = -9999.0
N_NIVEIS = 399


# ---------------------------------------------------------------------------
# Grade fixa de reserva (so usada se o arquivo nao trouxer as altitudes)
# ---------------------------------------------------------------------------
def grade_padrao(n: int = N_NIVEIS) -> np.ndarray:
    """Grade de 399 niveis: 60 m de -0,5 a 20,2 km, 180 m acima.

    Construida a partir do fundo (ponto medio do primeiro nivel em -0,47 km).
    Com 399 pontos o topo fica em 29,83 km (um nivel de 180 m abaixo do topo
    nominal de 30,1 km). Essa diferenca de 0,18 km no topo nao afeta o AOD, que
    praticamente so tem aerossol abaixo de 20 km.
    """
    baixo = -0.47 + 0.06 * np.arange(345)          # -0.47 ... 20.17
    alto = 20.29 + 0.18 * np.arange(n - len(baixo))  # 20.29 ...
    return np.concatenate([baixo, alto])[:n]


def ler_altitudes(hdf, n_perfis_niveis: int) -> tuple[np.ndarray, str]:
    """Altitudes (km, acima do mar) na ordem em que o arquivo as guarda."""
    # 1) SDS da V5.00
    try:
        sds = hdf.select("Lidar_Data_Altitudes")
        alt = np.asarray(sds.get(), dtype=float).ravel()
        sds.endaccess()
        if alt.size == n_perfis_niveis:
            return alt, "SDS Lidar_Data_Altitudes"
    except Exception:  # noqa: BLE001 - campo pode nao existir na versao
        pass
    # 2) metadado das versoes anteriores
    try:
        attrs = hdf.attributes()
        for nome in ("Lidar_Data_Altitude", "Lidar_Data_Altitudes"):
            if nome in attrs:
                alt = np.asarray(attrs[nome], dtype=float).ravel()
                if alt.size == n_perfis_niveis:
                    return alt, f"metadado {nome}"
    except Exception:  # noqa: BLE001
        pass
    # 3) grade fixa
    return grade_padrao(n_perfis_niveis), "grade fixa de reserva"


# ---------------------------------------------------------------------------
# Leitura do HDF4 (so roda se pyhdf estiver instalado e houver arquivo)
# ---------------------------------------------------------------------------
def ler_hdf4(caminho: str) -> dict:
    """Le os campos necessarios de um arquivo CAL_LID_L2_05kmAPro (.hdf)."""
    try:
        from pyhdf.SD import SD, SDC
    except ImportError as e:
        raise SystemExit(
            "pyhdf nao esta instalado. Instale com 'pip install pyhdf' ou, mais "
            "facil, use um ambiente conda: 'conda install -c conda-forge pyhdf'."
        ) from e

    campos = [
        "Latitude", "Longitude", "Profile_Time", "Extinction_532",
        "ExtinctionQC_532", "Aerosol_Optical_Depth_532", "DEM_Height",
        "Tropopause_Height", "Feature_Classification_Flags",
    ]
    hdf = SD(caminho, SDC.READ)
    dados = {}
    for c in campos:
        try:
            sds = hdf.select(c)
            dados[c] = np.array(sds.get(), dtype=float)
            sds.endaccess()
        except Exception:  # campo ausente na versao: segue sem ele
            dados[c] = None

    ext = dados["Extinction_532"]
    if ext is None:
        raise SystemExit("arquivo sem Extinction_532: nao e um perfil de aerossol?")
    alt, origem = ler_altitudes(hdf, ext.shape[1])
    dados["Altitude_km"] = alt
    dados["altitude_origem"] = origem
    dados["DEM_Height_km"] = (
        np.asarray(dados["DEM_Height"], dtype=float).ravel()
        if dados["DEM_Height"] is not None
        else np.zeros(ext.shape[0])
    )
    hdf.end()
    return dados


# ---------------------------------------------------------------------------
# Calculo (testavel sem HDF)
# ---------------------------------------------------------------------------
def mascara_valida(ext: np.ndarray, qc: np.ndarray | None = None) -> np.ndarray:
    ok = np.isfinite(ext) & (ext > FILL / 2)
    if qc is not None:
        ok &= np.isfinite(qc) & (qc >= 0) & (qc <= 1)  # 0/1 = confiavel
    return ok


def aod_por_camada(alt_agl_km, ext, qc=None, alt_blh_agl_km=None) -> dict:
    """AOD total e AOD abaixo de uma altura (camada limite), por integracao.

    `alt_agl_km` e a altitude ACIMA DO SOLO (nao acima do mar), em qualquer
    ordem (o arquivo real vem de cima para baixo).
    """
    alt = np.asarray(alt_agl_km, float)
    ext = np.asarray(ext, float)
    ok = mascara_valida(ext, qc)
    dz = np.abs(np.gradient(alt))  # espessura de cada nivel (km)
    acima_solo = alt >= 0
    ext_ok = np.where(ok & acima_solo, ext, 0.0)
    aod_total = float(np.sum(ext_ok * dz))
    if alt_blh_agl_km is None:
        aod_abl, fracao = np.nan, np.nan
    else:
        dentro = alt <= alt_blh_agl_km
        aod_abl = float(np.sum(np.where(dentro, ext_ok, 0.0) * dz))
        fracao = aod_abl / aod_total if aod_total > 0 else np.nan
    return {"aod_total": aod_total, "aod_abl": aod_abl, "fracao_abl": fracao,
            "n_niveis_validos": int(np.sum(ok & acima_solo))}


def perfis_perto(lat, lon, lat0, lon0, raio_km=25.0):
    """Indices dos perfis cuja trajetoria passa a ate raio_km do ponto."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    dlat = (lat - lat0) * 111.32
    dlon = (lon - lon0) * 111.32 * np.cos(np.radians(lat0))
    return np.where(np.hypot(dlat, dlon) <= raio_km)[0]


def tabela_por_perfil(dados: dict, lat0: float, lon0: float, alt_blh_agl_km: float,
                      raio_km: float = 25.0) -> pd.DataFrame:
    """Uma linha por perfil proximo do ponto, com a fracao do AOD na CL."""
    idx = perfis_perto(dados["Latitude"], dados["Longitude"], lat0, lon0, raio_km)
    ext = dados["Extinction_532"]
    qc = dados.get("ExtinctionQC_532")
    alt_asl = dados["Altitude_km"]
    dem = dados["DEM_Height_km"]
    linhas = []
    for i in idx:
        alt_agl = alt_asl - dem[i]  # DEM em km, por perfil
        r = aod_por_camada(alt_agl, ext[i], None if qc is None else qc[i], alt_blh_agl_km)
        linhas.append({
            "perfil": int(i),
            "lat": float(dados["Latitude"][i]),
            "lon": float(dados["Longitude"][i]),
            "tempo_perfil_s": float(dados["Profile_Time"][i]),
            "dem_km": float(dem[i]),
            "aod_total": r["aod_total"],
            "aod_abl": r["aod_abl"],
            "fracao_abl": r["fracao_abl"],
            "aod_produto": float(np.nansum(dados["Aerosol_Optical_Depth_532"][i]))
            if dados.get("Aerosol_Optical_Depth_532") is not None else np.nan,
        })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Autoteste: perfil sintetico em ordem topo-base, terreno em Brasilia
# ---------------------------------------------------------------------------
def autoteste() -> bool:
    """Perfil topo-base com terreno a 1,17 km e conta a mao.

    Camada de aerossol de 0,15 km^-1 entre 1,17 e 3,17 km (acima do mar), ou
    seja 2,0 km de espessura a partir do solo. CL de 1,5 km acima do solo
    (2,67 km acima do mar).
      AOD total  = 0,15 x 2,0  = 0,300
      AOD na CL  = 0,15 x 1,5  = 0,225
      fracao     = 0,75
    """
    alt_asl = grade_padrao()[::-1]          # topo -> base, como no arquivo real
    assert alt_asl.size == 399 and alt_asl[0] > alt_asl[-1]
    dem = 1.17
    ext = np.where((alt_asl >= dem) & (alt_asl <= dem + 2.0), 0.15, 0.0)
    qc = np.where(ext > 0, 1.0, -1.0)
    r = aod_por_camada(alt_asl - dem, ext, qc, alt_blh_agl_km=1.5)
    assert abs(r["aod_total"] - 0.30) < 0.01, r
    assert abs(r["aod_abl"] - 0.225) < 0.01, r
    assert abs(r["fracao_abl"] - 0.75) < 0.02, r

    # sem tirar o DEM, a fracao sai 0,15 (so a fatia de 1,17 a 1,5 km "cabe"
    # na CL): e o erro que este teste protege
    r_sem_dem = aod_por_camada(alt_asl, ext, qc, alt_blh_agl_km=1.5)
    assert abs(r_sem_dem["fracao_abl"] - 0.15) < 0.02, r_sem_dem

    # fumaca acima da CL: fracao zero
    alt2 = grade_padrao()[::-1]
    ext2 = np.where((alt2 >= 4.0) & (alt2 <= 6.0), 0.15, 0.0)
    qc2 = np.where(ext2 > 0, 1.0, -1.0)
    r2 = aod_por_camada(alt2 - 1.17, ext2, qc2, alt_blh_agl_km=1.5)
    assert r2["fracao_abl"] == 0.0, r2
    assert abs(r2["aod_total"] - 0.30) < 0.02, r2

    # QC ruim nao entra
    r3 = aod_por_camada(alt_asl - dem, ext, np.full_like(ext, 2.0), 1.5)
    assert r3["aod_total"] == 0.0, r3

    # grade de reserva tem 399 niveis e espacamento documentado
    g = grade_padrao()
    assert g.size == 399
    assert abs(np.median(np.diff(g[:344])) - 0.06) < 1e-9
    assert abs(np.median(np.diff(g[345:])) - 0.18) < 1e-9

    print("autoteste ok: 399 niveis topo-base, DEM de Brasilia, fracao 0,75 contra conta")
    print("a mao (e 0,15 se o DEM for esquecido), fumaca acima da CL e QC")
    return True


def main():
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
        dados = ler_hdf4(caminho)
        print(f"perfis: {dados['Extinction_532'].shape[0]}, niveis: {dados['Extinction_532'].shape[1]}")
        print(f"altitudes: {dados['altitude_origem']}; "
              f"{dados['Altitude_km'][0]:.2f} km (topo) a {dados['Altitude_km'][-1]:.2f} km")
        # exemplo: Goiania com CL de 1,5 km acima do solo (troque pelo BLH do ERA5)
        t = tabela_por_perfil(dados, SITES["Goiania"]["lat"], SITES["Goiania"]["lon"], 1.5)
        if t.empty:
            print("nenhum perfil a ate 25 km de Goiania neste arquivo")
        else:
            print(t.head(10).to_string(index=False))
            print(f"fracao mediana do AOD na CL: {t.fracao_abl.median():.2f}")
            salvar_csv(t, "calipso_perfis_exemplo.csv")
    else:
        autoteste()
        print("\nSem arquivo: rode o autoteste (ok) e use a docstring para baixar o")
        print("arquivo com a conta Earthdata. Exemplo: python codigo/05_leitor_calipso.py dados/calipso/ARQUIVO.hdf")


if __name__ == "__main__":
    main()
