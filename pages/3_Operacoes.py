import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from utils.db import fetch_table, insert_row, update_row, delete_row

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
            
            # --- SEÇÃO 1: FORMULÁRIO DE EDIÇÃO ---
            st.markdown("### 📝 Editar Dados da Operação")
            
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
                    idx_del = lista_del_id.index(int(del_atual_id)) if del_atual_id and int(del_atual_id) in lista_del_id else 0
                    
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
                        st.toast("Operação atualizada com sucesso!", icon="✔️")
                        st.rerun()
                        
                if btn_excluir_op:
                    delete_row("operacoes", id_op_selecionada)
                    st.success("🗑️ Operação excluída com sucesso!")
                    st.rerun()

            st.markdown("---")
            
            # --- SEÇÃO 2: EQUIPES SEPARADAS E ESCALADAS ---
            st.markdown("### 👥 Equipes e Efetivos")
            
            df_equipe_op = pd.DataFrame()
            if not df_equipes.empty:
                df_equipe_op = df_equipes[df_equipes["operacao_id"] == id_op_selecionada].copy()
            
            equipes_existentes = [f"Equipe {i:02d}" for i in range(1, 21)]
            
            # Mostra as equipes agrupadas na tela com informações individuais de folga
            if not df_equipe_op.empty:
                for eq_nome in sorted(df_equipe_op["nome_equipe"].unique()):
                    membros_eq = df_equipe_op[df_equipe_op["nome_equipe"] == eq_nome]
                    
                    # Procura se há um líder configurado nesta equipe
                    membro_lider = membros_eq[membros_eq.get("is_lider", False) == True]
                    lider_txt = "Não definido"
                    if not miembro_lider.empty:
                        lider_id = membro_lider.iloc[0]["servidor_id"]
                        lider_txt = mapa_servidores.get(lider_id, "Não encontrado")
                    
                    # Viatura da equipe
                    vtr_id_eq = None
                    for _, row_m in membros_eq.iterrows():
                        if pd.notna(row_m.get("viatura_id")):
                            vtr_id_eq = row_m["viatura_id"]
                            break
                    vtr_txt = mapa_viaturas.get(vtr_id_eq, "Sem Viatura designada")
                    
                    # Container Visual da Equipe
                    with st.container(border=True):
                        st.markdown(f"#### 🏷️ {eq_nome} — 👑 Líder: **{lider_txt}** — 🚗 Viatura: **{vtr_txt}**")
                        
                        dados_membros_exibir = []
                        for _, row_m in membros_eq.iterrows():
                            cargo_funcao = "👑 LÍDER DE EQUIPE" if row_m.get("is_lider", False) else "Membro"
                            
                            # Formata a folga individual de cada integrante
                            if row_m.get("possui_folga", False):
                                dt_f = pd.to_datetime(row_m.get("folga_data")).strftime("%d/%m/%Y") if row_m.get("folga_data") else "N/D"
                                folga_ind_txt = f"🌴 {row_m.get('folga_duracao', '01 dia')} ({dt_f})"
                            else:
                                folga_ind_txt = "Sem folga programada"
                            
                            dados_membros_exibir.append({
                                "ID Registro": row_m["id"],
                                "Policial": mapa_servidores.get(row_m["servidor_id"], "Não encontrado"),
                                "Função na Equipe": cargo_funcao,
                                "Folga Escolhida": folga_ind_txt
                            })
                        
                        df_eq_grid = pd.DataFrame(dados_membros_exibir)
                        st.dataframe(df_eq_grid, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum policial escalado em equipe ainda.")
            
            # Formulário para Adicionar Policial e Configurar a Folga de Maneira Individual
            st.markdown("#### ➕ Adicionar Policial à Equipe e Definir sua Folga")
            
            # Estado para habilitar as opções de folga individual do policial atual
            policial_quer_folga = st.checkbox("🌴 Este policial vai agendar uma folga individual?")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                input_folga_data = st.date_input("Escolha a Data da Folga deste Policial", value=date.today(), disabled=not policial_quer_folga)
            with col_f2:
                lista_folgas_duracao = [
                    "Meio período (Matutino)",
                    "Meio período (Vespertino)",
                    "01 dia",
                    "02 dias",
                    "03 dias"
                ]
                input_folga_duracao = st.selectbox("Duração da Folga Escolhida", options=lista_folgas_duracao, index=2, disabled=not policial_quer_folga)
                
            st.markdown("---")
            
            with st.form("form_add_policial_equipe"):
                col_eq1, col_eq2, col_eq3 = st.columns(3)
                with col_eq1:
                    add_servidor = st.selectbox("Selecione o Policial", options=list(mapa_servidores.keys()), format_func=lambda x: mapa_servidores[x])
                with col_eq2:
                    add_nome_equipe = st.selectbox("Escolha a Equipe", options=equipes_existentes)
                with col_eq3:
                    add_viatura = st.selectbox("Defina a Viatura da Equipe", options=[None] + list(mapa_viaturas.keys()), format_func=lambda x: "Nenhuma Viatura" if x is None else mapa_viaturas[x])
                
                # Checkbox para marcar se ele é o líder
                add_is_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")
                
                btn_confirmar_membro = st.form_submit_button("➕ Vincular Policial e Agendar Folga")
                
                if btn_confirmar_membro:
                    # Se este novo membro for líder, remove a liderança de qualquer outro membro antigo desta mesma equipe
                    if add_is_lider and not df_equipe_op.empty:
                        lideres_antigos = df_equipe_op[(df_equipe_op["nome_equipe"] == add_nome_equipe) & (df_equipe_op.get("is_lider", False) == True)]
                        for _, row_antigo in lideres_antigos.iterrows():
                            update_row("equipes_operacoes", row_antigo["id"], {"is_lider": False})
                    
                    # Insere o novo membro já com os dados de folga individuais dele
                    dados_membro = {
                        "operacao_id": int(id_op_selecionada),
                        "servidor_id": int(add_servidor),
                        "nome_equipe": add_nome_equipe,
                        "viatura_id": int(add_viatura) if add_viatura else None,
                        "is_lider": bool(add_is_lider),
                        "possui_folga": bool(policial_quer_folga),
                        "folga_data": input_folga_data.isoformat() if policial_quer_folga else None,
                        "folga_duracao": input_folga_duracao if policial_quer_folga else None
                    }
                    
                    resultado_link = insert_row("equipes_operacoes", dados_membro)
                    if resultado_link:
                        st.toast("Policial vinculado com sucesso com suas folgas configuradas!", icon="✔️")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar integrante.")

            # Opção de remoção de policial
            if not df_equipe_op.empty:
                with st.expander("🗑️ Remover Policial de uma Equipe"):
                    opcoes_remover = {
                        row["id"]: f"{mapa_servidores.get(row['servidor_id'], 'N/D')} — {row['nome_equipe']}"
                        for _, row in df_equipe_op.iterrows()
                    }
                    membro_remover_id = st.selectbox("Selecione o integrante para remover:", options=list(opcoes_remover.keys()), format_func=lambda x: opcoes_remover[x])
                    if st.button("❌ Confirmar Remoção da Equipe"):
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
            
            # Monta equipes estruturadas para o PDF, com Líder e as Folgas Individuais detalhadas
            texto_equipes_pdf = ""
            if not df_equipe_op.empty:
                for eq_nome in sorted(df_equipe_op["nome_equipe"].unique()):
                    membros_eq = df_equipe_op[df_equipe_op["nome_equipe"] == eq_nome]
                    
                    # Busca Líder da equipe
                    lider_eq_membros = membros_eq[membros_eq.get("is_lider", False) == True]
                    lider_pdf_txt = "Não definido"
                    if not lider_eq_membros.empty:
                        lider_pdf_txt = mapa_servidores.get(lider_eq_membros.iloc[0]["servidor_id"], "Não encontrado")
                    
                    # Busca Viatura
                    vtr_id_eq = None
                    for _, row_m in membros_eq.iterrows():
                        if pd.notna(row_m.get("viatura_id")):
                            vtr_id_eq = row_m["viatura_id"]
                            break
                    vtr_txt = mapa_viaturas.get(vtr_id_eq, "Sem Viatura")
                    
                    texto_equipes_pdf += f"\n👉 **{eq_nome}**\n"
                    texto_equipes_pdf += f"   • 👑 Líder: {lider_pdf_txt}\n"
                    texto_equipes_pdf += f"   • 🚗 Viatura: {vtr_txt}\n"
                    texto_equipes_pdf += f"   • Integrantes e Folgas agendadas:\n"
                    
                    for _, row_m in membros_eq.iterrows():
                        funcao_marcador = " [LÍDER]" if row_m.get("is_lider", False) else ""
                        nome_policial = mapa_servidores.get(row_m['servidor_id'], 'Policial')
                        
                        # Formata o texto de folga individual no relatório
                        if row_m.get("possui_folga", False):
                            dt_f_txt = pd.to_datetime(row_m.get("folga_data")).strftime("%d/%m/%Y") if row_m.get("folga_data") else "N/D"
                            folga_txt = f" (Folga: {row_m.get('folga_duracao', '01 dia')} em {dt_f_txt})"
                        else:
                            folga_txt = " (Sem Folga)"
                            
                        texto_equipes_pdf += f"     - {nome_policial}{funcao_marcador}{folga_txt}\n"
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
