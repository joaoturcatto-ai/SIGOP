import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from utils.db import (
    fetch_table,
    insert_row,
    update_row,
    delete_row,
    servidor_disponivel_periodo,
    viatura_disponivel_periodo,
)

st.set_page_config(page_title="Operações - SIGOP", layout="wide")

st.title("🎯 Gestão de Operações")

# Carrega os dados necessários do banco
df_operacoes = fetch_table("operacoes")
df_servidores = fetch_table("servidores")
df_viaturas = fetch_table("viaturas")
df_equipes = fetch_table("equipes_operacoes")

# Mapeamentos de apoio
mapa_servidores = {row["id"]: f"{row['nome']} ({row['cargo']})" for _, row in df_servidores.iterrows()} if not df_servidores.empty else {}
mapa_viaturas = {row["id"]: f"{row['identificacao']} — {row.get('placa_oficial') or row.get('placa_reservada') or 'Sem Placa'}" for _, row in df_viaturas.iterrows()} if not df_viaturas.empty else {}

# Abas principais
tab_gerenciar, tab_cadastrar = st.tabs(["⚙️ Gerenciar e Editar Operação", "➕ Cadastrar Nova Operação"])

# --- ABA 1: GERENCIAR, EDITAR E GERAR PDF ---
with tab_gerenciar:
    if df_operacoes.empty:
        st.info("Nenhuma operação cadastrada até o momento.")
    else:
        st.subheader("Selecione uma operação para ver detalhes / editar")

        opcoes_ops = {row["id"]: f"{row['nome']} ({pd.to_datetime(row['data_inicio']).strftime('%d/%m/%Y') if row.get('data_inicio') else 'Sem data'})" for _, row in df_operacoes.iterrows()}
        id_op_selecionada = st.selectbox("Operações Cadastradas:", options=list(opcoes_ops.keys()), format_func=lambda x: opcoes_ops[x])

        if id_op_selecionada:
            op_sel = df_operacoes[df_operacoes["id"] == id_op_selecionada].iloc[0]
            nome_operacao_atual = op_sel.get("nome", "Operação Sem Nome")

            # --- SEÇÃO 1: FORMULÁRIO DE EDIÇÃO GERAL ---
            st.markdown("### 📝 Editar Dados Gerais da Operação")

            data_ini_padrao = pd.to_datetime(op_sel.get("data_inicio", date.today())).date()
            data_fim_padrao = pd.to_datetime(op_sel.get("data_fim", date.today())).date()

            hora_raw = op_sel.get("horario", "08:00:00")
            try:
                hora_padrao = datetime.strptime(str(hora_raw), "%H:%M:%S").time() if hora_raw else time(8, 0)
            except Exception:
                try:
                    hora_padrao = datetime.strptime(str(hora_raw), "%H:%M").time() if hora_raw else time(8, 0)
                except Exception:
                    hora_padrao = time(8, 0)

            with st.form("form_editar_operacao_dados"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_nome = st.text_input("Nome da Operação", value=str(op_sel.get("nome", "")))
                    edit_local = st.text_input("Local / Ponto de Encontro", value=str(op_sel.get("local", "")))
                    edit_cidade = st.text_input("Cidade", value=str(op_sel.get("cidade", "")))

                    delegados = df_servidores[df_servidores["cargo"].str.contains("Delegado", case=False, na=False)] if not df_servidores.empty else pd.DataFrame()
                    lista_del_id = list(delegados["id"].unique()) if not delegados.empty else []
                    mapa_del = {row["id"]: row["nome"] for _, row in delegados.iterrows()} if not delegados.empty else {}

                    del_atual_id = op_sel.get("delegado_id")
                    if pd.notna(del_atual_id) and int(del_atual_id) in lista_del_id:
                        idx_del = lista_del_id.index(int(del_atual_id))
                    else:
                        idx_del = 0

                    edit_delegado = st.selectbox("Delegado Responsável", options=lista_del_id, format_func=lambda x: mapa_del.get(x, "Não selecionado"), index=idx_del)

                with col2:
                    edit_data_ini = st.date_input("Data de Início", value=data_ini_padrao)
                    edit_data_fim = st.date_input("Data de Fim", value=data_fim_padrao)
                    edit_horario = st.time_input("Horário", value=hora_padrao)

                    status_atual = str(op_sel.get("status", "Planejada"))
                    lista_status = ["Planejada", "Em Andamento", "Concluída", "Cancelada"]
                    idx_status = lista_status.index(status_atual) if status_atual in lista_status else 0
                    edit_status = st.selectbox("Status da Operação", lista_status, index=idx_status)

                st.markdown("---")
                edit_objetivo = st.text_area("Objetivo da Operação", value=str(op_sel.get("objetivo", "") or ""))
                edit_briefing = st.text_area("Briefing / Instruções", value=str(op_sel.get("briefing", "") or ""))

                col_btn_op1, col_btn_op2, _ = st.columns([1.5, 1.5, 4])
                with col_btn_op1:
                    btn_salvar_dados = st.form_submit_button("💾 Salvar Alterações da Operação", use_container_width=True)
                with col_btn_op2:
                    btn_excluir_op = st.form_submit_button("🗑️ Excluir Operação", use_container_width=True)

                if btn_salvar_dados:
                    if not edit_nome:
                        st.error("⚠️ O Nome da Operação é obrigatório!")
                    else:
                        dados_atualizados = {
                            "nome": edit_nome,
                            "local": edit_local,
                            "cidade": edit_cidade,
                            "delegado_id": edit_delegado if edit_delegado else None,
                            "data_inicio": edit_data_ini.isoformat(),
                            "data_fim": edit_data_fim.isoformat(),
                            "horario": edit_horario.strftime("%H:%M:%S"),
                            "status": edit_status,
                            "objetivo": edit_objetivo,
                            "briefing": edit_briefing
                        }
                        update_row("operacoes", id_op_selecionada, dados_atualizados)
                        st.toast("Operação atualizada!", icon="✔️")
                        st.rerun()

                if btn_excluir_op:
                    delete_row("operacoes", id_op_selecionada)
                    st.success("🗑️ Operação excluída com sucesso!")
                    st.rerun()

            st.markdown("---")

            # --- SEÇÃO ATUALIZADA: DATAS ALTERNADAS E REFERÊNCIA ---
            st.markdown("### 🌴 Configuração de Folga por Policial")

            df_equipe_op = pd.DataFrame()
            if not df_equipes.empty:
                df_equipe_op = df_equipes[df_equipes["operacao_id"] == id_op_selecionada].copy()

            if df_equipe_op.empty:
                st.info("Cadastre policiais em alguma equipe abaixo antes de definir as folgas individuais.")
            else:
                opcoes_policiais_folga = {
                    row["id"]: f"{mapa_servidores.get(row['servidor_id'], 'Policial')} ({row['nome_equipe']})"
                    for _, row in df_equipe_op.iterrows()
                }

                id_registro_selecionado = st.selectbox(
                    "Selecione o policial para definir/alterar a folga:",
                    options=list(opcoes_policiais_folga.keys()),
                    format_func=lambda x: opcoes_policiais_folga[x]
                )

                policial_sel_info = df_equipe_op[df_equipe_op["id"] == id_registro_selecionado].iloc[0]

                possui_folga_atual = bool(policial_sel_info.get("possui_folga", False))

                # Resgata as datas salvas anteriormente (se houver) para pré-selecionar no multiselect
                datas_salvas_str = policial_sel_info.get("folga_data", "")
                datas_padrao_list = []
                if datas_salvas_str:
                    # Pode ser salvo como uma única string ou datas separadas por vírgula
                    datas_padrao_list = [d.strip() for d in str(datas_salvas_str).split(",") if d.strip()]

                # Gera as datas possíveis com base no período da operação (ou dos próximos 30 dias se o período for inválido)
                hoje = date.today()
                op_start = pd.to_datetime(op_sel.get("data_inicio", hoje)).date()
                op_end = pd.to_datetime(op_sel.get("data_fim", hoje + timedelta(days=5))).date()

                # Cria a lista de opções de datas para o usuário clicar
                datas_disponiveis = []
                curr_d = op_start
                limit_d = max(op_end, op_start + timedelta(days=15)) # Garante pelo menos 15 dias de opções
                while curr_d <= limit_d:
                    datas_disponiveis.append(curr_d.strftime("%Y-%m-%d"))
                    curr_d += timedelta(days=1)

                duracoes_possiveis = ["Meio período (Matutino)", "Meio período (Vespertino)", "Integral"]
                duracao_atual = policial_sel_info.get("folga_duracao", "Integral")
                idx_duracao = duracoes_possiveis.index(duracao_atual) if duracao_atual in duracoes_possiveis else 2

                col_cf1, col_cf2, col_cf3 = st.columns([1.5, 3, 1.5])
                with col_cf1:
                    definir_possui_folga = st.checkbox("Este policial terá direito a folga?", value=possui_folga_atual, key=f"chk_{id_registro_selecionado}")
                with col_cf2:
                    # Multiselect para datas alternadas livres!
                    definir_folgas_selecionadas = st.multiselect(
                        "Selecione uma ou mais datas alternadas de folga:",
                        options=datas_disponiveis,
                        default=[d for d in datas_padrao_list if d in datas_disponiveis],
                        format_func=lambda x: pd.to_datetime(x).strftime("%d/%m/%Y"),
                        disabled=not definir_possui_folga,
                        key=f"multi_dt_{id_registro_selecionado}"
                    )
                with col_cf3:
                    definir_folga_duracao = st.selectbox("Período da folga", options=duracoes_possiveis, index=idx_duracao, disabled=not definir_possui_folga, key=f"dur_{id_registro_selecionado}")

                if st.button("💾 Salvar Folga do Policial Selecionado", type="primary"):
                    # Salvamos as datas unidas por vírgula no banco, além de guardar explicitamente a referência da operação!
                    dados_folga_atualizar = {
                        "possui_folga": bool(definir_possui_folga),
                        "folga_data": ",".join(definir_folgas_selecionadas) if definir_possui_folga and definir_folgas_selecionadas else None,
                        "folga_duracao": definir_folga_duracao if definir_possui_folga else None,
                        "referencia_operacao": nome_operacao_atual if definir_possui_folga else None # Campo chave para os afastamentos!
                    }
                    update_row("equipes_operacoes", id_registro_selecionado, dados_folga_atualizar)

                    # --- Sincroniza com a tabela 'afastamentos' para que a folga  ---
                    # --- realmente bloqueie o servidor em outras escalas/CQH.     ---
                    tag_referencia = f"[ref:eq{id_registro_selecionado}]"
                    servidor_da_folga = int(policial_sel_info["servidor_id"])

                    afastamentos_existentes = fetch_table("afastamentos")
                    if not afastamentos_existentes.empty:
                        antigos = afastamentos_existentes[
                            afastamentos_existentes["observacoes"].astype(str).str.contains(
                                tag_referencia, regex=False, na=False
                            )
                        ]
                        for antigo_id in antigos["id"].tolist():
                            delete_row("afastamentos", antigo_id)

                    if definir_possui_folga and definir_folgas_selecionadas:
                        for data_folga_str in definir_folgas_selecionadas:
                            insert_row(
                                "afastamentos",
                                {
                                    "servidor_id": servidor_da_folga,
                                    "tipo": "Folga Operacional",
                                    "data_inicio": data_folga_str,
                                    "data_fim": data_folga_str,
                                    "observacoes": (
                                        f"Folga ({definir_folga_duracao}) referente à operação "
                                        f"'{nome_operacao_atual}'. {tag_referencia}"
                                    ),
                                },
                            )

                    st.toast(f"Folgas salvas para {mapa_servidores.get(policial_sel_info['servidor_id'])}!", icon="🌴")
                    st.rerun()

            st.markdown("---")

            # --- SEÇÃO 2: EQUIPES SEPARADAS E ESCALADAS ---
            st.markdown("### 👥 Equipes e Efetivos")

            equipes_existentes = [f"Equipe {i:02d}" for i in range(1, 21)]

            if not df_equipe_op.empty:
                for eq_nome in sorted(df_equipe_op["nome_equipe"].unique()):
                    membros_eq = df_equipe_op[df_equipe_op["nome_equipe"] == eq_nome]

                    membro_lider = membros_eq[membros_eq.get("is_lider", False) == True]
                    lider_txt = "Não definido"
                    if not membro_lider.empty:
                        lider_id = membro_lider.iloc[0]["servidor_id"]
                        lider_txt = mapa_servidores.get(lider_id, "Não encontrado")

                    vtr_id_eq = None
                    for _, row_m in membros_eq.iterrows():
                        if pd.notna(row_m.get("viatura_id")):
                            vtr_id_eq = row_m["viatura_id"]
                            break
                    vtr_txt = mapa_viaturas.get(vtr_id_eq, "Sem Viatura designada")

                    with st.container(border=True):
                        st.markdown(f"#### 🏷️ {eq_nome} — 👑 Líder: **{lider_txt}** — 🚗 Viatura: **{vtr_txt}**")

                        dados_membros_exibir = []
                        for _, row_m in membros_eq.iterrows():
                            cargo_funcao = "👑 LÍDER DE EQUIPE" if row_m.get("is_lider", False) else "Membro"

                            # Formatação das múltiplas datas alternadas na tabela
                            if row_m.get("possui_folga", False) and row_m.get("folga_data"):
                                datas_lista = str(row_m["folga_data"]).split(",")
                                datas_fmtd = [pd.to_datetime(d.strip()).strftime("%d/%m/%Y") for d in datas_lista if d.strip()]
                                status_folga = f"📅 {row_m.get('folga_duracao', 'Integral')} em: {', '.join(datas_fmtd)}"
                            else:
                                status_folga = "❌ Sem folga registrada"

                            dados_membros_exibir.append({
                                "ID Registro": row_m["id"],
                                "Policial": mapa_servidores.get(row_m["servidor_id"], "Não encontrado"),
                                "Função na Equipe": cargo_funcao,
                                "Folga Programada": status_folga
                            })

                        df_eq_grid = pd.DataFrame(dados_membros_exibir)
                        st.dataframe(df_eq_grid, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum policial escalado em equipe ainda.")

            # Formulário para Adicionar Policial à Equipe
            st.markdown("#### ➕ Adicionar Policial à Equipe")
            st.caption(
                f"Período desta operação: {data_ini_padrao} até {data_fim_padrao}. "
                "A disponibilidade do policial e da viatura será checada nesse período inteiro."
            )
            with st.form("form_add_policial_equipe"):
                col_eq1, col_eq2, col_eq3 = st.columns(3)
                with col_eq1:
                    add_servidor = st.selectbox("Selecione o Policial", options=list(mapa_servidores.keys()), format_func=lambda x: mapa_servidores[x])
                with col_eq2:
                    add_nome_equipe = st.selectbox("Escolha a Equipe", options=equipes_existentes)
                with col_eq3:
                    add_viatura = st.selectbox("Defina a Viatura da Equipe", options=[None] + list(mapa_viaturas.keys()), format_func=lambda x: "Nenhuma Viatura" if x is None else mapa_viaturas[x])

                add_is_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")

                btn_confirmar_membro = st.form_submit_button("➕ Vincular à Equipe")

                if btn_confirmar_membro:
                    # --- Checagem de disponibilidade (mesma proteção usada no resto do sistema) ---
                    disponivel, motivo = servidor_disponivel_periodo(
                        int(add_servidor), data_ini_padrao, data_fim_padrao
                    )
                    viatura_ok = True
                    motivo_viatura = ""
                    if add_viatura is not None:
                        viatura_ok, motivo_viatura = viatura_disponivel_periodo(
                            int(add_viatura), data_ini_padrao, data_fim_padrao
                        )

                    if not disponivel:
                        st.error(f"⚠️ Não é possível escalar este policial: {motivo}")
                    elif not viatura_ok:
                        st.error(f"⚠️ Não é possível usar esta viatura: {motivo_viatura}")
                    else:
                        if add_is_lider and not df_equipe_op.empty:
                            lideres_antigos = df_equipe_op[(df_equipe_op["nome_equipe"] == add_nome_equipe) & (df_equipe_op.get("is_lider", False) == True)]
                            for _, row_antigo in lideres_antigos.iterrows():
                                update_row("equipes_operacoes", row_antigo["id"], {"is_lider": False})

                        dados_membro = {
                            "operacao_id": int(id_op_selecionada),
                            "servidor_id": int(add_servidor),
                            "nome_equipe": add_nome_equipe,
                            "viatura_id": int(add_viatura) if add_viatura else None,
                            "is_lider": bool(add_is_lider),
                            "possui_folga": False,
                            "folga_data": None,
                            "folga_duracao": None,
                            "referencia_operacao": None
                        }

                        resultado_link = insert_row("equipes_operacoes", dados_membro)
                        if resultado_link:
                            st.toast("Policial adicionado! Configure a folga no painel acima.", icon="✔️")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao salvar integrante.")

            if not df_equipe_op.empty:
                with st.expander("🗑️ Remover Policial de uma Equipe"):
                    opcoes_remover = {
                        row["id"]: f"{mapa_servidores.get(row['servidor_id'], 'N/D')} — {row['nome_equipe']}"
                        for _, row in df_equipe_op.iterrows()
                    }
                    membro_remover_id = st.selectbox("Selecione o integrante para remover:", options=list(opcoes_remover.keys()), format_func=lambda x: opcoes_remover[x])
                    if st.button("❌ Confirmar Remoção da Equipe"):
                        # Remove também qualquer folga vinculada a este vínculo, para não deixar
                        # um afastamento "órfão" bloqueando o servidor sem motivo aparente.
                        tag_referencia = f"[ref:eq{membro_remover_id}]"
                        afastamentos_existentes = fetch_table("afastamentos")
                        if not afastamentos_existentes.empty:
                            antigos = afastamentos_existentes[
                                afastamentos_existentes["observacoes"].astype(str).str.contains(
                                    tag_referencia, regex=False, na=False
                                )
                            ]
                            for antigo_id in antigos["id"].tolist():
                                delete_row("afastamentos", antigo_id)

                        delete_row("equipes_operacoes", membro_remover_id)
                        st.toast("Integrante removido!", icon="🗑️")
                        st.rerun()

            st.markdown("---")

            # --- SEÇÃO 3: PDF DA ORDEM DE SERVIÇO ---
            st.markdown("### 📄 Relatório / Ordem de Serviço")

            nome_operacao = op_sel.get("nome", "Operação Sem Nome")
            cidade_op = op_sel.get("cidade", "N/D")
            local_op = op_sel.get("local", "N/D")
            data_ini_op = pd.to_datetime(op_sel.get("data_inicio")).strftime("%d/%m/%Y") if op_sel.get("data_inicio") else "N/D"
            data_fim_op = pd.to_datetime(op_sel.get("data_fim")).strftime("%d/%m/%Y") if op_sel.get("data_fim") else "N/D"
            horario_op = str(op_sel.get("horario", "N/D"))
            delegado_nome = mapa_servidores.get(op_sel.get("delegado_id"), "Não informado")
            objetivo_op = op_sel.get("objetivo", "Não detalhado")
            briefing_op = op_sel.get("briefing", "Não detalhado")

            texto_equipes_pdf = ""
            if not df_equipe_op.empty:
                for eq_nome in sorted(df_equipe_op["nome_equipe"].unique()):
                    membros_eq = df_equipe_op[df_equipe_op["nome_equipe"] == eq_nome]

                    lider_eq_membros = membros_eq[membros_eq.get("is_lider", False) == True]
                    lider_pdf_txt = "Não definido"
                    if not lider_eq_membros.empty:
                        lider_pdf_txt = mapa_servidores.get(lider_eq_membros.iloc[0]["servidor_id"], "Não encontrado")

                    vtr_id_eq = None
                    for _, row_m in membros_eq.iterrows():
                        if pd.notna(row_m.get("viatura_id")):
                            vtr_id_eq = row_m["viatura_id"]
                            break
                    vtr_txt = mapa_viaturas.get(vtr_id_eq, "Sem Viatura")

                    texto_equipes_pdf += f"\n👉 **{eq_nome}**\n"
                    texto_equipes_pdf += f"   • 👑 Líder: {lider_pdf_txt}\n"
                    texto_equipes_pdf += f"   • 🚗 Viatura: {vtr_txt}\n"
                    texto_equipes_pdf += f"   • Integrantes e Folgas:\n"
                    for _, row_m in membros_eq.iterrows():
                        funcao_marcador = " [LÍDER]" if row_m.get("is_lider", False) else ""

                        if row_m.get("possui_folga", False) and row_m.get("folga_data"):
                            datas_l = str(row_m["folga_data"]).split(",")
                            datas_fmtd_l = [pd.to_datetime(d.strip()).strftime("%d/%m/%Y") for d in datas_l if d.strip()]
                            folga_desc = f" (Folga {row_m.get('folga_duracao', 'Integral')} em: {', '.join(datas_fmtd_l)})"
                        else:
                            folga_desc = " (Sem Folga)"

                        texto_equipes_pdf += f"     - {mapa_servidores.get(row_m['servidor_id'], 'Policial')}{funcao_marcador}{folga_desc}\n"
            else:
                texto_equipes_pdf = "Nenhuma equipe montada para esta operação."

            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; background-color: white; color: black; border-radius: 5px;">
                <h2 style="text-align: center; margin-bottom: 5px; color: #1a365d;">ORDEM DE SERVIÇO OPERACIONAL</h2>
                <h4 style="text-align: center; margin-top: 0; color: #4a5568;">SISTEMA INTEGRADO DE GESTÃO OPERACIONAL - SIGOP</h4>
                <hr style="border: 1px solid #1a365d;">

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr>
                        <td style="padding: 5px; font-weight: bold; width: 25%;">Operação:</td>
                        <td style="padding: 5px;">{nome_operacao}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Período:</td>
                        <td style="padding: 5px;">{data_ini_op} até {data_fim_op} às {horario_op}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Local / Cidade:</td>
                        <td style="padding: 5px;">{local_op} — {cidade_op}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Delegado Responsável:</td>
                        <td style="padding: 5px;">{delegado_nome}</td>
                    </tr>
                </table>

                <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">1. OBJETIVO DA OPERAÇÃO</h4>
                <p style="text-align: justify; white-space: pre-line;">{objetivo_op}</p>

                <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">2. BRIEFING / INSTRUÇÕES GERAIS</h4>
                <p style="text-align: justify; white-space: pre-line;">{briefing_op}</p>

                <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">3. DISTRIBUIÇÃO DAS EQUIPES E FOLGAS SELECIONADAS</h4>
                <p style="white-space: pre-line;">{texto_equipes_pdf}</p>

                <br><br>
                <div style="text-align: center; margin-top: 30px;">
                    <p>__________________________________________________</p>
                    <p style="font-weight: bold; margin-top: 5px;">{delegado_nome}</p>
                    <p style="font-size: 12px; color: #718096;">Delegado de Polícia - Responsável Operacional</p>
                </div>
            </div>
            """

            with st.expander("👁️ Visualizar Prévia do Documento"):
                st.html(html_content)

            st.markdown(
                f"""
                <a href="javascript:window.print()" style="text-decoration: none;">
                    <button style="
                        background-color: #ff4b4b;
                        color: white;
                        padding: 10px 24px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 16px;
                        width: 100%;">
                        🖨️ Imprimir Ordem de Serviço / Salvar em PDF
                    </button>
                </a>
                <p style="font-size: 11px; text-align: center; color: gray; margin-top: 5px;">
                    Utilize "Salvar como PDF" nas configurações de destino da sua impressora.
                </p>
                """,
                unsafe_allow_html=True
            )

# --- ABA 2: CADASTRAR NOVA OPERAÇÃO ---
with tab_cadastrar:
    st.subheader("Cadastrar Nova Operação")

    with st.form("form_nova_operacao", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            cad_nome = st.text_input("Nome da Operação", placeholder="Ex: Operação Devastate")
            cad_local = st.text_input("Ponto de Encontro / Local", placeholder="Ex: Sede da Diretoria")
            cad_cidade = st.text_input("Cidade", placeholder="Ex: Cuiabá")

            delegados = df_servidores[df_servidores["cargo"].str.contains("Delegado", case=False, na=False)] if not df_servidores.empty else pd.DataFrame()
            lista_del_id = list(delegados["id"].unique()) if not delegados.empty else []
            mapa_del = {row["id"]: row["nome"] for _, row in delegados.iterrows()} if not delegados.empty else {}

            cad_delegado = st.selectbox("Delegado Responsável", options=lista_del_id, format_func=lambda x: mapa_del.get(x, "Nenhum"))

        with col_c2:
            cad_data_ini = st.date_input("Data de Início", value=date.today())
            cad_data_fim = st.date_input("Data de Fim", value=date.today())
            cad_horario = st.time_input("Horário", value=time(8, 0))
            cad_status = st.selectbox("Status", ["Planejada", "Em Andamento"])

        st.markdown("---")
        cad_objetivo = st.text_area("Objetivo da Operação")
        cad_briefing = st.text_area("Briefing / Instruções")

        btn_cadastrar_op = st.form_submit_button("💾 Criar Operação")

        if btn_cadastrar_op:
            if not cad_nome:
                st.warning("⚠️ O nome da operação é obrigatório!")
            else:
                dados_nova_op = {
                    "nome": cad_nome,
                    "local": cad_local,
                    "cidade": cad_cidade,
                    "delegado_id": int(cad_delegado) if cad_delegado else None,
                    "data_inicio": cad_data_ini.isoformat(),
                    "data_fim": cad_data_fim.isoformat(),
                    "horario": cad_horario.strftime("%H:%M:%S"),
                    "status": cad_status,
                    "objetivo": cad_objetivo,
                    "briefing": cad_briefing
                }
                res = insert_row("operacoes", dados_nova_op)
                if res:
                    st.success(f"✔️ Operação '{cad_nome}' cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar operação.")
