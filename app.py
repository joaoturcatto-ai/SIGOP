import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA & INJEÇÃO DE IDENTIDADE VISUAL (CSS)
st.set_page_config(
    page_title="SIGOP 2.0 - Planejamento Operacional",
    page_icon="🚔",
    layout="wide"
)

# Estilização baseada na paleta: Azul Escuro, Branco e Dourado Policial
st.markdown("""
    <style>
        /* Fundo e texto base */
        .reportview-container { background: #f4f6f9; }
        
        /* Títulos em Dourado / Amarelo Sóbrio */
        h1, h2, h3 { color: #b89243 !important; font-family: 'Helvetica Neue', sans-serif; }
        
        /* Cartões de Indicadores (KPIs) */
        .kpi-card {
            background-color: #0a1931;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #b89243;
            color: white;
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        .kpi-number { font-size: 28px; font-weight: bold; color: #fff; }
        .kpi-label { font-size: 14px; color: #b89243; font-weight: 500; }
        
        /* Rodapé Institucional */
        .footer {
            position: fixed;
            left: 0; bottom: 0; width: 100%;
            background-color: #0a1931;
            color: #afb1b6;
            text-align: center;
            padding: 8px;
            font-size: 12px;
            border-top: 2px solid #b89243;
            z-index: 100;
        }
    </style>
""", unsafe_allow_index=True)

# 2. CARREGAMENTO CONFIÁVEL DE DADOS (Preservando a Base Atual)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=st.secrets["CONNECTIONS_GSHEETS_SPREADSHEET"], ttl=0)
    df = df.dropna(how="all")
except Exception as e:
    st.error("⚠️ Falha na comunicação com o banco de dados das equipes.")
    st.stop()

# 3. NAVEGAÇÃO DO SIGOP 2.0
menu = st.sidebar.radio("Navegação Tática", ["Dashboard", "Módulo Operações", "Efetivo Integrado"])

# ==========================================
# TELA 1: DASHBOARD INSTITUCIONAL
# ==========================================
if menu == "Dashboard":
    # Cabeçalho Centralizado e Sóbrio
    st.markdown("<h5 style='text-align: center; color: grey; margin-bottom:-10px;'>POLÍCIA CIVIL DO ESTADO DE MATO GROSSO</h5>", unsafe_allow_index=True)
    st.markdown("<h2 style='text-align: center; margin-bottom:-5px;'>DELEGACIA ESPECIALIZADA DE ESTELIONATO</h2>", unsafe_allow_index=True)
    st.markdown("<h4 style='text-align: center; color: #666;'>CUIABÁ/MT</h4>", unsafe_allow_index=True)
    
    st.markdown("<h1 style='text-align: center; font-size: 42px; margin-top: 20px; margin-bottom: 0px;'>SIGOP 2.0</h1>", unsafe_allow_index=True)
    st.markdown("<p style='text-align: center; font-style: italic; color: #b89243;'>Sistema Integrado de Gestão Operacional Policial</p>", unsafe_allow_index=True)
    st.markdown("<br>", unsafe_allow_index=True)

    # Simulação dos Indicadores Operacionais Reais (Métricas Dinâmicas ou Estáticas de Pronto-Emprego)
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    with col1:
        st.markdown('<div class="kpi-card"><div class="kpi-number">02</div><div class="kpi-label">Operações em Andamento</div></div>', unsafe_allow_index=True)
    with col2:
        st.markdown('<div class="kpi-card"><div class="kpi-number">05</div><div class="kpi-label">Operações Planejadas</div></div>', unsafe_allow_index=True)
    with col3:
        st.markdown('<div class="kpi-card"><div class="kpi-number">14</div><div class="kpi-label">Policiais Empregados Hoje</div></div>', unsafe_allow_index=True)
    
    st.markdown("<br>", unsafe_allow_index=True)
    
    with col4:
        st.markdown('<div class="kpi-card"><div class="kpi-number">09</div><div class="kpi-label">Policiais Disponíveis</div></div>', unsafe_allow_index=True)
    with col5:
        st.markdown('<div class="kpi-card"><div class="kpi-number">04</div><div class="kpi-label">Viaturas Empregadas</div></div>', unsafe_allow_index=True)
    with col6:
        st.markdown('<div class="kpi-card"><div class="kpi-number">OK</div><div class="kpi-label">CQH do Dia</div></div>', unsafe_allow_index=True)

# ==========================================
# TELA 2: MÓDULO OPERAÇÕES (O CORAÇÃO DO SISTEMA)
# ==========================================
elif menu == "Módulo Operações":
    st.title("⚡ Planejamento Técnico de Operação")
    st.write("Monte a sua operação, associe alvos, defina as equipes e viaturas em uma única tela rápida.")

    with st.form("form_nova_operacao"):
        c1, c2 = st.columns(2)
        with c1:
            nome_op = st.text_input("Nome da Operação / Ordem de Serviço", placeholder="Ex: Operação Simbose")
            delegado_responsavel = st.selectbox("Delegado Presidente", ["Selecione...", "Dr. João Turcatto", "Delegado Adjunto 01"])
        with c2:
            cidade_alvo = st.text_input("🔍 Pesquisa por Cidade/Alvo", placeholder="Ex: Cuiabá, Várzea Grande...")
            data_op = st.date_input("Data Prevista")

        st.markdown("---")
        st.subheader("👥 Composição das Equipes & Meios Logísticos")
        
        # Seleção simplificada e direta sem tabelas acessórias confusas
        policiais_selecionados = st.multiselect("Selecione os Policiais da Operação", ["Investigador A", "Investigador B", "Investigador C", "Escrivão A"])
        viaturas_selecionadas = st.multiselect("Selecione as Viaturas Operacionais", ["VTR Palio 01 (Velada)", "VTR Triton 02 (Caracterizada)", "VTR Amarok 03"])
        
        detalhes_missao = st.text_area("Objetivo / Briefing da Missão", placeholder="Detalhamento sucinto do cumprimento dos mandados...")

        # Botão de submissão
        btn_gerar = st.form_submit_button("🚀 Consolidar Operação & Gerar Ordem")
        
        if btn_gerar:
            if nome_op and delegado_responsavel != "Selecione...":
                st.success(f"Operação '{nome_op}' montada com sucesso no plano operacional!")
                st.info("Pronto para impressão ou exportação tática.")
            else:
                st.error("Por favor, informe ao menos o Nome da Operação e o Delegado responsável.")

# ==========================================
# TELA 3: EFETIVO (PRESERVADO INTEGRAMENTE)
# ==========================================
elif menu == "Efetivo Integrado":
    st.title("🗃️ Gestão Base de Efetivo")
    st.write("Dados históricos consolidados de policiais ativos vinculados à planilha principal.")
    
    # Exibição bruta e segura da base que você já tem cadastrada
    st.dataframe(df, use_container_width=True)

# ==========================================
# RODAPÉ IMPRESCINDÍVEL & DISCRETO
# ==========================================
st.markdown("""
    <div class="footer">
        SIGOP – Sistema Integrado de Gestão Operacional Policial &nbsp;|&nbsp; 
        <b>Desenvolvido por João T. Turcatto.</b>
    </div>
""", unsafe_allow_index=True)
