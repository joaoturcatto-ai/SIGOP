import streamlit as st
from utils.db import fetch_table, insert_row, update_row, delete_row

st.set_page_config(page_title="Viaturas - SIGOP", page_icon="🚓", layout="wide")
st.title("🚓 Viaturas")

ICONE_PLACA = {"Oficial": "🛡️", "Reservada": "🕵️"}

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
        viaturas_exibir["tipo"] = viaturas_exibir["tipo_placa"].map(
            lambda t: f"{ICONE_PLACA.get(t, '')} {t}"
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_status = st.multiselect(
                "Filtrar por status",
                options=viaturas["status"].unique().tolist(),
                default=viaturas["status"].unique().tolist(),
            )
        with col_f2:
            filtro_placa = st.multiselect(
                "Filtrar por tipo de placa",
                options=viaturas["tipo_placa"].unique().tolist(),
                default=viaturas["tipo_placa"].unique().tolist(),
            )

        filtrado = viaturas_exibir[
            viaturas_exibir["status"].isin(filtro_status)
            & viaturas_exibir["tipo_placa"].isin(filtro_placa)
        ]
        st.dataframe(
            filtrado[["id", "identificacao", "placa", "modelo", "tipo", "status"]],
            use_container_width=True,
        )
        st.caption("🛡️ Oficial = viatura caracterizada · 🕵️ Reservada = viatura descaracterizada")

        pendentes = filtrado[filtrado["placa"].isna() | (filtrado["placa"] == "")]
        if not pendentes.empty:
            st.warning(
                f"⚠️ {len(pendentes)} viatura(s) ainda sem placa cadastrada: "
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
                col1, col2 = st.columns(2)
                with col1:
                    identificacao = st.text_input("Identificação", value=dados["identificacao"])
                with col2:
                    placa = st.text_input("Placa*", value=dados.get("placa", "") or "")
                modelo = st.text_input("Modelo", value=dados.get("modelo", "") or "")
                col3, col4 = st.columns(2)
                with col3:
                    status = st.selectbox(
                        "Status",
                        ["Disponível", "Oficina", "Em operação"],
                        index=["Disponível", "Oficina", "Em operação"].index(dados["status"]),
                    )
                with col4:
                    tipo_placa = st.selectbox(
                        "Tipo de placa",
                        ["Oficial", "Reservada"],
                        index=["Oficial", "Reservada"].index(dados.get("tipo_placa", "Oficial")),
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
                            "placa": placa.upper(),
                            "modelo": modelo,
                            "status": status,
                            "tipo_placa": tipo_placa,
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
        col1, col2 = st.columns(2)
        with col1:
            identificacao = st.text_input("Identificação* (ex: L200 1012)")
        with col2:
            placa = st.text_input("Placa* (ex: ABC-1234)")
        modelo = st.text_input("Modelo")
        col3, col4 = st.columns(2)
        with col3:
            status = st.selectbox("Status", ["Disponível", "Oficina", "Em operação"])
        with col4:
            tipo_placa = st.selectbox(
                "Tipo de placa",
                ["Oficial", "Reservada"],
                help="Oficial = viatura caracterizada · Reservada = viatura descaracterizada",
            )
        enviado = st.form_submit_button("➕ Cadastrar viatura")

        if enviado:
            if not identificacao:
                st.error("O campo Identificação é obrigatório.")
            elif not placa:
                st.error("O campo Placa é obrigatório.")
            else:
                insert_row(
                    "viaturas",
                    {
                        "identificacao": identificacao,
                        "placa": placa.upper(),
                        "modelo": modelo,
                        "status": status,
                        "tipo_placa": tipo_placa,
                    },
                )
                st.success(f"Viatura '{identificacao}' (placa {placa.upper()}) cadastrada!")
                st.rerun()
