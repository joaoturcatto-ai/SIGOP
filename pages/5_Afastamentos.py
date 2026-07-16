import streamlit as st
import pandas as pd
from datetime import datetime, date
from functools import reduce
import operator
from utils.db import fetch_table, insert_row, update_row, delete_row

st.set_page_config(page_title="Afastamentos - SIGOP", layout="wide")

st.title("📅 Gestão de Afastamentos")
st.caption("Controle de férias, folgas, licenças e cursos do efetivo")

# Busca dados necessários do banco
df_afastamentos = fetch_table("afastamentos")
df_servidores = fetch_table("servidores")
df_equipes_ops = fetch_table("equipes_operacoes")

# Mapeia ID do servidor para o Nome correspondente
mapa_servidores = {}
if not df_servidores.empty:
    mapa_servidores = dict(zip(df_servidores["id"], df_servidores["nome"]))

# Lista de Tipos de Afastamento Padronizada
TIPOS_AFASTAMENTO = [
    "Férias",
    "Folga Operacional",
    "Licença Médica",
    "Licença Especial",
    "Curso / Qualificação",
    "Outros"
]

# --- PROCESSAMENTO E UNIFICAÇÃO DOS DADOS ---
linhas_unificadas = []

# 1. Processa Afastamentos Tradicionais
if not df_afastamentos.empty:
    for _, row in df_afastamentos.iterrows():
        linhas_unificadas.append({
            "id": row["id"],
            "origem": "afastamentos",  # Identificador de tabela
            "nome": mapa_servidores.get(row["servidor_id"], "Não cadastrado"),
            "tipo": row["tipo"],
            "data_inicio": pd.to_datetime(row["data_inicio"]).date(),
            "data_fim": pd.to_datetime(row["data_fim"]).date(),
            "observacoes": row["observacoes"] if pd.notna(row["observacoes"]) else ""
        })

# 2. Processa as Novas Folgas de Operações (com datas alternadas e referência)
if not df_equipes_ops.empty:
    df_folgas_ativas = df_equipes_ops[df_equipes_ops["possui_folga"] == True]
    
    for _, row in df_folgas_ativas.iterrows():
        serv_nome = mapa_servidores.get(row["servidor_id"], "Não cadastrado")
        ref_op = row.get("referencia_operacao") or "Operação não identificada"
        duracao = row.get("folga_duracao") or "Integral"
        
        # Extrai as datas alternadas gravadas (Ex: "2026-07-16,2026-07-18")
        datas_str = row.get("folga_data", "")
        if datas_str:
            lista_datas = [d.strip() for d in str(datas_str).split(",") if d.strip()]
            for data_individual in lista_datas:
                try:
                    data_parsed = pd.to_datetime(data_individual).date()
                    linhas_unificadas.append({
                        "id": row["id"],
                        "origem": "equipes_operacoes",  # Identificador de tabela
                        "nome": serv_nome,
                        "tipo": f"Folga Operacional ({duracao})",
                        "data_inicio": data_parsed,
                        "data_fim": data_parsed,  # Data única alternada
                        "observacoes": f"🌴 Folga vinculada à Operação: {ref_op}"
                    })
                except Exception:
                    continue

# Monta o DataFrame unificado
if linhas_unificadas:
    df_exibicao = pd.DataFrame(linhas_unificadas)
else:
    df_exibicao = pd.DataFrame(columns=["id", "origem", "nome", "tipo", "data_inicio", "data_fim", "observacoes"])

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
            
        # Aplicação dos filtros no DataFrame unificado
        df_filtrado = df_exibicao.copy()
        
        # Filtro 1: Cruzamento de Datas
        df_filtrado = df_filtrado[
            (df_filtrado["data_inicio"] <= data_filtro_fim) & 
            (df_filtrado["data_fim"] >= data_filtro_ini)
        ]
        
        # Filtro 2: Tipo de Afastamento (Suporta busca exata e parcial para Folgas Operacionais)
        if tipos_selecionados:
            condicoes = []
            for t in tipos_selecionados:
                if t == "Folga Operacional":
                    condicoes.append(df_filtrado["tipo"].str.contains("Folga Operacional", na=False))
                else:
                    condicoes.append(df_filtrado["tipo"] == t)
            if condicoes:
                df_filtrado = df_filtrado[reduce(operator.or_, condicoes)]
            
        st.write(f"**Resultados encontrados ({len(df_filtrado)}):**")
        
        # Exibe apenas as colunas amigáveis para o usuário
        df_visualizacao = df_filtrado[["nome", "tipo", "data_inicio", "data_fim", "observacoes"]].copy()
        df_visualizacao.columns = ["Policial / Servidor", "Tipo de Afastamento", "Data de Início", "Data de Fim", "Detalhes / Referência"]
        
        st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)
        
        # Seção para Exclusão Inteligente
        st.markdown("---")
        st.subheader("🗑️ Remover Afastamento / Folga")
        
        opcoes_remover = {}
        for _, row in df_filtrado.iterrows():
            if pd.notna(row['nome']):
                chave_composta = f"{row['origem']}_{row['id']}"
                
                if row["origem"] == "afastamentos":
                    opcoes_remover[chave_composta] = f"{row['nome']} — {row['tipo']} ({row['data_inicio'].strftime('%d/%m/%Y')} a {row['data_fim'].strftime('%d/%m/%Y')})"
                else:
                    # Informa que se trata de uma folga vinda de escala operacional
                    opcoes_remover[chave_composta] = f"⚠️ [Escala] {row['nome']} — {row['tipo']} em {row['data_inicio'].strftime('%d/%m/%Y')} ({row['observacoes']})"
        
        if opcoes_remover:
            id_remover_composto = st.selectbox(
                "Selecione o registro para remover:", 
                options=list(opcoes_remover.keys()), 
                format_func=lambda x: opcoes_remover[x]
            )
            btn_remover = st.button("🗑️ Confirmar Remoção")
            
            if btn_remover:
                origem_tabela, id_registro = id_remover_composto.split("_", 1)
                id_registro = int(id_registro)
                
                if origem_tabela == "afastamentos":
                    delete_row("afastamentos", id_registro)
                    st.success("✔️ Afastamento padrão removido com sucesso!")
                else:
                    # Limpa os campos de folga da escala da operação, permitindo desmarcar daqui
                    dados_limpeza = {
                        "possui_folga": False,
                        "folga_data": None,
                        "folga_duracao": None,
                        "referencia_operacao": None
                    }
                    update_row("equipes_operacoes", id_registro, dados_limpeza)
                    st.success("✔️ Folga operacional removida da escala de serviço!")
                
                st.rerun()
        else:
            st.info("Nenhum afastamento ou folga visível nos filtros acima para ser removido.")
            
    else:
        st.info("Nenhum afastamento ou folga cadastrada até o momento.")

# --- ABA 2: CADASTRAR NOVO AFASTAMENTO ---
with tab_cadastrar:
    st.subheader("Cadastrar Novo Afastamento")
    
    if df_servidores.empty:
        st.warning("⚠️ Você precisa cadastrar Servidores na aba 'Efetivo' antes de lançar um afastamento.")
    else:
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
