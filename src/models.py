"""Baseline e modelo de ML para prever focos mensais por bioma."""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error

FEATURES_HISTORICO = ["lag_1", "lag_2", "lag_3", "lag_12", "media_movel_3", "mes_sin", "mes_cos"]
FEATURES_CLIMA = ["t2m", "precipitacao"]
FEATURES = FEATURES_HISTORICO + FEATURES_CLIMA


def time_split(df: pd.DataFrame, test_start: str):
    """Divisão temporal (nunca embaralhar séries temporais)."""
    cutoff = pd.Timestamp(test_start)
    return df[df["mes"] < cutoff], df[df["mes"] >= cutoff]


def seasonal_naive(test: pd.DataFrame) -> np.ndarray:
    """Baseline: prevê o mesmo valor de 12 meses atrás."""
    return test["lag_12"].to_numpy()


def build_X(df: pd.DataFrame, columns=None, features: list[str] = FEATURES) -> pd.DataFrame:
    """Monta a matriz de entrada (features + bioma em dummies)."""
    X = pd.get_dummies(df[features + ["bioma"]], columns=["bioma"])
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0)
    return X


def train_lgbm(train: pd.DataFrame, features: list[str] = FEATURES) -> LGBMRegressor:
    model = LGBMRegressor(n_estimators=400, learning_rate=0.05, random_state=42, verbose=-1)
    X = build_X(train, features=features)
    model.fit(X, train["focos"])
    return model


def predict(model: LGBMRegressor, df: pd.DataFrame, features: list[str] = FEATURES) -> np.ndarray:
    X = build_X(df, columns=model.feature_name_, features=features)
    return model.predict(X)


def evaluate(test: pd.DataFrame, preds: np.ndarray) -> dict:
    mae = mean_absolute_error(test["focos"], preds)
    return {"MAE": mae}
