import streamlit as st
import pandas as pd
import locale
import os

# Configurar locale para formato brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Caminhos dos arquivos Parquet convertidos
ARQUIVOS_PARQUET = {
    "SOBEL": "rh/dados_sobel.parquet",
    "JMT": "rh/dados_jmt.parquet",
    "3F": "rh/dados_3f.parquet"
}

# Função para formatar datas e valores
def formatar_dados(df):
    for col in df.columns:
        if 'data' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')
        if 'salario' in col.lower() or 'valor' in col.lower():
            df[col] = pd.to_numeric(df[col], errors='coerce').apply(lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else '')
    return df

# Carregamento apenas de cabeçalhos para filtros
@st.cache_data
def carregar_cabecalhos():
    dados = []
    for empresa, path in ARQUIVOS_PARQUET.items():
        if os.path.exists(path):
            df = pd.read_parquet(path, columns=["codigo", "nome"])
            df["empresa"] = empresa
            dados.append(df)
    return pd.concat(dados, ignore_index=True)

# Carrega dados completos de um colaborador
@st.cache_data
def carregar_dados_colaborador(empresa, nome):
    df = pd.read_parquet(ARQUIVOS_PARQUET[empresa])
    df = df[df["nome"] == nome]
    return formatar_dados(df)

# Interface Streamlit
st.set_page_config(page_title="Ficha Cadastral de Colaboradores", layout="wide")
st.title("📋 Ficha Cadastral de Colaboradores")

cabecalhos = carregar_cabecalhos()

col1, col2 = st.columns(2)
empresa_sel = col1.selectbox("Selecione a Empresa:", sorted(cabecalhos["empresa"].unique()))

nomes = cabecalhos[cabecalhos["empresa"] == empresa_sel]["nome"].dropna().unique()
nome_sel = col2.selectbox("Selecione o Nome do Colaborador:", sorted(nomes))

if empresa_sel and nome_sel:
    df = carregar_dados_colaborador(empresa_sel, nome_sel)
    if df.empty:
        st.warning("Nenhum dado encontrado para o colaborador selecionado.")
    else:
        row = df.iloc[0]
        st.markdown(f"### 👤 {row['nome']}")

        with st.expander("🧍 Dados Pessoais"):
            st.write({
                "Matrícula": row.get("codigo"),
                "Data de Nascimento": row.get("datanascimento"),
                "Sexo": row.get("sexo"),
                "Raça": row.get("raca"),
                "Estado Civil": row.get("estadocivil"),
                "UF Nascimento": row.get("ufnascimento"),
                "Cidade Nascimento": row.get("cidadenascimento"),
                "Nome Pai": row.get("nomepai"),
                "Nome Mãe": row.get("nomemae")
            })

        with st.expander("🗂️ Documentos"):
            st.write({
                "CPF": row.get("cpf"),
                "CTPS": row.get("numeroctps"),
                "PIS": row.get("nis"),
                "Número Identidade": row.get("numeroidentidade"),
                "Órgão Emissor": row.get("orgaoemissor"),
                "UF Documento": row.get("ufdocumento"),
                "Data Expedição": row.get("dataexpedicao")
            })

        with st.expander("💼 Dados do Vínculo"):
            st.write({
                "Data de Admissão": row.get("dataadmissao"),
                "Salário Fixo": row.get("salariofixo"),
                "Categoria do Trabalhador": row.get("categoriatrabalhador"),
                "Tipo de Admissão": row.get("tipoadmissao"),
                "Tipo de Atividade": row.get("tipoatividade"),
                "Data Fim Contrato": row.get("datafimcontrato"),
                "Data de Rescisão": row.get("datarescisao"),
                "Motivo Rescisão": row.get("motivorescisao")
            })

        with st.expander("👨‍👩‍👧‍👦 Dependentes e Complementares"):
            st.write({
                "Salário Família": row.get("salariofamilia"),
                "Pensão Alimentícia": row.get("pensaoalimenticia"),
                "% Pensão": row.get("percentualpensaoalimenticia"),
                "% Pensão FGTS": row.get("percentualpensaoalimenticiafgts")
            })

            # Dados de dependentes
            dependentes_cols = [
                "nome_dependente", "datainclusao", "datanascimento", "tipoparentesco",
                "impostorenda", "salariofamilia", "pensaoalimenticia",
                "percentualpensaoalimenticia", "percentualpensaoalimenticiafgts",
                "cpf", "ufnascimento", "cidadenascimento",
                "cartoriocertidao", "numeroregistrocertidao", "dataentregacertidao"
            ]
            dependentes = df[dependentes_cols].dropna(subset=["nome_dependente"]).copy()

            if not dependentes.empty:
                st.markdown("#### Dependentes Cadastrados")
                st.dataframe(dependentes.reset_index(drop=True))
            else:
                st.info("Nenhum dependente cadastrado.")

        st.markdown("---")
