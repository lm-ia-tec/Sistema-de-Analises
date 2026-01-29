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
