"""Dashboard: rode com `streamlit run app/streamlit_app.py`."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src import features

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
DATA = PROCESSED / "focos_mensais_atualizado.csv"
FORECAST = PROCESSED / "previsao.csv"

st.set_page_config(page_title="Queimadas nos biomas brasileiros", layout="wide")
st.title("Focos de queimadas: Amazônia, Cerrado e Pantanal")

if not DATA.exists():
    st.info("Gere primeiro data/processed/focos_mensais_atualizado.csv (notebook 05).")
    st.stop()


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["mes"])


df = load_csv(DATA)

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

st.subheader("Evolução mensal dos focos")
st.plotly_chart(px.line(view, x="mes", y="focos", color="bioma"), width="stretch")

if FORECAST.exists():
    st.subheader("Previsão para os próximos meses")
    st.info(
        "Cenário estimado por um modelo que usa o histórico de focos e a média climática de cada mês. "
        "Numa checagem retroativa, a previsão do Cerrado foi a mais confiável; a da Amazônia "
        "superestimou o valor real e deve ser lida como tendência, não como número exato."
    )

    previsao = load_csv(FORECAST)
    previsao = previsao[previsao["bioma"].isin(biomas)]

    # últimos 24 meses observados + previsão, no mesmo gráfico
    ultimo_mes = df["mes"].max()
    observado = df[df["bioma"].isin(biomas) & (df["mes"] > ultimo_mes - pd.DateOffset(months=24))]
    observado = observado.assign(tipo="Observado")

    # repete o último ponto observado na linha da previsão para as duas linhas se encontrarem
    ponto_de_ligacao = observado[observado["mes"] == ultimo_mes].assign(tipo="Previsto")
    previsto = previsao.rename(columns={"focos_previsto": "focos"}).assign(tipo="Previsto")
    grafico = pd.concat([observado, ponto_de_ligacao, previsto], ignore_index=True)

    fig = px.line(
        grafico, x="mes", y="focos", color="bioma", line_dash="tipo",
        line_dash_map={"Observado": "solid", "Previsto": "dash"},
    )
    st.plotly_chart(fig, width="stretch")

    tabela = previsao.pivot(index="mes", columns="bioma", values="focos_previsto").round(0).astype(int)
    tabela.index = tabela.index.strftime("%m/%Y")
    st.dataframe(tabela)

st.subheader("Sazonalidade média por mês do ano")
sazonalidade = features.seasonal_average(view)
st.plotly_chart(
    px.bar(sazonalidade, x="mes_numero", y="focos", color="bioma", barmode="group"),
    width="stretch",
)

st.subheader("Focos por ano e mês (todos os biomas selecionados)")
total_mes = view.groupby("mes")["focos"].sum().reset_index()
total_mes["ano"] = total_mes["mes"].dt.year
total_mes["mes_numero"] = total_mes["mes"].dt.month
pivot = total_mes.pivot(index="ano", columns="mes_numero", values="focos")
st.plotly_chart(px.imshow(pivot, color_continuous_scale="Oranges", aspect="auto"), width="stretch")