import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.db import fetch_table

st.set_page_config(page_title="Dashboard - SIGOP", layout="wide")

st.title("🏠 Dashboard")

# --- CARGA DOS DADOS ---
df_servidores = fetch_table("servidores")
df_viaturas = fetch_table("viaturas")
df_operacoes = fetch_table("operacoes")
df_afastamentos = fetch_table("afastamentos")
df_equipes_ops = fetch_table("equipes_operacoes")

# Mapeamentos auxiliares para o PDF e exibição
mapa_servidores = {row["id"]: f"{row['nome']} ({row['cargo']})" for _, row in df_servidores.iterrows()} if not df_servidores.empty else {}
mapa_viaturas = {row["id"]: f"{row['identificacao']} — {row.get('placa_oficial') or row.get('placa_reservada') or 'Sem Placa'}" for _, row in df_viaturas.iterrows()} if not df_viaturas.empty else {}

# Métricas rápidas (Cards superiores)
total_servidores = len(df_servidores) if not df_servidores.empty else 0
total_viaturas = len(df_viaturas) if not df_viaturas.empty else 0
ops_planejadas = len(df_operacoes[df_operacoes["status"] == "Planejada"]) if not df_operacoes.empty else 0

hoje_str = date.today().isoformat()
afastados_hoje = 0
if not df_afastamentos.empty:
    afastados_hoje = len(df_afastamentos[
        (df_afastamentos["data_inicio"] <= hoje_str) & 
        (df_afastamentos["data_fim"] >= hoje_str)
    ])

# Exibição dos cards de métricas
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("👮 Total de servidores", total_servidores)
col_m2.metric("🚓 Viaturas cadastradas", total_viaturas)
col_m3.metric("🚨 Operações planejadas", ops_planejadas)
col_m4.metric("🌴 Afastamentos ativos hoje", afastados_hoje)

st.markdown("---")

# --- SEÇÃO DO MEIO (CQH & PRÓXIMAS OPERAÇÕES) ---
col_esquerda, col_direita = st.columns([1, 1.2])

with col_esquerda:
    st.subheader("🗓️ Escala de CQH de hoje")
    # CQH Placeholder conforme imagem
    st.info("Nenhum dado de CQH cadastrado ainda.")

