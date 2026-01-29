import streamlit as st
import hashlib

# =========================
# AUTENTICAÇÃO
# =========================

# Gere o hash uma vez e mantenha fixo
SENHA_HASH = hashlib.sha256("admin123".encode()).hexdigest()

def tela_login():
    st.markdown("## 🔐 Acesso ao Sistema")

    senha = st.text_input(
        "Digite a senha",
        type="password"
    )

    if st.button("Entrar"):
        senha_hash = hashlib.sha256(
            senha.encode()
        ).hexdigest()

        if senha_hash == SENHA_HASH:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

def verificar_autenticacao():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        tela_login()
        st.stop()