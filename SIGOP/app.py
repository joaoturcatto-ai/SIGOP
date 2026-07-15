import streamlit as st

st.set_page_config(
    page_title="SIGOP",
    page_icon="🚔",
    layout="wide"
)

st.title("🚔 SIGOP")
st.subheader("Sistema Integrado de Gerenciamento de Operações Policiais")
st.caption("Delegacia Especializada de Estelionato de Cuiabá/MT")

st.markdown("---")

st.markdown(
    """
    Use o menu à esquerda para navegar entre os módulos do sistema:

    - **🏠 Dashboard** — visão geral do dia e estatísticas rápidas
    - **👮 Efetivo** — cadastro de delegados, escrivães e investigadores
    - **🚨 Operações** — cadastro, briefing e escala de operações
    - **📅 CQH** — escala de plantão
    - **🏖️ Afastamentos** — férias, folgas e licenças
    - **🚓 Viaturas** — cadastro e disponibilidade da frota
    - **📊 Ranking** — estatísticas de emprego do efetivo
    - **📄 Gerar Documento** — gera a Ordem de Operação em PDF/Word
    """
)

st.success("Sistema iniciado com sucesso.")

with st.expander("⚙️ Status da conexão com o banco de dados"):
    try:
        from utils.db import get_client
        get_client()
        st.success("✅ Conexão com o Supabase configurada corretamente.")
    except Exception as e:
        st.error("⚠️ Não foi possível conectar ao Supabase.")
        st.code(str(e), language="python")
        st.info(
            "Verifique se as chaves SUPABASE_URL e SUPABASE_KEY estão "
            "configuradas em Settings → Secrets no Streamlit Cloud."
        )
