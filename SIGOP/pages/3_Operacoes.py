import streamlit as st
import pandas as pd
from utils.db import client  # Usando apenas o client direto para ignorar o 'insert_row' antigo

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Módulo Operações - SIGOP 2.0",
    page_icon="🚔",
    layout="wide"
)

st.title("👥 Equipes e Efetivos")
st.markdown("---")

# 2. CARREGAMENTO DOS DADOS TRATANDO OS VALORES 'NAN'
def carregar_dados_auxiliares():
    try:
        res_pol = client.table("efetivo").select("*").execute()
        df_pol = pd.DataFrame(res_pol.data) if res_pol.data else pd.DataFrame()
        
        res_vtr = client.table("viaturas").select("*").execute()
        df_vtr = pd.DataFrame(res_vtr.data) if res_vtr.data else pd.DataFrame()
        
        return df_pol, df_vtr
    except Exception as e:
        st.error(f"Erro ao carregar tabelas do Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_policiais, df_viaturas = carregar_dados_auxiliares()

# 3. EXIBIÇÃO DAS EQUIPES SALVAS
st.subheader("📋 Equipes e Efetivos Escalados")
try:
    res_eq = client.table("equipes_operacoes").select("*").execute()
    if res_eq.data:
        st.dataframe(pd.DataFrame(res_eq.data), use_container_width=True)
    else:
        st.info("Nenhum policial escalado em equipe ainda.")
except Exception:
    st.info("Nenhum policial escalado em equipe ainda.")

st.markdown("---")

# 4. FORMULÁRIO DE CADASTRO SEM INTERMEDIÁRIOS QUEBRADOS
st.subheader("➕ Adicionar Policial à Equipe")

if not df_policiais.empty:
    with st.form("form_vinculacao_direta"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dict_policiais = {}
            for _, row in df_policiais.iterrows():
                if 'nome' in row and str(row['nome']).strip() and str(row['nome']).lower() != 'nan':
                    cargo = f" ({row['cargo']})" if 'cargo' in row and str(row['cargo']).lower() != 'nan' else ""
                    dict_policiais[f"{str(row['nome']).upper()}{cargo}"] = int(row['id'])
            policial_sel = st.selectbox("Selecione o Policial", list(dict_policiais.keys()))
            
        with col2:
            equipe_sel = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])
            
        with col3:
            # LIMPEZA REAL: Substitui a string '— nan' por uma opção nula limpa
            dict_viaturas = {"NENHUMA VIATURA (A PÉ / APOIO)": None}
            if not df_viaturas.empty:
                for _, row in df_viaturas.iterrows():
                    vtr_nome = str(row.get('nome_viatura', '')).replace("nan", "").strip()
                    vtr_placa = str(row.get('placa', '')).replace("nan", "").strip()
                    if vtr_nome or vtr_placa:
                        dict_viaturas[f"{vtr_nome} - {vtr_placa}".strip(" - ")] = int(row['id'])
            viatura_sel = st.selectbox("Defina a Viatura da Equipe", list(dict_viaturas.keys()))

        eh_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")
        btn_vincular = st.form_submit_button("➕ Vincular à Equipe")

        if btn_vincular:
            # Criação do payload com tipos puros nativos
            dados_membro = {
                "policial_id": int(dict_policiais[policial_sel]),
                "equipe": str(equipe_sel),
                "viatura_id": dict_viaturas[viatura_sel], # Envia int ou None (NULL nativo no Supabase)
                "eh_lider": bool(eh_lider)
            }
            
            # Inserção direta ignorando a linha 280 antiga
            try:
                client.table("equipes_operacoes").insert(dados_membro).execute()
                st.success(f"✅ {policial_sel} adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error("❌ Erro ao salvar dados no Supabase.")
                st.code(str(e))
else:
    st.warning("⚠️ Cadastre dados na tabela 'efetivo' antes de montar as equipes.")
