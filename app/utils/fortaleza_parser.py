import pandas as pd

COL_MAP = {
    "data": ["data", "dt", "emissão", "emissao"],
    "doc": ["número", "numero", "nf", "nota"],
    "cnpj": ["cpf/cnpj", "cnpj", "cpf"],
    "razao": ["razão", "razao", "prestador", "nome"],
    "valor_iss": ["valor do iss", "iss", "imposto"],
    "valor_serv": ["valor dos serviços", "serviço", "servicos"],
    "status": ["status", "situação", "situacao"],
    "aceite": ["aceite", "aceitação", "aceitacao"]
}

def normalizar(txt):

    return (
        str(txt)
        .lower()
        .strip()
        .replace(".", "")
        .replace("/", "")
    )


def mapear_colunas(cols):

    mapa = {}

    for col in cols:

        c = normalizar(col)

        for padrao, chaves in COL_MAP.items():

            if any(k in c for k in chaves):

                mapa[padrao] = col

    return mapa

def ler_planilha(file):

    xls = pd.ExcelFile(file)

    for aba in xls.sheet_names:

        try:

            df = xls.parse(aba)

            if len(df.columns) >= 5:
                return df

        except Exception:
            continue

    return pd.DataFrame()

def limpar(df):

    df = df.copy()

    df = df.dropna(how="all")

    df.columns = df.columns.astype(str)

    return df

def ler_fortaleza(file):

    df_raw = ler_planilha(file)

    if df_raw.empty:
        raise ValueError("Nenhuma aba válida encontrada")

    df = limpar(df_raw)

    mapa = mapear_colunas(df.columns)

    obrigatorias = ["data", "doc", "cnpj", "valor_iss"]

    for c in obrigatorias:

        if c not in mapa:
            raise ValueError(f"Coluna obrigatória ausente: {c}")

    out = pd.DataFrame()

    out["Data"] = df[mapa["data"]]
    out["Número"] = df[mapa["doc"]]
    out["CPF/CNPJ"] = df[mapa["cnpj"]]

    if "razao" in mapa:
        out["Razao"] = df[mapa["razao"]]

    if "valor_serv" in mapa:
        out["Valor Serviços"] = df[mapa["valor_serv"]]

    out["Valor ISS"] = df[mapa["valor_iss"]]

    if "status" in mapa:
        out["Status"] = df[mapa["status"]]

    if "aceite" in mapa:
        out["Aceite"] = df[mapa["aceite"]]

    out["Origem"] = "Fortaleza"

    return out
