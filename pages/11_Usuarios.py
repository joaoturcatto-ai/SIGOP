import streamlit as st
import pandas as pd
from utils.db import fetch_table, update_row, delete_row
from utils.auth import check_login, mostrar_usuario_logado, is_admin

check_login()

st.set_page_config(page_title="Usuários - SIGOP", page_icon="🔑", layout="wide")
mostrar_usuario_logado()

st.title("🔑 Gerenciar Usuários")
st.caption("Só administradores podem ver esta tela.")

if not is_admin():
    st.error("🚫 Você não tem permissão para acessar esta página (é somente para administradores).")
    st.stop()

try:
    usuarios_db = fetch_table("usuarios", order_by="usuario")
except Exception as e:
    st.error("⚠️ Erro ao carregar usuários.")
    st.code(str(e), language="python")
    st.stop()

st.subheader("👥 Contas criadas pelos próprios usuários")

if usuarios_db.empty:
    st.info("Ainda não há nenhuma conta criada pela aba 'Criar conta'.")
else:
    st.dataframe(
        usuarios_db[["id", "usuario", "papel", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("✏️ Alterar papel ou excluir uma conta")

    mapa_usuarios = {row["id"]: row["usuario"] for _, row in usuarios_db.iterrows()}
    usuario_selecionado_id = st.selectbox(
        "Selecione o usuário",
        options=list(mapa_usuarios.keys()),
        format_func=lambda x: mapa_usuarios[x],
    )

    dados_usuario = usuarios_db[usuarios_db["id"] == usuario_selecionado_id].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        novo_papel = st.selectbox(
            "Papel",
            options=["visualizador", "admin"],
            index=["visualizador", "admin"].index(dados_usuario["papel"]),
        )
        if st.button("💾 Salvar novo papel"):
            update_row("usuarios", int(usuario_selecionado_id), {"papel": novo_papel})
            st.success(f"Papel de '{dados_usuario['usuario']}' atualizado para '{novo_papel}'.")
            st.rerun()

    with col2:
        st.write("")
        st.write("")
        confirmar = st.checkbox(f"Confirmo que quero excluir '{dados_usuario['usuario']}'")
        if st.button("🗑️ Excluir esta conta", type="primary", disabled=not confirmar):
            delete_row("usuarios", int(usuario_selecionado_id))
            st.success(f"Conta '{dados_usuario['usuario']}' excluída.")
            st.rerun()

st.markdown("---")
st.subheader("🛠️ Contas de administrador configuradas nos Secrets")
usuarios_admin = st.secrets.get("SIGOP_USERS", {})
if usuarios_admin:
    st.write(", ".join(usuarios_admin.keys()))
    st.caption(
        "Essas contas não aparecem na lista acima porque não ficam no banco de dados — "
        "para remover uma delas, edite os Secrets do app no Streamlit Cloud."
    )
else:
    st.info("Nenhuma conta configurada nos Secrets ainda.")
