"""Configurações centrais do projeto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Biomas analisados (devem bater com a coluna "bioma" dos CSVs do INPE)
BIOMES = ["Amazônia", "Cerrado", "Pantanal"]

# Arquivos anuais do INPE: focos do Brasil detectados pelo satélite de referência.
# Como o arquivo já vem só com o satélite de referência, não há filtro de satélite.
YEAR_URL_TEMPLATE = (
    "https://dataserver-coids.inpe.br/queimadas/queimadas/"
    "focos/csv/anual/Brasil_sat_ref/focos_br_ref_{year}.zip"
)

# Anos usados no projeto (2026 ainda não tem arquivo anual completo)
FIRST_YEAR = 2015
LAST_YEAR = 2025