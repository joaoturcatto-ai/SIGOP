"""
Autenticação e controle de acesso simples do SIGOP.

Cada página do sistema deve chamar check_login() logo no início,
antes de mostrar qualquer conteúdo.

Existem dois papéis:
- "admin"        -> pode criar, editar e excluir tudo.
- "visualizador" -> só pode ver as telas, não pode alterar nada.

Contas criadas pela aba "Criar conta" (auto-cadastro) sempre nascem como
"visualizador" por segurança. Só um admin pode promover alguém a admin,
usando a tela "Usuários".

Contas configuradas nos Secrets (SIGOP_USERS) são sempre "admin".
"""

import streamlit as st
import hashlib
from utils.db import fetch_table, insert_row, update_row, delete_row


def _hash_senha(senha: str) -> str:
    """Gera um hash da senha — nunca guardamos a senha em texto puro."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def check_login():
    """Mostra uma tela de login/cadastro e trava a página até o usuário
    entrar com um usuário/senha válidos."""

    if st.session_state.get("sigop_autenticado"):
        return

    st.set_page_config(page_title="SIGOP - Login", page_icon="🔒", layout="centered")
    st.title("🔒 SIGOP")
    st.caption("Sistema Integrado de Gerenciamento de Operações Policiais")
    st.markdown("---")

    aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])

    with aba_entrar:
        with st.form("form_login_sigop"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

            if entrar:
                if not usuario or not senha:
                    st.error("Preencha usuário e senha.")
                else:
                    autenticado = False
                    papel = "visualizador"

                    usuarios_admin = st.secrets.get("SIGOP_USERS", {})
                    if usuario in usuarios_admin and str(usuarios_admin[usuario]) == senha:
                        autenticado = True
                        papel = "admin"

                    if not autenticado:
                        try:
                            usuarios_db = fetch_table("usuarios")
                        except Exception:
                            usuarios_db = None
                        if usuarios_db is not None and not usuarios_db.empty:
                            linha = usuarios_db[usuarios_db["usuario"] == usuario]
                            if not linha.empty and linha.iloc[0]["senha_hash"] == _hash_senha(senha):
                                autenticado = True
                                papel_bruto = linha.iloc[0].get("papel")
                                papel = papel_bruto if papel_bruto in ("admin", "visualizador") else "visualizador"

                    if autenticado:
                        st.session_state["sigop_autenticado"] = True
                        st.session_state["sigop_usuario"] = usuario
                        st.session_state["sigop_papel"] = papel
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

    with aba_criar:
        st.caption(
            "Crie seu usuário e senha para acessar o sistema. "
            "Toda conta nova começa como **somente visualização** — "
            "peça a um administrador para liberar edição, se precisar."
        )
        with st.form("form_criar_conta_sigop"):
            novo_usuario = st.text_input("Escolha um nome de usuário")
            nova_senha = st.text_input("Escolha uma senha", type="password")
            confirmar_senha = st.text_input("Confirme a senha", type="password")
            criar = st.form_submit_button("Criar conta", use_container_width=True)

            if criar:
                if not novo_usuario or not nova_senha:
                    st.error("Preencha usuário e senha.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem.")
                elif len(nova_senha) < 4:
                    st.error("A senha precisa ter pelo menos 4 caracteres.")
                else:
                    try:
                        usuarios_db = fetch_table("usuarios")
                    except Exception as e:
                        st.error("⚠️ Não foi possível acessar a tabela de usuários.")
                        st.code(str(e), language="python")
                        usuarios_db = None

                    usuarios_admin = st.secrets.get("SIGOP_USERS", {})
                    ja_existe = novo_usuario in usuarios_admin
                    if usuarios_db is not None and not usuarios_db.empty:
                        ja_existe = ja_existe or (usuarios_db["usuario"] == novo_usuario).any()

                    if ja_existe:
                        st.error("Esse nome de usuário já está em uso. Escolha outro.")
                    elif usuarios_db is not None:
                        insert_row(
                            "usuarios",
                            {
                                "usuario": novo_usuario,
                                "senha_hash": _hash_senha(nova_senha),
                                "papel": "visualizador",
                            },
                        )
                        st.success(
                            "✅ Conta criada! Vá na aba 'Entrar' para acessar "
                            "(seu acesso inicial é somente visualização)."
                        )

    st.stop()


def fazer_logout():
    """Encerra a sessão do usuário atual."""
    st.session_state["sigop_autenticado"] = False
    st.session_state.pop("sigop_usuario", None)
    st.session_state.pop("sigop_papel", None)
    st.rerun()


def mostrar_usuario_logado():
    """Mostra, na barra lateral, quem está logado, o papel e um botão de sair."""
    usuario = st.session_state.get("sigop_usuario", "—")
    papel = st.session_state.get("sigop_papel", "visualizador")
    with st.sidebar:
        st.markdown("---")
        st.caption(f"👤 {usuario} · {'🛠️ Admin' if papel == 'admin' else '👁️ Somente visualização'}")
        if st.button("🚪 Sair", use_container_width=True):
            fazer_logout()


def is_admin() -> bool:
    """Retorna True se o usuário logado é admin (pode editar/excluir)."""
    return st.session_state.get("sigop_papel") == "admin"


def bloquear_se_visualizador(acao: str = "fazer essa alteração") -> bool:
    """Chame isso logo depois de um clique de botão de editar/excluir/criar.
    Se o usuário for 'visualizador', mostra um aviso e retorna True
    (significa: pare aqui, não execute a ação). Se for admin, retorna False
    (pode seguir normalmente)."""
    if not is_admin():
        st.warning(f"👁️ Sua conta é somente visualização — você não pode {acao}.")
        return True
    return False
