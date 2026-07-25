import streamlit as st
import pandas as pd
from datetime import date
from utils.db import fetch_table, insert_row, update_row, delete_row

st.set_page_config(page_title="Efetivo - SIGOP", page_icon="👮", layout="wide")
st.title("👮 Efetivo")
st.caption("Cadastro de Delegados, Escrivães e Investigadores de Polícia")

try:
    servidores = fetch_table("servidores", order_by="nome")
except Exception as e:
    st.error("⚠️ Erro ao carregar servidores.")
    st.code(str(e), language="python")
    st.stop()

tab_lista, tab_novo = st.tabs(["📋 Lista de servidores", "➕ Cadastrar novo"])

with tab_lista:
    if servidores.empty:
        st.info("Nenhum servidor cadastrado ainda. Use a aba 'Cadastrar novo'.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_cargo = st.multiselect(
                "Filtrar por cargo",
                options=servidores["cargo"].unique().tolist(),
                default=servidores["cargo"].unique().tolist(),
            )
        with col_f2:
            filtro_situacao = st.multiselect(
                "Filtrar por situação",
                options=servidores["situacao"].unique().tolist(),
                default=servidores["situacao"].unique().tolist(),
            )

        filtrado = servidores[
            servidores["cargo"].isin(filtro_cargo)
            & servidores["situacao"].isin(filtro_situacao)
        ]

        st.dataframe(
            filtrado[
                ["id", "nome", "matricula", "cargo", "equipe", "telefone", "situacao"]
            ],
            use_container_width=True,
        )

        st.markdown("---")
        st.subheader("✏️ Editar ou remover servidor")
        servidor_selecionado = st.selectbox(
            "Selecione um servidor",
            options=filtrado["id"].tolist(),
            format_func=lambda x: filtrado[filtrado["id"] == x]["nome"].values[0],
        )

        if servidor_selecionado:
            dados = servidores[servidores["id"] == servidor_selecionado].iloc[0]

            with st.form("editar_servidor"):
                col1, col2 = st.columns(2)
                with col1:
                    nome = st.text_input("Nome", value=dados["nome"])
                    matricula = st.text_input(
                        "Matrícula", value=dados.get("matricula", "") or ""
                    )
                    cargo = st.selectbox(
                        "Cargo",
                        ["Delegado de Polícia", "Escrivão de Polícia", "Investigador de Polícia"],
                        index=["Delegado de Polícia", "Escrivão de Polícia", "Investigador de Polícia"].index(
                            dados["cargo"]
                        ),
                    )
                    data_nasc_atual = dados.get("data_nascimento")
                    data_nascimento = st.date_input(
                        "Data de nascimento (opcional)",
                        value=pd.to_datetime(data_nasc_atual).date() if pd.notna(data_nasc_atual) else None,
                    )
                with col2:
                    equipe = st.text_input("Equipe", value=dados.get("equipe", "") or "")
                    telefone = st.text_input(
                        "Telefone", value=dados.get("telefone", "") or ""
                    )
                    situacao = st.selectbox(
                        "Situação",
                        ["Ativo", "Férias", "Licença"],
                        index=["Ativo", "Férias", "Licença"].index(dados["situacao"]),
                    )
                observacoes = st.text_area(
                    "Observações", value=dados.get("observacoes", "") or ""
                )

                col_btn1, col_btn2 = st.columns(2)
                salvar = col_btn1.form_submit_button("💾 Salvar alterações")
                remover = col_btn2.form_submit_button("🗑️ Remover servidor")

                if salvar:
                    update_row(
                        "servidores",
                        servidor_selecionado,
                        {
                            "nome": nome,
                            "matricula": matricula,
                            "cargo": cargo,
                            "equipe": equipe,
                            "telefone": telefone,
                            "situacao": situacao,
                            "observacoes": observacoes,
                            "data_nascimento": data_nascimento.isoformat() if data_nascimento else None,
                        },
                    )
                    st.success("Servidor atualizado com sucesso!")
                    st.rerun()

                if remover:
                    delete_row("servidores", servidor_selecionado)
                    st.success("Servidor removido.")
                    st.rerun()

with tab_novo:
    with st.form("novo_servidor", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome*")
            matricula = st.text_input("Matrícula")
            cargo = st.selectbox(
                "Cargo*",
                ["Delegado de Polícia", "Escrivão de Polícia", "Investigador de Polícia"],
            )
            data_nascimento = st.date_input("Data de nascimento (opcional)", value=None)
        with col2:
            equipe = st.text_input("Equipe")
            telefone = st.text_input("Telefone")
            situacao = st.selectbox("Situação", ["Ativo", "Férias", "Licença"])
        observacoes = st.text_area("Observações")

        enviado = st.form_submit_button("➕ Cadastrar servidor")

        if enviado:
            if not nome:
                st.error("O campo Nome é obrigatório.")
            else:
                insert_row(
                    "servidores",
                    {
                        "nome": nome,
                        "matricula": matricula,
                        "cargo": cargo,
                        "equipe": equipe,
                        "telefone": telefone,
                        "situacao": situacao,
                        "observacoes": observacoes,
                        "data_nascimento": data_nascimento.isoformat() if data_nascimento else None,
                    },
                )
                st.success(f"Servidor '{nome}' cadastrado com sucesso!")
                st.rerun()
