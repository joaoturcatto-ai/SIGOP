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


# Colunas esperadas de cada tabela.
TABLE_COLUMNS = {
    "servidores": [
        "id", "nome", "matricula", "cargo", "equipe", "telefone",
        "situacao", "observacoes", "created_at",
    ],
    "viaturas": ["id", "identificacao", "modelo", "status", "tipo_placa", "created_at"],
    "operacoes": [
        "id", "nome", "data_inicio", "data_fim", "horario", "local", "cidade",
        "delegado_responsavel", "objetivo", "briefing", "status", "created_at",
    ],
    "operacao_participantes": [
        "id", "operacao_id", "servidor_id", "equipe", "viatura_id",
        "folga_concedida", "created_at",
    ],
    "cqh": ["id", "data", "servidor_id", "equipe", "created_at"],
    "afastamentos": [
        "id", "servidor_id", "tipo", "data_inicio", "data_fim",
        "observacoes", "created_at",
    ],
}


def fetch_table(table: str, order_by: str | None = None) -> pd.DataFrame:
    """Busca todos os registros de uma tabela e retorna como DataFrame."""
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
    """Verifica se um servidor está disponível em uma data específica."""
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
    participantes = fetch_table("operacao_participantes")
    if not operacoes.empty and not participantes.empty:
        ops_do_dia = operacoes[
            (pd.to_datetime(operacoes["data_inicio"]).dt.date <= data_alvo)
            & (pd.to_datetime(operacoes["data_fim"]).dt.date >= data_alvo)
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


def viatura_disponivel(viatura_id: int, data_alvo: date) -> tuple[bool, str]:
    """Verifica se uma viatura já está alocada em outra operação na mesma data."""
    operacoes = fetch_table("operacoes")
    participantes = fetch_table("operacao_participantes")
    if operacoes.empty or participantes.empty:
        return True, "Disponível"

    ops_do_dia = operacoes[
        (pd.to_datetime(operacoes["data_inicio"]).dt.date <= data_alvo)
        & (pd.to_datetime(operacoes["data_fim"]).dt.date >= data_alvo)
    ]
    if ops_do_dia.empty:
        return True, "Disponível"

    ids_ops_do_dia = ops_do_dia["id"].tolist()
    conflito = participantes[
        (participantes["viatura_id"] == viatura_id)
        & (participantes["operacao_id"].isin(ids_ops_do_dia))
    ]
    if not conflito.empty:
        return False, "Viatura já está escalada em outra operação nesta data."
    return True, "Disponível"


def viatura_disponivel_periodo(
    viatura_id: int, data_inicio: date, data_fim: date
) -> tuple[bool, str]:
    """Verifica disponibilidade da viatura em todos os dias de um período."""
    dia = data_inicio
    while dia <= data_fim:
        disponivel, motivo = viatura_disponivel(viatura_id, dia)
        if not disponivel:
            return False, f"{motivo} (dia {dia})"
        dia += timedelta(days=1)
    return True, "Disponível"
