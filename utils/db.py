"""
Camada de acesso ao banco de dados (Supabase) para o SIGOP.
Todas as páginas importam funções deste módulo em vez de falar
diretamente com o Supabase - isso deixa o código mais fácil de manter.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """Cria (e reaproveita) o cliente do Supabase usando os Secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# Colunas esperadas de cada tabela. Usado para que o DataFrame retornado
# por fetch_table() nunca fique "sem colunas" quando a tabela está vazia -
# isso evita KeyError ao filtrar (ex: participantes["operacao_id"] == x)
# em telas que ainda não têm nenhum registro cadastrado.
TABLE_COLUMNS = {
    "servidores": [
        "id", "nome", "matricula", "cargo", "equipe", "telefone",
        "situacao", "observacoes", "created_at",
    ],
    "viaturas": ["id", "identificacao", "modelo", "status", "placa_oficial", "placa_reservada", "created_at"],
    "operacoes": [
        "id", "nome", "tipo", "data_inicio", "data_fim", "horario", "horario_fim_previsto",
        "local", "cidade", "delegado_id", "delegado_responsavel",
        "objetivo", "briefing", "status", "created_at",
    ],
    "operacao_participantes": [
        "id", "operacao_id", "servidor_id", "equipe", "viatura_id",
        "folga_concedida", "created_at",
    ],
    "equipes_operacoes": [
        "id", "operacao_id", "servidor_id", "nome_equipe", "viatura_id",
        "is_lider", "possui_folga", "folga_data", "folga_duracao",
        "referencia_operacao", "created_at",
    ],
    "cqh": ["id", "data", "servidor_id", "equipe", "created_at"],
    "afastamentos": [
        "id", "servidor_id", "tipo", "data_inicio", "data_fim",
        "observacoes", "created_at",
    ],
}


def fetch_table(table: str, order_by: str | None = None) -> pd.DataFrame:
    """Busca todos os registros de uma tabela e retorna como DataFrame.

    Se a tabela estiver vazia, retorna um DataFrame vazio mas já com as
    colunas corretas, para que filtros como df["coluna"] não quebrem.
    """
    client = get_client()
    query = client.table(table).select("*")
    if order_by:
        query = query.order(order_by)
    response = query.execute()
    data = response.data or []
    if not data:
        return pd.DataFrame(columns=TABLE_COLUMNS.get(table, []))
    return pd.DataFrame(data)


def insert_row(table: str, row: dict) -> dict:
    """Insere um registro na tabela informada."""
    client = get_client()
    response = client.table(table).insert(row).execute()
    return response.data


def update_row(table: str, row_id: int, changes: dict) -> dict:
    """Atualiza um registro existente pelo id."""
    client = get_client()
    response = client.table(table).update(changes).eq("id", row_id).execute()
    return response.data


def delete_row(table: str, row_id: int) -> dict:
    """Remove um registro pelo id."""
    client = get_client()
    response = client.table(table).delete().eq("id", row_id).execute()
    return response.data


def servidor_disponivel(servidor_id: int, data_alvo: date) -> tuple[bool, str]:
    """
    Verifica se um servidor está disponível em uma data específica,
    checando afastamentos, CQH e operações já agendadas.
    Retorna (disponivel: bool, motivo: str).
    """
    afastamentos = fetch_table("afastamentos")
    if not afastamentos.empty:
        conflito = afastamentos[
            (afastamentos["servidor_id"] == servidor_id)
            & (pd.to_datetime(afastamentos["data_inicio"]).dt.date <= data_alvo)
            & (pd.to_datetime(afastamentos["data_fim"]).dt.date >= data_alvo)
        ]
        if not conflito.empty:
            tipo = conflito.iloc[0]["tipo"]
            return False, f"Servidor está com {tipo} nesta data."

    cqh = fetch_table("cqh")
    if not cqh.empty:
        conflito_cqh = cqh[
            (cqh["servidor_id"] == servidor_id)
            & (pd.to_datetime(cqh["data"]).dt.date == data_alvo)
        ]
        if not conflito_cqh.empty:
            return False, "Servidor já está escalado no CQH nesta data."

    operacoes = fetch_table("operacoes")
    participantes = fetch_table("equipes_operacoes")
    if not operacoes.empty and not participantes.empty:
        data_fim_op = pd.to_datetime(operacoes["data_fim"]).dt.date
        tem_horario_fim = (
            operacoes["horario_fim_previsto"].notna()
            if "horario_fim_previsto" in operacoes.columns
            else pd.Series(False, index=operacoes.index)
        )
        # Se a operação tem horário de término previsto definido, entendemos que
        # ela termina de madrugada e o último dia (data_fim) não bloqueia a
        # pessoa/viatura para outros compromissos nesse mesmo dia.
        data_fim_efetiva = data_fim_op.where(~tem_horario_fim, data_fim_op - timedelta(days=1))

        ops_do_dia = operacoes[
            (pd.to_datetime(operacoes["data_inicio"]).dt.date <= data_alvo)
            & (data_fim_efetiva >= data_alvo)
        ]
        if not ops_do_dia.empty:
            ids_ops_do_dia = ops_do_dia["id"].tolist()
            conflito_op = participantes[
                (participantes["servidor_id"] == servidor_id)
                & (participantes["operacao_id"].isin(ids_ops_do_dia))
            ]
            if not conflito_op.empty:
                return False, "Servidor já está escalado em outra operação nesta data."

    return True, "Disponível"


