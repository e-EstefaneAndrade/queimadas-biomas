"""Dashboard simples: rode com `streamlit run app/streamlit_app.py`."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed" / "focos_mensais.csv"

st.set_page_config(page_title="Queimadas nos biomas brasileiros", layout="wide")
st.title("Focos de queimadas: Amazônia, Cerrado e Pantanal")

if not DATA.exists():
    st.info("Gere primeiro data/processed/focos_mensais.csv (notebook 01).")
    st.stop()

df = pd.read_csv(DATA, parse_dates=["mes"])
biomas = st.multiselect("Biomas", sorted(df["bioma"].unique()), default=sorted(df["bioma"].unique()))
view = df[df["bioma"].isin(biomas)]

st.plotly_chart(px.line(view, x="mes", y="focos", color="bioma"), use_container_width=True)
