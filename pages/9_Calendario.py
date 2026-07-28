import streamlit as st
import pandas as pd
from datetime import timedelta
from streamlit_calendar import calendar
from utils.db import fetch_table
from utils.auth import check_login

check_login()

st.set_page_config(page_title="Calendário - SIGOP", page_icon="📆", layout="wide")
st.title("📆 Calendário Integrado")
st.caption("Operações, CQH e afastamentos, tudo num só lugar.")

try:
    operacoes = fetch_table("operacoes", order_by="data_inicio")
    servidores = fetch_table("servidores")
    cqh = fetch_table("cqh")
    afastamentos = fetch_table("afastamentos")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

mapa_servidores_cal = {row["id"]: row["nome"] for _, row in servidores.iterrows()} if not servidores.empty else {}

# Cores por tipo de evento
COR_OPERACAO = "#d32f2f"        # vermelho
COR_PLANTAO_EVENTO = "#7b1fa2"  # roxo
COR_CQH = "#2e7d32"             # verde
COR_FERIAS = "#f57c00"          # laranja
COR_FOLGA = "#0288d1"           # azul claro
COR_LICENCA = "#616161"         # cinza
COR_FOLGA_OPERACIONAL = "#00897b"  # verde-azulado

st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    mostrar_operacoes = st.checkbox("🎯🕐 Mostrar Operações/Plantões", value=True)
with col_f2:
    mostrar_cqh = st.checkbox("🛡️ Mostrar CQH (prontidão)", value=True)
with col_f3:
    mostrar_afastamentos = st.checkbox("🏖️ Mostrar Afastamentos", value=True)

st.caption(
    "🔴 Operação · 🟣 Plantão/Evento · 🟢 CQH · 🟠 Férias · 🔵 Folga · "
    "⚪ Licença · 🟦 Folga Operacional"
)

eventos = []

if mostrar_operacoes and not operacoes.empty:
    for _, op in operacoes.iterrows():
        if pd.isna(op.get("data_inicio")):
            continue
        data_ini = pd.to_datetime(op["data_inicio"]).date()
        data_fim = (
            pd.to_datetime(op["data_fim"]).date() if pd.notna(op.get("data_fim")) else data_ini
        )
        tipo = op.get("tipo") if pd.notna(op.get("tipo")) else "Operação"
        icone = "🕐" if tipo == "Plantão/Evento" else "🎯"
        cor = COR_PLANTAO_EVENTO if tipo == "Plantão/Evento" else COR_OPERACAO
        eventos.append(
            {
                "title": f"{icone} {op['nome']}",
                "start": str(data_ini),
                "end": str(data_fim + timedelta(days=1)),  # exclusivo no FullCalendar
                "color": cor,
                "allDay": True,
            }
        )

if mostrar_cqh and not cqh.empty:
    for _, linha in cqh.iterrows():
        if pd.isna(linha.get("data")):
            continue
        nome = mapa_servidores_cal.get(linha.get("servidor_id"), "Servidor")
        eventos.append(
            {
                "title": f"🛡️ CQH — {nome}",
                "start": str(pd.to_datetime(linha["data"]).date()),
                "color": COR_CQH,
                "allDay": True,
            }
        )

if mostrar_afastamentos and not afastamentos.empty:
    cor_por_tipo = {
        "Férias": COR_FERIAS,
        "Folga": COR_FOLGA,
        "Licença": COR_LICENCA,
        "Folga Operacional": COR_FOLGA_OPERACIONAL,
    }
    icone_por_tipo = {
        "Férias": "🟠",
        "Folga": "🔵",
        "Licença": "⚪",
        "Folga Operacional": "🟦",
    }
    for _, linha in afastamentos.iterrows():
        if pd.isna(linha.get("data_inicio")):
            continue
        nome = mapa_servidores_cal.get(linha.get("servidor_id"), "Servidor")
        tipo_af = linha.get("tipo") if pd.notna(linha.get("tipo")) else "Folga"
        data_ini = pd.to_datetime(linha["data_inicio"]).date()
        data_fim = (
            pd.to_datetime(linha["data_fim"]).date() if pd.notna(linha.get("data_fim")) else data_ini
        )
        eventos.append(
            {
                "title": f"{icone_por_tipo.get(tipo_af, '🏖️')} {tipo_af} — {nome}",
                "start": str(data_ini),
                "end": str(data_fim + timedelta(days=1)),
                "color": cor_por_tipo.get(tipo_af, COR_FOLGA),
                "allDay": True,
            }
        )

calendar_options = {
    "locale": "pt-br",
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,listMonth",
    },
    "height": 720,
    "firstDay": 0,
}

st.markdown("---")
resultado_calendario = calendar(
    events=eventos,
    options=calendar_options,
    key="calendario_sigop",
)

if resultado_calendario.get("eventClick"):
    evento_clicado = resultado_calendario["eventClick"]["event"]
    st.info(f"📌 **{evento_clicado['title']}** — {evento_clicado.get('start', '')}")
