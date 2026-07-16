import streamlit as st
import pandas as pd
from utils.db import select_all, insert_data

st.set_page_config(page_title="Viaturas - SIGOP", layout="wide")

st.title("🚓 Gestão de Viaturas")

# Criamos duas abas: Uma para listar as viaturas e outra para cadastrar novas
tab_listar, tab_cadastrar = st.tabs(["📋 Viaturas Cadastradas", "➕ Cadastrar Nova Viatura"])

# --- ABA 1: LISTAR VIATURAS ---
with tab_listar:
    st.subheader("Frota de Viaturas")
    
    # Busca todas as viaturas registradas no banco de dados
    viaturas_data = select_all("viaturas")
    
    if viaturas_data:
        # Convertemos os dados para um DataFrame do Pandas para facilitar a exibição
        df = pd.DataFrame(viaturas_data)
        
        # Renomeamos as colunas para que fiquem amigáveis na tabela do usuário
        df_display = df.copy()
        df_display = df_display.rename(columns={
            "identificacao": "Prefixo / Identificação",
            "modelo": "Modelo",
            "tipo_placa": "Tipo de Placa",
            "placa_oficial": "Placa Oficial",
            "placa_reservada": "Placa Reservada (Fria)",
            "status": "Status"
        })
        
        # Selecionamos a ordem ideal de colunas para exibir
        colunas_exibicao = [
            "Prefixo / Identificação", 
            "Modelo", 
            "Placa Oficial", 
            "Placa Reservada (Fria)", 
            "Tipo de Placa", 
            "Status"
        ]
        
        # Filtramos para mostrar apenas as colunas que importam na tabela
        df_display = df_display[[c for c in colunas_exibicao if c in df_display.columns]]
        
        # Exibe a tabela formatada de forma limpa
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma viatura cadastrada até o momento.")

# --- ABA 2: CADASTRAR NOVA VIATURA ---
with tab_cadastrar:
    st.subheader("Cadastro de Nova Viatura")
    
    # Criamos o formulário de cadastro estruturado
    with st.form("form_cadastro_viatura", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            identificacao = st.text_input("Prefixo / Identificação da Viatura", placeholder="Ex: prefixo-10, VTR-01")
            modelo = st.text_input("Modelo do Veículo", placeholder="Ex: Toyota Hilux, Renault Duster")
            tipo_placa = st.selectbox("Tipo de Placa Predominante", ["Caracterizada / Oficial", "Velada / Reservada", "Outros"])
            
        with col2:
            placa_oficial = st.text_input("Placa Oficial", placeholder="Ex: RRY5B21")
            placa_reservada = st.text_input("Placa Reservada (Fria / Velada)", placeholder="Ex: SPY7F80")
            status = st.selectbox("Status de Disponibilidade", ["Ativa", "Em Manutenção", "Baixada", "Cedida"])
            
        btn_salvar = st.form_submit_button("Salvar Viatura")
        
        if btn_salvar:
            if not identificacao or not modelo:
                st.warning("⚠️ Os campos 'Prefixo / Identificação' e 'Modelo' são obrigatórios!")
            else:
                # Prepara o dicionário com os dados exatamente mapeados para o banco de dados
                dados_viatura = {
                    "identificacao": identificacao,
                    "modelo": modelo,
                    "tipo_placa": tipo_placa,
                    "placa_oficial": placa_oficial if placa_oficial else None,
                    "placa_reservada": placa_reservada if placa_reservada else None,
                    "status": status
                }
                
                # Executa a inserção no banco de dados do Supabase
                sucesso = insert_data("viaturas", dados_viatura)
                
                if sucesso:
                    st.success(f"✔️ Viatura {identificacao} cadastrada com sucesso!")
                    # Recarrega a página para atualizar a tabela na outra aba
                    st.rerun()
                else:
                    st.error("❌ Ocorreu um erro ao tentar salvar a viatura no banco de dados. Verifique a conexão.")
