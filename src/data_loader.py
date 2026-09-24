"""Coleta e leitura dos dados de focos de queimadas (INPE).

Colunas dos CSVs anuais (satélite de referência):
id_bdq, foco_id, lat, lon, data_pas, pais, estado, municipio, bioma
"""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

import pandas as pd
import requests

from .config import BIOMES, FIRST_YEAR, LAST_YEAR, RAW_DIR, YEAR_URL_TEMPLATE

log = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"data_pas", "estado", "municipio", "bioma", "lat", "lon"}


def download_year(year: int, dest: Path = RAW_DIR) -> Path | None:
    """Baixa o zip anual do INPE e extrai o CSV em data/raw/.

    Se o arquivo já existir, não baixa de novo.
    """
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"focos_br_ref_{year}.csv"
    if out.exists():
        return out
    url = YEAR_URL_TEMPLATE.format(year=year)
    try:
        resp = requests.get(url, timeout=300)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            zf.extractall(dest)
    except (requests.RequestException, zipfile.BadZipFile) as exc:
        log.warning("Falha ao baixar/extrair %s: %s", url, exc)
        return None
    return out if out.exists() else None


def download_all(first: int = FIRST_YEAR, last: int = LAST_YEAR) -> list[Path]:
    """Baixa todos os anos do intervalo."""
    paths = [download_year(y) for y in range(first, last + 1)]
    return [p for p in paths if p]


def _read_one(path: Path) -> pd.DataFrame:
    """Lê um CSV anual, tentando UTF-8 e depois latin-1."""
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, skipinitialspace=True, dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não consegui ler {path} com utf-8 nem latin-1")


def load_raw(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Lê todos os CSVs de data/raw e devolve um DataFrame padronizado.

    Padronizações: remove espaços em volta dos valores, converte lat/lon para
    número e cria a coluna `datahora` (a partir de `data_pas`, a data/hora da
    passagem do satélite).
    """
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {raw_dir}")

    df = pd.concat((_read_one(f) for f in files), ignore_index=True)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")

    for col in df.columns:
        df[col] = df[col].str.strip()

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["datahora"] = pd.to_datetime(df["data_pas"], errors="coerce")
    return df.dropna(subset=["datahora"])


def filter_reference(df: pd.DataFrame, biomes: list[str] = BIOMES) -> pd.DataFrame:
    """Mantém só os biomas de interesse.

    (O nome da função foi mantido; o arquivo já contém só o satélite de referência.)
    """
    return df[df["bioma"].isin(biomes)].copy()