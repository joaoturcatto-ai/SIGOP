import streamlit as st
from supabase import create_client, Client

# Configuração da página do Streamlit
st.set_page_config(page_title="Operações - SIGOP", layout="wide")

# 1. Conexão com o Supabase (garanta que as chaves estão configuradas no seu .env ou secrets)
@st.cache_resource
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
    st.stop()

# 2. Buscar delegados para preencher o campo de seleção (Dropdown)
@st.cache_data(ttl=60)
def buscar_delegados():
    try:
        # Busca os servidores que são delegados na tabela 'servidores'
        resposta = supabase.table("servidores").select("nome").eq("cargo", "DELEGADO").execute()
        # Retorna uma lista simples de nomes
        return [servidor["nome"] for servidor in resposta.data]
    except Exception:
        # Caso ocorra algum erro ou a tabela seja diferente, retorna uma lista padrão de teste
        return ["BRUNO MENDO PALMIRO", "MARLON RICHER", "VINICIUS", "Dra Eliane"]

lista_delegados = buscar_delegados()

# --- INTERFACE DO USUÁRIO (FORMULÁRIO) ---
st.title("📂 Cadastro de Operações")
st.markdown("Preencha os campos abaixo para registrar uma nova operação no sistema.")

# Formulário para envio dos dados
with st.form("form_operacao"):
    col1, col2 = st.columns(2)
    
    with col1:
        nome_operacao = st.text_input("Nome da Operação", placeholder="Ex: Operação Devastate 6ª fase")
        data_inicio = st.date_input("Data de Início")
        local = st.text_input("Local", placeholder="Ex: Delegacia de Estelionato")
        cidade = st.text_input("Cidade", placeholder="Ex: Cuiabá")
        
    with col2:
        # Seleção do Delegado Responsável
        delegado_selecionado = st.selectbox("Delegado Responsável", options=lista_delegados)
        horario = st.time_input("Horário")
        status = st.selectbox("Status", options=["Planejada", "Em Andamento", "Concluída", "Cancelada"])

    objetivo = st.text_area("Objetivo da Operação", placeholder="Descreva os objetivos principais...")
    briefing = st.text_area("Briefing / Instruções", placeholder="Diretrizes e detalhes estratégicos...")

    # Botão de envio dentro do formulário
    submetido = st.form_submit_button("💾 Criar Operação")

# 3. Processamento do envio e gravação no Supabase
if submetido:
    if not nome_operacao or not cidade:
        st.warning("⚠️ Por favor, preencha os campos obrigatórios (Nome da Operação e Cidade).")
    else:
        # Montagem dos dados exatamente como a tabela 'operacoes' espera no Supabase
        dados_operacao = {
            "nome": nome_operacao,
            "data_inicio": str(data_inicio),
            "horario": str(horario),
            "local": local,
            "cidade": cidade,
            "delegado_responsavel": delegado_selecionado,  # <--- CORRIGIDO: Nome exato da coluna no Supabase
            "objetivo": objetivo,
            "status": status
            # Se você possuir a coluna briefing no banco, pode descomentar a linha abaixo:
            # "briefing": briefing 
        }

        try:
            # Inserção segura no banco de dados
            resposta = supabase.table("operacoes").insert(dados_operacao).execute()
            
            # Se deu certo, exibe mensagem de sucesso
            st.success("🎉 Operação salva com sucesso no sistema!")
            st.balloons()
            
        except Exception as erro:
            st.error(f"Erro ao inserir dados na tabela operacoes: {erro}")
            st.error("❌ Erro ao salvar operação.")
