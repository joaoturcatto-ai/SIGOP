import streamlit as st
import pandas as pd
from utils.db import client

st.set_page_config(page_title="Operações - SIGOP", page_icon="👥", layout="wide")
st.title("👥 Equipes e Efetivos")
st.markdown("---")

try:
    df_policiais = pd.DataFrame(client.table("efetivo").select("*").execute().data).fillna("")
    df_viaturas = pd.DataFrame(client.table("viaturas").select("*").execute().data).fillna("")
except Exception as e:
    st.error(f"Erro ao carregar dados operacionais base: {e}")
    st.stop()

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

with st.form("form_novo_membro_equipe"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dict_pol = {}
        for _, row in df_policiais.iterrows():
            if 'nome' in row and str(row['nome']).strip() and str(row['nome']).lower() != 'nan':
                cargo = f" ({row['cargo']})" if 'cargo' in row and str(row['cargo']).lower() != 'nan' else ""
                dict_pol[f"{str(row['nome']).upper()}{cargo}"] = int(row['id'])
        pol_sel = st.selectbox("Selecione o Policial", list(dict_pol.keys()) if dict_pol else ["Nenhum policial cadastrado"])

    with col2:
        eq_sel = st.selectbox("Escolha a Equipe", ["Equipe 01", "Equipe 02", "Equipe 03", "Equipe 04"])

    with col3:
        dict_vtr = {"NENHUMA VIATURA (A PÉ / APOIO)": None}
        for _, row in df_viaturas.iterrows():
            nome_vtr = str(row.get('nome_viatura', '')).replace("nan", "").strip()
            placa_vtr = str(row.get('placa', '')).replace("nan", "").strip()
            if nome_vtr or placa_vtr:
                dict_vtr[f"{nome_vtr} - {placa_vtr}".strip(" - ")] = int(row['id'])
        vtr_sel = st.selectbox("Defina a Viatura da Equipe", list(dict_vtr.keys()))

    eh_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")
    btn_vincular = st.form_submit_button("➕ Vincular à Equipe")

    if btn_vincular and dict_pol:
        dados_membro = {
            "policial_id": int(dict_pol[pol_sel]),
            "equipe": str(eq_sel),
            "viatura_id": dict_vtr[vtr_sel],
            "eh_lider": bool(eh_lider)
        }
        try:
            client.table("equipes_operacoes").insert(dados_membro).execute()
            st.success(f"✅ {pol_sel} alocado na {eq_sel}!")
            st.rerun()
        except Exception as e:
            st.error("❌ Ocorreu um erro ao salvar o registro no banco.")
            st.code(str(e))
