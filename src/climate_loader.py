"""Coleta de clima (temperatura e chuva) na NASA POWER, por bioma.

A NASA POWER é uma API pública e gratuita, sem cadastro. Como ela responde
por coordenada (não por polígono de bioma), usamos um ponto representativo
de cada bioma (ver CLIMATE_POINTS em config.py). A temperatura já vem em
Celsius e a chuva em milímetros.
"""
from __future__ import annotations

import pandas as pd
import requests

from .config import CLIMATE_CACHE, CLIMATE_POINTS, CLIMATE_URL


def _parse_response(data: dict, bioma: str) -> pd.DataFrame:
    """Transforma o JSON da NASA POWER numa tabela [bioma, mes, t2m, precipitacao]."""
    parametros = data["properties"]["parameter"]
    temperatura = parametros["T2M"]
    chuva = parametros["PRECTOTCORR"]

    linhas = []
    for chave, valor_temp in temperatura.items():
        mes = chave[-2:]
        if mes == "13":  # "13" é a média/total anual, não um mês
            continue
        ano = chave[:4]
        linhas.append(
            {
                "bioma": bioma,
                "mes": pd.Timestamp(f"{ano}-{mes}-01"),
                "t2m": valor_temp,
                "precipitacao": chuva[chave],
            }
        )
    return pd.DataFrame(linhas)


def fetch_bioma_climate(bioma: str, lat: float, lon: float, first_year: int, last_year: int) -> pd.DataFrame:
    """Baixa o clima mensal de um único bioma (um ponto de coordenada)."""
    url = (
        f"{CLIMATE_URL}?parameters=T2M,PRECTOTCORR&community=AG"
        f"&longitude={lon}&latitude={lat}&start={first_year}&end={last_year}&format=JSON"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return _parse_response(resp.json(), bioma)


def load_climate(first_year: int, last_year: int, use_cache: bool = True) -> pd.DataFrame:
    """Baixa (ou lê do cache) o clima mensal de todos os biomas em CLIMATE_POINTS."""
    if use_cache and CLIMATE_CACHE.exists():
        return pd.read_csv(CLIMATE_CACHE, parse_dates=["mes"])

    partes = [
        fetch_bioma_climate(bioma, lat, lon, first_year, last_year)
        for bioma, (lat, lon) in CLIMATE_POINTS.items()
    ]
    clima = pd.concat(partes, ignore_index=True)
    CLIMATE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    clima.to_csv(CLIMATE_CACHE, index=False)
    return clima