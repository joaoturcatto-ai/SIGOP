import streamlit as st
from datetime import date, timedelta
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
            servidores[["id", "nome"]].rename(columns={"id": "servidor_ref"}),
            left_on="servidor_id",
            right_on="servidor_ref",
            how="left",
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
        modo_periodo = st.radio(
            "Como você quer definir o período?",
            ["Por quantidade de dias", "Por datas de início e fim"],
            horizontal=True,
        )

        with st.form("novo_afastamento", clear_on_submit=True):
            servidor_id = st.selectbox(
                "Servidor*",
                options=servidores["id"].tolist(),
                format_func=lambda x: servidores[servidores["id"] == x]["nome"].values[0],
            )
            tipo = st.selectbox("Tipo*", ["Férias", "Folga", "Licença", "Folga Operacional"])

            if modo_periodo == "Por quantidade de dias":
                col1, col2 = st.columns(2)
                with col1:
                    data_inicio = st.date_input(
                        "Data em que a folga/afastamento começa*", value=date.today()
                    )
                with col2:
                    quantidade_dias = st.number_input(
                        "Quantidade de dias*", min_value=1, max_value=90, value=1, step=1
                    )
                data_fim = data_inicio + timedelta(days=int(quantidade_dias) - 1)
                st.caption(f"📅 Período calculado: {data_inicio} até {data_fim}")
            else:
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
                    st.success(
                        f"Afastamento cadastrado com sucesso! ({data_inicio} até {data_fim})"
                    )
                    st.rerun()
