"""Coleta e leitura dos dados de focos de queimadas (INPE)."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import requests

from .config import BIOMES, FILE_URL_TEMPLATE, RAW_DIR, REFERENCE_SATELLITE

log = logging.getLogger(__name__)

# Colunas mínimas que o restante do pipeline espera (nomes em minúsculas).
REQUIRED_COLUMNS = {"datahora", "satelite", "municipio", "estado", "bioma"}


def download_month(year: int, month: int, dest: Path = RAW_DIR) -> Path | None:
    """Baixa o CSV de um mês. Retorna o caminho ou None se falhar."""
    dest.mkdir(parents=True, exist_ok=True)
    url = FILE_URL_TEMPLATE.format(year=year, month=month)
    out = dest / f"focos_{year}{month:02d}.csv"
    if out.exists():
        return out
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Falha ao baixar %s: %s", url, exc)
        return None
    out.write_bytes(resp.content)
    return out


def download_range(start_year: int, end_year: int) -> list[Path]:
    """Baixa todos os meses entre dois anos (inclusive)."""
    paths = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            p = download_month(year, month)
            if p:
                paths.append(p)
    return paths


def load_raw(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Lê todos os CSVs de data/raw e devolve um único DataFrame padronizado."""
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {raw_dir}")
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Colunas ausentes: {sorted(missing)}. "
            f"Ajuste REQUIRED_COLUMNS conforme o layout dos seus CSVs."
        )
    df["datahora"] = pd.to_datetime(df["datahora"], errors="coerce")
    return df.dropna(subset=["datahora"])


def filter_reference(df: pd.DataFrame, biomes: list[str] = BIOMES) -> pd.DataFrame:
    """Mantém só os biomas de interesse e o satélite de referência."""
    out = df[df["bioma"].isin(biomes)]
    return out[out["satelite"] == REFERENCE_SATELLITE].copy()
