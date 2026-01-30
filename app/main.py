import streamlit as st
from funcionalidades.conciliacao
import funcionalidades.importacao as importacao
import funcionalidades.evolucao as evolucao
from funcionalidades.conciliacao


# =========================================================
# CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira chamada)
# =========================================================
st.set_page_config(
    page_title="Sistema Contábil - Lucas Marques",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# RODAPÉ
# =========================================================
def rodape():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            text-align: center;
            font-size: 0.9em;
            color: #666;
            padding: 10px 0;
            background-color: #f0f2f6;
            border-top: 1px solid #ddd;
            z-index: 999;
        }
        /* Ajuste para não cobrir conteúdo no final da página */
        .content-spacer {
            height: 50px;
        }
        </style>

        <div class="content-spacer"></div>
        <div class="footer">
            Versão 3.0 | Desenvolvido por Lucas Marques
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# BARRA LATERAL (MENU)
# =========================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50) # Ícone genérico de contabilidade
    st.title("Menu Principal")
    
    operacao = st.radio(
        "Selecione a Ferramenta:",
        options=[
            "Conciliação ISS Retido",
            "Importação Fortes",
            "Evolução Patrimonial"
        ]
    )
    
    st.markdown("---")
    st.info("Utilize o menu acima para navegar entre as funcionalidades.")

# =========================================================
# ROTEAMENTO DE PÁGINAS
# =========================================================

if operacao == "Conciliação ISS Retido":
    conciliacao.pagina_conciliacao_iss()

elif operacao == "Importação Fortes":
    importacao.pagina_importacao()

elif operacao == "Evolução Patrimonial":
    evolucao.pagina_evolucao()

# Chamada do rodapé global

rodape()




