import pandas as pd


def parse_brl(serie):

    s = (
        serie.astype(str)
        .str.replace(r"[^\d,.-]", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    return pd.to_numeric(s, errors="coerce")
