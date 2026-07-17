import streamlit as st
import pandas as pd
from utils.db import insert_row, client # Mantendo a importação das suas funções base

# 1. CONFIGURAÇÃO DA PÁGINA INSTITUCIONAL
st.set_page_config(
    page_title="Módulo Operações - SIGOP 2.0",
    page_icon="🚔",
    layout="wide"
)

st.title("👥 Gestão de Equipes e Efetivos")
st.markdown("---")

# 2. CARREGAMENTO DOS DADOS COM TRATAMENTO DE ERROS CONTRA 'NAN'
@st.cache_data(ttl=10)
def carregar_dados_auxiliares():
    try:
        # Carrega policiais
        res_policiais = client.table("efetivo").select("*").execute()
        df_pol = pd.DataFrame(res_policiais.data).fillna("")
        
        # Carrega viaturas
        res_viaturas = client.table("viaturas").select("*").execute()
        df_vtr = pd.DataFrame(res_viaturas.data).fillna("")
        
        return df_pol, df_vtr
    except Exception as e:
        st.error("Erro ao carregar dados do Supabase. Verifique suas tabelas.")
        return pd.DataFrame(), pd.DataFrame()

df_policiais, df_viaturas = carregar_dados_auxiliares()

# 3. INTERFACE: EXIBIÇÃO DAS EQUIPES ATUAIS
st.subheader("📋 Equipes e Efetivos Escalados")

# Aqui você pode buscar as equipes já salvas para listar na tela
try:
    res_equipes = client.table("equipes_operacoes").select("*").execute()
    df_equipes_salvas = pd.DataFrame(res_equipes.data)
    
    if not df_equipes_salvas.empty:
        st.dataframe(df_equipes_salvas, use_container_width=True)
    else:
        st.info("Nenhum policial escalado em equipe ainda.")
except:
    st.info("Nenhum policial escalado em equipe ainda.")

st.markdown("---")

# 4. FORMULÁRIO: ADICIONAR POLICIAL À EQUIPE (BLINDADO)
st.subheader("➕ Adicionar Policial à Equipe")

if not df_policiais.empty and not df_viaturas.empty:
    with st.form("form_vincular_membro"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Monta lista de policiais sem IDs quebrados
            opcoes_policiais = {
                f"{row['nome'].upper()} ({row.get('cargo', 'Policial')})": row['id']
                for _, row in df_policiais.iterrows() if row['nome']
            }
            policial_selecionado = st.selectbox("Selecione o Policial", list(opcoes_policiais.keys()))
            
        with col2:
            equipe_selecionada = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])
            
        with col3:
            # SOLUÇÃO DO ERRO: Filtra e limpa o texto para NUNCA gerar "— nan"
            opcoes_viaturas = {}
            for _, row in df_viaturas.iterrows():
                nome_vtr = str(row.get('nome_viatura', '')).strip()
                placa_vtr = str(row.get('placa', '')).strip()
                
                # Se ambos estiverem vazios, ignora ou põe nome padrão
                if not nome_vtr and not placa_vtr:
                    continue
                    
                label_vtr = f"{nome_vtr} - {placa_vtr}".strip(" - ")
                opcoes_viaturas[label_vtr] = row['id']
            
            # Adiciona uma opção manual para caso de ir a pé ou sem VTR cadastrada
            opcoes_viaturas["NENHUMA VIATURA (A PÉ / APOIO)"] = None
            viatura_selecionada = st.selectbox("Defina a Viatura da Equipe", list(opcoes_viaturas.keys()))

        # Checkbox de Liderança
        eh_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")

        # Botão de Envio
        btn_vincular = st.form_submit_button("➕ Vincular à Equipe")

        if btn_vincular:
            # Resgata os IDs correspondentes do dicionário
            id_policial = opcoes_policiais[policial_selecionado]
            id_viatura = opcoes_viaturas[viatura_selecionada]
            
            # Monta o dicionário de inserção exatamente como o banco espera
            dados_membro = {
                "policial_id": int(id_policial),
                "equipe": str(equipe_selecionada),
                "viatura_id": int(id_viatura) if id_viatura is not None else None, # Envia NULL ao invés de NAN
                "eh_lider": bool(eh_lider)
            }
            
            # Executa a gravação na linha 280 tratada contra falhas de API
            try:
                response = client.table("equipes_operacoes").insert(dados_membro).execute()
                st.success(f"✅ {policial_selecionado} vinculado com sucesso à {equipe_selecionada}!")
                st.rerun() # Atualiza a tela para mostrar o novo membro na lista acima
            except Exception as e:
                st.error("❌ Erro de Integração com o Banco de Dados.")
                st.info("Verifique se as colunas da tabela 'equipes_operacoes' aceitam esses parâmetros.")
                with st.expander("Ver Detalhes Técnicos do Erro"):
                    st.code(str(e))
else:
    st.warning("⚠️ Certifique-se de que as tabelas 'efetivo' e 'viaturas' possuem dados cadastrados no Supabase.")
