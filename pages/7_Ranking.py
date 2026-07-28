import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import fetch_table
from utils.auth import check_login

check_login()

st.set_page_config(page_title="Ranking - SIGOP", page_icon="📊", layout="wide")
st.title("📊 Ranking Inteligente")
st.caption("Estatísticas de emprego do efetivo em operações")

try:
    servidores = fetch_table("servidores")
    operacoes = fetch_table("operacoes")
    participantes = fetch_table("equipes_operacoes")
    cqh = fetch_table("cqh")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

if servidores.empty or participantes.empty:
    st.info(
        "Ainda não há dados suficientes para gerar o ranking. "
        "Cadastre servidores e vincule-os a operações primeiro."
    )
    st.stop()

# Contagem de participações em operações
contagem_op = (
    participantes.groupby("servidor_id")
    .size()
    .reset_index(name="operacoes")
)
ranking = servidores.merge(contagem_op, left_on="id", right_on="servidor_id", how="left")
ranking["operacoes"] = ranking["operacoes"].fillna(0).astype(int)

# Contagem de CQH
if not cqh.empty:
    contagem_cqh = cqh.groupby("servidor_id").size().reset_index(name="dias_cqh")
    ranking = ranking.merge(contagem_cqh, left_on="id", right_on="servidor_id", how="left", suffixes=("", "_cqh"))
    ranking["dias_cqh"] = ranking["dias_cqh"].fillna(0).astype(int)
else:
    ranking["dias_cqh"] = 0

ranking = ranking.sort_values("operacoes", ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Quem mais participou de operações")
    top = ranking[["nome", "cargo", "operacoes", "dias_cqh"]].reset_index(drop=True)
    st.dataframe(top, use_container_width=True)

with col2:
    st.subheader("📈 Gráfico de participações")
    fig = px.bar(
        ranking.sort_values("operacoes", ascending=True),
        x="operacoes",
        y="nome",
        orientation="h",
        labels={"operacoes": "Nº de operações", "nome": "Servidor"},
        color="operacoes",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("⚖️ Distribuição equilibrada")
menor = ranking.tail(5)[["nome", "operacoes"]]
maior = ranking.head(5)[["nome", "operacoes"]]

col_a, col_b = st.columns(2)
with col_a:
    st.write("**Menos empregados em operações:**")
    st.dataframe(menor, use_container_width=True)
with col_b:
    st.write("**Mais empregados em operações:**")
    st.dataframe(maior, use_container_width=True)
