import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Simulador de Preço de Venda Sobel", layout="wide")
st.title("📊 Simulador de Formação de Preço de Venda")
st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=300)

# Session State
if 'df_editado' not in st.session_state:
    st.session_state.df_editado = None

# Carga padrão
arquivo_padrao = "Custo de reposição.xlsx"
if os.path.exists(arquivo_padrao):
    df_padrao = pd.read_excel(arquivo_padrao)
    df_padrao.columns = df_padrao.columns.str.strip()
else:
    st.warning("Arquivo padrão não encontrado.")
    df_padrao = pd.DataFrame()

# Sidebar
st.sidebar.header("Parâmetros Globais")
frete_padrao = st.sidebar.number_input("Frete por Caixa (R$)", min_value=0.0, value=1.50, step=0.01)
contrato_percentual = st.sidebar.number_input("% Contrato", min_value=0.0, max_value=100.0, value=1.00, step=0.01) / 100
comissao_padrao = st.sidebar.number_input("% Comissão", min_value=0.0, max_value=100.0, value=0.00, step=0.1) / 100
uf_selecionado = st.sidebar.selectbox("Selecione a UF", options=df_padrao["UF"].dropna().unique().tolist()) if not df_padrao.empty else ""
tipo_frete = st.sidebar.radio("Tipo de Frete", ("CIF", "FOB"))

# Upload
uploaded_file = st.file_uploader("📂 Envie sua planilha atualizada (.xlsx)", type="xlsx")

if uploaded_file:
    df_base = pd.read_excel(uploaded_file)
    df_base.columns = df_base.columns.str.strip()
    df_base = df_base[df_base["UF"] == uf_selecionado].copy()
elif not df_padrao.empty:
    df_base = df_padrao[df_padrao["UF"] == uf_selecionado].copy()
else:
    st.stop()
# Produtos esperados
produtos_esperados = [
    "ÁGUA SANITÁRIA 5L", "ÁGUA SANITÁRIA 2L", "ÁGUA SANITÁRIA 1L",
    "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
    "AMACIANTE 5L", "AMACIANTE 2L",
    "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
    "LAVA LOUÇAS 500ML", "LAVA LOUÇAS 5L",
    "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
    "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
    "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
]
df_base = df_base[df_base["Descrição"].isin(produtos_esperados)].copy()

# Ajustes
colunas_necessarias = ["Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", "ICMS ST", "ICMS", "MVA", "Comissão"]
for col in colunas_necessarias:
    if col not in df_base.columns:
        df_base[col] = 0.0 if col != "Quantidade" else 1

# Aplicação dos parâmetros globais
df_base["Frete Caixa"] = frete_padrao
df_base["Contrato"] = contrato_percentual
df_base["Comissão"] = df_base["Comissão"].apply(lambda x: comissao_padrao if pd.isna(x) or x == 0 else x)

# Preencher Ponto de Equilíbrio
def preencher_preco_equilibrio(df):
    df_atualizado = df.copy()
    alertas = []
    for index, row in df_atualizado.iterrows():
        custo_total_unit = row["Custo NET"] + row["Custo Fixo"]
        frete_unit = row["Frete Caixa"] if tipo_frete == "CIF" else 0
        despesas_percentuais = (
            row["ICMS"] + row["COFINS"] + row["PIS"] +
            row["Comissão"] + row["Bonificação"] +
            row["Contigência"] + row["Contrato"] + row["%Estrategico"]
        )

        if despesas_percentuais >= 1:
            alertas.append(f"{row['Descrição']}: Despesas acima de 100%.")
            preco_equilibrio_unit = 0
        else:
            try:
                preco_equilibrio_unit = (custo_total_unit + frete_unit) / (1 - despesas_percentuais)
                preco_equilibrio_unit = round(preco_equilibrio_unit, 2)
            except ZeroDivisionError:
                preco_equilibrio_unit = 0

        df_atualizado.at[index, "Preço de Venda"] = preco_equilibrio_unit

    return df_atualizado, alertas

# Botão
if st.button("📌 Preencher com Ponto de Equilíbrio"):
    df_base, alertas = preencher_preco_equilibrio(df_base)
    if alertas:
        for msg in alertas:
            st.warning(msg)

st.session_state.df_editado = df_base.copy()
# Editor
st.markdown("### ✏️ Edite os dados abaixo para simulação em lote")
df_editado = st.data_editor(st.session_state.df_editado, use_container_width=True, num_rows="dynamic")
st.session_state.df_editado = df_editado

