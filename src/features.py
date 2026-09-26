"""Construção das variáveis (features) mensais por bioma."""
from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega focos por bioma e mês: colunas [bioma, mes, focos]."""
    out = (
        df.assign(mes=df["datahora"].dt.to_period("M").dt.to_timestamp())
        .groupby(["bioma", "mes"])
        .size()
        .rename("focos")
        .reset_index()
    )
    return out


def seasonal_average(monthly: pd.DataFrame) -> pd.DataFrame:
    """Média de focos por mês do ano (1-12), para cada bioma."""
    out = monthly.copy()
    out["mes_numero"] = out["mes"].dt.month
    return out.groupby(["bioma", "mes_numero"])["focos"].mean().reset_index()


def merge_climate(monthly: pd.DataFrame, clima: pd.DataFrame) -> pd.DataFrame:
    """Junta a série de focos com o clima mensal (mesmo bioma e mês)."""
    return monthly.merge(clima, on=["bioma", "mes"], how="left")


def add_features(monthly: pd.DataFrame, lags=(1, 2, 3, 12)) -> pd.DataFrame:
    """Adiciona lags, média móvel e sazonalidade cíclica (por bioma)."""
    monthly = monthly.sort_values(["bioma", "mes"]).copy()
    g = monthly.groupby("bioma")["focos"]
    for lag in lags:
        monthly[f"lag_{lag}"] = g.shift(lag)
    monthly["media_movel_3"] = g.transform(lambda s: s.shift(1).rolling(3).mean())
    m = monthly["mes"].dt.month
    monthly["mes_sin"] = np.sin(2 * np.pi * m / 12)
    monthly["mes_cos"] = np.cos(2 * np.pi * m / 12)
    monthly["ano"] = monthly["mes"].dt.year
    return monthly.dropna().reset_index(drop=True)
