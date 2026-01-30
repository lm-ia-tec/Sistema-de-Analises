import pandas as pd
import chardet
import io

def detectar_encoding(file):

    raw = file.read()

    file.seek(0)

    result = chardet.detect(raw)

    return result["encoding"] or "utf-8"

def detectar_separador(sample):

    candidatos = [";", ",", "|", "\t"]

    contagem = {c: sample.count(c) for c in candidatos}

    return max(contagem, key=contagem.get)

def encontrar_header(linhas):

    palavras = [
        "data", "cnpj", "nsu", "valor", "liquido", "bandeira"
    ]

    for i, linha in enumerate(linhas):

        txt = linha.lower()

        if sum(p in txt for p in palavras) >= 2:
            return i

    return None

def normalizar(txt):

    return (
        str(txt)
        .lower()
        .strip()
        .replace(" ", "")
        .replace("/", "")
        .replace(".", "")
    )

COL_MAP = {
    "data": ["data", "dt"],
    "cnpj": ["cnpj", "documento"],
    "estab": ["estabelecimento", "filial", "loja"],
    "nsu": ["nsu", "autorizacao"],
    "bandeira": ["bandeira", "cartao"],
    "bruto": ["valorbruto", "bruto"],
    "taxa": ["taxa", "mdr"],
    "liquido": ["liquido", "líquido", "net"],
    "status": ["status", "situacao"]
}

def mapear_colunas(cols):

    mapa = {}

    for col in cols:

        c = normalizar(col)

        for key, termos in COL_MAP.items():

            if any(t in c for t in termos):
                mapa[key] = col

    return mapa

def ler_vr(file):

    encoding = detectar_encoding(file)

    conteudo = file.read().decode(encoding, errors="ignore")

    linhas = conteudo.splitlines()

    idx = encontrar_header(linhas)

    if idx is None:
        raise ValueError("Cabeçalho VR não identificado")

    sample = linhas[idx]

    sep = detectar_separador(sample)

    buffer = io.StringIO("\n".join(linhas[idx:]))

    df = pd.read_csv(
        buffer,
        sep=sep,
        decimal=",",
        engine="python"
    )

    df = df.dropna(how="all")

    mapa = mapear_colunas(df.columns)

    obrig = ["data", "cnpj", "nsu", "liquido"]

    for c in obrig:

        if c not in mapa:
            raise ValueError(f"Coluna obrigatória ausente: {c}")

    out = pd.DataFrame()

    out["Data"] = df[mapa["data"]]
    out["CNPJ"] = df[mapa["cnpj"]]
    out["Estabelecimento"] = df.get(mapa.get("estab"))
    out["NSU"] = df[mapa["nsu"]]
    out["Bandeira"] = df.get(mapa.get("bandeira"))

    out["Valor_Bruto"] = df.get(mapa.get("bruto"))
    out["Taxa"] = df.get(mapa.get("taxa"))
    out["Valor_Liquido"] = df[mapa["liquido"]]

    if "status" in mapa:
        out["Status"] = df[mapa["status"]]

    out["Origem"] = "VR"

    return out
