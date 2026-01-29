import pandas as pd

def carregar_arquivo_csv(arquivo, sep=None, decimal=None, **kwargs):
    # Prioridade para ponto e vírgula
    candidatos_sep = [sep, ';', ',', '\t', None]
    candidatos_encoding = [kwargs.pop('encoding', None), 'utf-8', 'latin-1', 'utf-16']
    candidatos_decimal = [decimal, ',', '.']
    for s in candidatos_sep:
        for enc in candidatos_encoding:
            for dec in candidatos_decimal:
                try:
                    params = dict(sep=s, encoding=enc, decimal=dec, engine='python', **kwargs)
                    if hasattr(arquivo, "seek"):
                        arquivo.seek(0)
                    df = pd.read_csv(arquivo, **{k: v for k, v in params.items() if v is not None})
                    if isinstance(df, pd.DataFrame) and df.shape[1] >= 1:
                        return df
                except Exception:
                    continue
    return pd.DataFrame()

def format_cnpj(cnpj):
    cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').replace(' ', '')
    if len(cnpj) < 14 and cnpj.isdigit():
        cnpj = cnpj.zfill(14)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj

def parse_moeda_brasil_robusto(serie):
        s = (serie.astype(str)
                 .str.replace(r'[^0-9,.\-]', '', regex=True)
                 .str.replace('.', '', regex=False)
                 .str.replace(',', '.', regex=False))
    return pd.to_numeric(s, errors='coerce')

def preparar_dataframe_fortaleza(file_like):
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
    columns_tomados = ['Data', 'CPF/CNPJ Prestador', 'Razão Social/Nome do Prestador',
                       'Número', 'Valor do ISS', 'Valor dos Serviços', 'ISS Retido', 'Status Aceite']
    columns_pendentes = ['Data', 'CNPJ/CPF Prestador', 'Razão Social/Nome do Prestador',
                          'Número', 'Valor do ISS', 'Valor do Serviço', 'ISS Retido', 'Status Aceite']
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

def preparar_dataframe_vr(file_like):
    try:
        df = pd.read_excel(file_like, skiprows=16)
    except Exception:
        try:
            file_like.seek(0)
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
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
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

def unificar_dataframes(df1, df2):
    df1 = df1.copy()
    df2 = df2.copy()

    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    df_unificado = pd.concat([df1, df2], ignore_index=True)

    return df_unificado

    s = (serie.astype(str)
                 .str.replace(r'[^0-9,.\-]', '', regex=True)
                 .str.replace('.', '', regex=False)
                 .str.replace(',', '.', regex=False))

    return pd.to_numeric(s, errors='coerce')

