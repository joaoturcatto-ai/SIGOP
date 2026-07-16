import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.db import fetch_table, insert_row, delete_row

st.set_page_config(page_title="Afastamentos - SIGOP", layout="wide")

st.title("📅 Gestão de Afastamentos")
st.caption("Controle de férias, folgas, licenças e cursos do efetivo")

# Busca dados necessários do banco
df_afastamentos = fetch_table("afastamentos")
df_servidores = fetch_table("servidores")

# Mapeia ID do servidor para o Nome correspondente
mapa_servidores = {}
if not df_servidores.empty:
    mapa_servidores = dict(zip(df_servidores["id"], df_servidores["nome"]))

# Lista de Tipos de Afastamento Padronizada (incluindo Curso / Qualificação)
TIPOS_AFASTAMENTO = [
    "Férias",
    "Folga Operacional",
    "Licença Médica",
    "Licença Especial",
    "Curso / Qualificação",
    "Outros"
]

# Prepara DataFrame de exibição mesclando o nome do servidor
df_exibicao = pd.DataFrame()
if not df_afastamentos.empty:
    df_exibicao = df_afastamentos.copy()
    df_exibicao["nome"] = df_exibicao["servidor_id"].map(mapa_servidores)
    df_exibicao["data_inicio"] = pd.to_datetime(df_exibicao["data_inicio"]).dt.date
    df_exibicao["data_fim"] = pd.to_datetime(df_exibicao["data_fim"]).dt.date
    # Reordena colunas para exibição limpa
    df_exibicao = df_exibicao[["id", "nome", "tipo", "data_inicio", "data_fim", "observacoes"]]

# Criação de abas para organizar a tela
tab_listar, tab_cadastrar = st.tabs(["📋 Afastamentos Cadastrados", "➕ Novo Afastamento"])

# --- ABA 1: LISTAR E CONSULTAR AFASTAMENTOS ---
with tab_listar:
    if not df_exibicao.empty:
        st.subheader("🔍 Consultar Afastados por Período e Tipo")
        
        # Filtros interativos
        col_filtro1, col_filtro2, col_filtro3 = st.columns([1.5, 1.5, 2])
        
        with col_filtro1:
            data_filtro_ini = st.date_input("Afastado a partir de:", value=date.today())
        with col_filtro2:
            data_filtro_fim = st.date_input("Até o dia:", value=date.today() + pd.Timedelta(days=7))
        with col_filtro3:
            tipos_selecionados = st.multiselect("Filtrar por tipo:", options=TIPOS_AFASTAMENTO)
            
        # Aplicação dos filtros no DataFrame de exibição
        df_filtrado = df_exibicao.copy()
        
        # Filtro 1: Cruzamento de Datas (Afastamento ativo em qualquer ponto do intervalo selecionado)
        df_filtrado = df_filtrado[
            (df_filtrado["data_inicio"] <= data_filtro_fim) & 
            (df_filtrado["data_fim"] >= data_filtro_ini)
        ]
        
        # Filtro 2: Tipo de Afastamento
        if tipos_selecionados:
            df_filtrado = df_filtrado[df_filtrado["tipo"].isin(tipos_selecionados)]
            
        st.write(f"**Resultados encontrados ({len(df_filtrado)}):**")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        # Seção para Exclusão
        st.markdown("---")
        st.subheader("🗑️ Remover Afastamento")
        
        opcoes_remover = {
            row["id"]: f"{row['nome']} — {row['tipo']} ({row['data_inicio'].strftime('%d/%m/%Y')} a {row['data_fim'].strftime('%d/%m/%Y')})"
            for _, row in df_filtrado.iterrows() if pd.notna(row['nome'])
        }
        
        if opcoes_remover:
            id_remover = st.selectbox("Selecione o registro para remover:", options=list(opcoes_remover.keys()), format_func=lambda x: opcoes_remover[x])
            btn_remover = st.button("🗑️ Confirmar Remoção")
            
            if btn_remover:
                delete_row("afastamentos", id_remover)
                st.success("✔️ Afastamento removido com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum afastamento visível nos filtros acima para ser removido.")
            
    else:
        st.info("Nenhum afastamento cadastrado até o momento.")

# --- ABA 2: CADASTRAR NOVO AFASTAMENTO ---
with tab_cadastrar:
    st.subheader("Cadastrar Novo Afastamento")
    
    if df_servidores.empty:
        st.warning("⚠️ Você precisa cadastrar Servidores na aba 'Efetivo' antes de lançar um afastamento.")
    else:
        # Dicionário de servidores para o selectbox
        opcoes_servidores = {
            row["id"]: f"{row['nome']} ({row['cargo']})"
            for _, row in df_servidores.iterrows()
        }
        
        with st.form("form_novo_afastamento", clear_on_submit=True):
            col_cad1, col_cad2 = st.columns(2)
            
            with col_cad1:
                servidor_id = st.selectbox("Servidor", options=list(opcoes_servidores.keys()), format_func=lambda x: opcoes_servidores[x])
                tipo = st.selectbox("Tipo de Afastamento", options=TIPOS_AFASTAMENTO)
                observacoes = st.text_area("Observações / Detalhes", placeholder="Ex: Nome do curso, número de portaria, motivo, etc.")
                
            with col_cad2:
                data_inicio = st.date_input("Data de Início", value=date.today())
                data_fim = st.date_input("Data de Fim", value=date.today())
                
            btn_salvar = st.form_submit_button("💾 Salvar Afastamento")
            
            if btn_salvar:
                if data_inicio > data_fim:
                    st.error("⚠️ A 'Data de Início' não pode ser posterior à 'Data de Fim'!")
                else:
                    dados_afastamento = {
                        "servidor_id": int(servidor_id),
                        "tipo": tipo,
                        "data_inicio": data_inicio.isoformat(),
                        "data_fim": data_fim.isoformat(),
                        "observacoes": observacoes if observacoes.strip() else None
                    }
                    
                    resultado = insert_row("afastamentos", dados_afastamento)
                    if resultado:
                        st.success("✔️ Afastamento registrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Não foi possível salvar o afastamento no banco de dados.")