with col_direita:
    st.subheader("🚨 Próximas operações")
    
    # Filtrando as próximas operações a partir de hoje
    df_proximas = pd.DataFrame()
    if not df_operacoes.empty:
        df_operacoes["data_inicio_parsed"] = pd.to_datetime(df_operacoes["data_inicio"]).dt.date
        df_proximas = df_operacoes[df_operacoes["data_inicio_parsed"] >= date.today()].sort_values("data_inicio_parsed")
    
    if df_proximas.empty:
        st.info("Nenhuma operação agendada para os próximos dias.")
    else:
        # Loop para gerar os cartões interativos de cada próxima operação
        for _, op in df_proximas.iterrows():
            id_op = op["id"]
            nome_op = op["nome"]
            data_ini = pd.to_datetime(op["data_inicio"]).strftime("%d/%m/%Y")
            horario = op.get("horario", "Sem horário")
            local = op.get("local", "Não definido")
            
            # Container visual para cada operação
            with st.container(border=True):
                col_info, col_botoes = st.columns([2.5, 1.5])
                
                with col_info:
                    st.markdown(f"##### **{nome_op}**")
                    st.markdown(f"📅 **Data/Hora:** {data_ini} às {horario} | 📍 **Local:** {local}")
                    
                with col_botoes:
                    btn_col1, btn_col2 = st.columns(2)
                    
                    # Botão 1: Ir para a Edição (Apenas 1 clique)
                    with btn_col1:
                        if st.button("✏️ Editar", key=f"edit_dashboard_{id_op}", use_container_width=True):
                            st.session_state["id_op_selecionada"] = id_op  # Salva a seleção no estado
                            # Redireciona para a página correspondente (ajuste o nome do arquivo se necessário)
                            try:
                                st.switch_page("pages/3_Operacoes.py")
                            except Exception:
                                st.switch_page("pages/Operacoes.py")
                    
                    # Botão 2: Gerar PDF/Ordem de Serviço na hora
                    with btn_col2:
                        # Usando toggle para abrir/fechar a prévia do PDF logo abaixo do card correspondente
                        gerar_pdf = st.toggle("📄 OS", key=f"pdf_dashboard_{id_op}")

                # Se o botão de OS for ativado, renderiza o documento de forma limpa abaixo do card
                if gerar_pdf:
                    st.markdown("---")
                    st.caption("🔍 Visualização da Ordem de Serviço da Operação")
                    
                    # Busca equipes vinculadas a esta operação específica
                    df_equipe_op = pd.DataFrame()
                    if not df_equipes_ops.empty:
                        df_equipe_op = df_equipes_ops[df_equipes_ops["operacao_id"] == id_op].copy()
                    
                    # Carrega Delegado Responsável
                    delegado_nome = mapa_servidores.get(op.get("delegado_id"), "Não informado")
                    
                    # Montagem da seção de equipes para o PDF
                    texto_equipes_pdf = ""
                    if not df_equipe_op.empty:
                        for eq_nome in sorted(df_equipe_op["nome_equipe"].unique()):
                            membros_eq = df_equipe_op[df_equipe_op["nome_equipe"] == eq_nome]
                            
                            lider_eq_membros = membros_eq[membros_eq.get("is_lider", False) == True]
                            lider_pdf_txt = "Não definido"
                            if not lider_eq_membros.empty:
                                lider_pdf_txt = mapa_servidores.get(lider_eq_membros.iloc[0]["servidor_id"], "Não encontrado")
                            
                            vtr_id_eq = None
                            for _, row_m in membros_eq.iterrows():
                                if pd.notna(row_m.get("viatura_id")):
                                    vtr_id_eq = row_m["viatura_id"]
                                    break
                            vtr_txt = mapa_viaturas.get(vtr_id_eq, "Sem Viatura")
                            
                            texto_equipes_pdf += f"\n👉 **{eq_nome}**\n"
                            texto_equipes_pdf += f"   • 👑 Líder: {lider_pdf_txt}\n"
                            texto_equipes_pdf += f"   • 🚗 Viatura: {vtr_txt}\n"
                            texto_equipes_pdf += f"   • Integrantes e Folgas:\n"
                            for _, row_m in membros_eq.iterrows():
                                funcao_marcador = " [LÍDER]" if row_m.get("is_lider", False) else ""
                                
                                if row_m.get("possui_folga", False) and row_m.get("folga_data"):
                                    datas_l = str(row_m["folga_data"]).split(",")
                                    datas_fmtd_l = [pd.to_datetime(d.strip()).strftime("%d/%m/%Y") for d in datas_l if d.strip()]
                                    folga_desc = f" (Folga {row_m.get('folga_duracao', 'Integral')} em: {', '.join(datas_fmtd_l)})"
                                else:
                                    folga_desc = " (Sem Folga)"
                                    
                                texto_equipes_pdf += f"     - {mapa_servidores.get(row_m['servidor_id'], 'Policial')}{funcao_marcador}{folga_desc}\n"
                    else:
                        texto_equipes_pdf = "Nenhuma equipe montada para esta operação."

                    # Template HTML da OS
                    html_content = f"""
                    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; background-color: white; color: black; border-radius: 5px; margin-bottom: 10px;">
                        <h2 style="text-align: center; margin-bottom: 5px; color: #1a365d;">ORDEM DE SERVIÇO OPERACIONAL</h2>
                        <h4 style="text-align: center; margin-top: 0; color: #4a5568;">SISTEMA INTEGRADO DE GESTÃO OPERACIONAL - SIGOP</h4>
                        <hr style="border: 1px solid #1a365d;">
                        
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                            <tr>
                                <td style="padding: 5px; font-weight: bold; width: 25%;">Operação:</td>
                                <td style="padding: 5px;">{nome_op}</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px; font-weight: bold;">Período:</td>
                                <td style="padding: 5px;">{data_ini} às {horario}</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px; font-weight: bold;">Local:</td>
                                <td style="padding: 5px;">{local}</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px; font-weight: bold;">Delegado Responsável:</td>
                                <td style="padding: 5px;">{delegado_nome}</td>
                            </tr>
                        </table>
                        
                        <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">1. OBJETIVO DA OPERAÇÃO</h4>
                        <p style="text-align: justify; white-space: pre-line;">{op.get("objetivo", "Não detalhado")}</p>
                        
                        <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">2. BRIEFING / INSTRUÇÕES GERAIS</h4>
                        <p style="text-align: justify; white-space: pre-line;">{op.get("briefing", "Não detalhado")}</p>
                        
                        <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">3. DISTRIBUIÇÃO DAS EQUIPES E FOLGAS SELECIONADAS</h4>
                        <p style="white-space: pre-line;">{texto_equipes_pdf}</p>
                        
                        <br><br>
                        <div style="text-align: center; margin-top: 30px;">
                            <p>__________________________________________________</p>
                            <p style="font-weight: bold; margin-top: 5px;">{delegado_nome}</p>
                            <p style="font-size: 12px; color: #718096;">Delegado de Polícia - Responsável Operacional</p>
                        </div>
                    </div>
                    """
                    st.html(html_content)
                    
                    # Botão inteligente para Impressão rápida
                    st.markdown(
                        """
                        <a href="javascript:window.print()" style="text-decoration: none;">
                            <button style="
                                background-color: #ff4b4b; 
                                color: white; 
                                padding: 8px 16px; 
                                border: none; 
                                border-radius: 4px; 
                                cursor: pointer; 
                                font-weight: bold;
                                font-size: 14px;
                                width: 100%;">
                                🖨️ Imprimir Ordem de Serviço / Salvar em PDF
                            </button>
                        </a>
                        """, 
                        unsafe_allow_html=True
                    )

st.markdown("---")

# --- SEÇÃO INFERIOR: SERVIDORES AFASTADOS HOJE ---
st.subheader("🏖️ Servidores afastados hoje")

df_afastados_exibicao = pd.DataFrame()
if not df_afastamentos.empty:
    # Filtra afastamentos que incluem a data de hoje
    df_hoje = df_afastamentos[
        (df_afastamentos["data_inicio"] <= hoje_str) & 
        (df_afastamentos["data_fim"] >= hoje_str)
    ].copy()
    
    if not df_hoje.empty:
        df_hoje["nome"] = df_hoje["servidor_id"].map(mapa_servidores)
        df_hoje["data_inicio"] = pd.to_datetime(df_hoje["data_inicio"]).dt.strftime("%d/%m/%Y")
        df_hoje["data_fim"] = pd.to_datetime(df_hoje["data_fim"]).dt.strftime("%d/%m/%Y")
        
        df_afastados_exibicao = df_hoje[["nome", "tipo", "data_inicio", "data_fim"]]
        df_afastados_exibicao.columns = ["Nome", "Tipo", "Data de Início", "Data de Fim"]

if df_afastados_exibicao.empty:
    st.info("Nenhum policial/servidor afastado na data de hoje.")
else:
    st.dataframe(df_afastados_exibicao, use_container_width=True, hide_index=True)
