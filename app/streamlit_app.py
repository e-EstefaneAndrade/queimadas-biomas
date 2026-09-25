"""Dashboard: rode com `streamlit run app/streamlit_app.py`."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src import features

DATA = Path(__file__).resolve().parents[1] / "data" / "processed" / "focos_mensais.csv"

st.set_page_config(page_title="Queimadas nos biomas brasileiros", layout="wide")
st.title("Focos de queimadas: Amazônia, Cerrado e Pantanal")

if not DATA.exists():
    st.info("Gere primeiro data/processed/focos_mensais.csv (notebook 01).")
    st.stop()


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA, parse_dates=["mes"])


df = load_data()

biomas = st.sidebar.multiselect(
    "Biomas", sorted(df["bioma"].unique()), default=sorted(df["bioma"].unique())
)
anos = sorted(df["mes"].dt.year.unique())
ano_min, ano_max = st.sidebar.select_slider(
    "Período", options=anos, value=(anos[0], anos[-1])
)

view = df[df["bioma"].isin(biomas) & df["mes"].dt.year.between(ano_min, ano_max)]

if view.empty:
    st.warning("Nenhum dado para os filtros escolhidos.")
    st.stop()

# indicadores rápidos
total_focos = int(view["focos"].sum())
pico = view.loc[view["focos"].idxmax()]

col1, col2, col3 = st.columns(3)
col1.metric("Total de focos no período", f"{total_focos:,}".replace(",", "."))
col2.metric("Mês com mais focos", pico["mes"].strftime("%m/%Y"))
col3.metric("Focos nesse mês", f"{int(pico['focos']):,}".replace(",", "."))

st.subheader("Focos por mês")
st.plotly_chart(px.line(view, x="mes", y="focos", color="bioma"), use_container_width=True)

st.subheader("Sazonalidade média (dia do ano todo)")
sazonalidade = features.seasonal_average(view)
st.plotly_chart(
    px.bar(sazonalidade, x="mes_numero", y="focos", color="bioma", barmode="group"),
    use_container_width=True,
)

st.subheader("Focos por ano e mês (todos os biomas selecionados)")
total_mes = view.groupby("mes")["focos"].sum().reset_index()
total_mes["ano"] = total_mes["mes"].dt.year
total_mes["mes_numero"] = total_mes["mes"].dt.month
pivot = total_mes.pivot(index="ano", columns="mes_numero", values="focos")
st.plotly_chart(px.imshow(pivot, color_continuous_scale="Oranges", aspect="auto"), use_container_width=True)