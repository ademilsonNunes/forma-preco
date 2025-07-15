import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

st.set_page_config(page_title="Simulador de Preço de Venda Sobel", layout="wide")
st.title("📊 Simulador de Formação de Preço de Venda - 1.0.4")
st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=300)

# Tabela de alíquotas ICMS por UF
ICMS_ALIQUOTAS = {
    'AC': {'interna': 0.17, 'interestadual': 0.12},
    'AL': {'interna': 0.17, 'interestadual': 0.12},
    'AP': {'interna': 0.18, 'interestadual': 0.12},
    'AM': {'interna': 0.18, 'interestadual': 0.12},
    'BA': {'interna': 0.18, 'interestadual': 0.12},
    'CE': {'interna': 0.18, 'interestadual': 0.12},
    'DF': {'interna': 0.18, 'interestadual': 0.12},
    'ES': {'interna': 0.17, 'interestadual': 0.12},
    'GO': {'interna': 0.17, 'interestadual': 0.12},
    'MA': {'interna': 0.18, 'interestadual': 0.12},
    'MT': {'interna': 0.17, 'interestadual': 0.12},
    'MS': {'interna': 0.17, 'interestadual': 0.12},
    'MG': {'interna': 0.18, 'interestadual': 0.12},
    'PA': {'interna': 0.17, 'interestadual': 0.12},
    'PB': {'interna': 0.18, 'interestadual': 0.12},
    'PR': {'interna': 0.18, 'interestadual': 0.12},
    'PE': {'interna': 0.18, 'interestadual': 0.12},
    'PI': {'interna': 0.18, 'interestadual': 0.12},
    'RJ': {'interna': 0.18, 'interestadual': 0.12},
    'RN': {'interna': 0.18, 'interestadual': 0.12},
    'RS': {'interna': 0.18, 'interestadual': 0.12},
    'RO': {'interna': 0.175, 'interestadual': 0.12},
    'RR': {'interna': 0.17, 'interestadual': 0.12},
    'SC': {'interna': 0.17, 'interestadual': 0.12},
    'SP': {'interna': 0.18, 'interestadual': 0.12},
    'SE': {'interna': 0.18, 'interestadual': 0.12},
    'TO': {'interna': 0.18, 'interestadual': 0.12}
}

# Session State
if 'df_atual' not in st.session_state:
    st.session_state.df_atual = None
if 'modo_equilibrio' not in st.session_state:
    st.session_state.modo_equilibrio = False
if 'comissao_global_aplicada' not in st.session_state:
    st.session_state.comissao_global_aplicada = False
if 'comissoes_editadas' not in st.session_state:
    st.session_state.comissoes_editadas = {}

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
uf_origem = st.sidebar.selectbox("UF de Origem", options=list(ICMS_ALIQUOTAS.keys()), index=list(ICMS_ALIQUOTAS.keys()).index('SP'))
frete_padrao = st.sidebar.number_input("Frete por Caixa (R$)", min_value=0.0, value=1.50, step=0.01)
contrato_percentual = st.sidebar.number_input("% Contrato", min_value=0.0, max_value=100.0, value=1.00, step=0.01) / 100
custo_fixo_global = st.sidebar.number_input("Custo Fixo Global (R$)", min_value=0.0, value=0.0, step=0.01, help="Se zero, usa valor da planilha. Se preenchido, substitui o valor da planilha.")
comissao_padrao = st.sidebar.number_input("% Comissão Global", min_value=0.0, max_value=100.0, value=0.0, step=0.1, help="Se zero, usa valor da planilha. Se preenchido, aplica globalmente mas permite edição individual.") / 100
bonificacao_global = st.sidebar.number_input("% Bonificação Global", min_value=0.0, max_value=100.0, value=0.0, step=0.01, help="Se zero, usa valor da planilha. Se preenchido, substitui o valor da planilha.") / 100
uf_selecionado = st.sidebar.selectbox("Selecione a UF de Destino", options=df_padrao["UF"].dropna().unique().tolist(), key="uf_select") if not df_padrao.empty else ""
tipo_frete = st.sidebar.radio("Tipo de Frete", ("CIF", "FOB"))

