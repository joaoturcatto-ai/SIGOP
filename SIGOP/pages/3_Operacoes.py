import streamlit as st
import pandas as pd
from utils.db import insert_row, client, fetch_query

# 1. CONFIGURAÇÃO DA PÁGINA (Padrão SIGOP 2.0)
st.set_page_config(
    page_title="Módulo Operações - SIGOP 2.0",
    page_icon="🚔",
    layout="wide"
)

st.title("👥 Equipes e Efetivos")
st.markdown("---")

# 2. CARREGAMENTO DOS DADOS TRATANDO VALORES NULOS ('NAN')
def carregar_dados():
    try:
        # Busca efetivo policial ativos
        res_pol = client.table("efetivo").select("id, nome, cargo").execute()
        df_pol = pd.DataFrame(res_pol.data) if res_pol.data else pd.DataFrame()
        
        # Busca viaturas cadastradas
        res_vtr = client.table("viaturas").select("id, nome_viatura, placa").execute()
        df_vtr = pd.DataFrame(res_vtr.data) if res_vtr.data else pd.DataFrame()
        
        return df_pol, df_vtr
    except Exception as e:
        st.error(f"Erro ao conectar ao Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_policiais, df_viaturas = carregar_dados()

# 3. INTERFACE PRINCIPAL: EXIBIÇÃO DA LISTA ATUAL
st.subheader("📋 Equipes e Efetivos Escalados")
try:
    res_eq = client.table("equipes_operacoes").select("*").execute()
    if res_eq.data:
        st.dataframe(pd.DataFrame(res_eq.data), use_container_width=True)
    else:
        st.info("Nenhum policial escalado em equipe ainda.")
except:
    st.info("Nenhum policial escalado em equipe ainda.")

st.markdown("---")

# 4. FORMULÁRIO DE CADASTRO (ANTI-NAN E SEM DELEGADO_ID QUEBRADO)
st.subheader("➕ Adicionar Policial à Equipe")

if not df_policiais.empty:
    with st.form("form_vincular_membro"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Dropdown de Policiais
            dict_policiais = {f"{row['nome'].upper()} ({row.get('cargo', 'Policial')})": row['id'] for _, row in df_policiais.iterrows()}
            policial_sel = st.selectbox("Selecione o Policial", list(dict_policiais.keys()))
            
        with col2:
            # Escolha da Equipe
            equipe_sel = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])
            
        with col3:
            # Dropdown de Viaturas limpando qualquer resquício de 'nan' físico
            dict_viaturas = {}
            if not df_viaturas.empty:
                for _, row in df_viaturas.iterrows():
                    vtr_nome = str(row.get('nome_viatura', '')).replace("nan", "").strip()
                    vtr_placa = str(row.get('placa', '')).replace("nan", "").strip()
                    if vtr_nome or vtr_placa:
                        dict_viaturas[f"{vtr_nome} - {vtr_placa}".strip(" - ")] = row['id']
            
            dict_viaturas["NENHUMA VIATURA (A PÉ / APOIO)"] = None
            viatura_sel = st.selectbox("Defina a Viatura da Equipe", list(dict_viaturas.keys()))

        eh_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")
        btn_vincular = st.form_submit_button("➕ Vincular à Equipe")

        if btn_vincular:
            # Montagem estruturada do dicionário
            id_policial = dict_policiais[policial_sel]
            id_viatura = dict_viaturas[viatura_sel]
            
            dados_membro = {
                "policial_id": int(id_policial),
                "equipe": str(equipe_sel),
                "viatura_id": int(id_viatura) if id_viatura is not None else None,
                "eh_lider": bool(eh_lider)
            }
            
            # Executa o insert usando sua função nativa tratada contra o erro 280
            try:
                resultado_link = insert_row("equipes_operacoes", dados_membro)
                st.success(f"✅ {policial_sel} adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error("Erro ao inserir dados na tabela 'equipes_operacoes'.")
                st.code(str(e))
else:
    st.warning("Preencha a tabela de efetivos no Supabase para listar os policiais.")
