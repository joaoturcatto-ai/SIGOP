import streamlit as st
import pandas as pd
from utils.db import client

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade Visual SIGOP 2.0)
st.set_page_config(
    page_title="SIGOP 2.0 - Planejamento Operacional",
    page_icon="🚔",
    layout="wide"
)

# Injeção de Estilo Sóbrio (Azul Escuro, Branco e Dourado)
st.markdown("""
    <style>
        h1, h2, h3 { color: #b89243 !important; font-family: 'Helvetica Neue', sans-serif; }
        .kpi-card {
            background-color: #0a1931; padding: 20px; border-radius: 10px;
            border-left: 5px solid #b89243; color: white; text-align: center;
        }
        .kpi-number { font-size: 28px; font-weight: bold; }
        .kpi-label { font-size: 14px; color: #b89243; font-weight: 500; }
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0a1931;
            color: #afb1b6; text-align: center; padding: 8px; font-size: 12px;
            border-top: 2px solid #b89243; z-index: 100;
        }
    </style>
""", unsafe_allow_html=True)

# 2. MENU LATERAL TÁTICO
menu = st.sidebar.radio("Navegação Tática", ["Dashboard", "Módulo Operações (Adicionar à Equipe)"])

# ==========================================
# TELA 1: DASHBOARD INSTITUCIONAL
# ==========================================
if menu == "Dashboard":
    st.markdown("<h5 style='text-align: center; color: grey; margin-bottom:-10px;'>POLÍCIA CIVIL DO ESTADO DE MATO GROSSO</h5>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-bottom:-5px;'>DELEGACIA ESPECIALIZADA DE ESTELIONATO</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #666;'>CUIABÁ/MT</h4>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 42px; margin-top: 20px; margin-bottom: 0px;'>SIGOP 2.0</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic; color: #b89243;'>Sistema Integrado de Gestão Operacional Policial</p><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="kpi-card"><div class="kpi-number">02</div><div class="kpi-label">Operações em Andamento</div></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="kpi-card"><div class="kpi-number">05</div><div class="kpi-label">Operações Planejadas</div></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="kpi-card"><div class="kpi-number">14</div><div class="kpi-label">Policiais Empregados Hoje</div></div>', unsafe_allow_html=True)

# ==========================================
# TELA 2: MÓDULO OPERAÇÕES (CENTRALIZADO E FILTRADO)
# ==========================================
elif menu == "Módulo Operações (Adicionar à Equipe)":
    st.title("👥 Equipes e Efetivos")
    st.markdown("---")

    # Carrega dados diretamente pelo cliente oficial
    try:
        df_policiais = pd.DataFrame(client.table("efetivo").select("*").execute().data).fillna("")
        df_viaturas = pd.DataFrame(client.table("viaturas").select("*").execute().data).fillna("")
    except Exception as e:
        st.error(f"Erro ao acessar tabelas base do Supabase: {e}")
        st.stop()

    # Exibição de quem já está escalado
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
    st.subheader("➕ Adicionar Policial à Equipe")

    with st.form("form_insercao_app_principal"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dict_pol = {}
            for _, row in df_policiais.iterrows():
                if 'nome' in row and str(row['nome']).strip() and str(row['nome']).lower() != 'nan':
                    cargo = f" ({row['cargo']})" if 'cargo' in row and str(row['cargo']).lower() != 'nan' else ""
                    dict_pol[f"{str(row['nome']).upper()}{cargo}"] = int(row['id'])
            pol_sel = st.selectbox("Selecione o Policial", list(dict_pol.keys()))

        with col2:
            eq_sel = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])

        with col3:
            # LIMPEZA REAL: Remove strings físicas contendo 'nan'
            dict_vtr = {"NENHUMA VIATURA (A PÉ / APOIO)": None}
            for _, row in df_viaturas.iterrows():
                n = str(row.get('nome_viatura', '')).replace("nan", "").strip()
                p = str(row.get('placa', '')).replace("nan", "").strip()
                if n or p:
                    dict_vtr[f"{n} - {p}".strip(" - ")] = int(row['id'])
            vtr_sel = st.selectbox("Defina a Viatura da Equipe", list(dict_vtr.keys()))

        eh_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")
        btn_vincular = st.form_submit_button("➕ Vincular à Equipe")

        if btn_vincular:
            # Montagem estruturada forçando os tipos primitivos limpos
            dados_membro = {
                "policial_id": int(dict_pol[pol_sel]),
                "equipe": str(eq_sel),
                "viatura_id": dict_vtr[vtr_sel], # Mandará int ou None (NULL), nunca string 'nan'
                "eh_lider": bool(eh_lider)
            }

            try:
                # Inserção direta ignorando subarquivos
                client.table("equipes_operacoes").insert(dados_membro).execute()
                st.success(f"✅ {pol_sel} vinculado com sucesso à {eq_sel}!")
                st.rerun()
            except Exception as e:
                st.error("❌ Erro interno do Supabase ao processar a gravação.")
                st.code(str(e))

# Rodapé Fixo
st.markdown('<div class="footer">SIGOP 2.0 &nbsp;|&nbsp; <b>Desenvolvido por João T. Turcatto.</b></div>', unsafe_allow_html=True)
