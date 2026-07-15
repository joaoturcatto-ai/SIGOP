"""
Camada de acesso ao banco de dados (Supabase) para o SIGOP.
Todas as páginas importam funções deste módulo em vez de falar
diretamente com o Supabase - isso deixa o código mais fácil de manter.
"""

import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """Cria (e reaproveita) o cliente do Supabase usando os Secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def fetch_table(table: str, order_by: str | None = None) -> pd.DataFrame:
    """Busca todos os registros de uma tabela e retorna como DataFrame."""
    client = get_client()
    query = client.table(table).select("*")
    if order_by:
        query = query.order(order_by)
    response = query.execute()
    data = response.data or []
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
    participantes = fetch_table("operacao_participantes")
    if not operacoes.empty and not participantes.empty:
        ops_do_dia = operacoes[pd.to_datetime(operacoes["data"]).dt.date == data_alvo]
        if not ops_do_dia.empty:
            ids_ops_do_dia = ops_do_dia["id"].tolist()
            conflito_op = participantes[
                (participantes["servidor_id"] == servidor_id)
                & (participantes["operacao_id"].isin(ids_ops_do_dia))
            ]
            if not conflito_op.empty:
                return False, "Servidor já está escalado em outra operação nesta data."

    return True, "Disponível"


def viatura_disponivel(viatura_id: int, data_alvo: date) -> tuple[bool, str]:
    """Verifica se uma viatura já está alocada em outra operação na mesma data."""
    operacoes = fetch_table("operacoes")
    participantes = fetch_table("operacao_participantes")
    if operacoes.empty or participantes.empty:
        return True, "Disponível"

    ops_do_dia = operacoes[pd.to_datetime(operacoes["data"]).dt.date == data_alvo]
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