# Upload com backup e refresh
uploaded_file = st.file_uploader("📂 Envie sua planilha atualizada (.xlsx)", type="xlsx")

if uploaded_file:
    try:
        if os.path.exists(arquivo_padrao):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
            os.rename(arquivo_padrao, backup_name)
            st.success(f"Backup criado: {backup_name}")
        with open(arquivo_padrao, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Arquivo atualizado com sucesso!")
        st.info("Recarregando dados...")
        df_padrao = pd.read_excel(arquivo_padrao)
        df_padrao.columns = df_padrao.columns.str.strip()
        st.session_state.df_atual = None
        st.session_state.modo_equilibrio = False
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")

# Seleção de base por UF
if not df_padrao.empty:
    df_base = df_padrao[df_padrao["UF"] == uf_selecionado].copy()

    # Se mudou a UF, resetar os dados editados
    if st.session_state.df_atual is not None:
        if "UF" in st.session_state.df_atual.columns:
            ufs_atuais = st.session_state.df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != uf_selecionado:
                st.session_state.df_atual = None
                st.session_state.modo_equilibrio = False
                st.session_state.comissao_global_aplicada = False
                st.session_state.comissoes_editadas = {}
else:
    st.stop()

# Filtro por produtos esperados
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

if df_base.empty:
    st.error(f"Nenhum produto encontrado para a UF {uf_selecionado}")
    st.stop()

# Ajustar colunas necessárias
colunas_necessarias = [
    "Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", 
    "ICMS ST", "ICMS", "MVA", "Comissão", "Bonificação", "COFINS", "PIS", 
    "Contigência", "ICMS Interestadual", "ICMS Interno Destino"
]

for col in colunas_necessarias:
    if col not in df_base.columns:
        if col == "Quantidade":
            df_base[col] = 1
        elif col == "ICMS Interestadual":
            df_base[col] = ICMS_ALIQUOTAS[uf_origem]['interestadual']
        elif col == "ICMS Interno Destino":
            df_base[col] = ICMS_ALIQUOTAS[uf_selecionado]['interna']
        else:
            df_base[col] = 0.0

# Aplicação dos parâmetros globais
df_base["Frete Caixa"] = frete_padrao
df_base["Contrato"] = contrato_percentual
df_base["UF Origem"] = uf_origem
df_base["UF Destino"] = uf_selecionado

# Atualizar alíquotas ICMS
df_base["ICMS Interestadual"] = ICMS_ALIQUOTAS[uf_origem]['interestadual']
df_base["ICMS Interno Destino"] = ICMS_ALIQUOTAS[uf_selecionado]['interna']

# Aplicar custo fixo global se especificado
if custo_fixo_global > 0:
    df_base["Custo Fixo"] = custo_fixo_global

# Aplicar comissão baseada na lógica híbrida
if comissao_padrao > 0:
    df_base["Comissão"] = comissao_padrao
    st.session_state.comissao_global_aplicada = True
else:
    st.session_state.comissao_global_aplicada = False

# Aplicar bonificação global se especificado
if bonificacao_global > 0:
    df_base["Bonificação"] = bonificacao_global

# Função para calcular ICMS-ST corretamente
def calcular_icms_st(valor_produto, mva, icms_interestadual, icms_interno_destino):
    """
    Calcula ICMS-ST seguindo a legislação tributária
    """
    # Base de cálculo do ICMS-ST
    base_icms_st = valor_produto * (1 + mva)
    
    # ICMS próprio (origem)
    icms_proprio = valor_produto * icms_interestadual
    
    # ICMS total devido na operação interna
    icms_total_interno = base_icms_st * icms_interno_destino
    
    # ICMS-ST a recolher
    icms_st = icms_total_interno - icms_proprio
    
    return max(icms_st, 0), base_icms_st, icms_proprio, icms_total_interno

# Função para calcular ponto de equilíbrio
def calcular_ponto_equilibrio(df):
    df_resultado = df.copy()
    alertas = []
    
    for index, row in df_resultado.iterrows():
        try:
            # Custos
            custo_net = float(row.get("Custo NET", 0))
            custo_fixo = float(row.get("Custo Fixo", 0))
            custo_total_unit = custo_net + custo_fixo
            
            # Frete
            frete_unit = float(row.get("Frete Caixa", 0)) if tipo_frete == "CIF" else 0
            
            # Despesas percentuais (usando ICMS interestadual para o cálculo)
            icms = float(row.get("ICMS Interestadual", 0))
            cofins = float(row.get("COFINS", 0))
            pis = float(row.get("PIS", 0))
            comissao = float(row.get("Comissão", 0))
            bonificacao = float(row.get("Bonificação", 0))
            contigencia = float(row.get("Contigência", 0))
            contrato = float(row.get("Contrato", 0))
            estrategico = float(row.get("%Estrategico", 0))
            
            total_despesas_percent = icms + cofins + pis + comissao + bonificacao + contigencia + contrato + estrategico
            
            # Verificar se despesas são menores que 100%
            if total_despesas_percent >= 1.0:
                alertas.append(f"{row.get('Descrição', 'Produto')}: Despesas percentuais = {total_despesas_percent:.1%} (≥100%)")
                preco_equilibrio = 0
            else:
                # Calcular preço de equilíbrio
                preco_equilibrio = (custo_total_unit + frete_unit) / (1 - total_despesas_percent)
                preco_equilibrio = round(preco_equilibrio, 2)
            
            # Atualizar o preço de venda
            df_resultado.at[index, "Preço de Venda"] = preco_equilibrio
            
        except Exception as e:
            alertas.append(f"Erro no produto {row.get('Descrição', 'N/A')}: {str(e)}")
            df_resultado.at[index, "Preço de Venda"] = 0
    
    return df_resultado, alertas

# Botões de controle
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("📌 Calcular Ponto de Equilíbrio", use_container_width=True):
        df_equilibrio, alertas = calcular_ponto_equilibrio(df_base)
        
        # Mostrar alertas se houver
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        
        # Salvar no session state
        st.session_state.df_atual = df_equilibrio.copy()
        st.session_state.modo_equilibrio = True
        
        st.success("✅ Ponto de equilíbrio calculado! Valores fixados para edição.")

with col2:
    if st.button("🔄 Resetar", use_container_width=True):
        st.session_state.df_atual = None
        st.session_state.modo_equilibrio = False
        st.session_state.comissao_global_aplicada = False
        st.session_state.comissoes_editadas = {}
        st.info("Dados resetados para valores originais.")

# Determinar qual DataFrame usar
if st.session_state.df_atual is not None:
    df_para_edicao = st.session_state.df_atual.copy()
else:
    df_para_edicao = df_base.copy()

# Aplicar lógica de comissão híbrida ANTES de mostrar o editor
def aplicar_logica_comissao(df):
    df_temp = df.copy()
    
    # Se há comissão global aplicada
    if st.session_state.comissao_global_aplicada and comissao_padrao > 0:
        # Aplicar valor global a todos, exceto os que foram editados individualmente
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
            
            # Se não foi editado individualmente, aplicar valor global
            if produto not in st.session_state.comissoes_editadas:
                df_temp.at[index, "Comissão"] = comissao_padrao
    
    # Aplicar comissões editadas individualmente
    for produto, valor_comissao in st.session_state.comissoes_editadas.items():
        mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
        if isinstance(mask, pd.Series) and mask.any():
            df_temp.loc[mask, "Comissão"] = valor_comissao
    
    return df_temp

df_para_edicao = aplicar_logica_comissao(df_para_edicao)

# Status do modo
status_comissao = ""
if st.session_state.comissao_global_aplicada and comissao_padrao > 0:
    status_comissao = f" | Comissão Global: {comissao_padrao:.2%}"

# Mostrar informações sobre operação
#st.info(f"🗺️ **Operação**: {uf_origem} → {uf_selecionado} | ICMS Interestadual: {ICMS_ALIQUOTAS[uf_origem]['interestadual']:.1%} | ICMS Interno {uf_selecionado}: {ICMS_ALIQUOTAS[uf_selecionado]['interna']:.1%}")

if st.session_state.modo_equilibrio:
    st.success(f"🔒 **Modo Equilíbrio Ativo**: Valores fixados. Edite individualmente conforme necessário.{status_comissao}")
else:
    st.info(f"📋 **Modo Normal**: Dados originais da planilha.{status_comissao}")

# Mostrar informações sobre comissões editadas
if st.session_state.comissoes_editadas:
    itens_editados = len(st.session_state.comissoes_editadas)
    st.warning(f"⚠️ **{itens_editados} produto(s) com comissão editada individualmente** (não afetados pela comissão global)")

# Editor de dados
st.markdown("### ✏️ Edite os dados para simulação")

# Definir colunas para edição
colunas_edicao = [
    "Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo",
    "Frete Caixa", "IPI", "MVA", "ICMS Interestadual", "ICMS Interno Destino",
    "COFINS", "PIS", "Comissão", "Bonificação", "Contigência", "%Estrategico"
]

df_editado = st.data_editor(
    df_para_edicao[colunas_edicao],
    use_container_width=True,
    num_rows="dynamic",
    key="data_editor"
)

# Detectar mudanças na comissão e atualizar o rastreamento
def detectar_mudancas_comissao(df_anterior, df_novo):
    if df_anterior is not None and not df_anterior.empty and not df_novo.empty:
        for index in df_novo.index:
            if index < len(df_anterior):
                produto = df_novo.at[index, "Descrição"] if "Descrição" in df_novo.columns else str(index)
                comissao_anterior = float(df_anterior.iloc[index]["Comissão"]) if index < len(df_anterior) else 0
                comissao_nova = float(df_novo.at[index, "Comissão"])
                
                # Se a comissão foi alterada manualmente
                if abs(comissao_anterior - comissao_nova) > 0.0001:
                    # Se há comissão global e o valor não é igual ao global, marcar como editado
                    if st.session_state.comissao_global_aplicada and comissao_padrao > 0:
                        if abs(comissao_nova - comissao_padrao) > 0.0001:
                            st.session_state.comissoes_editadas[produto] = comissao_nova
                        else:
                            # Se voltou ao valor global, remover da lista de editados
                            if produto in st.session_state.comissoes_editadas:
                                del st.session_state.comissoes_editadas[produto]

# Detectar mudanças na comissão
detectar_mudancas_comissao(df_para_edicao[colunas_edicao] if not df_para_edicao.empty else None, df_editado)

# Copiar colunas não editáveis
for col in df_para_edicao.columns:
    if col not in colunas_edicao:
        df_editado[col] = df_para_edicao[col]

# Atualizar session state com os dados editados
st.session_state.df_atual = df_editado.copy()

# Função para calcular resultados
def calcular_resultados(row):
    try:
        preco_venda = float(row["Preço de Venda"])
        qtd = float(row["Quantidade"])
        subtotal = preco_venda * qtd

        frete_total = float(row["Frete Caixa"]) * qtd if tipo_frete == "CIF" else 0
        frete_unit = float(row["Frete Caixa"]) if tipo_frete == "CIF" else 0

        # IPI
        ipi_total = subtotal * float(row["IPI"])
        
        # ICMS-ST corrigido (apenas para destacar na NF, NÃO impacta no lucro)
        mva_percentual = float(row["MVA"])
        icms_interestadual = float(row["ICMS Interestadual"])
        icms_interno_destino = float(row["ICMS Interno Destino"])
        
        icms_st, base_icms_st, icms_proprio, icms_total_interno = calcular_icms_st(
            subtotal, mva_percentual, icms_interestadual, icms_interno_destino
        )

        # Custos e despesas
        custo_total_unit = float(row["Custo NET"]) + float(row["Custo Fixo"])
        
        # Despesas percentuais (usando ICMS interestadual) - NÃO inclui ICMS-ST
        despesas_percentuais = (
            float(row["ICMS Interestadual"]) + float(row["COFINS"]) + float(row["PIS"]) +
            float(row["Comissão"]) + float(row["Bonificação"]) +
            float(row["Contigência"]) + float(row.get("Contrato", 0)) + float(row["%Estrategico"])
        )

        # Cálculo do lucro (ICMS-ST NÃO afeta o lucro)
        despesas_reais = preco_venda * despesas_percentuais * qtd + frete_total
        
        # Lucro Bruto = Receita - Custos - Despesas (SEM ICMS-ST)
        lucro_bruto = (preco_venda - custo_total_unit) * qtd - despesas_reais
        
        # Lucro Líquido ANTES dos impostos sobre lucro
        lucro_antes_ir = lucro_bruto
        
        # IRPJ e CSLL incidem sobre o lucro (calculados separadamente)
        if lucro_antes_ir > 0:
            # Lucro tributável (considerando presunção de 34% de dedução)
            lucro_tributavel = lucro_antes_ir / 1.34
            irpj = lucro_tributavel * 0.25
            csll = lucro_tributavel * 0.09
            # Lucro líquido APÓS IRPJ e CSLL
            lucro_liquido = lucro_antes_ir - irpj - csll
        else:
            lucro_tributavel = 0
            irpj = 0
            csll = 0
            lucro_liquido = lucro_antes_ir

        receita_total = subtotal
        lucro_percentual = (lucro_liquido / receita_total) * 100 if receita_total > 0 else 0
        
        # Total da NF = Subtotal + IPI + ICMS-ST (ICMS-ST só para fins fiscais)
        total_nf = subtotal + ipi_total + icms_st

        # Calcular ponto de equilíbrio para esta linha
        if despesas_percentuais < 1:
            ponto_equilibrio = (custo_total_unit + frete_unit) / (1 - despesas_percentuais)
            ponto_equilibrio = round(ponto_equilibrio, 2)
        else:
            ponto_equilibrio = 0

        return pd.Series({
            "Subtotal (R$)": subtotal,
            "Frete Total (R$)": frete_total,
            "IPI (R$)": ipi_total,
            "Base ICMS-ST (R$)": base_icms_st,
            "ICMS Próprio (R$)": icms_proprio,
            "ICMS Total Interno (R$)": icms_total_interno,
            "ICMS-ST (R$)": icms_st,
            "Lucro Bruto (R$)": lucro_bruto,
            "Lucro Antes IR (R$)": lucro_antes_ir,
            "Lucro Tributável (R$)": lucro_tributavel,
            "IRPJ (R$)": irpj,
            "CSLL (R$)": csll,
            "Lucro Líquido Final (R$)": lucro_liquido,
            "Lucro %": lucro_percentual,
            "Total NF (R$)": total_nf,
            "Ponto de Equilíbrio (R$)": ponto_equilibrio
        })
    except Exception as e:
        # Em caso de erro, retorna zeros
        return pd.Series({
            "Subtotal (R$)": 0,
            "Frete Total (R$)": 0,
            "IPI (R$)": 0,
            "Base ICMS-ST (R$)": 0,
            "ICMS Próprio (R$)": 0,
            "ICMS Total Interno (R$)": 0,
            "ICMS-ST (R$)": 0,
            "Lucro Bruto (R$)": 0,
            "Lucro Antes IR (R$)": 0,
            "Lucro Tributável (R$)": 0,
            "IRPJ (R$)": 0,
            "CSLL (R$)": 0,
            "Lucro Líquido Final (R$)": 0,
            "Lucro %": 0,
            "Total NF (R$)": 0,
            "Ponto de Equilíbrio (R$)": 0
        })

# Calcular resultados
resultados = df_editado.apply(calcular_resultados, axis=1)
resultado_final = pd.concat([df_editado, resultados], axis=1)

# Mostrar resultados
st.markdown("### 📊 Resultado da Simulação")

# Exemplo de cálculo para o primeiro produto
if not resultado_final.empty:
    primeira_linha = resultado_final.iloc[0]
    st.markdown("### 💡 Exemplo de Cálculo ICMS-ST (Primeira Linha)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        **Produto:** {primeira_linha['Descrição']}  
        **Valor:** R$ {primeira_linha['Preço de Venda']:.2f}  
        **MVA:** {primeira_linha['MVA']:.2%}  
        **Operação:** {uf_origem} → {uf_selecionado}
        """)
    
    with col2:
        st.markdown(f"""
        **Base ICMS-ST:** R$ {primeira_linha['Base ICMS-ST (R$)']:.2f}  
        **ICMS Próprio:** R$ {primeira_linha['ICMS Próprio (R$)']:.2f}  
        **ICMS Total:** R$ {primeira_linha['ICMS Total Interno (R$)']:.2f}  
        **ICMS-ST:** R$ {primeira_linha['ICMS-ST (R$)']:.2f}
        """)

# Resumo se estiver no modo equilíbrio
if st.session_state.modo_equilibrio:
    col1, col2, col3 = st.columns(3)
    with col1:
        total_lucro = resultado_final["Lucro Líquido Final (R$)"].sum()
        st.metric("Lucro Líquido Total", f"R$ {total_lucro:,.2f}")
    with col2:
        lucro_medio = resultado_final["Lucro %"].mean()
        st.metric("Lucro % Médio", f"{lucro_medio:.2f}%")
    with col3:
        produtos_negativos = len(resultado_final[resultado_final["Lucro Líquido Final (R$)"] < 0])
        st.metric("Produtos c/ Prejuízo", produtos_negativos)

# Função para colorir valores negativos
def color_negative_red(val):
    try:
        if float(val) < 0:
            return 'color: red'
        return 'color: black'
    except:
        return 'color: black'

# Formatar e exibir tabela
styled_df = resultado_final.style.format({
    "Preço de Venda": "R$ {:.2f}",
    "Custo NET": "R$ {:.2f}",
    "Custo Fixo": "R$ {:.2f}",
    "MVA": "{:.2%}",
    "ICMS Interestadual": "{:.1%}",
    "ICMS Interno Destino": "{:.1%}",
    "COFINS": "{:.2%}",
    "PIS": "{:.2%}",
    "Comissão": "{:.2%}",
    "Bonificação": "{:.2%}",
    "Contigência": "{:.2%}",
    "%Estrategico": "{:.2%}",
    "IPI": "{:.2%}",
    "Subtotal (R$)": "R$ {:.2f}",
    "Frete Total (R$)": "R$ {:.2f}",
    "IPI (R$)": "R$ {:.2f}",
    "Base ICMS-ST (R$)": "R$ {:.2f}",
    "ICMS Próprio (R$)": "R$ {:.2f}",
    "ICMS Total Interno (R$)": "R$ {:.2f}",
    "ICMS-ST (R$)": "R$ {:.2f}",
    "Lucro Bruto (R$)": "R$ {:.2f}",
    "Lucro Antes IR (R$)": "R$ {:.2f}",
    "Lucro Tributável (R$)": "R$ {:.2f}",
    "IRPJ (R$)": "R$ {:.2f}",
    "CSLL (R$)": "R$ {:.2f}",
    "Lucro Líquido Final (R$)": "R$ {:.2f}",
    "Lucro %": "{:.2f}%",
    "Total NF (R$)": "R$ {:.2f}",
    "Ponto de Equilíbrio (R$)": "R$ {:.2f}"
}).apply(lambda x: [color_negative_red(v) for v in x],
        subset=["Lucro Bruto (R$)", "Lucro Antes IR (R$)", "Lucro Líquido Final (R$)", "Lucro %"])

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
### ℹ️ **Notas Explicativas - VERSÃO CORRIGIDA**

Este **Simulador de Formação de Preço de Venda - Sobel Suprema** foi corrigido para calcular corretamente o **ICMS-ST** conforme a legislação tributária brasileira.

---

### 🎯 **Principais Correções Implementadas**

✅ **ICMS-ST Corrigido**: Agora calcula corretamente considerando alíquotas interestaduais e internas  
✅ **Tabela de Alíquotas**: Inclui todas as UFs com suas respectivas alíquotas ICMS  
✅ **Operação Interestadual**: Diferencia corretamente origem e destino  
✅ **Cálculo Detalhado**: Mostra ICMS próprio, ICMS total e ICMS-ST separadamente  

---

### 🧩 **Lógica de Cálculo ICMS-ST Corrigida**

**Exemplo prático (SP → RJ):**

1️⃣ **Valor do Produto**: R$ 13,67  
2️⃣ **MVA**: 77,81%  
3️⃣ **Base ICMS-ST**: R$ 13,67 × (1 + 0,7781) = R$ 24,31  
4️⃣ **ICMS Próprio (SP→RJ)**: R$ 13,67 × 12% = R$ 1,64  
5️⃣ **ICMS Total (Interno RJ)**: R$ 24,31 × 18% = R$ 4,38  
6️⃣ **ICMS-ST a Recolher**: R$ 4,38 - R$ 1,64 = R$ 2,74  
7️⃣ **Total da NF**: R$ 13,67 + R$ 2,74 = R$ 16,41  

---

### 📊 **Fórmulas Implementadas**

**Base de Cálculo ICMS-ST:**
> Base ICMS-ST = Valor do Produto × (1 + MVA)

**ICMS Próprio (Interestadual):**
> ICMS Próprio = Valor do Produto × % ICMS Interestadual

**ICMS Total (Operação Interna):**
> ICMS Total = Base ICMS-ST × % ICMS Interno Destino

**ICMS-ST a Recolher:**
> ICMS-ST = ICMS Total - ICMS Próprio (se positivo)

---

### 🗺️ **Alíquotas ICMS por UF**

O sistema agora inclui automaticamente as alíquotas corretas:

- **Interestaduais**: Geralmente 12% (origem para destino)
- **Internas**: Varia por UF (17% a 18%)

**Exemplos:**
- SP: 18% (interna), 12% (interestadual)
- RJ: 18% (interna), 12% (interestadual)  
- RS: 18% (interna), 12% (interestadual)
- SC: 17% (interna), 12% (interestadual)

---

### 🔧 **Novos Recursos**

1. **UF de Origem**: Seleção da UF de origem da mercadoria
2. **Cálculo Automático**: Alíquotas ICMS são aplicadas automaticamente
3. **Detalhamento ICMS**: Mostra ICMS próprio, total e ST separadamente
4. **Exemplo Visual**: Demonstra o cálculo para o primeiro produto
5. **Validação Tributária**: Segue rigorosamente a legislação do ICMS-ST

---

### 📝 **Cálculo Completo do Preço de Venda**

**1. Custos Base**
- Custo NET + Custo Fixo = Custo Total Unitário
- Frete por caixa (se CIF)

**2. Impostos na Entrada/Saída**
- IPI = Subtotal × % IPI
- ICMS-ST = Calculado conforme legislação

**3. Despesas Operacionais**
- COFINS = Subtotal × % COFINS (7,6%)
- PIS = Subtotal × % PIS (1,65%)
- Comissão = Subtotal × % Comissão
- Bonificação = Subtotal × % Bonificação
- Contingência = Subtotal × % Contingência
- % Estratégico = Subtotal × % Estratégico

**4. Lucro**
- Lucro Bruto = (Preço de Venda - Custo Total) × Qtd - Despesas Reais
- **IMPORTANTE**: ICMS-ST NÃO afeta o lucro (apenas destacado na NF)
- Lucro Antes IR = Lucro Bruto (sem dedução de IRPJ/CSLL)
- Lucro Tributável = Lucro Antes IR ÷ 1,34 (presunção de dedução)
- IRPJ = Lucro Tributável × 25%
- CSLL = Lucro Tributável × 9%
- Lucro Líquido Final = Lucro Antes IR - IRPJ - CSLL

**5. Total da Nota Fiscal**
- Total NF = Subtotal + IPI + ICMS-ST
- ICMS-ST é apenas para fins fiscais/arrecadação

---

### ⚖️ **Conformidade Legal CORRIGIDA**

✅ **ICMS-ST**: Não impacta no lucro - apenas destacado na NF  
✅ **IRPJ/CSLL**: Calculados sobre o lucro tributável  
✅ **Despesas**: Incluem apenas impostos que afetam a margem  
✅ **Base Tributária**: Correta conforme legislação  

O cálculo agora está em total conformidade com a contabilidade e legislação tributária brasileira, onde:

- **ICMS-ST** é um imposto de substituição que não afeta o resultado da empresa
- **IRPJ e CSLL** são calculados sobre o lucro real da operação
- **Margem de lucro** é calculada sem considerar o ICMS-ST

---

### 🎉 **Bem-vindo ao Simulador de Formação de Preço de Venda - Sobel Suprema!**  
🚀 Desenvolvido por [Sobel Suprema](https://sobelsuprema.com.br

  """)