"""
Autenticação simples do SIGOP.
Cada página do sistema deve chamar check_login() logo no início,
antes de mostrar qualquer conteúdo.
"""

import streamlit as st


def check_login():
    """Mostra uma tela de login e trava a página até o usuário
    digitar um usuário/senha válidos (configurados nos Secrets)."""

    if st.session_state.get("sigop_autenticado"):
        return

    st.set_page_config(page_title="SIGOP - Login", page_icon="🔒", layout="centered")
    st.title("🔒 SIGOP")
    st.caption("Sistema Integrado de Gerenciamento de Operações Policiais")
    st.markdown("---")

    with st.form("form_login_sigop"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            usuarios_validos = st.secrets.get("SIGOP_USERS", {})
            if not usuarios_validos:
                st.error(
                    "⚠️ Nenhum usuário configurado nos Secrets. "
                    "Adicione a seção [SIGOP_USERS] nas configurações do Streamlit Cloud."
                )
            elif usuario in usuarios_validos and str(usuarios_validos[usuario]) == senha:
                st.session_state["sigop_autenticado"] = True
                st.session_state["sigop_usuario"] = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    st.stop()


def fazer_logout():
    """Encerra a sessão do usuário atual."""
    st.session_state["sigop_autenticado"] = False
    st.session_state.pop("sigop_usuario", None)
    st.rerun()


def mostrar_usuario_logado():
    """Mostra, na barra lateral, quem está logado e um botão de sair."""
    usuario = st.session_state.get("sigop_usuario", "—")
    with st.sidebar:
        st.markdown("---")
        st.caption(f"👤 Logado como: **{usuario}**")
        if st.button("🚪 Sair", use_container_width=True):
            fazer_logout()
