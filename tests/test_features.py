import pandas as pd

from src.features import add_features, monthly_counts


def _fake():
    rng = pd.date_range("2020-01-01", "2022-12-31", freq="D")
    rows = []
    for b in ["Amazônia", "Cerrado"]:
        for d in rng:
            rows.append({"bioma": b, "datahora": d})
    return pd.DataFrame(rows)


def test_monthly_and_features():
    m = monthly_counts(_fake())
    assert {"bioma", "mes", "focos"} <= set(m.columns)
    f = add_features(m)
    assert "lag_12" in f.columns and not f.isna().any().any()
