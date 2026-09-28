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


def climate_normals(clima: pd.DataFrame) -> pd.DataFrame:
    """Média histórica de temperatura e chuva por bioma e mês do ano (1-12).

    Usada como estimativa de clima para meses futuros, que ainda não aconteceram.
    """
    normais = clima.copy()
    normais["mes_numero"] = normais["mes"].dt.month
    return normais.groupby(["bioma", "mes_numero"])[["t2m", "precipitacao"]].mean()


def forecast_future(monthly: pd.DataFrame, model: LGBMRegressor, normais: pd.DataFrame, n_months: int = 12) -> pd.DataFrame:
    """Prevê os próximos `n_months` meses, bioma a bioma, de forma recursiva.

    Cada previsão vira o "lag" da previsão seguinte, e o clima futuro usa a
    normal climatológica (média histórica) daquele mês do ano.
    """
    resultados = []
    for bioma, hist in monthly.groupby("bioma"):
        hist = hist.sort_values("mes")
        serie = hist["focos"].tolist()
        ultimo_mes = hist["mes"].max()

        for i in range(1, n_months + 1):
            proximo_mes = ultimo_mes + pd.DateOffset(months=i)
            mes_numero = proximo_mes.month
            t2m, precipitacao = normais.loc[(bioma, mes_numero)]

            linha = pd.DataFrame([{
                "bioma": bioma,
                "lag_1": serie[-1],
                "lag_2": serie[-2],
                "lag_3": serie[-3],
                "lag_12": serie[-12],
                "media_movel_3": np.mean(serie[-3:]),
                "mes_sin": np.sin(2 * np.pi * mes_numero / 12),
                "mes_cos": np.cos(2 * np.pi * mes_numero / 12),
                "t2m": t2m,
                "precipitacao": precipitacao,
            }])
            X = build_X(linha, columns=model.feature_name_, features=FEATURES)
            previsto = max(model.predict(X)[0], 0)  # focos não podem ser negativos

            resultados.append({"bioma": bioma, "mes": proximo_mes, "focos_previsto": previsto})
            serie.append(previsto)

    return pd.DataFrame(resultados)