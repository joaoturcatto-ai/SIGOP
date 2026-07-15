import streamlit as st
import pandas as pd
from datetime import date, time
from utils.db import (
    fetch_table,
    insert_row,
    update_row,
    delete_row,
    servidor_disponivel,
    viatura_disponivel,
)

st.set_page_config(page_title="Operações - SIGOP", page_icon="🚨", layout="wide")
st.title("🚨 Operações")

try:
    operacoes = fetch_table("operacoes", order_by="data")
    servidores = fetch_table("servidores", order_by="nome")
    viaturas = fetch_table("viaturas", order_by="identificacao")
    participantes = fetch_table("operacao_participantes")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

tab_lista, tab_nova = st.tabs(["📋 Operações cadastradas", "➕ Nova operação"])

# ------------------------------------------------------------------
# ABA: LISTA / DETALHE DE OPERAÇÃO
# ------------------------------------------------------------------
with tab_lista:
    if operacoes.empty:
        st.info("Nenhuma operação cadastrada ainda. Use a aba 'Nova operação'.")
    else:
        st.dataframe(
            operacoes[["id", "nome", "data", "horario", "local", "status"]],
            use_container_width=True,
        )

        st.markdown("---")
        operacao_id = st.selectbox(
            "Selecione uma operação para ver detalhes / montar a equipe",
            options=operacoes["id"].tolist(),
            format_func=lambda x: operacoes[operacoes["id"] == x]["nome"].values[0],
        )

        if operacao_id:
            dados_op = operacoes[operacoes["id"] == operacao_id].iloc[0]

            st.subheader(f"📌 {dados_op['nome']}")
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Data:** {dados_op['data']}")
            col2.write(f"**Horário:** {dados_op.get('horario', '—')}")
            col3.write(f"**Status:** {dados_op['status']}")
            st.write(f"**Local:** {dados_op.get('local', '—')} — **Cidade:** {dados_op.get('cidade', '—')}")
            st.write(f"**Delegado responsável:** {dados_op.get('delegado_responsavel', '—')}")

            with st.expander("🎯 Objetivo da operação"):
                st.write(dados_op.get("objetivo") or "Não informado.")

            with st.expander("📋 Briefing"):
                st.write(dados_op.get("briefing") or "Não informado.")

            st.markdown("---")
            st.subheader("👥 Equipe escalada")

            participantes_op = participantes[participantes["operacao_id"] == operacao_id]
            if not participantes_op.empty:
                exibir = participantes_op.merge(
                    servidores[["id", "nome", "cargo"]],
                    left_on="servidor_id",
                    right_on="id",
                    how="left",
                    suffixes=("", "_srv"),
                )
                if not viaturas.empty:
                    exibir = exibir.merge(
                        viaturas[["id", "identificacao"]],
                        left_on="viatura_id",
                        right_on="id",
                        how="left",
                        suffixes=("", "_vtr"),
                    )
                else:
                    exibir["identificacao"] = None

                colunas_exibir = ["nome", "cargo", "equipe", "identificacao", "folga_concedida"]
                st.dataframe(exibir[colunas_exibir], use_container_width=True)

                st.markdown("**Remover participante:**")
                remover_id = st.selectbox(
                    "Selecione o participante a remover",
                    options=participantes_op["id"].tolist(),
                    format_func=lambda x: exibir[exibir["id"] == x]["nome"].values[0]
                    if x in exibir["id"].values
                    else str(x),
                    key="remover_participante",
                )
                if st.button("🗑️ Remover participante da operação"):
                    delete_row("operacao_participantes", remover_id)
                    st.success("Participante removido.")
                    st.rerun()
            else:
                st.info("Nenhum servidor escalado nesta operação ainda.")

            st.markdown("---")
            st.subheader("➕ Adicionar servidor à equipe")

            if servidores.empty:
                st.warning("Cadastre servidores primeiro na página 'Efetivo'.")
            else:
                with st.form("adicionar_participante"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        servidor_id = st.selectbox(
                            "Servidor",
                            options=servidores["id"].tolist(),
                            format_func=lambda x: servidores[servidores["id"] == x]["nome"].values[0],
                        )
                    with col2:
                        equipe_nome = st.text_input("Nome da equipe (ex: Equipe Alfa)")
                    with col3:
                        viatura_id = st.selectbox(
                            "Viatura (opcional)",
                            options=[None] + viaturas["id"].tolist()
                            if not viaturas.empty
                            else [None],
                            format_func=lambda x: "— Nenhuma —"
                            if x is None
                            else viaturas[viaturas["id"] == x]["identificacao"].values[0],
                        )
                    folga_concedida = st.selectbox(
                        "Folga a ser concedida após a operação",
                        ["Sem folga", "Meio período", "Dia integral"],
                    )
                    adicionar = st.form_submit_button("➕ Adicionar à equipe")

                    if adicionar:
                        data_op = pd.to_datetime(dados_op["data"]).date()
                        disponivel, motivo = servidor_disponivel(servidor_id, data_op)
                        if not disponivel:
                            st.error(f"⚠️ Não é possível escalar este servidor: {motivo}")
                        elif viatura_id is not None and not viatura_disponivel(viatura_id, data_op)[0]:
                            st.error("⚠️ Esta viatura já está escalada em outra operação nesta data.")
                        else:
                            insert_row(
                                "operacao_participantes",
                                {
                                    "operacao_id": operacao_id,
                                    "servidor_id": servidor_id,
                                    "equipe": equipe_nome,
                                    "viatura_id": viatura_id,
                                    "folga_concedida": folga_concedida,
                                },
                            )
                            # Se folga foi concedida, registra também em afastamentos
                            if folga_concedida != "Sem folga":
                                insert_row(
                                    "afastamentos",
                                    {
                                        "servidor_id": servidor_id,
                                        "tipo": "Folga Operacional",
                                        "data_inicio": str(data_op),
                                        "data_fim": str(data_op),
                                        "observacoes": f"Folga ({folga_concedida}) referente à operação '{dados_op['nome']}'.",
                                    },
                                )
                            st.success("Servidor adicionado à equipe!")
                            st.rerun()

            st.markdown("---")
            st.subheader("⚙️ Atualizar status da operação")
            novo_status = st.selectbox(
                "Status",
                ["Planejada", "Em andamento", "Concluída", "Cancelada"],
                index=["Planejada", "Em andamento", "Concluída", "Cancelada"].index(
                    dados_op["status"]
                ),
                key="status_op",
            )
            if st.button("💾 Atualizar status"):
                update_row("operacoes", operacao_id, {"status": novo_status})
                st.success("Status atualizado!")
                st.rerun()

# ------------------------------------------------------------------
# ABA: NOVA OPERAÇÃO
# ------------------------------------------------------------------
with tab_nova:
    with st.form("nova_operacao", clear_on_submit=True):
        nome = st.text_input("Nome da operação* (ex: Operação Aletheia)")
        col1, col2, col3 = st.columns(3)
        with col1:
            data_op = st.date_input("Data*", value=date.today())
        with col2:
            horario_op = st.time_input("Horário", value=time(6, 0))
        with col3:
            cidade = st.text_input("Cidade")
        local = st.text_input("Local")
        delegado_responsavel = st.text_input("Delegado responsável")
        objetivo = st.text_area(
            "Objetivo da operação",
            placeholder="Ex: Cumprimento de mandados de busca e apreensão...",
        )
        briefing = st.text_area(
            "Briefing",
            placeholder="Ex: Equipe Alfa entra pela frente. Uso obrigatório do colete...",
            height=150,
        )
        enviado = st.form_submit_button("➕ Cadastrar operação")

        if enviado:
            if not nome:
                st.error("O campo Nome da operação é obrigatório.")
            else:
                insert_row(
                    "operacoes",
                    {
                        "nome": nome,
                        "data": str(data_op),
                        "horario": str(horario_op),
                        "local": local,
                        "cidade": cidade,
                        "delegado_responsavel": delegado_responsavel,
                        "objetivo": objetivo,
                        "briefing": briefing,
                        "status": "Planejada",
                    },
                )
                st.success(f"Operação '{nome}' cadastrada com sucesso!")
                st.rerun()
