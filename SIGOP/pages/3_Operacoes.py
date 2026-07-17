import streamlit as st
import pandas as pd
from utils.db import insert_row, client

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Módulo Operações - SIGOP 2.0",
    page_icon="🚔",
    layout="wide"
)

st.title("👥 Equipes e Efetivos")
st.markdown("---")

# 2. CARREGAMENTO DOS DADOS AUXILIARES
def carregar_dados_auxiliares():
    try:
        res_pol = client.table("efetivo").select("*").execute()
        df_pol = pd.DataFrame(res_pol.data) if res_pol.data else pd.DataFrame()
        
        res_vtr = client.table("viaturas").select("*").execute()
        df_vtr = pd.DataFrame(res_vtr.data) if res_vtr.data else pd.DataFrame()
        
        return df_pol, df_vtr
    except Exception as e:
        st.error(f"Erro ao carregar dados auxiliares: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_policiais, df_viaturas = carregar_dados_auxiliares()

# 3. EXIBIÇÃO DA LISTA ATUAL DE EQUIPES
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

# 4. FORMULÁRIO DE CADASTRO
st.subheader("➕ Adicionar Policial à Equipe")

if not df_policiais.empty:
    with st.form("form_vincular_membro"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dict_policiais = {f"{row['nome'].upper()}": row['id'] for _, row in df_policiais.iterrows() if 'nome' in row}
            policial_sel = st.selectbox("Selecione o Policial", list(dict_policiais.keys()))
            
        with col2:
            equipe_sel = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])
            
        with col3:
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
            id_policial = dict_policiais[policial_sel]
            id_viatura = dict_viaturas[viatura_sel]
            
            # Montagem do dicionário limpo
            dados_membro = {
                "policial_id": int(id_policial),
                "equipe": str(equipe_sel),
                "viatura_id": int(id_viatura) if id_viatura is not None else None,
                "eh_lider": bool(eh_lider)
            }
            
            # Executa o insert usando sua função estruturada (Linha 280)
            try:
                resultado_link = insert_row("equipes_operacoes", dados_membro)
                st.success(f"✅ {policial_sel} adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error("Erro ao inserir dados.")
                st.code(str(e))
else:
    st.warning("Verifique se a tabela 'efetivo' possui dados no Supabase.")
