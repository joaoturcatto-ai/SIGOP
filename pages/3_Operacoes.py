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
df_equipes = fetch_table("equipes_operacoes")  # Ajuste o nome se no seu banco for diferente (ex: "escalas")

# Mapeamentos para exibição amigável
mapa_servidores = {row["id"]: f"{row['nome']} ({row['cargo']})" for _, row in df_servidores.iterrows()} if not df_servidores.empty else {}
mapa_viaturas = {row["id"]: f"{row['identificacao']} - {row['modelo']} ({row.get('placa_oficial') or row.get('placa_reservada') or 'S/P'})" for _, row in df_viaturas.iterrows()} if not df_viaturas.empty else {}

# Abas principais: Gerenciar Existentes ou Cadastrar Nova
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
            # Obtém a operação selecionada diretamente do banco atualizado
            op_sel = df_operacoes[df_operacoes["id"] == id_op_selecionada].iloc[0]
            
            # --- SEÇÃO 1: FORMULÁRIO DE EDIÇÃO DOS DADOS DA OPERAÇÃO ---
            st.markdown("### 📝 Editar Dados da Operação")
            
            # Tratamento de datas e horários para o formulário
            data_ini_padrao = pd.to_datetime(op_sel.get("data_inicio", date.today())).date()
            data_fim_padrao = pd.to_datetime(op_sel.get("data_fim", date.today())).date()
            
            # Converte string de hora para o tipo datetime.time
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
                    
                    # Seleção de Delegado Responsável
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
                    
                    # Seleção de Status
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
            
            # --- SEÇÃO 2: EQUIPE ESCALADA (VISUALIZAÇÃO, EDIÇÃO E EXCLUSÃO) ---
            st.markdown("### 👥 Equipe Escalada")
            
            # Filtrar equipe escalada nesta operação
            df_equipe_op = pd.DataFrame()
            if not df_equipes.empty:
                df_equipe_op = df_equipes[df_equipes["operacao_id"] == id_op_selecionada].copy()
            
            if not df_equipe_op.empty:
                df_equipe_op["Servidor"] = df_equipe_op["servidor_id"].map(mapa_servidores)
                df_equipe_op["Viatura"] = df_equipe_op["viatura_id"].map(mapa_viaturas).fillna("Sem Viatura")
                df_equipe_op = df_equipe_op.rename(columns={"nome_equipe": "Nome da Equipe"})
                
                # Tabela organizada de exibição
                st.dataframe(df_equipe_op[["id", "Servidor", "Nome da Equipe", "Viatura"]], use_container_width=True, hide_index=True)
                
                # Remover servidor da equipe
                with st.expander("🗑️ Remover integrante da escala"):
                    opcoes_rem_membro = {
                        row["id"]: f"{row['Servidor']} — {row['Nome da Equipe']}"
                        for _, row in df_equipe_op.iterrows()
                    }
                    membro_remover_id = st.selectbox("Selecione o servidor para remover da operação:", options=list(opcoes_rem_membro.keys()), format_func=lambda x: opcoes_rem_membro[x])
                    if st.button("❌ Remover Servidor da Operação"):
                        delete_row("equipes_operacoes", membro_remover_id)
                        st.toast("Servidor removido da equipe!", icon="🗑️")
                        st.rerun()
            else:
                st.info("Nenhum servidor escalado nesta operação ainda.")
            
            # Adicionar novos servidores à equipe
            with st.expander("➕ Adicionar servidor à equipe"):
                with st.form("form_add_equipe"):
                    col_add1, col_add2, col_add3 = st.columns(3)
                    with col_add1:
                        add_servidor = st.selectbox("Servidor", options=list(mapa_servidores.keys()), format_func=lambda x: mapa_servidores[x])
                    with col_add2:
                        add_nome_equipe = st.text_input("Nome da equipe (ex: Equipe Alpha, Operacional)", value="Equipe Alfa")
                    with col_add3:
                        add_viatura = st.selectbox("Viatura (opcional)", options=[None] + list(mapa_viaturas.keys()), format_func=lambda x: "Nenhuma" if x is None else mapa_viaturas[x])
                    
                    btn_add_membro = st.form_submit_button("➕ Confirmar Escala")
                    if btn_add_membro:
                        dados_membro = {
                            "operacao_id": int(id_op_selecionada),
                            "servidor_id": int(add_servidor),
                            "nome_equipe": add_nome_equipe,
                            "viatura_id": int(add_viatura) if add_viatura else None
                        }
                        insert_row("equipes_operacoes", dados_membro)
                        st.toast("Membro adicionado!", icon="✔️")
                        st.rerun()

            st.markdown("---")
            
            # --- SEÇÃO 3: PDF DA ORDEM DE SERVIÇO ---
            st.markdown("### 📄 Relatório / Ordem de Serviço")
            
            # Prepara os dados para o PDF
            nome_operacao = op_sel.get("nome", "Operação Sem Nome")
            cidade_op = op_sel.get("cidade", "N/D")
            local_op = op_sel.get("local", "N/D")
            data_ini_op = pd.to_datetime(op_sel.get("data_inicio")).strftime("%d/%m/%Y") if op_sel.get("data_inicio") else "N/D"
            data_fim_op = pd.to_datetime(op_sel.get("data_fim")).strftime("%d/%m/%Y") if op_sel.get("data_fim") else "N/D"
            horario_op = str(op_sel.get("horario", "N/D"))
            delegado_nome = mapa_servidores.get(op_sel.get("delegado_id"), "Não informado")
            objetivo_op = op_sel.get("objetivo", "Não detalhado")
            briefing_op = op_sel.get("briefing", "Não detalhado")
            
            # Montar a lista de equipe formatada para texto
            texto_equipe = ""
            if not df_equipe_op.empty:
                for _, row in df_equipe_op.iterrows():
                    texto_equipe += f"- {row['Servidor']} | Equipe: {row['Nome da Equipe']} | Viatura: {row['Viatura']}\n"
            else:
                texto_equipe = "Nenhum efetivo escalado até o momento."

            # Função simples para renderizar HTML estilizado de visualização prévia e exportação rápida
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
                
                <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">3. EFETIVO E LOGÍSTICA ESCALADA</h4>
                <p style="white-space: pre-line;">{texto_equipe}</p>
                
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
            
            # Botão de impressão nativo do navegador
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
                    Ao clicar no botão, utilize a opção "Salvar como PDF" nas configurações de destino da sua impressora.
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
