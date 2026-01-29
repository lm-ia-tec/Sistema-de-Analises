import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# =========================================================
# ============ TRANSFORMAÇÃO DE PLANILHA ==================
# =========================================================

def pagina_transformacao_planilha():
    st.markdown("## Movimentação Bancária - Santander")

    arquivo = st.file_uploader(
        "📄 Envie o arquivo Excel (xls ou xlsx)",
        type=["xls", "xlsx"]
    )

    if not arquivo:
        st.info("Aguardando upload do arquivo.")
        return

    if not st.button("⚙️ Processar"):
        return

    with st.spinner("Processando arquivo..."):

        # ===== LÓGICA ORIGINAL =====
        df = pd.read_excel(arquivo)
        
        # Seleção de colunas
        df = df[['Data', 'Transação', 'Valor', 'Ação', 'Origem/Destino', 'Histórico']]
        df['Origem/Destino'] = (
          df['Origem/Destino']
              .combine_first(df['Histórico'])
              .combine_first(df['Transação'])
              .fillna('Não identificado')
         )


        cols_drop = [c for c in ['Débito', 'Crédito'] if c in df.columns]
        df = df.drop(columns=cols_drop, errors='ignore')

        contas_contabeis = {
            'CB - Tarifas Bancárias - TAR EMISSAO TED CIP PGTO FORNEC': 'Despesas Bancárias (TED/CIP)',
            'CB - Transferência entre Bancos - Entrada': 'Receita de Transferência Bancária',
            'CR - Baixa de Titulo a Receber': 'Receita de Títulos a Receber',
            'CB - Transferência entre Bancos - Saída': 'Despesas de Transferência Bancária',
            'CB - TAR PIX PGTO FORNEC - OUTRA INST': 'Despesas Bancárias (PIX/Fornecedor)',
            'CB - TAR PIX PGTO FORNEC - MESMA INST': 'Despesas Bancárias (PIX/Fornecedor)',
            'CP - Baixa de Pagamento Escritural': 'Despesas com Pagamentos Escriturais',
            'CP - Baixa de Título a Pagar': 'Despesas com Títulos a Pagar',
            'CB - Tarifas Bancárias - TARIFA EXTRATO INTELIGENTE': 'Despesas Bancárias (Extrato)',
            'CB - Tarifas Bancárias - DEBITO AUT. CARNE/ASSEMELHADOS REDECARD': 'Despesas Bancárias (Débito Automático)',
            'CB - Tarifas Bancárias - TAR EXTRATO CONCILIACAO BANCARIA': 'Despesas Bancárias (Conciliação)',
            'CB - Tarifas Bancárias - TARIFA MENSALIDADE PACOTE SERVICOS': 'Despesas Bancárias (Mensalidade Pacote)'
        }

        df['Conta Contábil'] = df['Transação'].map(contas_contabeis)

        mapeamento = {
            **{t: {'debito': '458919019', 'credito': '1213190110004'} for t in [
                'CB - TAR PIX PGTO FORNEC - MESMA INST',
                'CB - TAR PIX PGTO FORNEC - OUTRA INST',
                'CB - Tarifas Bancárias - DEBITO AUT. CARNE/ASSEMELHADOS REDECARD',
                'CB - Tarifas Bancárias - TAR EMISSAO TED CIP PGTO FORNEC',
                'CB - Tarifas Bancárias - TAR EXTRATO CONCILIACAO BANCARIA',
                'CB - Tarifas Bancárias - TARIFA EXTRATO INTELIGENTE',
                'CB - Tarifas Bancárias - TARIFA MENSALIDADE PACOTE SERVICOS'
            ]},
            'CB - Transferência entre Bancos - Entrada': {'debito': '1213190110004', 'credito': '1214190110004'},
            'CB - Transferência entre Bancos - Saída': {'debito': '1214190110004', 'credito': '1213190110004'},
            'CP - Baixa de Pagamento Escritural': {'debito': '2182190110006', 'credito': '1213190110004'},
            'CP - Baixa de Título a Pagar': {'debito': '2182190110006', 'credito': '1213190110004'},
            'CR - Baixa de Titulo a Receber': {'debito': '1213190110004', 'credito': '124119011'},
            'CB - Transferências Judiciais': {'debito': '1278190180001', 'credito': '1213190110004'},
            'CB - Estorno de Pagamento': {'debito': '1213190110004', 'credito': '2182190110006'},
            'CB - TRANSACAO PARA OUTRA CONTA BANCARIA (LIV SAUDE)': {'debito': '2182190110006', 'credito': '1213190110004'}
        }

        df['conta de debito'] = df['Transação'].map(lambda x: mapeamento.get(x, {}).get('debito'))
        df['conta de credito'] = df['Transação'].map(lambda x: mapeamento.get(x, {}).get('credito'))

        df.loc[df['Origem/Destino'].str.contains('Onnibank', case=False, na=False),
               'conta de debito'] = '1213190110005'

        df.loc[df['Origem/Destino'].str.contains('COMPANHIA DE AGUA', case=False, na=False),
               'conta de debito'] = '218889084'

        df.loc[df['Origem/Destino'].str.contains('COMPANHIA ENERGETICA', case=False, na=False),
               'conta de debito'] = '4631190140001'

        df.loc[df['Origem/Destino'].str.contains('PREFEITURA MUNICIPAL', case=False, na=False),
               'conta de debito'] = '216219013'

        df['Descrição'] = np.where(
            df['Ação'] == 'C',
            'REF A PGTO DE ' + df['Origem/Destino'].fillna('').astype(str),
             np.where(df['Ação'] == 'D', 'VR REF A ' + df['Origem/Destino'].fillna('').astype(str), '')
        )

        df['Descrição'] = np.where(
            df['Histórico'].astype(str).str.startswith('APLICACAO'),
            'REF A APLICAÇÃO FINANCEIRA',
            np.where(
                df['Histórico'].astype(str).str.startswith('RESGATE'),
                'VR REF A RESGATE SOBRE APLICAÇÃO FINANCEIRA',
                df['Descrição']
            )
        )

        df['Indice'] = 1

        df_final = df[['Indice', 'Data', 'conta de debito', 'conta de credito', 'Valor', 'Descrição']].copy()
        df_final['Data'] = df_final['Data'].dt.strftime('%d/%m/%Y')
        df_final['Valor'] = df_final['Valor'].apply(
            lambda x: f'{x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notna(x) else ''
        )

        csv = [';'.join(df_final.columns)] + df_final.astype(str).agg(';'.join, axis=1).tolist()
        buffer = BytesIO()
        buffer.write('\ufeff'.encode('utf-8') + '\n'.join(csv).encode('utf-8'))
        buffer.seek(0)

    st.success("Arquivo gerado com sucesso!")

    st.download_button(
        "📥 Baixar CSV Fortes",
        data=buffer,
        file_name=arquivo.name.rsplit('.', 1)[0] + "_fortes.csv",
        mime="text/csv"
    )

