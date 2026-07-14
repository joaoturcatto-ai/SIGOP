import streamlit as st
from datetime import date
from utils.db import fetch_table, insert_row, delete_row

st.set_page_config(page_title="Afastamentos - SIGOP", page_icon="🏖️", layout="wide")
st.title("🏖️ Afastamentos")
st.caption("Férias, folgas e licenças do efetivo")

try:
    afastamentos = fetch_table("afastamentos", order_by="data_inicio")
    servidores = fetch_table("servidores", order_by="nome")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

tab_lista, tab_novo = st.tabs(["📋 Afastamentos cadastrados", "➕ Novo afastamento"])

with tab_lista:
    if afastamentos.empty:
        st.info("Nenhum afastamento cadastrado ainda.")
    else:
        exibir = afastamentos.merge(
            servidores[["id", "nome"]], left_on="servidor_id", right_on="id", how="left"
        )
        filtro_tipo = st.multiselect(
            "Filtrar por tipo",
            options=exibir["tipo"].unique().tolist(),
            default=exibir["tipo"].unique().tolist(),
        )
        filtrado = exibir[exibir["tipo"].isin(filtro_tipo)]
        st.dataframe(
            filtrado[["id", "nome", "tipo", "data_inicio", "data_fim", "observacoes"]],
            use_container_width=True,
        )

        st.markdown("---")
        st.subheader("🗑️ Remover afastamento")
        remover_id = st.selectbox(
            "Selecione o registro a remover",
            options=filtrado["id"].tolist(),
            format_func=lambda x: f"{filtrado[filtrado['id'] == x]['nome'].values[0]} — "
            f"{filtrado[filtrado['id'] == x]['tipo'].values[0]}",
        )
        if st.button("🗑️ Remover"):
            delete_row("afastamentos", remover_id)
            st.success("Afastamento removido.")
            st.rerun()

with tab_novo:
    if servidores.empty:
        st.warning("Cadastre servidores primeiro na página 'Efetivo'.")
    else:
        with st.form("novo_afastamento", clear_on_submit=True):
            servidor_id = st.selectbox(
                "Servidor*",
                options=servidores["id"].tolist(),
                format_func=lambda x: servidores[servidores["id"] == x]["nome"].values[0],
            )
            tipo = st.selectbox("Tipo*", ["Férias", "Folga", "Licença"])
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data de início*", value=date.today())
            with col2:
                data_fim = st.date_input("Data de fim*", value=date.today())
            observacoes = st.text_area("Observações")

            enviado = st.form_submit_button("➕ Cadastrar afastamento")

            if enviado:
                if data_fim < data_inicio:
                    st.error("A data de fim não pode ser anterior à data de início.")
                else:
                    insert_row(
                        "afastamentos",
                        {
                            "servidor_id": servidor_id,
                            "tipo": tipo,
                            "data_inicio": str(data_inicio),
                            "data_fim": str(data_fim),
                            "observacoes": observacoes,
                        },
                    )
                    st.success("Afastamento cadastrado com sucesso!")
                    st.rerun()
