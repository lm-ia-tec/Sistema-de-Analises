import openpyxl
from io import BytesIO


def gerar_excel(pref, fin):

    out = BytesIO()

    with openpyxl.Workbook() as wb:

        ws1 = wb.active
        ws1.title = "Prefeitura"

        ws2 = wb.create_sheet("Financeiro")

    out.seek(0)

    return out
