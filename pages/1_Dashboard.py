import streamlit as st
import pandas as pd
from datetime import date
from utils.db import fetch_table

st.set_page_config(page_title="Dashboard - SIGOP", page_icon="🏠", layout="wide")
st.title("🏠 Dashboard")

hoje = date.today()

try:
    servidores = fetch_table("servidores")
    operacoes = fetch_table("operacoes")
    viaturas = fetch_table("viaturas")
    afastamentos = fetch_table("afastamentos")
    cqh = fetch_table("cqh")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados do banco.")
    st.code(str(e), language="python")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("👮 Total de servidores", len(servidores) if not servidores.empty else 0)
col2.metric("🚓 Viaturas cadastradas", len(viaturas) if not viaturas.empty else 0)
col3.metric(
    "🚨 Operações planejadas",
    len(operacoes[operacoes["status"] == "Planejada"]) if not operacoes.empty else 0,
)
col4.metric(
    "🏖️ Afastamentos ativos",
    len(
        afastamentos[
            (pd.to_datetime(afastamentos["data_inicio"]).dt.date <= hoje)
            & (pd.to_datetime(afastamentos["data_fim"]).dt.date >= hoje)
        ]
    )
    if not afastamentos.empty
    else 0,
)

st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📅 Escala de CQH de hoje")
    if not cqh.empty and not servidores.empty:
        cqh_hoje = cqh[pd.to_datetime(cqh["data"]).dt.date == hoje]
        if not cqh_hoje.empty:
            cqh_hoje = cqh_hoje.merge(
                servidores[["id", "nome", "cargo"]],
                left_on="servidor_id",
                right_on="id",
                how="left",
            )
            st.dataframe(
                cqh_hoje[["nome", "cargo", "equipe"]], use_container_width=True
            )
        else:
            st.info("Nenhum servidor escalado no CQH para hoje.")
    else:
        st.info("Nenhum dado de CQH cadastrado ainda.")

with col_b:
    st.subheader("🚨 Próximas operações")
    if not operacoes.empty:
        proximas = operacoes[pd.to_datetime(operacoes["data_fim"]).dt.date >= hoje]
        proximas = proximas.sort_values("data_inicio").head(5)
        if not proximas.empty:
            st.dataframe(
                proximas[["nome", "data_inicio", "data_fim", "horario", "local", "status"]],
                use_container_width=True,
            )
        else:
            st.info("Nenhuma operação futura cadastrada.")
    else:
        st.info("Nenhuma operação cadastrada ainda.")

st.markdown("---")
st.subheader("🏖️ Servidores afastados hoje")
if not afastamentos.empty and not servidores.empty:
    afastados_hoje = afastamentos[
        (pd.to_datetime(afastamentos["data_inicio"]).dt.date <= hoje)
        & (pd.to_datetime(afastamentos["data_fim"]).dt.date >= hoje)
    ]
    if not afastados_hoje.empty:
        afastados_hoje = afastados_hoje.merge(
            servidores[["id", "nome"]], left_on="servidor_id", right_on="id", how="left"
        )
        st.dataframe(
            afastados_hoje[["nome", "tipo", "data_inicio", "data_fim"]],
            use_container_width=True,
        )
    else:
        st.info("Nenhum servidor afastado hoje.")
else:
    st.info("Nenhum afastamento cadastrado ainda.")