def servidor_disponivel_periodo(
    servidor_id: int, data_inicio: date, data_fim: date
) -> tuple[bool, str]:
    """Verifica disponibilidade do servidor em todos os dias de um período."""
    dia = data_inicio
    while dia <= data_fim:
        disponivel, motivo = servidor_disponivel(servidor_id, dia)
        if not disponivel:
            return False, f"{motivo} (dia {dia})"
        dia += timedelta(days=1)
    return True, "Disponível"


def viatura_disponivel(
    viatura_id: int,
    data_alvo: date,
    operacao_atual_id: int | None = None,
    nome_equipe_atual: str | None = None,
) -> tuple[bool, str]:
    """Verifica se uma viatura já está alocada em outra operação na mesma data.

    Se operacao_atual_id e nome_equipe_atual forem informados, um uso da
    mesma viatura pela MESMA equipe dentro da MESMA operação não conta como
    conflito (é normal vários membros da mesma equipe usarem o mesmo carro).
    """
    operacoes = fetch_table("operacoes")
    participantes = fetch_table("equipes_operacoes")
    if operacoes.empty or participantes.empty:
        return True, "Disponível"

    ops_do_dia = operacoes[
        (pd.to_datetime(operacoes["data_inicio"]).dt.date <= data_alvo)
        & (
            pd.to_datetime(operacoes["data_fim"]).dt.date.where(
                operacoes["horario_fim_previsto"].isna()
                if "horario_fim_previsto" in operacoes.columns
                else pd.Series(True, index=operacoes.index),
                pd.to_datetime(operacoes["data_fim"]).dt.date - timedelta(days=1),
            )
            >= data_alvo
        )
    ]
    if ops_do_dia.empty:
        return True, "Disponível"

    ids_ops_do_dia = ops_do_dia["id"].tolist()
    conflito = participantes[
        (participantes["viatura_id"] == viatura_id)
        & (participantes["operacao_id"].isin(ids_ops_do_dia))
    ]

    if operacao_atual_id is not None and nome_equipe_atual is not None and not conflito.empty:
        conflito = conflito[
            ~(
                (conflito["operacao_id"] == operacao_atual_id)
                & (conflito["nome_equipe"] == nome_equipe_atual)
            )
        ]

    if not conflito.empty:
        return False, "Viatura já está escalada em outra operação/equipe nesta data."
    return True, "Disponível"


def viatura_disponivel_periodo(
    viatura_id: int,
    data_inicio: date,
    data_fim: date,
    operacao_atual_id: int | None = None,
    nome_equipe_atual: str | None = None,
) -> tuple[bool, str]:
    """Verifica disponibilidade da viatura em todos os dias de um período."""
    dia = data_inicio
    while dia <= data_fim:
        disponivel, motivo = viatura_disponivel(
            viatura_id, dia, operacao_atual_id, nome_equipe_atual
        )
        if not disponivel:
            return False, f"{motivo} (dia {dia})"
        dia += timedelta(days=1)
    return True, "Disponível"


# Cliente global, mantido por compatibilidade com páginas que fazem
# "from utils.db import client" em vez de chamar get_client() diretamente.
client = get_client()
