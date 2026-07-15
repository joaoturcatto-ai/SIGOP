import streamlit as st
from utils.db import fetch_table, insert_row, update_row, delete_row

st.set_page_config(page_title="Viaturas - SIGOP", page_icon="🚓", layout="wide")
st.title("🚓 Viaturas")

try:
    viaturas = fetch_table("viaturas", order_by="identificacao")
except Exception as e:
    st.error("⚠️ Erro ao carregar viaturas.")
    st.code(str(e), language="python")
    st.stop()

tab_lista, tab_novo = st.tabs(["📋 Lista de viaturas", "➕ Cadastrar nova"])

with tab_lista:
    if viaturas.empty:
        st.info("Nenhuma viatura cadastrada ainda.")
    else:
        filtro_status = st.multiselect(
            "Filtrar por status",
            options=viaturas["status"].unique().tolist(),
            default=viaturas["status"].unique().tolist(),
        )
        filtrado = viaturas[viaturas["status"].isin(filtro_status)]
        st.dataframe(
            filtrado[["id", "identificacao", "modelo", "status"]],
            use_container_width=True,
        )

        st.markdown("---")
        st.subheader("✏️ Editar ou remover viatura")
        selecionada = st.selectbox(
            "Selecione uma viatura",
            options=filtrado["id"].tolist(),
            format_func=lambda x: filtrado[filtrado["id"] == x]["identificacao"].values[0],
        )

        if selecionada:
            dados = viaturas[viaturas["id"] == selecionada].iloc[0]
            with st.form("editar_viatura"):
                identificacao = st.text_input("Identificação", value=dados["identificacao"])
                modelo = st.text_input("Modelo", value=dados.get("modelo", "") or "")
                status = st.selectbox(
                    "Status",
                    ["Disponível", "Oficina", "Em operação"],
                    index=["Disponível", "Oficina", "Em operação"].index(dados["status"]),
                )
                col1, col2 = st.columns(2)
                salvar = col1.form_submit_button("💾 Salvar")
                remover = col2.form_submit_button("🗑️ Remover")

                if salvar:
                    update_row(
                        "viaturas",
                        selecionada,
                        {"identificacao": identificacao, "modelo": modelo, "status": status},
                    )
                    st.success("Viatura atualizada!")
                    st.rerun()
                if remover:
                    delete_row("viaturas", selecionada)
                    st.success("Viatura removida.")
                    st.rerun()

with tab_novo:
    with st.form("nova_viatura", clear_on_submit=True):
        identificacao = st.text_input("Identificação* (ex: L200 1012)")
        modelo = st.text_input("Modelo")
        status = st.selectbox("Status", ["Disponível", "Oficina", "Em operação"])
        enviado = st.form_submit_button("➕ Cadastrar viatura")

        if enviado:
            if not identificacao:
                st.error("O campo Identificação é obrigatório.")
            else:
                insert_row(
                    "viaturas",
                    {"identificacao": identificacao, "modelo": modelo, "status": status},
                )
                st.success(f"Viatura '{identificacao}' cadastrada!")
                st.rerun()
