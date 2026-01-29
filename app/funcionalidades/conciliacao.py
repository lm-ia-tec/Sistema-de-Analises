import streamlit as st
import pandas as pd
import numpy as np
import openpyxl

from openpyxl.styles import PatternFill
from openpyxl.formatting.rule import CellIsRule
from io import BytesIO


# =========================================================
# UTILIDADES
# =========================================================

def _reset_file(file):
    if file is not None and hasattr(file, "seek"):
        try:
            file.seek(0)
        except Exception:
            pass


# =========================================================
# LEITURA CSV
# =========================================================

def carregar_arquivo_csv(arquivo, sep=None, decimal=None, **kwargs):

    candidatos_sep = [sep, ';', ',', '\t', None]
    candidatos_encoding = [kwargs.pop('encoding', None), 'utf-8', 'latin-1', 'utf-16']
    candidatos_decimal = [decimal, ',', '.']

    for s in candidatos_sep:
        for enc in candidatos_encoding:
            for dec in candidatos_decimal:

                try:
                    params = dict(
                        sep=s,
                        encoding=enc,
                        decimal=dec,
                        engine='python',
                        **kwargs
                    )

                    _reset_file(arquivo)

                    df = pd.read_csv(
                        arquivo,
                        **{k: v for k, v in params.items() if v is not None}
                    )

                    if isinstance(df, pd.DataFrame) and df.shape[1] >= 1:
                        return df

                except Exception:
                    continue

    return pd.DataFrame()


# =========================================================
# FORMATAÇÕES
# =========================================================

def format_cnpj(cnpj):

    cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').replace(' ', '')

    if len(cnpj) < 14 and cnpj.isdigit():
        cnpj = cnpj.zfill(14)

    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    return cnpj


