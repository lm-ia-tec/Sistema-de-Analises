import streamlit as st

from core.conciliacao import executar_conciliacao


def pagina_conciliacao():

    st.title("Conciliação ISS")

    f1 = st.file_uploader("Fortaleza", ["xlsx"])
    f2 = st.file_uploader("VR", ["xls", "xlsx"])
    f3 = st.file_uploader("Razão", ["csv", "xls", "xlsx"])

    if st.button("Processar"):

        with st.spinner("Processando..."):

            pref, fin, excel = executar_conciliacao(
                f1, f2, f3
            )

        st.success("Pronto")

        st.download_button(
            "Baixar Excel",
            excel.getvalue(),
            "conciliado.xlsx"
        )
