import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_client() -> Client:
    url = st.secrets.get("supabase_url") or st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("supabase_key") or st.secrets.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Credenciais de acesso ao Supabase não foram encontradas no Secrets do Streamlit.")
        st.stop()
        
    return create_client(url, key)

# Garante a exportação global limpa da variável 'client'
client = get_client()
