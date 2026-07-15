import streamlit as st
import pandas as pd
from datetime import date
from utils.db import fetch_table, insert_row, delete_row, servidor_disponivel

st.set_page_config(page_title="CQH - SIGOP", page_icon="📅", layout="wide")
st.title("📅 Escala de CQH")

try:
    cqh = fetch_table("cqh", order_by="data")
    servidores = fetch_table("servidores", order_by="nome")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

tab_lista, tab_nova = st.tabs(["📋 Escala cadastrada", "➕ Escalar servidor"])

with tab_lista:
    if cqh.empty:
        st.info("Nenhuma escala de CQH cadastrada ainda.")
    else:
       exibir = cqh.merge(
            servidores[["id", "nome", "cargo"]].rename(columns={"id": "servidor_ref"}),
            left_on="servidor_id",
            right_on="servidor_ref",
            how="left",
        )
        )
        st.dataframe(
            exibir[["id", "data", "nome", "cargo", "equipe"]].sort_values("data"),
            use_container_width=True,
        )

        st.markdown("---")
        st.subheader("🗑️ Remover escala")
        remover_id = st.selectbox(
            "Selecione o registro a remover",
            options=exibir["id"].tolist(),
            format_func=lambda x: f"{exibir[exibir['id'] == x]['data'].values[0]} — "
            f"{exibir[exibir['id'] == x]['nome'].values[0]}",
        )
        if st.button("🗑️ Remover"):
            delete_row("cqh", remover_id)
            st.success("Escala removida.")
            st.rerun()

with tab_nova:
    if servidores.empty:
        st.warning("Cadastre servidores primeiro na página 'Efetivo'.")
    else:
        with st.form("nova_escala_cqh", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                data_escala = st.date_input("Data do plantão*", value=date.today())
                servidor_id = st.selectbox(
                    "Servidor*",
                    options=servidores["id"].tolist(),
                    format_func=lambda x: servidores[servidores["id"] == x]["nome"].values[0],
                )
            with col2:
                equipe = st.text_input("Equipe (opcional)")

            enviado = st.form_submit_button("➕ Escalar")

            if enviado:
                disponivel, motivo = servidor_disponivel(servidor_id, data_escala)
                if not disponivel:
                    st.error(f"⚠️ Não é possível escalar: {motivo}")
                else:
                    insert_row(
                        "cqh",
                        {
                            "data": str(data_escala),
                            "servidor_id": servidor_id,
                            "equipe": equipe,
                        },
                    )
                    st.success("Servidor escalado no CQH com sucesso!")
                    st.rerun()
