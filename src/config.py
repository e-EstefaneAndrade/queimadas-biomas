"""Configurações centrais do projeto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Biomas analisados (os nomes devem bater com a coluna "bioma" dos CSVs do INPE)
BIOMES = ["Amazônia", "Cerrado", "Pantanal"]

# Satélite de referência: usar apenas um evita contar o mesmo fogo várias vezes.
# TODO: confirme no site do INPE o nome exato do satélite de referência na base.
REFERENCE_SATELLITE = "AQUA_M-T"

# TODO: confirme no portal de dados abertos do Programa Queimadas (INPE) o
# endereço real dos CSVs e ajuste o padrão abaixo. Os caminhos podem mudar.
# Exemplo de placeholders: {year} e {month:02d}.
BASE_URL = "https://dataserver-coids.inpe.br/queimadas/queimadas/"
FILE_URL_TEMPLATE = BASE_URL + "COLOQUE_AQUI_O_CAMINHO/focos_mensal_{year}{month:02d}.csv"
