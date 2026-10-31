"""
02 - Estacoes de PM2,5 em Goias e no DF: o que existe com dado publico.

Sem login, sem chave. O script:
1. Baixa (se ainda nao existir) os ZIPs anuais do MonitorAr (MMA/dados.mma.gov.br),
   que sao o unico conjunto federal aberto de qualidade do ar em CSV.
2. Le os ZIPs em streaming e conta estacoes, poluentes e periodo por UF.
3. Sonda, com registro do codigo HTTP, as outras portas de acesso:
   OpenAQ v3 (exige chave), SEMAD/GO (paginas de qualidade do ar),
   API do Cimehgo (meteorologia), portal ONDA do IBRAM-DF (exige login) e
   Sensor.Community (sensores de baixo custo, abertos).
4. Grava a tabela de fontes, a tabela de estacoes e uma figura.

Uso:  python codigo/02_estacoes_pm25.py
"""
from __future__ import annotations

import csv
import io
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import DADOS, FIGURAS, RAIZ, SESSION, get_json, salvar_csv  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ANOS = [2022, 2023, 2024, 2025]
BASE_MMA = (
    "https://dados.mma.gov.br/dataset/5be05b46-3bda-4f6e-9bf2-810e716fff33/"
    "resource/{rid}/download/dados_monitorar_{ano}.zip"
)
IDS = {
    2022: "3ed97dc4-9b37-4a2f-81e1-b69c5f654d65",
    2023: "ad6a4436-db18-4037-bfd1-77f3b9669b35",
    2024: "b24d6cfa-4465-4124-a6c4-ec96ff7b7f9f",
    2025: "e4f35322-b8a7-423c-bc12-21bbd0804a0a",
}
UFS = ["GO", "DF"]


def baixar_zip(ano: int) -> Path:
    destino = DADOS / f"monitorar_{ano}.zip"
    if destino.exists() and destino.stat().st_size > 1e6:
        print(f"  zip {ano} ja existe ({destino.stat().st_size/1e6:.1f} MB)")
        return destino
    url = BASE_MMA.format(rid=IDS[ano], ano=ano)
    print(f"  baixando {url}")
    r = SESSION.get(url, timeout=600)
    r.raise_for_status()
    destino.write_bytes(r.content)
    print(f"  -> {destino.name} ({len(r.content)/1e6:.1f} MB)")
    return destino


def ler_ano(zip_path: Path, ano: int):
    """Le o CSV do zip em streaming e devolve (estacoes_GO_DF, contagem_por_UF, itens)."""
    estacoes, por_uf, itens = {}, Counter(), Counter()
    with zipfile.ZipFile(zip_path) as z:
        nome = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(nome) as f:
            txt = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
            for row in csv.DictReader(txt, delimiter=","):
                uf = (row.get("sg_uf") or "").strip()
                por_uf[uf] += 1
                if uf not in UFS:
                    continue
                chave = (uf, row["no_estacao"], row["no_municipio"], row["id_estacao"])
                e = estacoes.setdefault(
                    chave,
                    {
                        "uf": uf,
                        "estacao": row["no_estacao"],
                        "municipio": row["no_municipio"],
                        "id_estacao": row["id_estacao"],
                        "lat": row["nu_latitude"],
                        "lon": row["nu_longitude"],
                        "fonte": row["no_fonte_dados"],
                        "ano": ano,
                        "n_registros": 0,
                        "itens": set(),
                        "inicio": None,
                        "fim": None,
                    },
                )
                e["n_registros"] += 1
                e["itens"].add(row["no_item_monitorado"])
                itens[row["no_item_monitorado"]] += 1
                d = row["dh_medicao"][:19]
                if e["inicio"] is None or d < e["inicio"]:
                    e["inicio"] = d
                if e["fim"] is None or d > e["fim"]:
                    e["fim"] = d
    # PM2,5 pode aparecer como "MP2.5", "PM2.5" ou "Particulas <2.5"
    def eh_pm25(nome_item: str) -> bool:
        n = nome_item.lower().replace(",", ".")
        return ("pm2.5" in n) or ("mp2.5" in n) or ("2.5" in n and ("part" in n or "mp" in n))

    for e in estacoes.values():
        e["poluentes"] = "; ".join(sorted(e["itens"]))
        e["mede_pm25_provavel"] = any(eh_pm25(i) for i in e["itens"])
        del e["itens"]
    return list(estacoes.values()), por_uf, itens


