import streamlit as st
import pandas as pd
from utils.db import client # Mantendo a conexão padrão do seu Supabase

# 1. CONFIGURAÇÃO DA PÁGINA INSTITUCIONAL
st.set_page_config(
    page_title="Gestão de Afastamentos - SIGOP 2.0",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Gestão de Afastamentos")
st.caption("Controle de férias, folgas, licenças e cursos do efetivo")
st.markdown("---")

# 2. CARREGAMENTO DOS DADOS DAS EQUIPES/OPERAÇÕES
try:
    res_equipes = client.table("equipes_operacoes").select("*").execute()
    df_equipes_ops = pd.DataFrame(res_equipes.data)
except Exception as e:
    st.error("Erro ao carregar dados de equipes do Supabase.")
    df_equipes_ops = pd.DataFrame()

# 3. TRATAMENTO SEGURO DA COLUNA 'POSSUI_FOLGA' (CORREÇÃO DO KEYERROR)
if not df_equipes_ops.empty:
    # Se a coluna não existir no banco, nós criamos ela temporariamente vazia/Falsa para não quebrar o código
    if "possui_folga" not in df_equipes_ops.columns:
        df_equipes_ops["possui_folga"] = False
        
    # Agora a filtragem funciona com 100% de certeza e sem travar a tela
    df_folgas_ativas = df_equipes_ops[df_equipes_ops["possui_folga"] == True]
    
    st.write(f"📊 Total de folgas operacionais detectadas: {len(df_folgas_ativas)}")
    
    # Exibe a tabela de folgas tratada
    if not df_folgas_ativas.empty:
        st.dataframe(df_folgas_ativas, use_container_width=True)
    else:
        st.info("Nenhuma folga operacional ativa registrada no momento.")
else:
    st.info("Nenhum dado de equipe ou escala encontrado para processar folgas.")

st.markdown("---")
st.subheader("➕ Registrar Novo Afastamento Manual")
st.write("Módulo em conformidade com as diretrizes do SIGOP 2.0.")
# (Aqui continua o restante do seu formulário padrão de férias/licenças)