# Função cálculo
def calcular_linha(row):
    preco_venda = row["Preço de Venda"]
    qtd = row["Quantidade"]
    subtotal = preco_venda * qtd

    frete_total = row["Frete Caixa"] * qtd if tipo_frete == "CIF" else 0
    frete_unit = row["Frete Caixa"] if tipo_frete == "CIF" else 0

    ipi_total = subtotal * row["IPI"]
    mva_percentual = row["MVA"]
    base_icms_st = (subtotal + ipi_total) * (1 + mva_percentual)
    icms_proprio = subtotal * row["ICMS"]
    icms_st = (base_icms_st * row["ICMS"]) - icms_proprio
    icms_st = max(icms_st, 0)

    custo_total_unit = row["Custo NET"] + row["Custo Fixo"]
    despesas_percentuais = (
        row["ICMS"] + row["COFINS"] + row["PIS"] +
        row["Comissão"] + row["Bonificação"] +
        row["Contigência"] + row["Contrato"] + row["%Estrategico"]
    )

    despesas_reais = preco_venda * despesas_percentuais * qtd + frete_total
    lucro_bruto = (preco_venda - custo_total_unit) * qtd - despesas_reais

    if lucro_bruto > 0:
        lucro_liquido = lucro_bruto / 1.34
        irpj = lucro_liquido * 0.25
        csll = lucro_liquido * 0.09
    else:
        lucro_liquido = lucro_bruto
        irpj = 0
        csll = 0

    receita_total = subtotal
    lucro_percentual = (lucro_liquido / receita_total) * 100 if receita_total > 0 else 0
    total_nf = subtotal + ipi_total + icms_st

    if lucro_liquido < 0 and despesas_percentuais < 1:
        try:
            preco_equilibrio_unit = (custo_total_unit + frete_unit) / (1 - despesas_percentuais)
            preco_equilibrio_unit = round(preco_equilibrio_unit, 2)
        except ZeroDivisionError:
            preco_equilibrio_unit = 0
    else:
        preco_equilibrio_unit = preco_venda

    return pd.Series({
        "Subtotal (R$)": subtotal,
        "Frete Total (R$)": frete_total,
        "IPI (R$)": ipi_total,
        "Base ICMS-ST (R$)": base_icms_st,
        "ICMS-ST (R$)": icms_st,
        "Lucro Bruto (R$)": lucro_bruto,
        "Lucro Líquido (R$)": lucro_liquido,
        "IRPJ (R$)": irpj,
        "CSLL (R$)": csll,
        "Lucro %": lucro_percentual,
        "Total NF (R$)": total_nf,
        "Ponto de Equilíbrio (R$)": preco_equilibrio_unit
    })

# Cálculo
resultados = st.session_state.df_editado.apply(calcular_linha, axis=1)
resultado_final = pd.concat([st.session_state.df_editado, resultados], axis=1)
# Resultado
st.markdown("### 📊 Resultado da Simulação")
def color_negative_red(val):
    try:
        if float(val) < 0:
            return 'color: red'
        return 'color: black'
    except:
        return 'color: black'

styled_df = resultado_final.style.format({
    "Preço de Venda": "R$ {:.2f}",
    "Custo NET": "R$ {:.2f}",
    "Custo Fixo": "R$ {:.2f}",
    "Subtotal (R$)": "R$ {:.2f}",
    "Frete Total (R$)": "R$ {:.2f}",
    "IPI (R$)": "R$ {:.2f}",
    "Base ICMS-ST (R$)": "R$ {:.2f}",
    "ICMS-ST (R$)": "R$ {:.2f}",
    "Lucro Bruto (R$)": "R$ {:.2f}",
    "Lucro Líquido (R$)": "R$ {:.2f}",
    "IRPJ (R$)": "R$ {:.2f}",
    "CSLL (R$)": "R$ {:.2f}",
    "Lucro %": "{:.2f}%",
    "Total NF (R$)": "R$ {:.2f}",
    "Ponto de Equilíbrio (R$)": "R$ {:.2f}"
}).apply(lambda x: [color_negative_red(v) for v in x],
        subset=["Lucro Bruto (R$)", "Lucro Líquido (R$)", "Lucro %"])

st.dataframe(styled_df, use_container_width=True)

# Exportação
st.markdown("### 📄 Baixar resultado em Excel")
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    resultado_final.to_excel(writer, index=False, sheet_name="Resultado")

st.download_button(
    label="📄 Baixar Excel com Resultado",
    data=excel_buffer.getvalue(),
    file_name="resultado_simulacao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Notas explicativas
st.markdown("""
### ℹ️ **Notas Explicativas**

Este **Simulador de Formação de Preço de Venda - Sobel Suprema** foi desenvolvido para apoiar as áreas **Comercial, Financeira e Controladoria**, garantindo uma correta formação de preço, considerando todos os componentes de custo, despesas, impostos e margens estratégicas.

---

### 🎯 **Objetivo**
Permitir que os gestores realizem simulações e ajustes na composição do preço de venda, de forma prática e transparente, facilitando a análise do impacto de cada variável na margem e no resultado final.

---

### 🧩 **Lógica de Cálculo Utilizada**

1️⃣ **Subtotal Calculado**  
> **Subtotal = Preço de Venda × Quantidade + Frete Total**

2️⃣ **IPI Total**  
> **IPI Total = Subtotal × % IPI**

3️⃣ **Base de Cálculo ICMS-ST**  
> **Base ICMS-ST = (Subtotal + IPI Total) × (1 + MVA)**  
> **ICMS-ST = (Base × % ICMS) - (Subtotal × % ICMS)**

4️⃣ **Despesas Percentuais e Fixas**  
> Soma de: ICMS, COFINS, PIS, Comissão, Bonificação, Contingência, Contrato, % Estratégico  
> **Despesas = Preço × Soma % × Quantidade + Frete Total**

5️⃣ **Lucro Bruto**  
> **(Preço - Custo Unitário) × Quantidade - Despesas**

6️⃣ **Lucro Líquido (presumido com carga de 34%)**  
> **Lucro Bruto ÷ 1,34**

7️⃣ **IRPJ e CSLL**  
> **IRPJ = 25% do Lucro Líquido**  
> **CSLL = 9% do Lucro Líquido**

8️⃣ **Lucro %**  
> **(Lucro Líquido ÷ Receita) × 100**

9️⃣ **Total NF**  
> **Subtotal + IPI + ICMS-ST**

---

### 💡 Observação
O campo **Comissão** agora aceita dois comportamentos:
- Valor global da sidebar é aplicado como padrão;
- Se a célula do produto estiver preenchida com valor > 0, ela prevalece.

---
""")