# =========================================================
# ============ TRANSFORMAÇÃO DE PLANILHA(Provisões) ==================
# =========================================================
def pagina_transformacao_planilha_servicos():

    st.markdown("## Conversão de Planilha — Serviços Tomados (Fortes)")

    arquivo = st.file_uploader(
        "📄 Envie o arquivo Excel (xls ou xlsx)",
        type=["xls", "xlsx"],
        key="servicos"
    )

    if not arquivo:
        st.info("Aguardando upload do arquivo.")
        return

    if not st.button("⚙️ Processar Serviços Tomados"):
        return

    with st.spinner("Processando arquivo..."):

        df = pd.read_excel(arquivo)

        df = df[['Data', 'Número', 'Valor dos Serviços', 'Item da Lista',
                 'Razão Social/Nome do Prestador', 'PIS', 'COFINS',
                 'IRRF', 'CSLL', 'INSS', 'ISS', 'ISS Retido']]

        df['Valor Líquido'] = (
            df['Valor dos Serviços']
            - df['PIS']
            - df['COFINS']
            - df['IRRF']
            - df['INSS']
            - np.where(df['ISS Retido'] == 'Não', 0, df['ISS'])
        )

        debit_mapping = {
            1.03: '463919014',
            1.05: '4631190190006',
            1.06: '462119013',
            1.07: '4633190130001',
            4.01: '4631190190005',
            4.02: '462119019',
            4.03: '4631190190005',
            4.07: '4631190190005',
            4.06: '462119014',
            4.08: '462119014',
            4.09: '462119014',
            7.01: '4631190190003',
            7.02: '4631190190003',
            7.05: '4631190190003',
            7.06: '4631190190003',
            7.09: '463119015',
            7.10: '463119015',
            7.13: '463119015',
            7.11: '462119019',
            7.12: '463119015',
            8.02: '462119014',
            10.01: '462119019',
            10.02: '462119019',
            11.01: '4639190190001',
            11.02: '462119019',
            13.04: '4681190190002',
            13.05: '4681190190002',
            14.01: '4633190130001',
            14.02: '4633190130001',
            14.11: '4633190130001',
            17.01: '462119013',
            17.02: '462119019',
            17.03: '462119019',
            17.05: '462119014',
            17.08: '462119019',
            17.09: '462119019',
            17.13: '462119014',
            17.14: '462119019',
            17.15: '462119014',
            17.18: '462119014',
            17.19: '462119019',
            24.01: '462119019',
            27.01: '462119019',
            99.03: '463319011',
            99.99: '462119019'
        }

        df['Débito'] = df['Item da Lista'].map(debit_mapping).fillna('462119019')
        df['Crédito'] = '2182190110006'
        df['Indice'] = 1

        df['Histórico'] = (
            'Vr. ref. a ' +
            df['Razão Social/Nome do Prestador'] +
            ' - Doc. N° ' +
            df['Número'].astype(str)
        )

        df_final = df[['Indice', 'Data', 'Débito', 'Crédito',
                       'Valor dos Serviços', 'Histórico']].copy()

        df_final['Data'] = pd.to_datetime(df_final['Data'], dayfirst=True).dt.strftime('%d/%m/%Y')
        df_final['Valor dos Serviços'] = df_final['Valor dos Serviços'].apply(
            lambda x: f'{x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        )

        csv = [';'.join(df_final.columns)] + df_final.astype(str).agg(';'.join, axis=1).tolist()
        buffer = BytesIO()
        buffer.write('\ufeff'.encode('utf-8') + '\n'.join(csv).encode('utf-8'))
        buffer.seek(0)

    st.success("Arquivo Fortes (Serviços Tomados) gerado com sucesso!")

    st.download_button(
        "📥 Baixar CSV Fortes",
        data=buffer,
        file_name=arquivo.name.rsplit('.', 1)[0] + "_fortes_servicos.csv",
        mime="text/csv"
    )

def pagina_importacao():
    st.markdown("## Importação Fortes")

    tipo_transformacao = st.radio(
        "Escolha o tipo de operação:",
        [
            "Movimentação Bancária - Santander",
            "Notas de Serviços Tomados"
        ]
    )
    
    st.markdown("---")

    if tipo_transformacao == "Movimentação Bancária - Santander":
        pagina_transformacao_planilha()

    elif tipo_transformacao == "Notas de Serviços Tomados":
        pagina_transformacao_planilha_servicos()