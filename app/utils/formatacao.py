def criar_ids(df, num_col, val_col):

    df = df.copy()

    n = df[num_col].astype(str).str.replace(".0", "")
    v = df[val_col].astype(str).str.replace(".0", "")

    df["ID"] = n + v

    return df
