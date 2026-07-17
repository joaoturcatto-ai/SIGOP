import streamlit as st
import pandas as pd
from utils.db import client  # Importamos apenas o cliente de conexão padrão do seu Supabase

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade Visual SIGOP 2.0)
st.set_page_config(
    page_title="Módulo Operações - SIGOP 2.0",
    page_icon="🚔",
    layout="wide"
)

st.title("👥 Equipes e Efetivos")
st.markdown("---")

# 2. CARREGAMENTO DOS DADOS AUXILIARES (Limpando qualquer 'nan' na memória)
def carregar_dados_auxiliares():
    try:
        # Busca policiais
        res_pol = client.table("efetivo").select("*").execute()
        df_pol = pd.DataFrame(res_pol.data) if res_pol.data else pd.DataFrame()
        
        # Busca viaturas
        res_vtr = client.table("viaturas").select("*").execute()
        df_vtr = pd.DataFrame(res_vtr.data) if res_vtr.data else pd.DataFrame()
        
        return df_pol, df_vtr
    except Exception as e:
        st.error(f"Erro ao carregar tabelas base do Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_policiais, df_viaturas = carregar_dados_auxiliares()

# 3. EXIBIÇÃO DA LISTA ATUAL DE POLICIAIS ESCALADOS
st.subheader("📋 Equipes e Efetivos Escalados")
try:
    res_eq = client.table("equipes_operacoes").select("*").execute()
    if res_eq.data:
        df_exibir = pd.DataFrame(res_eq.data)
        st.dataframe(df_exibir, use_container_width=True)
    else:
        st.info("Nenhum policial escalado em equipe ainda.")
except Exception:
    st.info("Nenhum policial escalado em equipe ainda.")

st.markdown("---")

# 4. FORMULÁRIO DE CADASTRO (BLINDADO CONTRA 'NAN' E TIPAGEM INCORRETA)
st.subheader("➕ Adicionar Policial à Equipe")

if not df_policiais.empty:
    with st.form("form_vincular_membro", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtra nomes válidos e mapeia para seus respectivos IDs (int)
            dict_policiais = {}
            for _, row in df_policiais.iterrows():
                if 'nome' in row and str(row['nome']).strip() and str(row['nome']).lower() != 'nan':
                    cargo = f" ({row['cargo']})" if 'cargo' in row and str(row['cargo']).lower() != 'nan' else ""
                    label_pol = f"{str(row['nome']).upper()}{cargo}"
                    dict_policiais[label_pol] = int(row['id'])
            
            policial_sel = st.selectbox("Selecione o Policial", list(dict_policiais.keys()))
            
        with col2:
            equipe_sel = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])
            
        with col3:
            # Monta o dicionário de viaturas tratando campos textuais 'nan'
            dict_viaturas = {"NENHUMA VIATURA (A PÉ / APOIO)": None}
            if not df_viaturas.empty:
                for _, row in df_viaturas.iterrows():
                    vtr_nome = str(row.get('nome_viatura', '')).replace("nan", "").strip()
                    vtr_placa = str(row.get('placa', '')).replace("nan", "").strip()
                    if vtr_nome or vtr_placa:
                        label_vtr = f"{vtr_nome} - {vtr_placa}".strip(" - ")
                        dict_viaturas[label_vtr] = int(row['id'])
            
            viatura_sel = st.selectbox("Defina a Viatura da Equipe", list(dict_viaturas.keys()))

        eh_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")
        
        # Botão de Envio
        btn_vincular = st.form_submit_button("➕ Vincular à Equipe")

        if btn_vincular:
            # Resgata chaves mapeadas com tipagem forçada pura
            id_policial = dict_policiais[policial_sel]
            id_viatura = dict_viaturas[viatura_sel]
            
            # Montagem exata das chaves aceitas na tabela 'equipes_operacoes'
            dados_membro = {
                "policial_id": int(id_policial),
                "equipe": str(equipe_sel),
                "viatura_id": int(id_viatura) if id_viatura is not None else None,
                "eh_lider": bool(eh_lider)
            }
            
            # Execução Direta pelo Cliente Oficial para ignorar travas de arquivos externos
            try:
                query_insert = client.table("equipes_operacoes").insert(dados_membro).execute()
                
                # Sucesso na inserção
                st.success(f"✅ {policial_sel} inserido com sucesso na {equipe_sel}!")
                st.rerun()
                
            except Exception as error_supabase:
                st.error("❌ Ocorreu um erro ao salvar na tabela 'equipes_operacoes'.")
                st.info("Abaixo está a resposta exata do banco de dados para identificarmos se falta alguma coluna:")
                st.code(str(error_supabase), language="json")
else:
    st.warning("⚠️ A tabela 'efetivo' precisa conter registros no Supabase para listar os policiais.")
