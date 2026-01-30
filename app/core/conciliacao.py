import pandas as pd

from utils.fortaleza_parser import ler_fortaleza
from utils.vr_parser import ler_fortaleza
from utils.formatacao import criar_ids
from utils.moeda import parse_brl
from exports.excel import gerar_excel


def validar(df1, df2):

    df1 = df1.copy()
    df2 = df2.copy()

    df1["Status_Validacao"] = df1["ID"].isin(df2["ID"]).map(
        lambda x: "Validado" if x else "Não Encontrado"
    )

    df2["Status_Validacao"] = df2["ID"].isin(df1["ID"]).map(
        lambda x: "Validado" if x else "Não Encontrado"
    )

    return df1, df2


def executar_conciliacao(fort, vr, razao, progress=None):

    def p(v, m):
        if progress:
            progress(v, m)

    p(10, "Lendo arquivos")

    df_fort = ler_fortaleza(fort)
    df_vr = ler_vr(vr)
    df_razao = ler_razao(razao)

    p(40, "Unificando")

    prefeitura = pd.concat([df_fort, df_vr])

    p(60, "Criando IDs")

    prefeitura = criar_ids(prefeitura, "Número", "Valor do ISS")
    financeiro = criar_ids(df_razao, "Número", "Crédito")

    p(80, "Validando")

    pref_v, fin_v = validar(prefeitura, financeiro)

    p(95, "Exportando")

    excel = gerar_excel(pref_v, fin_v)

    p(100, "Concluído")

    return pref_v, fin_v, excel
