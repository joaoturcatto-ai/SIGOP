import streamlit as st
from utils.db import fetch_table, insert_row, update_row, delete_row
from utils.auth import check_login

check_login()

st.set_page_config(page_title="Viaturas - SIGOP", page_icon="🚓", layout="wide")
st.title("🚓 Viaturas")
st.caption("Cada viatura pode ter uma placa oficial e uma placa reservada (usada em operações disfarçadas).")

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
        viaturas_exibir = viaturas.copy()
        viaturas_exibir["placa_oficial_fmt"] = viaturas_exibir["placa_oficial"].apply(
            lambda p: f"🛡️ {p}" if p else "🛡️ —"
        )
        viaturas_exibir["placa_reservada_fmt"] = viaturas_exibir["placa_reservada"].apply(
            lambda p: f"🕵️ {p}" if p else "🕵️ —"
        )

        filtro_status = st.multiselect(
            "Filtrar por status",
            options=viaturas["status"].unique().tolist(),
            default=viaturas["status"].unique().tolist(),
        )
        filtrado = viaturas_exibir[viaturas_exibir["status"].isin(filtro_status)]

        st.dataframe(
            filtrado[
                ["id", "identificacao", "modelo", "placa_oficial_fmt", "placa_reservada_fmt", "status"]
            ].rename(
                columns={
                    "placa_oficial_fmt": "Placa Oficial",
                    "placa_reservada_fmt": "Placa Reservada",
                }
            ),
            use_container_width=True,
        )

        pendentes = filtrado[
            (filtrado["placa_oficial"].isna() | (filtrado["placa_oficial"] == ""))
            | (filtrado["placa_reservada"].isna() | (filtrado["placa_reservada"] == ""))
        ]
        if not pendentes.empty:
            st.warning(
                f"⚠️ {len(pendentes)} viatura(s) com placa (oficial e/ou reservada) pendente: "
                + ", ".join(pendentes["identificacao"].tolist())
                + ". Use 'Editar viatura' abaixo para preencher."
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
                col1, col2 = st.columns(2)
                with col1:
                    placa_oficial = st.text_input(
                        "🛡️ Placa Oficial", value=dados.get("placa_oficial", "") or ""
                    )
                with col2:
                    placa_reservada = st.text_input(
                        "🕵️ Placa Reservada", value=dados.get("placa_reservada", "") or ""
                    )
                status = st.selectbox(
                    "Status",
                    ["Disponível", "Oficina", "Em operação"],
                    index=["Disponível", "Oficina", "Em operação"].index(dados["status"]),
                )
                col_btn1, col_btn2 = st.columns(2)
                salvar = col_btn1.form_submit_button("💾 Salvar")
                remover = col_btn2.form_submit_button("🗑️ Remover")

                if salvar:
                    update_row(
                        "viaturas",
                        selecionada,
                        {
                            "identificacao": identificacao,
                            "modelo": modelo,
                            "placa_oficial": placa_oficial.upper(),
                            "placa_reservada": placa_reservada.upper(),
                            "status": status,
                        },
                    )
                    st.success("Viatura atualizada!")
                    st.rerun()
                if remover:
                    delete_row("viaturas", selecionada)
                    st.success("Viatura removida.")
                    st.rerun()

with tab_novo:
    with st.form("nova_viatura", clear_on_submit=True):
        identificacao = st.text_input("Identificação* (ex: EQUIPE A2 - Jony e Debora)")
        modelo = st.text_input("Modelo")
        col1, col2 = st.columns(2)
        with col1:
            placa_oficial = st.text_input("🛡️ Placa Oficial (ex: ABC-1234)")
        with col2:
            placa_reservada = st.text_input("🕵️ Placa Reservada (ex: XYZ-5678)")
        status = st.selectbox("Status", ["Disponível", "Oficina", "Em operação"])
        enviado = st.form_submit_button("➕ Cadastrar viatura")

        if enviado:
            if not identificacao:
                st.error("O campo Identificação é obrigatório.")
            else:
                insert_row(
                    "viaturas",
                    {
                        "identificacao": identificacao,
                        "modelo": modelo,
                        "placa_oficial": placa_oficial.upper(),
                        "placa_reservada": placa_reservada.upper(),
                        "status": status,
                    },
                )
                st.success(f"Viatura '{identificacao}' cadastrada!")
                st.rerun()
