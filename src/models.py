"""Baseline e modelo de ML para prever focos mensais por bioma."""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error

FEATURES = ["lag_1", "lag_2", "lag_3", "lag_12", "media_movel_3", "mes_sin", "mes_cos"]


def time_split(df: pd.DataFrame, test_start: str):
    """Divisão temporal (nunca embaralhar séries temporais)."""
    cutoff = pd.Timestamp(test_start)
    return df[df["mes"] < cutoff], df[df["mes"] >= cutoff]


def seasonal_naive(test: pd.DataFrame) -> np.ndarray:
    """Baseline: prevê o mesmo valor de 12 meses atrás."""
    return test["lag_12"].to_numpy()


def train_lgbm(train: pd.DataFrame) -> LGBMRegressor:
    model = LGBMRegressor(n_estimators=400, learning_rate=0.05, random_state=42, verbose=-1)
    # bioma como categoria permite um único modelo comparar os três biomas
    X = pd.get_dummies(train[FEATURES + ["bioma"]], columns=["bioma"])
    model.fit(X, train["focos"])
    return model


def evaluate(test: pd.DataFrame, preds: np.ndarray) -> dict:
    mae = mean_absolute_error(test["focos"], preds)
    return {"MAE": mae}
