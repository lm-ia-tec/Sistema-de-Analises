import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pickle
import os
import io

# =========================
# CONFIGURAÇÕES GLOBAIS
# =========================
MEM_FILE = "base_memoria.pkl"

# =========================
# FUNÇÕES AUXILIARES (CLASSIFICAÇÃO E FORMATAÇÃO)
# =========================
def formatar_brl(valor):
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "-"

def ordenar_planos(plano):
    if pd.isna(plano):
        return "9" * 30
    s = str(plano).strip()
    s = "".join(c for c in s if c.isdigit())
    if s == "":
        return "9" * 30
    return s.zfill(30)

def classificar_grupo(codigo):
    if pd.isna(codigo):
        return "Indefinido"
    s = str(codigo).strip()
    if s == "":
        return "Indefinido"
    grupo = s[0]
    mapa = {
        "1": "Ativo",
        "2": "Passivo",
        "3": "Receita",
        "4": "Despesa"
    }
    return mapa.get(grupo, "Outros")

# =========================
# FUNÇÕES DE ARQUIVO E PERSISTÊNCIA
# =========================
def carregar_arquivo_upload(file):
    # Tenta ler CSV com diferentes encodings
    if file.name.lower().endswith(".csv"):
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                df = pd.read_csv(
                    file,
                    skiprows=6,
                    sep=";",
                    encoding=enc,
                    engine="python"
                )
                break
            except:
                file.seek(0)
    else:
        # Lê Excel
        df = pd.read_excel(file, skiprows=6)

    # Limpeza de colunas
    df.columns = df.columns.astype(str).str.strip()
    
    mapa = {}
    for col in df.columns:
        c = col.lower()
        if "codigo" in c or "código" in c:
            mapa["Codigo"] = col
        elif "plano" in c or "descrição" in c or "descricao" in c:
            mapa["Plano"] = col
        elif "movimento" in c or "valor" in c or "saldo atual" in c:
            # Ajuste conforme o layout do seu arquivo, priorizando Movimento ou Saldo
            mapa["Movimento"] = col

    # Validação simples
    if len(mapa) < 2: # Pelo menos Codigo e Plano
        st.error("❌ Colunas obrigatórias (Código, Plano, Movimento) não encontradas.")
        return None

    # Se não achou movimento explícito, tenta pegar a última coluna numérica (fallback)
    if "Movimento" not in mapa:
         st.warning("Coluna de Movimento não identificada com precisão. Verifique o layout.")
         return None

    df = df[list(mapa.values())]
    df.columns = ["Codigo", "Plano", "Movimento"]

    df = df.dropna(how="all")
    df = df.dropna(subset=["Codigo", "Plano"])

    df["Codigo"] = df["Codigo"].astype(str).str.strip()
    df["Plano"] = df["Plano"].astype(str).str.strip()

    # Classificação
    df["Grupo"] = df["Codigo"].apply(classificar_grupo)

    # Tratamento numérico
    df["Movimento"] = (
        df["Movimento"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    
    df["Movimento"] = pd.to_numeric(
        df["Movimento"],
        errors="coerce"
    ).fillna(0)

    return df

def salvar_base(df):
    with open(MEM_FILE, "wb") as f:
        pickle.dump(df, f)

def carregar_base():
    if os.path.exists(MEM_FILE):
        with open(MEM_FILE, "rb") as f:
            try:
                return pickle.load(f)
            except:
                pass # Se falhar, retorna vazio
    return pd.DataFrame(columns=["Mes", "Codigo", "Plano", "Grupo", "Movimento"])

# =========================
# PÁGINA PRINCIPAL DA FUNCIONALIDADE
# =========================
def pagina_evolucao():
    st.markdown("## 📊 Evolução Patrimonial – Análise Contábil")

    # --- Carregar Memória ---
    if "base" not in st.session_state:
        st.session_state.base = carregar_base()

    # --- Inputs de Mês e Arquivo ---
    col1, col2 = st.columns([1, 2])
    with col1:
        mes_input = st.text_input(
            "📅 Mês de referência (mm/aaaa)",
            value=pd.Timestamp.now().strftime("%m/%Y")
        )
    
    with col2:
        uploaded_file = st.file_uploader(
            "📂 Anexar o Balancete a ser analisado",
            type=["xlsx", "xls", "csv"]
        )

    # Processamento da Data
    try:
        mes_dt = pd.to_datetime("01/" + mes_input, dayfirst=True)
        mes_str = mes_dt.strftime("%m/%Y")
    except:
        st.error("Formato de data inválido. Use mm/aaaa.")
        return

    # --- Processamento do Upload ---
    if uploaded_file:
        df_novo = carregar_arquivo_upload(uploaded_file)
        
        if df_novo is not None:
            df_novo["Mes"] = mes_dt
            
            # Remove dados anteriores desse mesmo mês para evitar duplicidade
            st.session_state.base = st.session_state.base[
                st.session_state.base["Mes"] != mes_dt
            ]
            
            # Concatena
            st.session_state.base = pd.concat(
                [st.session_state.base, df_novo],
                ignore_index=True
            )
            
            salvar_base(st.session_state.base)
            st.success(f"✅ Dados de {mes_str} carregados com sucesso!")

    st.markdown("---")

    # --- Gerenciamento de Meses (Exclusão) ---
    if not st.session_state.base.empty:
        with st.expander("🗑️ Gerenciar Meses Carregados"):
            meses_disponiveis = (
                st.session_state.base["Mes"]
                .drop_duplicates()
                .sort_values()
            )
            meses_fmt = [m.strftime("%m/%Y") for m in meses_disponiveis]
            
            c_exc1, c_exc2 = st.columns([2, 1])
            mes_exc = c_exc1.selectbox("Selecione o mês para excluir", meses_fmt)
            
            if c_exc2.button("Excluir Mês"):
                mes_dt_exc = pd.to_datetime("01/" + mes_exc, dayfirst=True)
                st.session_state.base = st.session_state.base[
                    st.session_state.base["Mes"] != mes_dt_exc
                ]
                salvar_base(st.session_state.base)
                st.rerun()

    # --- Filtros e Visualização ---
    if not st.session_state.base.empty:
        
        # Filtro de Grupo
        grupos = st.multiselect(
            "📌 Filtrar por grupo contábil",
            ["Ativo", "Passivo", "Receita", "Despesa", "Outros"],
            default=["Ativo", "Passivo", "Receita", "Despesa"]
        )

        base_filtrada = st.session_state.base[
            st.session_state.base["Grupo"].isin(grupos)
        ]

        if base_filtrada.empty:
            st.warning("Nenhum dado para os grupos selecionados.")
            return

        # Filtro de Planos
        planos_unicos = (
            base_filtrada["Plano"]
            .drop_duplicates()
            .sort_values(key=lambda x: x.map(ordenar_planos))
        )
        
        if "planos_sel" not in st.session_state:
            st.session_state.planos_sel = list(planos_unicos)

        # Checkbox selecionar todos
        if st.checkbox("Selecionar todos os planos listados", value=True):
            planos_pre_sel = list(planos_unicos)
        else:
            planos_pre_sel = []

        selecionados = st.multiselect(
            "Filtrar contas específicas (Planos)",
            planos_unicos,
            default=planos_pre_sel
        )

        dados = base_filtrada[base_filtrada["Plano"].isin(selecionados)]

        if dados.empty:
            st.warning("Nenhuma conta selecionada.")
            return

        # --- Pivot Table (Criação da Tabela Final) ---
        resumo = dados.groupby(
            ["Codigo", "Plano", "Grupo", "Mes"],
            as_index=False
        )["Movimento"].sum()

        tabela = resumo.pivot_table(
            index=["Codigo", "Plano", "Grupo"],
            columns="Mes",
            values="Movimento",
            fill_value=0
        ).sort_index(axis=1)

        # Cálculo de Variação Horizontal (A.H.)
        variacao = tabela.pct_change(axis=1)
        
        final = pd.DataFrame(index=tabela.index)
        
        for col in tabela.columns:
            mes_nome = col.strftime("%m/%Y")
            final[mes_nome] = tabela[col]
            # Adiciona coluna de variação se não for a primeira coluna
            if col != tabela.columns[0]:
                final[f"A. H. {mes_nome}"] = variacao[col]

        final = final.reset_index()
        final["Codigo"] = final["Codigo"].astype(str).str.strip()
        
        # Ordenação final por Código
        final = final.sort_values(by="Codigo", kind="mergesort").reset_index(drop=True)
        final = final.fillna(0)

        # --- Exibição na Tela ---
        st.subheader("📋 Análise Horizontal")
        
        # Formatação para exibição
        movimento_cols = [c for c in final.columns if not c.startswith("A. H.") and c not in ["Codigo", "Plano", "Grupo"]]
        ah_cols = [c for c in final.columns if c.startswith("A. H.")]
        
        format_dict = {c: formatar_brl for c in movimento_cols}
        format_dict.update({c: "{:.2%}" for c in ah_cols})
        
        st.dataframe(
            final.style.format(format_dict),
            use_container_width=True,
            height=500
        )

        # --- Gráfico ---
        st.markdown("### 📈 Visualização Gráfica")
        
        df_grafico = tabela.reset_index()
        df_long = df_grafico.melt(
            id_vars=["Codigo", "Plano", "Grupo"],
            var_name="Mes",
            value_name="Movimento"
        )
        df_long["Mes_dt"] = pd.to_datetime(df_long["Mes"])
        df_long["Mes_fmt"] = df_long["Mes_dt"].dt.strftime("%m/%Y")
        df_long = df_long.sort_values("Mes_dt")

        fig = px.bar(
            df_long,
            x="Plano",
            y="Movimento",
            color="Mes_fmt",
            facet_row="Grupo",
            barmode="group",
            height=600,
            hover_data={"Codigo": True, "Grupo": True, "Mes_fmt": True, "Movimento": ":,.2f"}
        )
        fig.update_layout(
            title="Evolução Contábil por Grupo",
            xaxis_title="Conta / Plano",
            yaxis_title="Movimento (R$)"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Exportação Excel ---
        st.markdown("### 📥 Exportação")
        
        output = io.BytesIO()
        
        # Prepara DF para excel (remove formatação de string se houver, garante float)
        final_export = final.copy()
        
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            final_export.to_excel(writer, index=False, sheet_name="Evolucao")
            
            workbook = writer.book
            worksheet = writer.sheets["Evolucao"]
            
            fmt_valor = workbook.add_format({"num_format": "#,##0.00"})
            fmt_percent = workbook.add_format({"num_format": "0.00%"})
            
            for i, col in enumerate(final_export.columns):
                if col.startswith("A. H."):
                    worksheet.set_column(i, i, 15, fmt_percent)
                elif col not in ["Codigo", "Plano", "Grupo"]:
                    worksheet.set_column(i, i, 18, fmt_valor)
                else:
                    worksheet.set_column(i, i, 25) # Largura maior para descrições
            
            worksheet.autofilter(0, 0, final_export.shape[0], final_export.shape[1] - 1)

        st.download_button(
            "💾 Baixar Relatório Completo (Excel)",
            data=output.getvalue(),
            file_name="Evolucao_Contabil_Completa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )