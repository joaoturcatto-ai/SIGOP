import streamlit as st
import pandas as pd
from utils.db import client
from utils.auth import check_login

check_login()

# Configuração Padrão Institucional SIGOP 2.0
st.set_page_config(
    page_title="SIGOP 2.0 - Painel Integrado",
    page_icon="🚔",
    layout="wide"
)

# Estilização Visual Sóbria
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

st.markdown("<h5 style='text-align: center; color: grey; margin-bottom:-10px;'>POLÍCIA CIVIL DO ESTADO DE MATO GROSSO</h5>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; margin-bottom:-5px;'>DELEGACIA ESPECIALIZADA DE ESTELIONATO</h2>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-size: 42px; margin-top: 20px;'>SIGOP 2.0</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; color: #b89243;'>Sistema Integrado de Gestão Operacional Policial</p><br>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: st.markdown('<div class="kpi-card"><div class="kpi-number">02</div><div class="kpi-label">Operações em Andamento</div></div>', unsafe_allow_html=True)
with c2: st.markdown('<div class="kpi-card"><div class="kpi-number">05</div><div class="kpi-label">Operações Planejadas</div></div>', unsafe_allow_html=True)
with c3: st.markdown('<div class="kpi-card"><div class="kpi-number">14</div><div class="kpi-label">Policiais Empregados</div></div>', unsafe_allow_html=True)

st.markdown('<div class="footer">SIGOP 2.0 &nbsp;|&nbsp; <b>Desenvolvido por João T. Turcatto.</b></div>', unsafe_allow_html=True)
