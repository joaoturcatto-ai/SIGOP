import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from utils.db import fetch_table

st.set_page_config(page_title="Gerar Documento - SIGOP", page_icon="📄", layout="wide")
st.title("📄 Gerar Ordem de Operação")
st.caption("Gera o documento oficial da operação em Word (.docx) ou PDF")

try:
    operacoes = fetch_table("operacoes", order_by="data")
    servidores = fetch_table("servidores")
    viaturas = fetch_table("viaturas")
    participantes = fetch_table("operacao_participantes")
except Exception as e:
    st.error("⚠️ Erro ao carregar dados.")
    st.code(str(e), language="python")
    st.stop()

if operacoes.empty:
    st.info("Cadastre uma operação primeiro na página 'Operações'.")
    st.stop()

operacao_id = st.selectbox(
    "Selecione a operação",
    options=operacoes["id"].tolist(),
    format_func=lambda x: operacoes[operacoes["id"] == x]["nome"].values[0],
)

dados_op = operacoes[operacoes["id"] == operacao_id].iloc[0]
participantes_op = participantes[participantes["operacao_id"] == operacao_id]

if not participantes_op.empty:
    equipe = participantes_op.merge(
        servidores[["id", "nome", "cargo"]], left_on="servidor_id", right_on="id", how="left"
    )
    if not viaturas.empty:
        equipe = equipe.merge(
            viaturas[["id", "identificacao"]],
            left_on="viatura_id",
            right_on="id",
            how="left",
            suffixes=("", "_vtr"),
        )
    else:
        equipe["identificacao"] = None
else:
    equipe = pd.DataFrame(columns=["nome", "cargo", "equipe", "identificacao"])

st.markdown("---")
st.subheader("Pré-visualização")
st.write(f"**Operação:** {dados_op['nome']}")
st.write(f"**Data:** {dados_op['data']} — **Horário:** {dados_op.get('horario', '—')}")
st.write(f"**Local:** {dados_op.get('local', '—')} — **Cidade:** {dados_op.get('cidade', '—')}")
st.write(f"**Delegado responsável:** {dados_op.get('delegado_responsavel', '—')}")
st.write("**Objetivo:**")
st.write(dados_op.get("objetivo") or "Não informado.")
st.write("**Briefing:**")
st.write(dados_op.get("briefing") or "Não informado.")
if not equipe.empty:
    st.write("**Equipe:**")
    st.dataframe(equipe[["nome", "cargo", "equipe", "identificacao"]], use_container_width=True)


def gerar_docx() -> BytesIO:
    doc = Document()

    titulo = doc.add_paragraph()
    run = titulo.add_run("POLÍCIA CIVIL DO ESTADO DE MATO GROSSO")
    run.bold = True
    run.font.size = Pt(14)
    titulo.alignment = 1

    subtitulo = doc.add_paragraph()
    run = subtitulo.add_run("Delegacia Especializada de Estelionato de Cuiabá/MT")
    run.font.size = Pt(11)
    subtitulo.alignment = 1

    doc.add_paragraph()
    nome_op = doc.add_paragraph()
    run = nome_op.add_run(f"ORDEM DE OPERAÇÃO — {dados_op['nome'].upper()}")
    run.bold = True
    run.font.size = Pt(13)
    nome_op.alignment = 1

    doc.add_paragraph()
    doc.add_paragraph(f"Data: {dados_op['data']}    Horário: {dados_op.get('horario', '—')}")
    doc.add_paragraph(f"Local: {dados_op.get('local', '—')}    Cidade: {dados_op.get('cidade', '—')}")
    doc.add_paragraph(f"Delegado responsável: {dados_op.get('delegado_responsavel', '—')}")

    doc.add_heading("Objetivo", level=2)
    doc.add_paragraph(dados_op.get("objetivo") or "Não informado.")

    doc.add_heading("Briefing", level=2)
    doc.add_paragraph(dados_op.get("briefing") or "Não informado.")

    doc.add_heading("Equipe", level=2)
    if not equipe.empty:
        tabela = doc.add_table(rows=1, cols=4)
        tabela.style = "Light Grid Accent 1"
        hdr = tabela.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = (
            "Nome", "Cargo", "Equipe", "Viatura"
        )
        for _, linha in equipe.iterrows():
            cells = tabela.add_row().cells
            cells[0].text = str(linha.get("nome", "") or "")
            cells[1].text = str(linha.get("cargo", "") or "")
            cells[2].text = str(linha.get("equipe", "") or "")
            cells[3].text = str(linha.get("identificacao", "") or "—")
    else:
        doc.add_paragraph("Nenhum servidor escalado.")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def gerar_pdf() -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>POLÍCIA CIVIL DO ESTADO DE MATO GROSSO</b>", styles["Title"]))
    elementos.append(Paragraph("Delegacia Especializada de Estelionato de Cuiabá/MT", styles["Normal"]))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"<b>ORDEM DE OPERAÇÃO — {dados_op['nome'].upper()}</b>", styles["Heading2"]))
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph(f"<b>Data:</b> {dados_op['data']} &nbsp;&nbsp; <b>Horário:</b> {dados_op.get('horario', '—')}", styles["Normal"]))
    elementos.append(Paragraph(f"<b>Local:</b> {dados_op.get('local', '—')} &nbsp;&nbsp; <b>Cidade:</b> {dados_op.get('cidade', '—')}", styles["Normal"]))
    elementos.append(Paragraph(f"<b>Delegado responsável:</b> {dados_op.get('delegado_responsavel', '—')}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>Objetivo</b>", styles["Heading3"]))
    elementos.append(Paragraph(dados_op.get("objetivo") or "Não informado.", styles["Normal"]))
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph("<b>Briefing</b>", styles["Heading3"]))
    elementos.append(Paragraph((dados_op.get("briefing") or "Não informado.").replace("\n", "<br/>"), styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>Equipe</b>", styles["Heading3"]))
    if not equipe.empty:
        tabela_dados = [["Nome", "Cargo", "Equipe", "Viatura"]]
        for _, linha in equipe.iterrows():
            tabela_dados.append(
                [
                    str(linha.get("nome", "") or ""),
                    str(linha.get("cargo", "") or ""),
                    str(linha.get("equipe", "") or ""),
                    str(linha.get("identificacao", "") or "—"),
                ]
            )
        tabela = Table(tabela_dados, hAlign="LEFT")
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            )
        )
        elementos.append(tabela)
    else:
        elementos.append(Paragraph("Nenhum servidor escalado.", styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer


st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("📝 Gerar documento Word (.docx)"):
        buffer = gerar_docx()
        st.download_button(
            "⬇️ Baixar Word",
            data=buffer,
            file_name=f"ordem_operacao_{dados_op['nome'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
with col2:
    if st.button("📄 Gerar documento PDF"):
        buffer = gerar_pdf()
        st.download_button(
            "⬇️ Baixar PDF",
            data=buffer,
            file_name=f"ordem_operacao_{dados_op['nome'].replace(' ', '_')}.pdf",
            mime="application/pdf",
        )
