import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.db import fetch_table
from utils.auth import check_login

check_login()

st.set_page_config(page_title="Pendências - SIGOP", page_icon="⚠️", layout="wide")
st.title("⚠️ Painel de Pendências")
st.caption("Coisas que merecem sua atenção — nada aqui bloqueia o sistema, é só um lembrete.")

try:
    servidores = fetch_table("servidores")
    operacoes = fetch_table("operacoes")
    equipes = fetch_table("equipes_operacoes")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

hoje = date.today()

# ------------------------------------------------------------------
# 🎂 ANIVERSARIANTES PRÓXIMOS
# ------------------------------------------------------------------
st.subheader("🎂 Aniversariantes dos próximos 30 dias")

if servidores.empty or "data_nascimento" not in servidores.columns:
    st.info("Nenhum servidor com data de nascimento cadastrada ainda.")
else:
    aniversariantes = []
    for _, srv in servidores.iterrows():
        nasc_raw = srv.get("data_nascimento")
        if pd.isna(nasc_raw):
            continue
        nasc = pd.to_datetime(nasc_raw).date()

        # Calcula o próximo aniversário (esse ano ou o ano que vem, se já passou)
        try:
            prox_aniversario = nasc.replace(year=hoje.year)
        except ValueError:
            # 29 de fevereiro em ano não bissexto -> usa 28/02
            prox_aniversario = nasc.replace(year=hoje.year, day=28)
        if prox_aniversario < hoje:
            try:
                prox_aniversario = nasc.replace(year=hoje.year + 1)
            except ValueError:
                prox_aniversario = nasc.replace(year=hoje.year + 1, day=28)

        dias_faltando = (prox_aniversario - hoje).days
        if 0 <= dias_faltando <= 30:
            idade_que_fara = prox_aniversario.year - nasc.year
            aniversariantes.append(
                {
                    "Nome": srv["nome"],
                    "Cargo": srv.get("cargo", ""),
                    "Data": prox_aniversario.strftime("%d/%m"),
                    "Faz anos": f"{idade_que_fara} anos",
                    "Faltam": "🎉 Hoje!" if dias_faltando == 0 else f"{dias_faltando} dia(s)",
                    "_ordem": dias_faltando,
                }
            )

    if aniversariantes:
        df_aniversariantes = pd.DataFrame(aniversariantes).sort_values("_ordem").drop(columns=["_ordem"])
        st.dataframe(df_aniversariantes, use_container_width=True, hide_index=True)
    else:
        st.success("Nenhum aniversário nos próximos 30 dias.")

st.markdown("---")

# ------------------------------------------------------------------
# 🌴 FOLGAS SEM DATA DEFINIDA
# ------------------------------------------------------------------
st.subheader("🌴 Folgas com direito confirmado mas sem data marcada")

if equipes.empty:
    st.info("Nenhuma equipe cadastrada ainda.")
else:
    mapa_servidores_pend = {row["id"]: row["nome"] for _, row in servidores.iterrows()} if not servidores.empty else {}
    mapa_operacoes_pend = {row["id"]: row["nome"] for _, row in operacoes.iterrows()} if not operacoes.empty else {}

    pendentes_folga = equipes[
        (equipes.get("possui_folga", False) == True)
        & (equipes["folga_data"].isna() | (equipes["folga_data"] == ""))
    ]

    if pendentes_folga.empty:
        st.success("Nenhuma folga pendente de data.")
    else:
        linhas_folga = []
        for _, linha in pendentes_folga.iterrows():
            sid = linha.get("servidor_id")
            nome = mapa_servidores_pend.get(sid, "—") if pd.notna(sid) else (linha.get("nome_externo") or "Externo")
            linhas_folga.append(
                {
                    "Nome": nome,
                    "Equipe": linha.get("nome_equipe", ""),
                    "Operação": mapa_operacoes_pend.get(linha.get("operacao_id"), "—"),
                    "Duração combinada": linha.get("folga_duracao") or "—",
                }
            )
        st.dataframe(pd.DataFrame(linhas_folga), use_container_width=True, hide_index=True)
        st.caption("Vá em Operações → Configuração de Folga por Policial para marcar a(s) data(s).")

st.markdown("---")

# ------------------------------------------------------------------
# 🚨 OPERAÇÕES SEM VIATURA OU SEM DELEGADO
# ------------------------------------------------------------------
st.subheader("🚨 Operações futuras sem viatura ou sem delegado definido")

if operacoes.empty:
    st.info("Nenhuma operação cadastrada ainda.")
else:
    futuras = operacoes[
        operacoes["data_fim"].isna()
        | (pd.to_datetime(operacoes["data_fim"], errors="coerce").dt.date >= hoje)
    ]

    sem_delegado = futuras[futuras["delegado_id"].isna()]
    if not equipes.empty:
        ops_com_viatura = set(equipes[equipes["viatura_id"].notna()]["operacao_id"].tolist())
    else:
        ops_com_viatura = set()
    sem_viatura = futuras[~futuras["id"].isin(ops_com_viatura)]

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write("**Sem delegado responsável:**")
        if sem_delegado.empty:
            st.success("Todas as operações futuras têm delegado definido.")
        else:
            st.dataframe(
                sem_delegado[["id", "nome", "data_inicio"]].rename(columns={"id": "#ID"}),
                use_container_width=True,
                hide_index=True,
            )
    with col_p2:
        st.write("**Sem nenhuma viatura escalada:**")
        if sem_viatura.empty:
            st.success("Todas as operações futuras têm ao menos uma viatura.")
        else:
            st.dataframe(
                sem_viatura[["id", "nome", "data_inicio"]].rename(columns={"id": "#ID"}),
                use_container_width=True,
                hide_index=True,
            )

st.markdown("---")

# ------------------------------------------------------------------
# 📉 SERVIDORES SEM OPERAÇÃO HÁ MUITO TEMPO
# ------------------------------------------------------------------
st.subheader("📉 Servidores sem nenhuma operação nos últimos 60 dias")

if servidores.empty:
    st.info("Nenhum servidor cadastrado ainda.")
else:
    limite = hoje - timedelta(days=60)

    if not equipes.empty and not operacoes.empty:
        equipes_com_data = equipes.merge(
            operacoes[["id", "data_inicio"]], left_on="operacao_id", right_on="id", how="left", suffixes=("", "_op")
        )
        recentes = equipes_com_data[
            pd.to_datetime(equipes_com_data["data_inicio"], errors="coerce").dt.date >= limite
        ]
        ids_escalados_recente = set(recentes["servidor_id"].dropna().tolist())
    else:
        ids_escalados_recente = set()

    servidores_parados = servidores[
        (servidores["situacao"] == "Ativo")
        & (~servidores["id"].isin(ids_escalados_recente))
        & (~servidores["equipe"].astype(str).str.contains("intelig", case=False, na=False))
    ]

    if servidores_parados.empty:
        st.success("Todo mundo ativo participou de alguma operação nos últimos 60 dias.")
    else:
        st.dataframe(
            servidores_parados[["nome", "cargo", "equipe"]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Núcleo de Inteligência já foi excluído dessa lista, por não entrar na rotação normal.")
