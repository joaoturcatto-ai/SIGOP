import streamlit as st
import pandas as pd
from datetime import date, time, timedelta
from utils.db import (
    fetch_table,
    insert_row,
    update_row,
    delete_row,
    servidor_disponivel_periodo,
    viatura_disponivel_periodo,
)

st.set_page_config(page_title="Operações - SIGOP", page_icon="🚨", layout="wide")
st.title("🚨 Operações")

try:
    operacoes = fetch_table("operacoes", order_by="data_inicio")
    servidores = fetch_table("servidores", order_by="nome")
    viaturas = fetch_table("viaturas", order_by="identificacao")
    participantes = fetch_table("operacao_participantes")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

ICONE_PLACA = {"Oficial": "🛡️", "Reservada": "🕵️"}

tab_lista, tab_nova = st.tabs(["📋 Operações cadastradas", "➕ Nova operação"])

# ------------------------------------------------------------------
# ABA: LISTA / DETALHE DE OPERAÇÃO
# ------------------------------------------------------------------
with tab_lista:
    if operacoes.empty:
        st.info("Nenhuma operação cadastrada ainda. Use a aba 'Nova operação'.")
    else:
        st.dataframe(
            operacoes[["id", "nome", "data_inicio", "data_fim", "horario", "local", "status"]],
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
            data_inicio_op = pd.to_datetime(dados_op["data_inicio"]).date()
            data_fim_op = pd.to_datetime(dados_op["data_fim"]).date()
            qtd_dias_op = (data_fim_op - data_inicio_op).days + 1

            st.subheader(f"📌 {dados_op['nome']}")
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Período:** {data_inicio_op} até {data_fim_op}")
            col2.write(f"**Duração:** {qtd_dias_op} dia(s)")
            col3.write(f"**Status:** {dados_op['status']}")
            st.write(f"**Horário:** {dados_op.get('horario', '—')}")
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
                        viaturas[["id", "identificacao", "tipo_placa"]],
                        left_on="viatura_id",
                        right_on="id",
                        how="left",
                        suffixes=("", "_vtr"),
                    )
                    exibir["viatura"] = exibir.apply(
                        lambda r: f"{ICONE_PLACA.get(r.get('tipo_placa'), '')} {r.get('identificacao') or '—'}".strip()
                        if pd.notna(r.get("identificacao"))
                        else "—",
                        axis=1,
                    )
                else:
                    exibir["viatura"] = "—"

                colunas_exibir = ["nome", "cargo", "equipe", "viatura", "folga_concedida"]
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
                            else f"{ICONE_PLACA.get(viaturas[viaturas['id'] == x]['tipo_placa'].values[0], '')} "
                            f"{viaturas[viaturas['id'] == x]['identificacao'].values[0]}",
                        )

                    st.caption(
                        f"Esta operação dura {qtd_dias_op} dia(s): de {data_inicio_op} até {data_fim_op}. "
                        "A disponibilidade do servidor e da viatura será checada em todos esses dias."
                    )

                    st.markdown("**Folga a ser concedida após a operação**")
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        folga_concedida = st.selectbox(
                            "Tipo de folga",
                            ["Sem folga", "Meio período", "Dia integral"],
                        )
                    with col5:
                        dias_folga = st.number_input(
                            "Quantidade de dias de folga",
                            min_value=0,
                            max_value=30,
                            value=0,
                            step=1,
                            help="Deixe 0 se a folga não deve gerar um afastamento agendado.",
                        )
                    with col6:
                        data_inicio_folga = st.date_input(
                            "Data em que a folga será usufruída",
                            value=data_fim_op + timedelta(days=1),
                        )

                    adicionar = st.form_submit_button("➕ Adicionar à equipe")

                    if adicionar:
                        disponivel, motivo = servidor_disponivel_periodo(
                            servidor_id, data_inicio_op, data_fim_op
                        )
                        if not disponivel:
                            st.error(f"⚠️ Não é possível escalar este servidor: {motivo}")
                        elif viatura_id is not None and not viatura_disponivel_periodo(
                            viatura_id, data_inicio_op, data_fim_op
                        )[0]:
                            st.error("⚠️ Esta viatura já está escalada em outra operação neste período.")
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
                            if dias_folga and int(dias_folga) > 0:
                                data_fim_folga = data_inicio_folga + timedelta(
                                    days=int(dias_folga) - 1
                                )
                                insert_row(
                                    "afastamentos",
                                    {
                                        "servidor_id": servidor_id,
                                        "tipo": "Folga Operacional",
                                        "data_inicio": str(data_inicio_folga),
                                        "data_fim": str(data_fim_folga),
                                        "observacoes": (
                                            f"{int(dias_folga)} dia(s) de folga ({folga_concedida}) "
                                            f"referente à operação '{dados_op['nome']}'."
                                        ),
                                    },
                                )
                                st.success(
                                    f"Servidor adicionado à equipe! Folga agendada de "
                                    f"{data_inicio_folga} até {data_fim_folga}."
                                )
                            else:
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
            data_inicio_nova = st.date_input("Data de início*", value=date.today())
        with col2:
            data_fim_nova = st.date_input("Data de fim*", value=date.today())
        with col3:
            horario_op = st.time_input("Horário", value=time(6, 0))

        col4, col5 = st.columns(2)
        with col4:
            local = st.text_input("Local")
        with col5:
            cidade = st.text_input("Cidade")

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
            elif data_fim_nova < data_inicio_nova:
                st.error("A data de fim não pode ser anterior à data de início.")
            else:
                insert_row(
                    "operacoes",
                    {
                        "nome": nome,
                        "data_inicio": str(data_inicio_nova),
                        "data_fim": str(data_fim_nova),
                        "horario": str(horario_op),
                        "local": local,
                        "cidade": cidade,
                        "delegado_responsavel": delegado_responsavel,
                        "objetivo": objetivo,
                        "briefing": briefing,
                        "status": "Planejada",
                    },
                )
                dias = (data_fim_nova - data_inicio_nova).days + 1
                st.success(
                    f"Operação '{nome}' cadastrada com sucesso! ({dias} dia(s): "
                    f"{data_inicio_nova} até {data_fim_nova})"
                )
                st.rerun()
