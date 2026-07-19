import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from utils.db import (
    fetch_table,
    insert_row,
    update_row,
    delete_row,
    servidor_disponivel_periodo,
    viatura_disponivel_periodo,
)

st.set_page_config(page_title="Operações - SIGOP", layout="wide")

st.title("🎯 Gestão de Operações")


def formatar_datas_folga(raw):
    """Converte a string de datas separadas por vírgula em uma lista de datas
    formatadas (dd/mm/aaaa), ignorando qualquer valor inválido (nan, vazio, etc.)
    em vez de quebrar o app."""
    if not raw:
        return []
    datas_fmt = []
    for d in str(raw).split(","):
        d = d.strip()
        if not d or d.lower() in ("nan", "none", "nat"):
            continue
        dt = pd.to_datetime(d, errors="coerce")
        if pd.notna(dt):
            datas_fmt.append(dt.strftime("%d/%m/%Y"))
    return datas_fmt


def placa_disponivel(row):
    """Retorna a primeira placa válida (oficial ou reservada) sem nunca
    devolver o texto 'nan' quando o campo está vazio."""
    p_of = row.get("placa_oficial")
    if pd.notna(p_of) and str(p_of).strip():
        return str(p_of)
    p_res = row.get("placa_reservada")
    if pd.notna(p_res) and str(p_res).strip():
        return str(p_res)
    return "Sem Placa"


def filtrar_por_busca(mapa: dict, termo: str) -> dict:
    """Filtra um dicionário {id: rótulo} por um termo de busca.
    Aceita tanto substring do nome quanto as iniciais das palavras
    (ex: 'MDS' encontra 'MARCELO DE SOUZA')."""
    if not termo:
        return mapa
    termo_up = termo.strip().upper()
    resultado = {}
    for chave, rotulo in mapa.items():
        rotulo_up = str(rotulo).upper()
        nome_parte = rotulo_up.split(" (")[0]
        iniciais = "".join(p[0] for p in nome_parte.split() if p)
        if termo_up in rotulo_up or termo_up in iniciais:
            resultado[chave] = rotulo
    return resultado


# Carrega os dados necessários do banco
df_operacoes = fetch_table("operacoes", order_by="id")
df_servidores = fetch_table("servidores")
df_viaturas = fetch_table("viaturas")
df_equipes = fetch_table("equipes_operacoes")

# Mapeamentos de apoio
mapa_servidores = {row["id"]: f"{row['nome']} ({row['cargo']})" for _, row in df_servidores.iterrows()} if not df_servidores.empty else {}
mapa_viaturas = {row["id"]: f"{row['identificacao']} — {placa_disponivel(row)}" for _, row in df_viaturas.iterrows()} if not df_viaturas.empty else {}

# Abas principais
tab_gerenciar, tab_cadastrar = st.tabs(["⚙️ Gerenciar e Editar Operação", "➕ Cadastrar Nova Operação"])

