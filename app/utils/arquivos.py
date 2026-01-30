import pandas as pd

from utils.moeda import parse_brl


def ler_fortaleza(file):

    xls = pd.ExcelFile(file)
    df = xls.parse(xls.sheet_names[0])

    df["Origem"] = "Fortaleza"

    df["Valor do ISS"] = parse_brl(df["Valor do ISS"])

    return df


def ler_vr(file):

    df = pd.read_excel(file, skiprows=16)

    df["Origem"] = "Volta Redonda"

    df["Valor do ISS"] = parse_brl(df["Valor do ISS"])

    return df


def ler_razao(file):

    nome = file.name.lower()

    if nome.endswith(".csv"):
        df = pd.read_csv(file, sep=";")

    else:
        df = pd.read_excel(file)

    df["Crédito"] = parse_brl(df["Crédito"])

    return df