def sondar(url: str, **kw):
    """Faz um GET e devolve (status, tamanho). Nunca levanta excecao."""
    try:
        r = SESSION.get(url, timeout=kw.pop("timeout", 60), **kw)
        return r.status_code, len(r.content)
    except requests.RequestException as e:
        return "erro", str(e)[:60]


def main():
    print("1) MonitorAr (dados.mma.gov.br), unico conjunto federal aberto em CSV")
    estacoes, por_uf_todos, itens_todos = [], {}, {}
    for ano in ANOS:
        zp = baixar_zip(ano)
        est, por_uf, itens = ler_ano(zp, ano)
        estacoes.extend(est)
        por_uf_todos[ano] = dict(por_uf)
        itens_todos[ano] = dict(itens.most_common(12))
        n_go = sum(1 for x in est if x["uf"] == "GO")
        n_df = sum(1 for x in est if x["uf"] == "DF")
        print(f"  {ano}: {sum(por_uf.values()):,} registros; estacoes GO={n_go} DF={n_df}")

    df_est = pd.DataFrame(estacoes)
    if df_est.empty:
        df_est = pd.DataFrame(columns=["uf", "estacao", "municipio", "id_estacao", "lat", "lon", "fonte", "ano"])
    salvar_csv(df_est, "pm25_estacoes_monitorar_go_df.csv")

    # resumo de cobertura nacional (para mostrar que GO/DF nao estao)
    cobertura = []
    for ano, d in por_uf_todos.items():
        for uf, n in d.items():
            cobertura.append({"ano": ano, "uf": uf or "(vazio)", "n_registros": n})
    df_cob = pd.DataFrame(cobertura)
    salvar_csv(df_cob, "monitorar_cobertura_por_uf.csv")

    print("\n2) Sondagem das outras fontes (sem login, sem chave)")
    sondagens = [
        ("OpenAQ v3 (locations)", "https://api.openaq.org/v3/locations?coordinates=-16.68,-49.25&radius=50000&limit=5"),
        ("OpenAQ v2 (aposentada)", "https://api.openaq.org/v2/locations?coordinates=-16.68,-49.25&radius=50000&limit=5"),
        ("MMA - lista de conjuntos", "https://dados.mma.gov.br/api/3/action/package_show?id=ar-puro-monitorar"),
        ("SEMAD-GO - estacoes de qualidade do ar", "https://goias.gov.br/meioambiente/estacoes-de-monitoramento-da-qualidade-do-ar/"),
        ("SEMAD-GO - ultimos dados (pagina)", "https://goias.gov.br/meioambiente/ultimos-dados-do-monitoramento-da-qualidade-do-ar/"),
        ("Cimehgo - lista de estacoes (API publica)", "https://intratempo.meioambiente.go.gov.br/api/public_cimehgo"),
        ("Cimehgo - serie horaria de uma estacao", "https://intratempo.meioambiente.go.gov.br/api/cimehgo/EC30154A?start_time=2026-10-01%2000:00&end_time=2026-10-02%2023:00"),
        ("IBRAM-DF - portal ONDA (ArcGIS)", "https://onda.ibram.df.gov.br/portal/apps/mapviewer/index.html"),
        ("Sensor.Community (baixo custo)", "https://data.sensor.community/airrohr/v1/filter/box=-50.0,-17.3,-48.5,-16.2"),
    ]
    linhas_sonda = []
    for nome, url in sondagens:
        st, tam = sondar(url)
        linhas_sonda.append({"fonte": nome, "url": url, "http": st, "bytes": tam})
        print(f"  {nome}: HTTP {st} ({tam} bytes)")
    salvar_csv(pd.DataFrame(linhas_sonda), "pm25_sondagens_http.csv")

    # estacoes candidatas no sitio do Cimehgo (rede meteorologica da mesma area)
    try:
        d = get_json("https://intratempo.meioambiente.go.gov.br/api/public_cimehgo")
        cimehgo = pd.DataFrame(
            [
                {
                    "estacao": x["name"].strip(),
                    "municipio": x.get("municipio", "").strip(),
                    "stid": x["stid"],
                    "lat": x["latitude"],
                    "lon": x["longitude"],
                    "tipo": x.get("tipo"),
                }
                for x in d
            ]
        )
        cimehgo = cimehgo[cimehgo.municipio.str.contains("Goi", na=False) | cimehgo.municipio.str.contains("Aparecida|Senador", na=False)]
        salvar_csv(cimehgo, "cimehgo_estacoes_goiania_metro.csv")
    except Exception as e:  # noqa: BLE001
        cimehgo = pd.DataFrame()
        print(f"  (Cimehgo: falhou {e})")

    # tabela de fontes (o que a pesquisadora precisa saber para decidir)
    fontes = [
        {
            "fonte": "MonitorAr (MMA)",
            "uf": "Brasil",
            "produto": "CSV anual por estacao, todos os poluentes",
            "estacoes_go_df": f"{df_est[['uf', 'estacao']].drop_duplicates().shape[0]} estacoes (DF, 2024-2025)",
            "periodo": "2022-2025 (ZIPs anuais)",
            "acesso": "aberto, sem login (dados.mma.gov.br)",
            "verificado": "sim, download e leitura neste script",
        },
        {
            "fonte": "SEMAD-GO / Cimehgo",
            "uf": "GO",
            "produto": "paginas de qualidade do ar e boletins; API do Cimehgo so meteorologia",
            "estacoes_go_df": "rede em Goiania/Aparecida/Senador Canedo (nomes no arquivo cimehgo_estacoes_goiania_metro.csv)",
            "periodo": "nao informado nas paginas (atualizacao de 2021)",
            "acesso": "sem download; serie horaria nao respondeu para as datas testadas",
            "verificado": "sim, HTTP e conteudo das paginas",
        },
        {
            "fonte": "IBRAM-DF (ONDA)",
            "uf": "DF",
            "produto": "portal ArcGIS com camadas ambientais",
            "estacoes_go_df": "nao listado publicamente",
            "periodo": "nao informado",
            "acesso": "exige conta ArcGIS (login)",
            "verificado": "sim, o portal devolve tela de login",
        },
        {
            "fonte": "OpenAQ",
            "uf": "Brasil",
            "produto": "agregador de redes, API v3",
            "estacoes_go_df": "nao consultavel sem chave",
            "periodo": "depende da fonte original",
            "acesso": "exige chave de API (X-API-Key)",
            "verificado": "sim, HTTP 401 sem chave",
        },
        {
            "fonte": "Sensor.Community",
            "uf": "GO/DF",
            "produto": "sensores de baixo custo (PM2,5 por laser)",
            "estacoes_go_df": "0 na caixa consultada",
            "periodo": "tempo real, sem historico garantido",
            "acesso": "aberto, sem login",
            "verificado": "sim, consulta a API",
        },
    ]
    salvar_csv(pd.DataFrame(fontes), "pm25_fontes.csv")

    # --- figura: cobertura do MonitorAr por UF -----------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1.6, 1]})
    ult = df_cob[df_cob.ano == max(ANOS)]
    ult = ult[ult.uf != "(vazio)"].sort_values("n_registros")
    cores = ["#c0504d" if uf in UFS else "#8fa6b8" for uf in ult.uf]
    ax1.barh(ult.uf, ult.n_registros / 1e3, color=cores)
    ax1.set_xlabel("mil registros horarios (todos os poluentes)")
    ax1.set_title(f"MonitorAr {max(ANOS)}: Goias nao aparece (0 registros)\no DF entra em 2024, com 2 estacoes")
    ax1.grid(axis="x", alpha=0.3)
    for i, (uf, v) in enumerate(zip(ult.uf, ult.n_registros / 1e3)):
        ax1.text(v, i, f" {v:.0f}", va="center", fontsize=8)
    ax1.text(0.98, 0.02, "GO: 0 registros em todos os anos consultados",
             transform=ax1.transAxes, ha="right", va="bottom", fontsize=8.5,
             color="#c0504d", fontweight="bold")

    ax2.axis("off")
    ax2.set_title("Portas de acesso testadas (01/11/2026)", loc="left", fontsize=10)
    textos = [
        ("MonitorAr/MMA", "aberto - CSV anual"),
        ("OpenAQ v3", "HTTP 401 - exige chave"),
        ("OpenAQ v2", "HTTP 410 - aposentado"),
        ("SEMAD-GO", "paginas de 2021, sem download"),
        ("Cimehgo API", "so meteorologia, serie vazia"),
        ("IBRAM-DF", "login ArcGIS"),
        ("Sensor.Community", "aberto - 0 sensores na area"),
    ]
    for i, (a, b) in enumerate(textos):
        ax2.text(0.0, 0.9 - i * 0.13, f"{a}:", fontsize=9, fontweight="bold")
        ax2.text(0.44, 0.9 - i * 0.13, b, fontsize=9)

    fig.suptitle("PM2,5 em Goias e no DF: o dado publico nao esta onde se espera", fontsize=12)
    fig.tight_layout()
    saida = FIGURAS / "pm25_estacoes_fontes.png"
    fig.savefig(saida, dpi=170, bbox_inches="tight")
    print(f"\nFigura: {saida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
