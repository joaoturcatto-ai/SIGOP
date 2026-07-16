import streamlit as st
import pandas as pd
from utils.db import fetch_table, insert_row, update_row, delete_row

st.set_page_config(page_title="Viaturas - SIGOP", layout="wide")

st.title("🚓 Gestão de Viaturas")

# Criamos as abas para organizar o fluxo de trabalho
tab_listar, tab_cadastrar = st.tabs(["📋 Viaturas Cadastradas", "➕ Cadastrar Nova Viatura"])

# --- ABA 1: LISTAR E EDITAR VIATURAS ---
with tab_listar:
    st.subheader("Frota de Viaturas")
    
    # Busca as viaturas cadastradas diretamente do banco
    df_viaturas = fetch_table("viaturas")
    
    if not df_viaturas.empty:
        df_display = df_viaturas.copy()
        
        # Garante que as novas colunas existam no DataFrame
        colunas_obrigatorias = ["identificacao", "modelo", "status", "tipo_placa", "placa_oficial", "placa_reservada"]
        for col in colunas_obrigatorias:
            if col not in df_display.columns:
                df_display[col] = None
        
        # Renomeia colunas para exibição amigável
        df_display = df_display.rename(columns={
            "id": "ID",
            "identificacao": "Prefixo / Identificação",
            "modelo": "Modelo",
            "tipo_placa": "Tipo de Placa",
            "placa_oficial": "Placa Oficial",
            "placa_reservada": "Placa Reservada",
            "status": "Status"
        })
        
        colunas_exibicao = ["ID", "Prefixo / Identificação", "Modelo", "Placa Oficial", "Placa Reservada", "Tipo de Placa", "Status"]
        df_display = df_display[[c for c in colunas_exibicao if c in df_display.columns]]
        
        # Exibe a tabela
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("📝 Editar ou Remover Viatura")
        
        # Cria um seletor com as viaturas cadastradas
        opcoes_viaturas = {
            row["id"]: f"{row['identificacao']} - {row['modelo']} (Oficial: {row.get('placa_oficial') or 'N/D'})"
            for _, row in df_viaturas.iterrows()
        }
        
        id_selecionado = st.selectbox("Selecione uma viatura para editar ou remover:", options=list(opcoes_viaturas.keys()), format_func=lambda x: opcoes_viaturas[x])
        
        if id_selecionado:
            # Recupera a linha da viatura selecionada
            vtr_sel = df_viaturas[df_viaturas["id"] == id_selecionado].iloc[0]
            
            with st.form("form_editar_viatura"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_identificacao = st.text_input("Identificação / Prefixo", value=str(vtr_sel.get("identificacao", "")))
                    edit_modelo = st.text_input("Modelo", value=str(vtr_sel.get("modelo", "")))
                    
                    # Seleciona o tipo de placa correspondente
                    tipo_atual = str(vtr_sel.get("tipo_placa", "Oficial"))
                    lista_tipos = ["Oficial", "Reservada", "Outros"]
                    idx_tipo = lista_tipos.index(tipo_atual) if tipo_atual in lista_tipos else 0
                    edit_tipo_placa = st.selectbox("Tipo de Placa Predominante", lista_tipos, index=idx_tipo)
                
                with col2:
                    edit_placa_oficial = st.text_input("Placa Oficial", value=str(vtr_sel.get("placa_oficial", "") or ""))
                    edit_placa_reservada = st.text_input("Placa Reservada", value=str(vtr_sel.get("placa_reservada", "") or ""))
                    
                    # Seleciona o status correspondente
                    status_atual = str(vtr_sel.get("status", "Disponível"))
                    lista_status = ["Disponível", "Oficina", "Em operação", "Ativa", "Em Manutenção", "Baixada", "Cedida"]
                    idx_status = lista_status.index(status_atual) if status_atual in lista_status else 0
                    edit_status = st.selectbox("Status", lista_status, index=idx_status)
                
                c_btn1, c_btn2, _ = st.columns([1.2, 1.2, 4])
                with c_btn1:
                    btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with c_btn2:
                    btn_excluir = st.form_submit_button("🗑️ Excluir Viatura", use_container_width=True)
                
                if btn_salvar_edicao:
                    if not edit_identificacao or not edit_modelo:
                        st.error("⚠️ Identificação e Modelo são campos obrigatórios!")
                    else:
                        dados_atualizados = {
                            "identificacao": edit_identificacao,
                            "modelo": edit_modelo,
                            "tipo_placa": edit_tipo_placa,
                            "placa_oficial": edit_placa_oficial if edit_placa_oficial.strip() else None,
                            "placa_reservada": edit_placa_reservada if edit_placa_reservada.strip() else None,
                            "status": edit_status
                        }
                        
                        # Atualiza no banco
                        resultado = update_row("viaturas", id_selecionado, dados_atualizados)
                        if resultado:
                            st.toast("Alterações salvas com sucesso!", icon="✔️")
                            st.success("✔️ Viatura atualizada com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível salvar as alterações no banco de dados. Verifique o console.")
                        
                if btn_excluir:
                    delete_row("viaturas", id_selecionado)
                    st.success("🗑️ Viatura removida com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhuma viatura cadastrada até o momento.")

# --- ABA 2: CADASTRAR NOVA VIATURA ---
with tab_cadastrar:
    st.subheader("Cadastro de Nova Viatura")
    
    with st.form("form_cadastro_viatura", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            identificacao = st.text_input("Prefixo / Identificação da Viatura", placeholder="Ex: prefixo-10, VTR-01")
            modelo = st.text_input("Modelo do Veículo", placeholder="Ex: Toyota Hilux, Renault Duster")
            tipo_placa = st.selectbox("Tipo de Placa Predominante", ["Oficial", "Reservada", "Outros"])
            
        with col2:
            placa_oficial = st.text_input("Placa Oficial", placeholder="Ex: RRY5B21")
            placa_reservada = st.text_input("Placa Reservada", placeholder="Ex: SPY7F80")
            status = st.selectbox("Status de Disponibilidade", ["Disponível", "Oficina", "Em operação", "Ativa", "Em Manutenção", "Baixada", "Cedida"])
            
        btn_salvar = st.form_submit_button("Salvar Viatura")
        
        if btn_salvar:
            if not identificacao or not modelo:
                st.warning("⚠️ Os campos 'Prefixo / Identificação' e 'Modelo' são obrigatórios!")
            else:
                dados_viatura = {
                    "identificacao": identificacao,
                    "modelo": modelo,
                    "tipo_placa": tipo_placa,
                    "placa_oficial": placa_oficial if placa_oficial.strip() else None,
                    "placa_reservada": placa_reservada if placa_reservada.strip() else None,
                    "status": status
                }
                
                response_data = insert_row("viaturas", dados_viatura)
                if response_data:
                    st.success(f"✔️ Viatura {identificacao} cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar dados no Supabase. Verifique se removeu a restrição de tipo de placa no Supabase.")