def parse_moeda_brasil_robusto(serie):

    s = (
        serie.astype(str)
        .str.replace(r'[^0-9,.\-]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )

    return pd.to_numeric(s, errors='coerce')


# =========================================================
# FORTALEZA
# =========================================================

def preparar_dataframe_fortaleza(file_like):

    _reset_file(file_like)

    try:
        xls = pd.ExcelFile(file_like)
    except Exception:
        return pd.DataFrame()

    try:
        df_tomados = xls.parse('Serviços Tomados', header=0)
    except Exception:
        try:
            df_tomados = xls.parse(xls.sheet_names[0], header=0)
        except Exception:
            return pd.DataFrame()

    if 'Status Doc.' in df_tomados.columns:
        df_tomados = df_tomados[df_tomados['Status Doc.'] != 'CANCELADA']

    if 'ISS Retido' in df_tomados.columns:
        df_tomados = df_tomados[~df_tomados['ISS Retido'].isin(['Não', 'NÃO'])]

    try:
        df_pendentes = xls.parse('Serviços Pendentes', header=8)
        df_pendentes['Status Aceite'] = 'Pendente'
    except Exception:
        df_pendentes = pd.DataFrame()

    columns_tomados = [
        'Data', 'CPF/CNPJ Prestador', 'Razão Social/Nome do Prestador',
        'Número', 'Valor do ISS', 'Valor dos Serviços',
        'ISS Retido', 'Status Aceite'
    ]

    columns_pendentes = [
        'Data', 'CNPJ/CPF Prestador', 'Razão Social/Nome do Prestador',
        'Número', 'Valor do ISS', 'Valor do Serviço',
        'ISS Retido', 'Status Aceite'
    ]

    df_tomados = df_tomados[[c for c in columns_tomados if c in df_tomados.columns]].copy()

    if not df_pendentes.empty:

        df_pendentes = df_pendentes[[c for c in columns_pendentes if c in df_pendentes.columns]].copy()

        df_pendentes = df_pendentes.rename(columns={
            'CNPJ/CPF Prestador': 'CPF/CNPJ Prestador',
            'Valor do Serviço': 'Valor dos Serviços'
        })

        merged_df = pd.concat([df_tomados, df_pendentes], ignore_index=True)

    else:
        merged_df = df_tomados.copy()

    merged_df['Origem'] = 'Fortaleza'

    if 'Status Doc.' not in merged_df.columns:
        merged_df['Status Doc.'] = None

    if 'CPF/CNPJ Prestador' in merged_df.columns:
        merged_df['CPF/CNPJ Prestador'] = merged_df['CPF/CNPJ Prestador'].astype(str)

    if 'Número' in merged_df.columns:
        merged_df['Número'] = merged_df['Número'].astype(str).str.replace(r'\.0$', '', regex=True)

    if 'Valor do ISS' in merged_df.columns:
        merged_df['Valor do ISS'] = pd.to_numeric(merged_df['Valor do ISS'], errors='coerce')

    if 'Valor dos Serviços' in merged_df.columns:
        merged_df['Valor dos Serviços'] = pd.to_numeric(merged_df['Valor dos Serviços'], errors='coerce')

    return merged_df


# =========================================================
# VOLTA REDONDA
# =========================================================

def preparar_dataframe_vr(file_like):

    _reset_file(file_like)

    try:
        df = pd.read_excel(file_like, skiprows=16)

    except Exception:

        try:
            _reset_file(file_like)
            df = pd.read_excel(file_like)

        except Exception:
            return pd.DataFrame()

    rename_map = {
        'CNPJ Prestador': 'CPF/CNPJ Prestador',
        'Razão Social': 'Razão Social/Nome do Prestador',
        'Nº': 'Número',
        'Dt Emiss': 'Data',
        'Nota Fiscal': 'Valor dos Serviços',
        'Imposto': 'Valor do ISS',
        'Retido': 'ISS Retido',
        'Status': 'Status Doc.'
    }

    df = df.rename(
        columns={k: v for k, v in rename_map.items() if k in df.columns}
    ).copy()

    if 'Razão Social/Nome do Prestador' in df.columns:
        df = df.dropna(subset=['Razão Social/Nome do Prestador'])

    if 'CPF/CNPJ Prestador' in df.columns:
        df['CPF/CNPJ Prestador'] = df['CPF/CNPJ Prestador'].astype(str)

    if 'Número' in df.columns:
        df['Número'] = df['Número'].astype(str).str.replace(r'\.0$', '', regex=True)

    df['Origem'] = 'Volta Redonda'

    if 'Valor do ISS' in df.columns:
        df['Valor do ISS'] = pd.to_numeric(df['Valor do ISS'], errors='coerce')

    if 'Valor dos Serviços' in df.columns:
        df['Valor dos Serviços'] = pd.to_numeric(df['Valor dos Serviços'], errors='coerce')

    return df

# =========================================================
# FUNÇÕES INTERNAS (antigo utils)
# =========================================================

def unificar_dataframes(df1, df2):

    df1 = df1.copy()
    df2 = df2.copy()

    if df1.empty and df2.empty:
        return pd.DataFrame()

    if df1.empty:
        return df2

    if df2.empty:
        return df1

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    return pd.concat([df1, df2], ignore_index=True)


def limpar_df_prefeitura(df):

    df = df.copy()

    df['Numero_Key'] = df['Número'].astype(str).str.strip()
    df['ISS_Key'] = df['Valor do ISS'].round(2)

    return df


def limpar_df_financeiro(df):

    df = df.copy()

    # Garantir que Crédito seja numérico
    if 'Crédito' in df.columns:

        df['Crédito'] = parse_moeda_brasil_robusto(df['Crédito'])

        df['Credito_Key'] = df['Crédito'].round(2)

    else:
        df['Credito_Key'] = 0


    # Garantir Número
    if 'Número' in df.columns:

        df['Numero_Key'] = (
            df['Número']
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)
        )

    else:
        df['Numero_Key'] = ''


    return df

    else:
        df['Credito_Key'] = 0

    if 'Número' in df.columns:
        df['Numero_Key'] = df['Número'].astype(str).str.strip()
    else:
        df['Numero_Key'] = ''

    return df


def criar_ids(df, col_num, col_valor):

    df = df.copy()

    df['ID_Conciliacao'] = (
        df[col_num].astype(str).str.strip() +
        "_" +
        df[col_valor].round(2).astype(str)
    )

    return df


def aplicar_validacao(df_pref, df_fin):

    df_pref = df_pref.copy()
    df_fin = df_fin.copy()

    ids_fin = set(df_fin['ID_Conciliacao'])

    df_pref['Status_Validacao'] = np.where(
        df_pref['ID_Conciliacao'].isin(ids_fin),
        'Validado',
        'Não Encontrado'
    )

    ids_pref = set(df_pref['ID_Conciliacao'])

    df_fin['Status_Validacao'] = np.where(
        df_fin['ID_Conciliacao'].isin(ids_pref),
        'Validado',
        'Não Encontrado'
    )

    return df_pref, df_fin


def exportar_para_excel_bytes(df_pref, df_fin):

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:

        df_pref.to_excel(writer, sheet_name='Prefeitura', index=False)
        df_fin.to_excel(writer, sheet_name='Financeiro', index=False)

    buffer.seek(0)

    return buffer



# =========================================================
# CONCILIAÇÃO
# =========================================================

def conciliar_notas(file_fortaleza=None, file_vr=None, file_razao=None, progress_callback=None):

    logs = []

    def p(pct, msg=None):

        if progress_callback:

            try:
                progress_callback(pct, msg)
            except Exception:
                pass


    p(5, "Iniciando leitura de arquivos.")


    if file_fortaleza is not None:

        _reset_file(file_fortaleza)

        try:
            df_fortaleza = preparar_dataframe_fortaleza(file_fortaleza)

        except Exception as e:
            df_fortaleza = pd.DataFrame()
            logs.append(f"Erro ao processar Fortaleza: {e}")

    else:
        df_fortaleza = pd.DataFrame()
        logs.append("Fortaleza não fornecido.")


    if file_vr is not None:

        _reset_file(file_vr)

        try:
            df_vr = preparar_dataframe_vr(file_vr)

        except Exception as e:
            df_vr = pd.DataFrame()
            logs.append(f"Erro ao processar Volta Redonda: {e}")

    else:
        df_vr = pd.DataFrame()
        logs.append("Volta Redonda não fornecido.")


    p(40, "Unificando registros das Prefeituras.")

    df_unificado = unificar_dataframes(df_fortaleza, df_vr)


    p(55, "Lendo arquivo Razão.")

    df_financeiro_raw = pd.DataFrame()

    if file_razao is not None:

        try:

            nome_arquivo = file_razao.name.lower()

            _reset_file(file_razao)

            if nome_arquivo.endswith(('.xls', '.xlsx')):

                df_financeiro_raw = pd.read_excel(file_razao)

                if 'Crédito' in df_financeiro_raw.columns:

                    if not pd.api.types.is_numeric_dtype(df_financeiro_raw['Crédito']):
                        df_financeiro_raw['Crédito'] = parse_moeda_brasil_robusto(
                            df_financeiro_raw['Crédito']
                        )

            elif nome_arquivo.endswith('.csv'):

                df_financeiro_raw = carregar_arquivo_csv(file_razao)

            else:

                logs.append("Arquivo Razão em formato não suportado.")

        except Exception as e:

            df_financeiro_raw = pd.DataFrame()
            logs.append(f"Erro ao carregar Razão: {e}")

    else:

        logs.append("Razão não fornecido.")


    p(70, "Limpando dados.")

    df_prefeitura = limpar_df_prefeitura(df_unificado)
    df_financeiro = limpar_df_financeiro(df_financeiro_raw)


    p(82, "Gerando IDs.")

    df_prefeitura = criar_ids(df_prefeitura, 'Número', 'Valor do ISS')
    df_financeiro = criar_ids(df_financeiro, 'Número', 'Crédito')


    p(92, "Aplicando validação.")

    df_prefeitura_valid, df_financeiro_valid = aplicar_validacao(
        df_prefeitura,
        df_financeiro
    )


    p(97, "Gerando Excel.")

    excel_buffer = exportar_para_excel_bytes(
        df_prefeitura_valid,
        df_financeiro_valid
    )


    p(100, "Concluído.")


    return df_prefeitura_valid, df_financeiro_valid, excel_buffer, logs


# =========================================================
# PÁGINA STREAMLIT
# =========================================================

def pagina_conciliacao_iss():

    colh1, colh2 = st.columns([4, 1])

    with colh1:
        st.markdown('<div class="big-title">Conciliação do ISS Retido</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title">Automação fiscal personalizada para LIV SAÚDE.</div>', unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Upload dos Documentos")

    col1, col2, col3 = st.columns(3)

    with col1:
        file_fortaleza = st.file_uploader("📄 NFS Fortaleza", type=["xlsx"])

    with col2:
        file_vr = st.file_uploader("📄 NFS Volta Redonda", type=["xls", "xlsx"])

    with col3:
        file_razao = st.file_uploader("📊 Razão Contábil", type=["csv", "xls", "xlsx"])


    if 'logs' not in st.session_state:
        st.session_state.logs = []

    if 'progress' not in st.session_state:
        st.session_state.progress = 0


    def progress_cb(pct, msg=None):

        st.session_state.progress = int(pct)

        if msg:
            st.session_state.logs.append(f"{pct}% - {msg}")


    if st.button("🚀 Processar"):

        st.session_state.logs = []
        st.session_state.progress = 0


        with st.spinner("Executando conciliação..."):

            df_pref, df_fin, excel_buf, logs = conciliar_notas(
                file_fortaleza,
                file_vr,
                file_razao,
                progress_callback=progress_cb
            )

            for l in logs:
                st.session_state.logs.append(l)

            st.success("Conciliação concluída!")
            
            # 1️⃣ Log de execução
            #st.subheader("📘 Log de Execução")
            #for l in st.session_state.logs[-200:]:
            #    st.write("•", l)

            # 2️⃣ Resumo da conciliação
            st.markdown("### 📊 Resumo da Conciliação")

            col1, col2 = st.columns(2)

            # Resumo da Prefeitura
            with col1:
                st.markdown("#### 🏛️ Prefeitura")

                total_pref = len(df_pref)
                validados_pref = (df_pref['Status_Validacao'] == 'Validado').sum()
                nao_encontrados_pref = (df_pref['Status_Validacao'] == 'Não Encontrado').sum()

                st.metric("Total de registros", total_pref)
                st.metric("✅ Validados", validados_pref)
                st.metric("❌ Não encontrados", nao_encontrados_pref)

            # Resumo do Financeiro
            with col2:
                st.markdown("#### 💰 Financeiro")

                total_fin = len(df_fin)
                validados_fin = (df_fin['Status_Validacao'] == 'Validado').sum()
                nao_encontrados_fin = (df_fin['Status_Validacao'] == 'Não Encontrado').sum()

                st.metric("Total de registros", total_fin)
                st.metric("✅ Validados", validados_fin)
                st.metric("❌ Não encontrados", nao_encontrados_fin)

            # 3️⃣ Botão para baixar planilha  
            if excel_buf:
                st.download_button(
                    "📥 Baixar Planilha Conciliada",
                    data=excel_buf.getvalue(),
                    file_name="Planilha Conciliada.xlsx"
                )