# --- ABA 1: GERENCIAR, EDITAR E GERAR PDF ---
with tab_gerenciar:
    if df_operacoes.empty:
        st.info("Nenhuma operação cadastrada até o momento.")
    else:
        st.subheader("Selecione uma operação para ver detalhes / editar")

        opcoes_ops = {
            row["id"]: (
                f"#{row['id']} — {row['nome']} "
                f"({pd.to_datetime(row['data_inicio']).strftime('%d/%m/%Y') if row.get('data_inicio') else 'Sem data'})"
            )
            for _, row in df_operacoes.iterrows()
        }

        busca_op = st.text_input(
            "🔎 Buscar operação por nome ou iniciais (ou deixe em branco para ver todas)",
            key="busca_operacao",
        )
        opcoes_ops_filtradas = filtrar_por_busca(opcoes_ops, busca_op)
        if busca_op and not opcoes_ops_filtradas:
            st.warning("Nenhuma operação encontrada com esse termo.")
        opcoes_ops_exibir = opcoes_ops_filtradas if opcoes_ops_filtradas else opcoes_ops

        id_op_selecionada = st.selectbox(
            "Operações Cadastradas:",
            options=list(opcoes_ops_exibir.keys()),
            format_func=lambda x: opcoes_ops_exibir.get(x, opcoes_ops.get(x, str(x))),
            key="sel_operacao",
        )

        if id_op_selecionada:
            op_sel = df_operacoes[df_operacoes["id"] == id_op_selecionada].iloc[0]
            nome_operacao_atual = op_sel.get("nome", "Operação Sem Nome")

            # --- SEÇÃO 1: FORMULÁRIO DE EDIÇÃO GERAL ---
            st.markdown("### 📝 Editar Dados Gerais da Operação")

            data_inicio_raw = op_sel.get("data_inicio")
            data_fim_raw = op_sel.get("data_fim")
            data_ini_padrao = pd.to_datetime(data_inicio_raw).date() if pd.notna(data_inicio_raw) else None
            data_fim_padrao = pd.to_datetime(data_fim_raw).date() if pd.notna(data_fim_raw) else None

            hora_raw = op_sel.get("horario", "08:00:00")
            try:
                hora_padrao = datetime.strptime(str(hora_raw), "%H:%M:%S").time() if hora_raw else time(8, 0)
            except Exception:
                try:
                    hora_padrao = datetime.strptime(str(hora_raw), "%H:%M").time() if hora_raw else time(8, 0)
                except Exception:
                    hora_padrao = time(8, 0)

            delegados = df_servidores[df_servidores["cargo"].str.contains("Delegado", case=False, na=False)] if not df_servidores.empty else pd.DataFrame()
            mapa_del = {row["id"]: row["nome"] for _, row in delegados.iterrows()} if not delegados.empty else {}

            busca_del_edit = st.text_input(
                "🔎 Buscar delegado por nome ou iniciais (ex: 'BMP')", key="busca_del_edit"
            )
            mapa_del_edit_filtrado = filtrar_por_busca(mapa_del, busca_del_edit)
            if busca_del_edit and not mapa_del_edit_filtrado:
                st.warning("Nenhum delegado encontrado com esse termo.")
            opcoes_del_edit = mapa_del_edit_filtrado if mapa_del_edit_filtrado else mapa_del
            lista_del_id = list(opcoes_del_edit.keys())

            del_atual_id = op_sel.get("delegado_id")
            if pd.notna(del_atual_id) and int(del_atual_id) in lista_del_id:
                idx_del = lista_del_id.index(int(del_atual_id))
            else:
                idx_del = 0

            cidades_existentes = (
                sorted(df_operacoes["cidade"].dropna().unique().tolist())
                if not df_operacoes.empty and "cidade" in df_operacoes.columns
                else []
            )
            cidade_atual = str(op_sel.get("cidade", "") or "")
            busca_cidade_edit = st.text_input(
                "🔎 Buscar cidade já usada (ou deixe em branco para digitar uma nova abaixo)",
                key="busca_cidade_edit",
            )
            cidades_filtradas_edit = filtrar_por_busca(
                {c: c for c in cidades_existentes}, busca_cidade_edit
            )
            opcoes_cidade_edit = ["— Digitar nova cidade —"] + (
                list(cidades_filtradas_edit.values()) if busca_cidade_edit else cidades_existentes
            )
            idx_cidade_edit = (
                opcoes_cidade_edit.index(cidade_atual) if cidade_atual in opcoes_cidade_edit else 0
            )
            cidade_selecionada_edit = st.selectbox(
                "Cidade cadastrada", options=opcoes_cidade_edit, index=idx_cidade_edit, key="sel_cidade_edit"
            )

            with st.form("form_editar_operacao_dados"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_nome = st.text_input("Nome da Operação", value=str(op_sel.get("nome", "")))
                    edit_local = st.text_input("Local / Ponto de Encontro", value=str(op_sel.get("local", "")))
                    if cidade_selecionada_edit == "— Digitar nova cidade —":
                        edit_cidade = st.text_input("Digite a nova cidade", value=cidade_atual)
                    else:
                        edit_cidade = cidade_selecionada_edit

                    edit_delegado = st.selectbox("Delegado Responsável", options=lista_del_id, format_func=lambda x: opcoes_del_edit.get(x, "Não selecionado"), index=idx_del)

                with col2:
                    edit_data_ini = st.date_input("Data de Início (opcional)", value=data_ini_padrao)
                    edit_data_fim = st.date_input("Data de Fim (opcional)", value=data_fim_padrao)
                    edit_horario = st.time_input("Horário", value=hora_padrao)

                    status_atual = str(op_sel.get("status", "Planejada"))
                    lista_status = ["Planejada", "Em Andamento", "Concluída", "Cancelada"]
                    idx_status = lista_status.index(status_atual) if status_atual in lista_status else 0
                    edit_status = st.selectbox("Status da Operação", lista_status, index=idx_status)

                st.markdown("---")
                edit_objetivo = st.text_area("Objetivo da Operação", value=str(op_sel.get("objetivo", "") or ""))
                edit_briefing = st.text_area("Briefing / Instruções", value=str(op_sel.get("briefing", "") or ""))

                col_btn_op1, col_btn_op2, _ = st.columns([1.5, 1.5, 4])
                with col_btn_op1:
                    btn_salvar_dados = st.form_submit_button("💾 Salvar Alterações da Operação", use_container_width=True)
                with col_btn_op2:
                    btn_excluir_op = st.form_submit_button("🗑️ Excluir Operação", use_container_width=True)

                if btn_salvar_dados:
                    if not edit_nome:
                        st.error("⚠️ O Nome da Operação é obrigatório!")
                    else:
                        dados_atualizados = {
                            "nome": edit_nome,
                            "local": edit_local,
                            "cidade": edit_cidade,
                            "delegado_id": int(edit_delegado) if edit_delegado else None,
                            "data_inicio": edit_data_ini.isoformat() if edit_data_ini else None,
                            "data_fim": edit_data_fim.isoformat() if edit_data_fim else None,
                            "horario": edit_horario.strftime("%H:%M:%S"),
                            "status": edit_status,
                            "objetivo": edit_objetivo,
                            "briefing": edit_briefing
                        }
                        update_row("operacoes", id_op_selecionada, dados_atualizados)
                        st.toast("Operação atualizada!", icon="✔️")
                        st.rerun()

                if btn_excluir_op:
                    delete_row("operacoes", id_op_selecionada)
                    st.success("🗑️ Operação excluída com sucesso!")
                    st.rerun()

            st.markdown("---")

            # --- SEÇÃO ATUALIZADA: DATAS ALTERNADAS E REFERÊNCIA ---
            st.markdown("### 🌴 Configuração de Folga por Policial")

            df_equipe_op = pd.DataFrame()
            if not df_equipes.empty:
                df_equipe_op = df_equipes[df_equipes["operacao_id"] == id_op_selecionada].copy()

            if df_equipe_op.empty:
                st.info("Cadastre policiais em alguma equipe abaixo antes de definir as folgas individuais.")
            else:
                opcoes_policiais_folga = {
                    row["id"]: f"{mapa_servidores.get(row['servidor_id'], 'Policial')} ({row['nome_equipe']})"
                    for _, row in df_equipe_op.iterrows()
                }

                id_registro_selecionado = st.selectbox(
                    "Selecione o policial para definir/alterar a folga:",
                    options=list(opcoes_policiais_folga.keys()),
                    format_func=lambda x: opcoes_policiais_folga[x]
                )

                policial_sel_info = df_equipe_op[df_equipe_op["id"] == id_registro_selecionado].iloc[0]

                possui_folga_atual = bool(policial_sel_info.get("possui_folga", False))

                # Resgata as datas salvas anteriormente (se houver) para pré-selecionar no multiselect
                datas_salvas_str = policial_sel_info.get("folga_data", "")
                datas_padrao_list = []
                if datas_salvas_str:
                    datas_padrao_list = [
                        d.strip() for d in str(datas_salvas_str).split(",")
                        if d.strip() and d.strip().lower() not in ("nan", "none", "nat")
                    ]

                # Gera as datas possíveis com base no período da operação (ou dos próximos 30 dias se o período for inválido)
                hoje = date.today()
                op_start = data_ini_padrao if data_ini_padrao else hoje
                op_end = data_fim_padrao if data_fim_padrao else hoje + timedelta(days=15)

                # Cria a lista de opções de datas para o usuário clicar
                datas_disponiveis = []
                curr_d = op_start
                limit_d = max(op_end, op_start + timedelta(days=15)) # Garante pelo menos 15 dias de opções
                while curr_d <= limit_d:
                    datas_disponiveis.append(curr_d.strftime("%Y-%m-%d"))
                    curr_d += timedelta(days=1)

                duracoes_possiveis = ["Meio período (Matutino)", "Meio período (Vespertino)", "Integral"]
                duracao_atual = policial_sel_info.get("folga_duracao", "Integral")
                idx_duracao = duracoes_possiveis.index(duracao_atual) if duracao_atual in duracoes_possiveis else 2

                col_cf1, col_cf2, col_cf3 = st.columns([1.5, 3, 1.5])
                with col_cf1:
                    definir_possui_folga = st.checkbox("Este policial terá direito a folga?", value=possui_folga_atual, key=f"chk_{id_registro_selecionado}")
                with col_cf2:
                    # Multiselect para datas alternadas livres!
                    definir_folgas_selecionadas = st.multiselect(
                        "Selecione uma ou mais datas alternadas de folga:",
                        options=datas_disponiveis,
                        default=[d for d in datas_padrao_list if d in datas_disponiveis],
                        format_func=lambda x: pd.to_datetime(x).strftime("%d/%m/%Y"),
                        disabled=not definir_possui_folga,
                        key=f"multi_dt_{id_registro_selecionado}"
                    )
                with col_cf3:
                    definir_folga_duracao = st.selectbox("Período da folga", options=duracoes_possiveis, index=idx_duracao, disabled=not definir_possui_folga, key=f"dur_{id_registro_selecionado}")

                if st.button("💾 Salvar Folga do Policial Selecionado", type="primary"):
                    dados_folga_atualizar = {
                        "possui_folga": bool(definir_possui_folga),
                        "folga_data": ",".join(definir_folgas_selecionadas) if definir_possui_folga and definir_folgas_selecionadas else None,
                        "folga_duracao": definir_folga_duracao if definir_possui_folga else None,
                        "referencia_operacao": nome_operacao_atual if definir_possui_folga else None
                    }
                    update_row("equipes_operacoes", id_registro_selecionado, dados_folga_atualizar)

                    # --- Sincroniza com a tabela 'afastamentos' para que a folga  ---
                    # --- realmente bloqueie o servidor em outras escalas/CQH.     ---
                    tag_referencia = f"[ref:eq{id_registro_selecionado}]"
                    servidor_da_folga = int(policial_sel_info["servidor_id"])

                    afastamentos_existentes = fetch_table("afastamentos")
                    if not afastamentos_existentes.empty:
                        antigos = afastamentos_existentes[
                            afastamentos_existentes["observacoes"].astype(str).str.contains(
                                tag_referencia, regex=False, na=False
                            )
                        ]
                        for antigo_id in antigos["id"].tolist():
                            delete_row("afastamentos", antigo_id)

                    if definir_possui_folga and definir_folgas_selecionadas:
                        for data_folga_str in definir_folgas_selecionadas:
                            insert_row(
                                "afastamentos",
                                {
                                    "servidor_id": servidor_da_folga,
                                    "tipo": "Folga Operacional",
                                    "data_inicio": data_folga_str,
                                    "data_fim": data_folga_str,
                                    "observacoes": (
                                        f"Folga ({definir_folga_duracao}) referente à operação "
                                        f"'{nome_operacao_atual}'. {tag_referencia}"
                                    ),
                                },
                            )

                    st.toast(f"Folgas salvas para {mapa_servidores.get(policial_sel_info['servidor_id'])}!", icon="🌴")
                    st.rerun()

            st.markdown("---")

            # --- SEÇÃO 2: EQUIPES SEPARADAS E ESCALADAS ---
            st.markdown("### 👥 Equipes e Efetivos")

            equipes_existentes = [f"Equipe {i:02d}" for i in range(1, 21)]

            if not df_equipe_op.empty:
                for eq_nome in sorted(df_equipe_op["nome_equipe"].unique()):
                    membros_eq = df_equipe_op[df_equipe_op["nome_equipe"] == eq_nome]

                    membro_lider = membros_eq[membros_eq.get("is_lider", False) == True]
                    lider_txt = "Não definido"
                    if not membro_lider.empty:
                        lider_id = membro_lider.iloc[0]["servidor_id"]
                        lider_txt = mapa_servidores.get(lider_id, "Não encontrado")

                    vtr_id_eq = None
                    for _, row_m in membros_eq.iterrows():
                        if pd.notna(row_m.get("viatura_id")):
                            vtr_id_eq = row_m["viatura_id"]
                            break
                    vtr_txt = mapa_viaturas.get(vtr_id_eq, "Sem Viatura designada")

                    with st.container(border=True):
                        st.markdown(f"#### 🏷️ {eq_nome} — 👑 Líder: **{lider_txt}** — 🚗 Viatura: **{vtr_txt}**")

                        dados_membros_exibir = []
                        for _, row_m in membros_eq.iterrows():
                            cargo_funcao = "👑 LÍDER DE EQUIPE" if row_m.get("is_lider", False) else "Membro"

                            if row_m.get("possui_folga", False) and row_m.get("folga_data"):
                                datas_fmtd = formatar_datas_folga(row_m["folga_data"])
                                if datas_fmtd:
                                    status_folga = f"📅 {row_m.get('folga_duracao', 'Integral')} em: {', '.join(datas_fmtd)}"
                                else:
                                    status_folga = "❌ Sem folga registrada"
                            else:
                                status_folga = "❌ Sem folga registrada"

                            dados_membros_exibir.append({
                                "ID Registro": row_m["id"],
                                "Policial": mapa_servidores.get(row_m["servidor_id"], "Não encontrado"),
                                "Função na Equipe": cargo_funcao,
                                "Folga Programada": status_folga
                            })

                        df_eq_grid = pd.DataFrame(dados_membros_exibir)
                        st.dataframe(df_eq_grid, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum policial escalado em equipe ainda.")

            # Formulário para Adicionar Policial à Equipe
            st.markdown("#### ➕ Adicionar Policial à Equipe")
            if data_ini_padrao and data_fim_padrao:
                st.caption(
                    f"Período desta operação: {data_ini_padrao} até {data_fim_padrao}. "
                    "A disponibilidade do policial e da viatura será checada nesse período inteiro."
                )
            else:
                st.caption(
                    "⚠️ Esta operação não tem datas definidas — a checagem automática de "
                    "disponibilidade (conflitos de escala) não será aplicada."
                )

            busca_add_policial = st.text_input(
                "🔎 Buscar policial por nome ou iniciais (ex: 'MDS' para Marcelo De Souza)",
                key="busca_add_policial",
            )
            mapa_servidores_busca = filtrar_por_busca(mapa_servidores, busca_add_policial)
            if busca_add_policial and not mapa_servidores_busca:
                st.warning("Nenhum policial encontrado com esse termo de busca.")
            opcoes_policial_form = mapa_servidores_busca if mapa_servidores_busca else mapa_servidores

            with st.form("form_add_policial_equipe"):
                col_eq1, col_eq2, col_eq3 = st.columns(3)
                with col_eq1:
                    add_servidor = st.selectbox(
                        "Selecione o Policial",
                        options=list(opcoes_policial_form.keys()),
                        format_func=lambda x: opcoes_policial_form.get(x, mapa_servidores.get(x, "")),
                    )
                with col_eq2:
                    add_nome_equipe = st.selectbox("Escolha a Equipe", options=equipes_existentes)
                with col_eq3:
                    add_viatura = st.selectbox("Defina a Viatura da Equipe", options=[None] + list(mapa_viaturas.keys()), format_func=lambda x: "Nenhuma Viatura" if x is None else mapa_viaturas[x])

                add_is_lider = st.checkbox("👑 Definir este policial como Líder da Equipe selecionada")

                btn_confirmar_membro = st.form_submit_button("➕ Vincular à Equipe")

                if btn_confirmar_membro:
                    if data_ini_padrao and data_fim_padrao:
                        disponivel, motivo = servidor_disponivel_periodo(
                            int(add_servidor), data_ini_padrao, data_fim_padrao
                        )
                        viatura_ok = True
                        motivo_viatura = ""
                        if add_viatura is not None:
                            viatura_ok, motivo_viatura = viatura_disponivel_periodo(
                                int(add_viatura), data_ini_padrao, data_fim_padrao
                            )
                    else:
                        disponivel, motivo = True, ""
                        viatura_ok, motivo_viatura = True, ""

                    if not disponivel:
                        st.error(f"⚠️ Não é possível escalar este policial: {motivo}")
                    elif not viatura_ok:
                        st.error(f"⚠️ Não é possível usar esta viatura: {motivo_viatura}")
                    else:
                        if add_is_lider and not df_equipe_op.empty:
                            lideres_antigos = df_equipe_op[(df_equipe_op["nome_equipe"] == add_nome_equipe) & (df_equipe_op.get("is_lider", False) == True)]
                            for _, row_antigo in lideres_antigos.iterrows():
                                update_row("equipes_operacoes", row_antigo["id"], {"is_lider": False})

                        dados_membro = {
                            "operacao_id": int(id_op_selecionada),
                            "servidor_id": int(add_servidor),
                            "nome_equipe": add_nome_equipe,
                            "viatura_id": int(add_viatura) if add_viatura else None,
                            "is_lider": bool(add_is_lider),
                            "possui_folga": False,
                            "folga_data": None,
                            "folga_duracao": None,
                            "referencia_operacao": None
                        }

                        resultado_link = insert_row("equipes_operacoes", dados_membro)
                        if resultado_link:
                            st.toast("Policial adicionado! Configure a folga no painel acima.", icon="✔️")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao salvar integrante.")

            if not df_equipe_op.empty:
                with st.expander("🗑️ Remover Policial de uma Equipe"):
                    opcoes_remover = {
                        row["id"]: f"{mapa_servidores.get(row['servidor_id'], 'N/D')} — {row['nome_equipe']}"
                        for _, row in df_equipe_op.iterrows()
                    }
                    membro_remover_id = st.selectbox("Selecione o integrante para remover:", options=list(opcoes_remover.keys()), format_func=lambda x: opcoes_remover[x])
                    if st.button("❌ Confirmar Remoção da Equipe"):
                        tag_referencia = f"[ref:eq{membro_remover_id}]"
                        afastamentos_existentes = fetch_table("afastamentos")
                        if not afastamentos_existentes.empty:
                            antigos = afastamentos_existentes[
                                afastamentos_existentes["observacoes"].astype(str).str.contains(
                                    tag_referencia, regex=False, na=False
                                )
                            ]
                            for antigo_id in antigos["id"].tolist():
                                delete_row("afastamentos", antigo_id)

                        delete_row("equipes_operacoes", membro_remover_id)
                        st.toast("Integrante removido!", icon="🗑️")
                        st.rerun()

            st.markdown("---")

            # --- SEÇÃO 3: PDF DA ORDEM DE SERVIÇO ---
            st.markdown("### 📄 Relatório / Ordem de Serviço")

            nome_operacao = op_sel.get("nome", "Operação Sem Nome")
            cidade_op = op_sel.get("cidade", "N/D")
            local_op = op_sel.get("local", "N/D")
            data_ini_op = pd.to_datetime(op_sel.get("data_inicio")).strftime("%d/%m/%Y") if op_sel.get("data_inicio") else "N/D"
            data_fim_op = pd.to_datetime(op_sel.get("data_fim")).strftime("%d/%m/%Y") if op_sel.get("data_fim") else "N/D"
            horario_op = str(op_sel.get("horario", "N/D"))
            delegado_nome = mapa_servidores.get(op_sel.get("delegado_id"), "Não informado")
            objetivo_op = op_sel.get("objetivo", "Não detalhado")
            briefing_op = op_sel.get("briefing", "Não detalhado")

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
                            datas_fmtd_l = formatar_datas_folga(row_m["folga_data"])
                            if datas_fmtd_l:
                                folga_desc = f" (Folga {row_m.get('folga_duracao', 'Integral')} em: {', '.join(datas_fmtd_l)})"
                            else:
                                folga_desc = " (Sem Folga)"
                        else:
                            folga_desc = " (Sem Folga)"

                        texto_equipes_pdf += f"     - {mapa_servidores.get(row_m['servidor_id'], 'Policial')}{funcao_marcador}{folga_desc}\n"
            else:
                texto_equipes_pdf = "Nenhuma equipe montada para esta operação."

            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; background-color: white; color: black; border-radius: 5px;">
                <h2 style="text-align: center; margin-bottom: 5px; color: #1a365d;">ORDEM DE SERVIÇO OPERACIONAL</h2>
                <h4 style="text-align: center; margin-top: 0; color: #4a5568;">SISTEMA INTEGRADO DE GESTÃO OPERACIONAL - SIGOP</h4>
                <hr style="border: 1px solid #1a365d;">

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr>
                        <td style="padding: 5px; font-weight: bold; width: 25%;">Operação:</td>
                        <td style="padding: 5px;">{nome_operacao}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Período:</td>
                        <td style="padding: 5px;">{data_ini_op} até {data_fim_op} às {horario_op}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Local / Cidade:</td>
                        <td style="padding: 5px;">{local_op} — {cidade_op}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Delegado Responsável:</td>
                        <td style="padding: 5px;">{delegado_nome}</td>
                    </tr>
                </table>

                <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">1. OBJETIVO DA OPERAÇÃO</h4>
                <p style="text-align: justify; white-space: pre-line;">{objetivo_op}</p>

                <h4 style="color: #1a365d; border-bottom: 1px solid #ddd; padding-bottom: 5px;">2. BRIEFING / INSTRUÇÕES GERAIS</h4>
                <p style="text-align: justify; white-space: pre-line;">{briefing_op}</p>

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

            with st.expander("👁️ Visualizar Prévia do Documento"):
                st.html(html_content)

            st.markdown(
                f"""
                <a href="javascript:window.print()" style="text-decoration: none;">
                    <button style="
                        background-color: #ff4b4b;
                        color: white;
                        padding: 10px 24px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 16px;
                        width: 100%;">
                        🖨️ Imprimir Ordem de Serviço / Salvar em PDF
                    </button>
                </a>
                <p style="font-size: 11px; text-align: center; color: gray; margin-top: 5px;">
                    Utilize "Salvar como PDF" nas configurações de destino da sua impressora.
                </p>
                """,
                unsafe_allow_html=True
            )

# --- ABA 2: CADASTRAR NOVA OPERAÇÃO ---
with tab_cadastrar:
    st.subheader("Cadastrar Nova Operação")

    if "msg_operacao_criada" in st.session_state:
        msg = st.session_state.pop("msg_operacao_criada")
        st.success(msg["sucesso"])
        if msg.get("conflitos"):
            st.warning(
                "⚠️ Estes policiais NÃO foram escalados por conflito de agenda "
                "(já estavam ocupados nesta data em outro compromisso):\n\n"
                + "\n".join(f"- {a}" for a in msg["conflitos"])
            )

    delegados_novo = df_servidores[df_servidores["cargo"].str.contains("Delegado", case=False, na=False)] if not df_servidores.empty else pd.DataFrame()
    mapa_del_novo = {row["id"]: row["nome"] for _, row in delegados_novo.iterrows()} if not delegados_novo.empty else {}

    busca_del_novo = st.text_input(
        "🔎 Buscar delegado por nome ou iniciais", key="busca_del_novo"
    )
    mapa_del_novo_filtrado = filtrar_por_busca(mapa_del_novo, busca_del_novo)
    if busca_del_novo and not mapa_del_novo_filtrado:
        st.warning("Nenhum delegado encontrado com esse termo.")
    opcoes_del_novo = mapa_del_novo_filtrado if mapa_del_novo_filtrado else mapa_del_novo

    cidades_existentes_novo = (
        sorted(df_operacoes["cidade"].dropna().unique().tolist())
        if not df_operacoes.empty and "cidade" in df_operacoes.columns
        else []
    )
    busca_cidade_novo = st.text_input(
        "🔎 Buscar cidade já usada (ou deixe em branco para digitar uma nova abaixo)",
        key="busca_cidade_novo",
    )
    cidades_filtradas_novo = filtrar_por_busca(
        {c: c for c in cidades_existentes_novo}, busca_cidade_novo
    )
    opcoes_cidade_novo = ["— Digitar nova cidade —"] + (
        list(cidades_filtradas_novo.values()) if busca_cidade_novo else cidades_existentes_novo
    )
    cidade_selecionada_novo = st.selectbox(
        "Cidade cadastrada", options=opcoes_cidade_novo, key="sel_cidade_novo"
    )

    st.markdown("---")
    st.markdown("### 👥 Montar equipes já nesta etapa (opcional)")
    qtd_equipes_novo = st.number_input(
        "Quantas equipes você quer montar agora?",
        min_value=0, max_value=20, value=0, step=1,
        key="qtd_equipes_novo",
        help="Deixe 0 se preferir montar as equipes depois, na aba 'Gerenciar e Editar Operação'.",
    )

    with st.form("form_nova_operacao", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            cad_nome = st.text_input("Nome da Operação", placeholder="Ex: Operação Devastate")
            cad_local = st.text_input("Ponto de Encontro / Local", placeholder="Ex: Sede da Diretoria")
            if cidade_selecionada_novo == "— Digitar nova cidade —":
                cad_cidade = st.text_input("Digite a nova cidade", placeholder="Ex: Cuiabá")
            else:
                cad_cidade = cidade_selecionada_novo
                st.text_input("Cidade selecionada", value=cad_cidade, disabled=True)

            cad_delegado = st.selectbox(
                "Delegado Responsável",
                options=list(opcoes_del_novo.keys()),
                format_func=lambda x: opcoes_del_novo.get(x, mapa_del_novo.get(x, "Nenhum")),
            )

        with col_c2:
            cad_data_ini = st.date_input("Data de Início (opcional)", value=None)
            cad_data_fim = st.date_input("Data de Fim (opcional)", value=None)
            cad_horario = st.time_input("Horário", value=time(8, 0))
            cad_status = st.selectbox("Status", ["Planejada", "Em Andamento"])

        st.markdown("---")
        cad_objetivo = st.text_area("Objetivo da Operação")
        cad_briefing = st.text_area("Briefing / Instruções")

        equipes_form_data = []
        if qtd_equipes_novo > 0:
            st.markdown("---")
            st.markdown("#### 👥 Equipes desta operação")
            for i in range(1, int(qtd_equipes_novo) + 1):
                st.markdown(f"**Equipe {i:02d}**")
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    membros_eq_i = st.multiselect(
                        f"Policiais da Equipe {i:02d}",
                        options=list(mapa_servidores.keys()),
                        format_func=lambda x: mapa_servidores[x],
                        key=f"membros_eq_{i}",
                    )
                with col_e2:
                    lider_eq_i = st.selectbox(
                        f"Líder da Equipe {i:02d}",
                        options=[None] + list(mapa_servidores.keys()),
                        format_func=lambda x: "— Nenhum —" if x is None else mapa_servidores[x],
                        key=f"lider_eq_{i}",
                    )
                with col_e3:
                    viatura_eq_i = st.selectbox(
                        f"Viatura da Equipe {i:02d}",
                        options=[None] + list(mapa_viaturas.keys()),
                        format_func=lambda x: "— Nenhuma —" if x is None else mapa_viaturas[x],
                        key=f"viatura_eq_{i}",
                    )
                equipes_form_data.append({
                    "nome_equipe": f"Equipe {i:02d}",
                    "membros": membros_eq_i,
                    "lider": lider_eq_i,
                    "viatura": viatura_eq_i,
                })

        btn_cadastrar_op = st.form_submit_button("💾 Criar Operação")

        if btn_cadastrar_op:
            if not cad_nome:
                st.warning("⚠️ O nome da operação é obrigatório!")
            elif cad_data_ini and cad_data_fim and cad_data_fim < cad_data_ini:
                st.warning("⚠️ A data de fim não pode ser anterior à data de início.")
            else:
                dados_nova_op = {
                    "nome": cad_nome,
                    "local": cad_local,
                    "cidade": cad_cidade,
                    "delegado_id": int(cad_delegado) if cad_delegado else None,
                    "data_inicio": cad_data_ini.isoformat() if cad_data_ini else None,
                    "data_fim": cad_data_fim.isoformat() if cad_data_fim else None,
                    "horario": cad_horario.strftime("%H:%M:%S"),
                    "status": cad_status,
                    "objetivo": cad_objetivo,
                    "briefing": cad_briefing
                }
                res = insert_row("operacoes", dados_nova_op)
                if res:
                    nova_operacao_id = res[0]["id"]

                    avisos_conflito = []
                    total_inseridos = 0

                    for equipe_info in equipes_form_data:
                        membros_finais = set(equipe_info["membros"])
                        if equipe_info["lider"] is not None:
                            membros_finais.add(equipe_info["lider"])

                        for servidor_id_membro in membros_finais:
                            if cad_data_ini and cad_data_fim:
                                disponivel, motivo = servidor_disponivel_periodo(
                                    int(servidor_id_membro), cad_data_ini, cad_data_fim
                                )
                            else:
                                disponivel, motivo = True, ""

                            viatura_ok, motivo_viatura = True, ""
                            if equipe_info["viatura"] is not None and cad_data_ini and cad_data_fim:
                                viatura_ok, motivo_viatura = viatura_disponivel_periodo(
                                    int(equipe_info["viatura"]), cad_data_ini, cad_data_fim
                                )

                            if not disponivel:
                                avisos_conflito.append(
                                    f"{mapa_servidores.get(servidor_id_membro, servidor_id_membro)} "
                                    f"({equipe_info['nome_equipe']}): {motivo}"
                                )
                                continue
                            if not viatura_ok:
                                avisos_conflito.append(
                                    f"{mapa_servidores.get(servidor_id_membro, servidor_id_membro)} "
                                    f"({equipe_info['nome_equipe']}) — viatura indisponível: {motivo_viatura}"
                                )
                                continue

                            insert_row(
                                "equipes_operacoes",
                                {
                                    "operacao_id": int(nova_operacao_id),
                                    "servidor_id": int(servidor_id_membro),
                                    "nome_equipe": equipe_info["nome_equipe"],
                                    "viatura_id": int(equipe_info["viatura"]) if equipe_info["viatura"] else None,
                                    "is_lider": servidor_id_membro == equipe_info["lider"],
                                    "possui_folga": False,
                                    "folga_data": None,
                                    "folga_duracao": None,
                                    "referencia_operacao": None,
                                },
                            )
                            total_inseridos += 1

                    st.session_state["msg_operacao_criada"] = {
                        "sucesso": (
                            f"Operação '{cad_nome}' cadastrada com sucesso! "
                            f"{total_inseridos} policial(is) escalado(s) nas equipes."
                        ),
                        "conflitos": avisos_conflito,
                    }
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar operação.")
