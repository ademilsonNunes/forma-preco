import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

st.set_page_config(page_title="Simulador de Preço de Venda Sobel", layout="wide")
st.title("📊 Simulador de Formação de Preço de Venda - 2.5")

# Verificar se a imagem existe antes de tentar carregá-la
if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
    st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=300)

# Tabela de alíquotas ICMS e FCP por UF
ICMS_ALIQUOTAS = {
    'AC': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
    'AL': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
    'AP': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
    'AM': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
    'BA': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'CE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.025},
    'DF': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
    'ES': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
    'GO': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
    'MA': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'MT': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
    'MS': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
    'MG': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'PA': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
    'PB': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'PR': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'PE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'PI': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'RJ': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'RN': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'RS': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'RO': {'interna': 0.175, 'interestadual': 0.12, 'fcp': 0.0},
    'RR': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
    'SC': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
    'SP': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
    'SE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
    'TO': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0}
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
if 'bonificacoes_editadas' not in st.session_state:
    st.session_state.bonificacoes_editadas = {}
if 'valores_originais' not in st.session_state:
    st.session_state.valores_originais = {}

# Carga padrão
arquivo_padrao = "Custo de reposição.xlsx"
if os.path.exists(arquivo_padrao):
    df_padrao = pd.read_excel(arquivo_padrao)
    df_padrao.columns = df_padrao.columns.str.strip()
else:
    st.warning("Arquivo padrão 'Custo de reposição.xlsx' não encontrado. Faça upload de uma planilha.")
    df_padrao = pd.DataFrame()

# Layout em colunas para parâmetros
col_param1, col_param2, col_param3 = st.columns([1, 1, 1])

with col_param1:
    st.markdown("#### ⚙️ Parâmetros de Origem")
    # Origem fixada como SP
    uf_origem = 'SP'
    st.info(f"🏭 **Origem fixada:** {uf_origem} (São Paulo)")
    frete_padrao = st.number_input("Frete/Caixa (R$)", min_value=0.0, value=1.50, step=0.01)
    tipo_frete = st.radio("Tipo de Frete", ("CIF", "FOB"))

with col_param2:
    st.markdown("#### 📍 Parâmetros de Destino")
    uf_selecionado = st.selectbox("UF de Destino", 
                                 options=df_padrao["UF"].dropna().unique().tolist() if not df_padrao.empty else [], 
                                 key="uf_select")
    contrato_percentual = st.number_input("% Contrato", min_value=0.0, max_value=100.0, value=1.00, step=0.01) / 100
    
    # Mostrar alíquotas (SP sempre como origem)
    if uf_selecionado:
        icms_inter = ICMS_ALIQUOTAS['SP']['interestadual']  # SP sempre 12%
        icms_interno = ICMS_ALIQUOTAS[uf_selecionado]['interna']
        fcp_destino = ICMS_ALIQUOTAS[uf_selecionado]['fcp']
        
        info_tributos = f"ICMS SP→{uf_selecionado}: {icms_inter:.1%} | Interno {uf_selecionado}: {icms_interno:.1%}"
        if fcp_destino > 0:
            info_tributos += f" | FCP: {fcp_destino:.1%}"
        st.info(info_tributos)

with col_param3:
    st.markdown("#### 💰 Parâmetros Globais")
    custo_fixo_global = st.number_input("Custo Fixo Global (R$)", min_value=0.0, value=0.0, step=0.01, 
                                       help="Se zero, usa valor da planilha")
    comissao_padrao = st.number_input("% Comissão Global", min_value=0.0, max_value=100.0, value=0.0, step=0.1, 
                                     help="Se zero, usa valor da planilha") / 100
    bonificacao_global = st.number_input("% Bonificação Global", min_value=0.0, max_value=100.0, value=0.0, step=0.01, 
                                        help="Se zero, usa valor da planilha") / 100

# Upload com backup
uploaded_file = st.file_uploader("📂 Atualizar planilha base (.xlsx)", type="xlsx")

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
        df_padrao = pd.read_excel(arquivo_padrao)
        df_padrao.columns = df_padrao.columns.str.strip()
        st.session_state.df_atual = None
        st.session_state.modo_equilibrio = False
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")

# Validação e preparação dos dados
if df_padrao.empty or not uf_selecionado:
    st.warning("Carregue uma planilha e selecione uma UF de destino.")
    st.stop()

# Filtrar por UF
df_base = df_padrao[df_padrao["UF"] == uf_selecionado].copy()

# Resetar dados se mudou UF
if st.session_state.df_atual is not None:
    if "UF" in st.session_state.df_atual.columns:
        ufs_atuais = st.session_state.df_atual["UF"].unique()
        if len(ufs_atuais) > 0 and ufs_atuais[0] != uf_selecionado:
            st.session_state.df_atual = None
            st.session_state.modo_equilibrio = False
            st.session_state.comissao_global_aplicada = False
            st.session_state.comissoes_editadas = {}
            st.session_state.bonificacoes_editadas = {}
            st.session_state.valores_originais = {}

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
    "Contigência", "ICMS Interestadual", "ICMS Interno Destino", "FCP"
]

for col in colunas_necessarias:
    if col not in df_base.columns:
        if col == "Quantidade":
            df_base[col] = 1
        elif col == "ICMS Interestadual":
            df_base[col] = ICMS_ALIQUOTAS['SP']['interestadual']
        elif col == "ICMS Interno Destino":
            df_base[col] = ICMS_ALIQUOTAS[uf_selecionado]['interna']
        elif col == "FCP":
            df_base[col] = ICMS_ALIQUOTAS[uf_selecionado]['fcp']
        else:
            df_base[col] = 0.0

# Aplicação dos parâmetros globais
df_base["Frete Caixa"] = frete_padrao
df_base["Contrato"] = contrato_percentual
df_base["UF Origem"] = 'SP'  # Sempre SP
df_base["UF Destino"] = uf_selecionado
df_base["ICMS Interestadual"] = ICMS_ALIQUOTAS['SP']['interestadual']  # SP sempre 12%
df_base["ICMS Interno Destino"] = ICMS_ALIQUOTAS[uf_selecionado]['interna']
df_base["FCP"] = ICMS_ALIQUOTAS[uf_selecionado]['fcp']

if custo_fixo_global > 0:
    df_base["Custo Fixo"] = custo_fixo_global

if comissao_padrao > 0:
    df_base["Comissão"] = comissao_padrao
    st.session_state.comissao_global_aplicada = True
else:
    st.session_state.comissao_global_aplicada = False

if bonificacao_global > 0:
    df_base["Bonificação"] = bonificacao_global

# Função auxiliar para arredondamento consistente
def arredondar_valor(valor, decimais=2):
    """Arredonda valores para evitar problemas de precisão"""
    try:
        return round(float(valor), decimais)
    except (ValueError, TypeError):
        return 0.0

# Função para calcular ICMS-ST com IPI e FCP (CORRIGIDA)
def calcular_icms_st_completo(valor_produto, ipi_valor, mva, icms_interestadual, icms_interno_destino, fcp_aliquota):
    """
    Calcula ICMS-ST conforme legislação tributária brasileira
    Inclui IPI na base quando aplicável e calcula FCP
    CORREÇÃO: Se MVA = 0, não há ICMS-ST nem FCP
    """
    # Se MVA = 0, não há substituição tributária
    if mva <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    # Base inicial = Valor do produto + IPI (quando há IPI)
    base_inicial = arredondar_valor(valor_produto + ipi_valor)
    
    # Base de cálculo do ICMS-ST = (Valor + IPI) × (1 + MVA)
    base_icms_st = arredondar_valor(base_inicial * (1 + mva))
    
    # ICMS próprio (origem) - calculado sobre valor sem IPI para operação interestadual
    icms_proprio = arredondar_valor(valor_produto * icms_interestadual)
    
    # ICMS total devido se fosse operação interna no destino
    icms_total_interno = arredondar_valor(base_icms_st * icms_interno_destino)
    
    # ICMS-ST a recolher = diferença entre ICMS total e ICMS próprio
    icms_st = arredondar_valor(max(icms_total_interno - icms_proprio, 0))
    
    # FCP (Fundo de Combate à Pobreza) - calculado sobre a mesma base do ICMS-ST
    fcp_valor = arredondar_valor(base_icms_st * fcp_aliquota) if fcp_aliquota > 0 else 0.0
    
    return icms_st, base_icms_st, icms_proprio, icms_total_interno, fcp_valor

# Função para calcular ponto de equilíbrio (CORRIGIDA)
def calcular_ponto_equilibrio(df):
    """
    Calcula o preço que resulta em LUCRO LÍQUIDO = ZERO
    FCP é calculado sobre a base do ICMS-ST, não como % direto sobre receita
    CORREÇÃO: Se MVA = 0, não calcula ICMS-ST nem FCP
    """
    df_resultado = df.copy()
    alertas = []
    
    for index, row in df_resultado.iterrows():
        try:
            # Custos base
            custo_net = float(row.get("Custo NET", 0))
            custo_fixo = float(row.get("Custo Fixo", 0))
            custo_total_unit = custo_net + custo_fixo
            frete_unit = float(row.get("Frete Caixa", 0)) if tipo_frete == "CIF" else 0
            
            # Despesas percentuais diretas sobre receita
            icms = float(row.get("ICMS Interestadual", 0))
            cofins = float(row.get("COFINS", 0))
            pis = float(row.get("PIS", 0))
            comissao = float(row.get("Comissão", 0))
            bonificacao = float(row.get("Bonificação", 0))
            contigencia = float(row.get("Contigência", 0))
            contrato = float(row.get("Contrato", 0))
            estrategico = float(row.get("%Estrategico", 0))
            
            # Parâmetros para FCP (calculado sobre base ICMS-ST)
            mva = float(row.get("MVA", 0))
            ipi_percent = float(row.get("IPI", 0))
            fcp_aliquota = float(row.get("FCP", 0))
            
            # Despesas diretas (sem FCP que é calculado diferente)
            despesas_diretas = icms + cofins + pis + comissao + bonificacao + contigencia + contrato + estrategico
            
            # Se MVA = 0, não há ICMS-ST nem FCP, cálculo simplificado
            if mva <= 0:
                if despesas_diretas >= 1.0:
                    alertas.append(f"{row.get('Descrição', 'Produto')}: Despesas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    custos_totais = custo_total_unit + frete_unit
                    preco_equilibrio = custos_totais / (1 - despesas_diretas)
                    preco_equilibrio = arredondar_valor(preco_equilibrio, 2)
            else:
                # Método iterativo para encontrar o preço de equilíbrio com FCP
                preco_tentativa = (custo_total_unit + frete_unit) / (1 - despesas_diretas) if despesas_diretas < 1.0 else 0
                
                if preco_tentativa <= 0 or despesas_diretas >= 1.0:
                    alertas.append(f"{row.get('Descrição', 'Produto')}: Despesas diretas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    # Iteração para convergir considerando FCP
                    for iteracao in range(10):  # Máximo 10 iterações
                        # Calcular FCP baseado no preço atual
                        valor_produto = preco_tentativa
                        ipi_valor = valor_produto * ipi_percent
                        base_inicial = valor_produto + ipi_valor
                        base_icms_st = base_inicial * (1 + mva)
                        fcp_valor = base_icms_st * fcp_aliquota
                        
                        # FCP como despesa adicional
                        fcp_percentual = fcp_valor / valor_produto if valor_produto > 0 else 0
                        
                        # Despesas totais incluindo FCP calculado
                        despesas_totais = despesas_diretas + fcp_percentual
                        
                        if despesas_totais >= 1.0:
                            preco_equilibrio = 0.0
                            break
                        
                        # Novo preço considerando FCP
                        novo_preco = (custo_total_unit + frete_unit) / (1 - despesas_totais)
                        
                        # Verificar convergência
                        if abs(novo_preco - preco_tentativa) < 0.01:
                            preco_equilibrio = arredondar_valor(novo_preco, 2)
                            break
                        
                        preco_tentativa = novo_preco
                    else:
                        # Se não convergiu, usar último valor
                        preco_equilibrio = arredondar_valor(preco_tentativa, 2)
            
            # Garantir que não seja negativo
            preco_equilibrio = max(0.0, preco_equilibrio)
            
            df_resultado.at[index, "Preço de Venda"] = preco_equilibrio
            
        except Exception as e:
            alertas.append(f"Erro no produto {row.get('Descrição', 'N/A')}: {str(e)}")
            df_resultado.at[index, "Preço de Venda"] = 0.0
    
    return df_resultado, alertas

# Função para calcular resultados (CORRIGIDA - LUCRO REAL)
def calcular_resultados_completos(row):
    try:
        # Valores base
        preco_venda = arredondar_valor(row["Preço de Venda"])
        qtd = arredondar_valor(row["Quantidade"], 0)
        subtotal = arredondar_valor(preco_venda * qtd)
        
        # Custos
        custo_net = arredondar_valor(row.get("Custo NET", 0))
        custo_fixo = arredondar_valor(row.get("Custo Fixo", 0))
        custo_total_unit = arredondar_valor(custo_net + custo_fixo)
        custo_total = arredondar_valor(custo_total_unit * qtd)
        
        # Frete
        frete_total = arredondar_valor(float(row["Frete Caixa"]) * qtd) if tipo_frete == "CIF" else 0.0
        frete_unit = arredondar_valor(float(row["Frete Caixa"])) if tipo_frete == "CIF" else 0.0
        
        # IPI
        ipi_percent = float(row.get("IPI", 0))
        ipi_total = arredondar_valor(subtotal * ipi_percent)
        
        # ICMS-ST com IPI e FCP (CORRIGIDO)
        mva = float(row.get("MVA", 0))
        icms_interestadual = float(row["ICMS Interestadual"])
        icms_interno_destino = float(row["ICMS Interno Destino"])
        fcp_aliquota = float(row.get("FCP", 0))
        
        icms_st, base_icms_st, icms_proprio, icms_total_interno, fcp_valor = calcular_icms_st_completo(
            subtotal, ipi_total, mva, icms_interestadual, icms_interno_destino, fcp_aliquota
        )
        
        # Despesas operacionais (sobre o subtotal)
        cofins = float(row.get("COFINS", 0))
        pis = float(row.get("PIS", 0))
        comissao = float(row.get("Comissão", 0))
        bonificacao = float(row.get("Bonificação", 0))
        contigencia = float(row.get("Contigência", 0))
        contrato = float(row.get("Contrato", 0))
        estrategico = float(row.get("%Estrategico", 0))
        
        # Valores das despesas operacionais
        icms_valor = arredondar_valor(subtotal * icms_interestadual)
        cofins_valor = arredondar_valor(subtotal * cofins)
        pis_valor = arredondar_valor(subtotal * pis)
        comissao_valor = arredondar_valor(subtotal * comissao)
        bonificacao_valor = arredondar_valor(subtotal * bonificacao)
        contigencia_valor = arredondar_valor(subtotal * contigencia)
        contrato_valor = arredondar_valor(subtotal * contrato)
        estrategico_valor = arredondar_valor(subtotal * estrategico)
        # FCP como despesa operacional
        fcp_despesa = fcp_valor
        
        total_despesas_operacionais = arredondar_valor(icms_valor + cofins_valor + pis_valor + comissao_valor + 
                                     bonificacao_valor + contigencia_valor + contrato_valor + 
                                     estrategico_valor + fcp_despesa)
        
        # LUCRO ANTES DOS IMPOSTOS SOBRE LUCRO
        lucro_antes_ir = arredondar_valor(subtotal - custo_total - total_despesas_operacionais - frete_total)
        
        # IRPJ e CSLL (LUCRO REAL - apenas se houver lucro positivo)
        if lucro_antes_ir > 0:
            irpj = arredondar_valor(lucro_antes_ir * 0.15)  # 15% base
            csll = arredondar_valor(lucro_antes_ir * 0.09)  # 9% base
            
            # Adicional de 10% sobre excesso (simplificado)
            if lucro_antes_ir > 20000:  # Limite mensal R$ 20k
                adicional_irpj = arredondar_valor((lucro_antes_ir - 20000) * 0.10)
                irpj = arredondar_valor(irpj + adicional_irpj)
            
            lucro_liquido = arredondar_valor(lucro_antes_ir - irpj - csll)
        else:
            # Se não há lucro, não paga IRPJ/CSLL
            irpj = 0.0
            csll = 0.0
            lucro_liquido = arredondar_valor(lucro_antes_ir)
        
        # Percentuais de margem
        margem_antes_ir = arredondar_valor((lucro_antes_ir / subtotal) * 100, 1) if subtotal > 0 else 0.0
        margem_liquida = arredondar_valor((lucro_liquido / subtotal) * 100, 1) if subtotal > 0 else 0.0
        
        # Total da NF (com ICMS-ST e FCP para fins fiscais)
        total_nf = arredondar_valor(subtotal + ipi_total + icms_st + fcp_valor)
        
        # Ponto de equilíbrio (preço para lucro líquido = 0)
        # CORREÇÃO: Se MVA = 0, não há ICMS-ST nem FCP
        despesas_diretas = (icms_interestadual + cofins + pis + comissao + 
                           bonificacao + contigencia + contrato + estrategico)
        
        if mva <= 0:
            # Sem substituição tributária, cálculo direto
            if despesas_diretas < 1:
                ponto_equilibrio = arredondar_valor((custo_total_unit + frete_unit) / (1 - despesas_diretas))
            else:
                ponto_equilibrio = 0.0
        else:
            # Com substituição tributária, método iterativo
            if despesas_diretas < 1:
                # Estimativa inicial sem FCP
                preco_inicial = (custo_total_unit + frete_unit) / (1 - despesas_diretas)
                
                # Iteração para incluir FCP
                preco_equilibrio_calc = preco_inicial
                for i in range(5):  # 5 iterações são suficientes
                    # Calcular FCP baseado no preço atual
                    ipi_calc = preco_equilibrio_calc * ipi_percent
                    base_inicial_calc = preco_equilibrio_calc + ipi_calc
                    base_icms_st_calc = base_inicial_calc * (1 + mva)
                    fcp_calc = base_icms_st_calc * fcp_aliquota
                    
                    # FCP como percentual da receita
                    fcp_percent_calc = fcp_calc / preco_equilibrio_calc if preco_equilibrio_calc > 0 else 0
                    
                    # Despesas totais
                    despesas_totais_calc = despesas_diretas + fcp_percent_calc
                    
                    if despesas_totais_calc >= 1:
                        preco_equilibrio_calc = 0.0
                        break
                    
                    # Novo preço
                    novo_preco = (custo_total_unit + frete_unit) / (1 - despesas_totais_calc)
                    
                    # Verificar convergência
                    if abs(novo_preco - preco_equilibrio_calc) < 0.01:
                        preco_equilibrio_calc = novo_preco
                        break
                    
                    preco_equilibrio_calc = novo_preco
                
                ponto_equilibrio = arredondar_valor(preco_equilibrio_calc)
            else:
                ponto_equilibrio = 0.0
        
        return pd.Series({
            # Dados de entrada
            "Preço Venda": preco_venda,
            "Qtd": qtd,
            "Custo NET": custo_net,
            "Custo Fixo": custo_fixo,
            "MVA": mva,
            "Comissão": comissao,
            "Bonificação": bonificacao,
            
            # Cálculos fiscais
            "Subtotal": subtotal,
            "IPI": ipi_total,
            "Base ICMS-ST": base_icms_st,
            "ICMS Próprio": icms_proprio,
            "ICMS-ST": icms_st,
            "FCP": fcp_valor,
            "Total NF": total_nf,
            
            # Cálculos de resultado (CORRIGIDOS)
            "Custo Total": custo_total,
            "Frete Total": frete_total,
            "Total Despesas": total_despesas_operacionais,
            "Lucro Antes IR": lucro_antes_ir,
            "IRPJ": irpj,
            "CSLL": csll,
            "Lucro Líquido": lucro_liquido,
            "Margem Antes IR %": margem_antes_ir,
            "Margem Líquida %": margem_liquida,
            "Ponto Equilíbrio": ponto_equilibrio
        })
        
    except Exception as e:
        # Em caso de erro, retorna zeros
        return pd.Series({
            "Preço Venda": 0, "Qtd": 0, "Custo NET": 0, "Custo Fixo": 0, "MVA": 0,
            "Comissão": 0, "Bonificação": 0, "Subtotal": 0, "IPI": 0, "Base ICMS-ST": 0,
            "ICMS Próprio": 0, "ICMS-ST": 0, "FCP": 0, "Total NF": 0, "Custo Total": 0,
            "Frete Total": 0, "Total Despesas": 0, "Lucro Antes IR": 0, "IRPJ": 0,
            "CSLL": 0, "Lucro Líquido": 0, "Margem Antes IR %": 0, "Margem Líquida %": 0,
            "Ponto Equilíbrio": 0
        })

# Aplicar lógica de comissão e bonificação híbrida
def aplicar_logica_comissao_bonificacao(df):
    df_temp = df.copy()
    
    # Garantir que colunas Comissão e Bonificação existam e sejam numéricas
    if "Comissão" not in df_temp.columns:
        df_temp["Comissão"] = 0.0
    if "Bonificação" not in df_temp.columns:
        df_temp["Bonificação"] = 0.0
    
    # Converter para float e tratar valores inválidos
    df_temp["Comissão"] = pd.to_numeric(df_temp["Comissão"], errors='coerce').fillna(0.0)
    df_temp["Bonificação"] = pd.to_numeric(df_temp["Bonificação"], errors='coerce').fillna(0.0)
    
    # Armazenar valores originais se ainda não foram armazenados
    if not st.session_state.valores_originais:
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
            st.session_state.valores_originais[produto] = {
                'comissao': float(df_temp.at[index, "Comissão"]),
                'bonificacao': float(df_temp.at[index, "Bonificação"])
            }
    
    # Aplicar comissão global se ativa e não editada individualmente
    if st.session_state.comissao_global_aplicada and comissao_padrao > 0:
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
            if produto not in st.session_state.comissoes_editadas:
                df_temp.at[index, "Comissão"] = float(comissao_padrao)
    
    # Aplicar bonificação global se ativa e não editada individualmente
    if bonificacao_global > 0:
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
            if produto not in st.session_state.bonificacoes_editadas:
                df_temp.at[index, "Bonificação"] = float(bonificacao_global)
    
    # Aplicar valores editados individualmente (PRIORIDADE MÁXIMA)
    for produto, valor_comissao in st.session_state.comissoes_editadas.items():
        mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
        if isinstance(mask, pd.Series) and mask.any():
            df_temp.loc[mask, "Comissão"] = float(valor_comissao)
    
    for produto, valor_bonificacao in st.session_state.bonificacoes_editadas.items():
        mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
        if isinstance(mask, pd.Series) and mask.any():
            df_temp.loc[mask, "Bonificação"] = float(valor_bonificacao)
    
    # Garantir que os valores finais sejam float válidos
    df_temp["Comissão"] = df_temp["Comissão"].astype(float)
    df_temp["Bonificação"] = df_temp["Bonificação"].astype(float)
    
    return df_temp

# Botões de controle
col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🎯 Calcular Ponto de Equilíbrio", use_container_width=True):
        df_equilibrio, alertas = calcular_ponto_equilibrio(df_base)
        
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        
        st.session_state.df_atual = df_equilibrio.copy()
        st.session_state.modo_equilibrio = True
        st.success("✅ Ponto de equilíbrio calculado!")

with col2:
    if st.button("🔄 Resetar", use_container_width=True):
        st.session_state.df_atual = None
        st.session_state.modo_equilibrio = False
        st.session_state.comissao_global_aplicada = False
        st.session_state.comissoes_editadas = {}
        st.session_state.bonificacoes_editadas = {}
        st.session_state.valores_originais = {}
        st.info("Dados resetados.")

# Determinar DataFrame para edição
if st.session_state.df_atual is not None:
    df_para_edicao = st.session_state.df_atual.copy()
else:
    df_para_edicao = df_base.copy()

df_para_edicao = aplicar_logica_comissao_bonificacao(df_para_edicao)

# Status do modo
status_info = f"🗺️ **SP → {uf_selecionado}** | "
if st.session_state.modo_equilibrio:
    status_info += "🔒 **Modo Equilíbrio Ativo**"
else:
    status_info += "📋 **Modo Normal**"

# Informações sobre parâmetros globais ativos
parametros_ativos = []
if st.session_state.comissao_global_aplicada and comissao_padrao > 0:
    parametros_ativos.append(f"Comissão Global: {comissao_padrao:.1%}")
if bonificacao_global > 0:
    parametros_ativos.append(f"Bonificação Global: {bonificacao_global:.1%}")

if parametros_ativos:
    status_info += f" | {' | '.join(parametros_ativos)}"

# Informações sobre edições individuais
edicoes_individuais = []
if st.session_state.comissoes_editadas:
    edicoes_individuais.append(f"Comissões editadas: {len(st.session_state.comissoes_editadas)}")
if st.session_state.bonificacoes_editadas:
    edicoes_individuais.append(f"Bonificações editadas: {len(st.session_state.bonificacoes_editadas)}")

if edicoes_individuais:
    status_info += f" | 🎯 {' | '.join(edicoes_individuais)}"

st.info(status_info)

# Tabela consolidada editável com resultados
st.markdown("### 📊 Simulação Consolidada - Dados + Resultados")

# Mostrar resumo de edições individuais se houver
if st.session_state.comissoes_editadas or st.session_state.bonificacoes_editadas:
    with st.expander("🎯 Resumo das Edições Individuais", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.comissoes_editadas:
                st.markdown("**Comissões Personalizadas:**")
                for produto, valor in st.session_state.comissoes_editadas.items():
                    original = st.session_state.valores_originais.get(produto, {}).get('comissao', 0)
                    global_val = comissao_padrao if comissao_padrao > 0 else original
                    st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
            
            if st.button("🔄 Limpar Comissões Editadas"):
                st.session_state.comissoes_editadas = {}
                st.rerun()
        
        with col2:
            if st.session_state.bonificacoes_editadas:
                st.markdown("**Bonificações Personalizadas:**")
                for produto, valor in st.session_state.bonificacoes_editadas.items():
                    original = st.session_state.valores_originais.get(produto, {}).get('bonificacao', 0)
                    global_val = bonificacao_global if bonificacao_global > 0 else original
                    st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
            
            if st.button("🔄 Limpar Bonificações Editadas"):
                st.session_state.bonificacoes_editadas = {}
                st.rerun()

# Preparar dados para edição (apenas colunas editáveis)
colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                 "MVA", "Comissão", "Bonificação", "%Estrategico"]

# Garantir tipos de dados corretos antes da edição
df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()

# Converter colunas numéricas para float
colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
for col in colunas_numericas:
    if col in df_para_edicao_clean.columns:
        df_para_edicao_clean[col] = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
        df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)

# Converter colunas percentuais para formato percentual (0-100) para edição
colunas_percentuais = ["MVA", "Comissão", "Bonificação", "%Estrategico"]
for col in colunas_percentuais:
    if col in df_para_edicao_clean.columns:
        valores = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
        # Converter de decimal (0-1) para percentual (0-100)
        df_para_edicao_clean[col] = (valores * 100).round(2)

# Editor de dados - chave fixa para manter estado
df_editado = st.data_editor(
    df_para_edicao_clean,
    use_container_width=True,
    num_rows="dynamic",
    key="editor_principal",
    column_config={
        "Descrição": st.column_config.TextColumn("Produto", disabled=True),
        "Preço de Venda": st.column_config.NumberColumn("Preço Venda", format="%.2f", min_value=0.0, step=0.01),
        "Quantidade": st.column_config.NumberColumn("Qtd", format="%.0f", min_value=1, step=1),
        "Custo NET": st.column_config.NumberColumn("Custo NET", format="%.2f", min_value=0.0, step=0.01),
        "Custo Fixo": st.column_config.NumberColumn("Custo Fixo", format="%.2f", min_value=0.0, step=0.01),
        "MVA": st.column_config.NumberColumn("MVA (%)", format="%.2f", min_value=0.0, max_value=500.0, step=0.1),
        "Comissão": st.column_config.NumberColumn("Comissão (%) ⭐", format="%.2f", min_value=0.0, max_value=50.0, step=0.1,
                                                  help="⭐ = Editável individualmente. Sobrepõe valor global."),
        "Bonificação": st.column_config.NumberColumn("Bonificação (%) ⭐", format="%.2f", min_value=0.0, max_value=50.0, step=0.1,
                                                     help="⭐ = Editável individualmente. Sobrepõe valor global."),
        "%Estrategico": st.column_config.NumberColumn("% Estratégico", format="%.2f", min_value=0.0, max_value=50.0, step=0.1)
    }
)

# Processar dados editados
df_processado = df_editado.copy()

# Converter valores percentuais de volta para decimal (0-1) para os cálculos
for col in colunas_percentuais:
    if col in df_processado.columns:
        df_processado[col] = pd.to_numeric(df_processado[col], errors='coerce').fillna(0.0) / 100

# Arredondar valores monetários
for col in colunas_numericas:
    if col in df_processado.columns:
        df_processado[col] = df_processado[col].round(2)

# Detectar mudanças nas comissões e bonificações de forma simplificada
produtos_com_mudancas = []

# Verificar mudanças linha por linha
for index in df_processado.index:
    if index < len(df_para_edicao):
        produto = df_processado.at[index, "Descrição"]
        
        # Comissão
        try:
            comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
            comissao_editada = float(df_processado.at[index, "Comissão"])
            
            if abs(comissao_original - comissao_editada) > 0.001:
                st.session_state.comissoes_editadas[produto] = comissao_editada
                produtos_com_mudancas.append(f"Comissão {produto}: {comissao_editada:.2%}")
        except (ValueError, TypeError, KeyError):
            pass
        
        # Bonificação
        try:
            bonificacao_original = float(df_para_edicao.iloc[index]["Bonificação"])
            bonificacao_editada = float(df_processado.at[index, "Bonificação"])
            
            if abs(bonificacao_original - bonificacao_editada) > 0.001:
                st.session_state.bonificacoes_editadas[produto] = bonificacao_editada
                produtos_com_mudancas.append(f"Bonificação {produto}: {bonificacao_editada:.2%}")
        except (ValueError, TypeError, KeyError):
            pass

# Mostrar mudanças detectadas
if produtos_com_mudancas:
    st.info(f"🎯 Mudanças detectadas: {', '.join(produtos_com_mudancas[:3])}{'...' if len(produtos_com_mudancas) > 3 else ''}")

# Criar DataFrame final combinando dados editados com não editados
df_final = df_para_edicao.copy()

# Atualizar com dados editados
for col in colunas_edicao:
    if col in df_processado.columns:
        df_final[col] = df_processado[col]

# Atualizar session state
st.session_state.df_atual = df_final.copy()

# Calcular resultados e mostrar tabela consolidada
if not df_final.empty:
    # Calcular resultados
    resultados = df_final.apply(calcular_resultados_completos, axis=1)
    
    # Criar DataFrame consolidado para exibição
    df_display = pd.DataFrame({
        "Produto": df_final["Descrição"].values,
        "Preço Venda": resultados["Preço Venda"].values,
        "Qtd": resultados["Qtd"].values,
        "Subtotal": resultados["Subtotal"].values,
        "IPI": resultados["IPI"].values,
        "ICMS-ST": resultados["ICMS-ST"].values,
        "FCP": resultados["FCP"].values,
        "Total NF": resultados["Total NF"].values,
        "Custo Total": resultados["Custo Total"].values,
        "Despesas": resultados["Total Despesas"].values,
        "Lucro Antes IR": resultados["Lucro Antes IR"].values,
        "IRPJ+CSLL": (resultados["IRPJ"] + resultados["CSLL"]).values,
        "Lucro Líquido": resultados["Lucro Líquido"].values,
        "Margem %": resultados["Margem Líquida %"].values,
        "Equilíbrio": resultados["Ponto Equilíbrio"].values
    })
    
    # Arredondar todos os valores para evitar -0.00
    colunas_monetarias = ["Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
                         "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
                         "Lucro Líquido", "Equilíbrio"]
    
    for col in colunas_monetarias:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: arredondar_valor(x, 2))
    
    # Arredondar margem para 1 casa decimal
    if "Margem %" in df_display.columns:
        df_display["Margem %"] = df_display["Margem %"].apply(lambda x: arredondar_valor(x, 1))
    
    # Função para colorir valores
    def colorir_valores(val):
        try:
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'color: red; font-weight: bold'
                elif val > 0:
                    return 'color: green'
            return 'color: black'
        except:
            return 'color: black'
    
    # Aplicar formatação
    styled_display = df_display.style.format({
        "Preço Venda": "R$ {:.2f}",
        "Subtotal": "R$ {:.2f}",
        "IPI": "R$ {:.2f}",
        "ICMS-ST": "R$ {:.2f}",
        "FCP": "R$ {:.2f}",
        "Total NF": "R$ {:.2f}",
        "Custo Total": "R$ {:.2f}",
        "Despesas": "R$ {:.2f}",
        "Lucro Antes IR": "R$ {:.2f}",
        "IRPJ+CSLL": "R$ {:.2f}",
        "Lucro Líquido": "R$ {:.2f}",
        "Margem %": "{:.1f}%",
        "Equilíbrio": "R$ {:.2f}"
    }).applymap(colorir_valores, subset=["Lucro Antes IR", "Lucro Líquido", "Margem %"])
    
    st.dataframe(styled_display, use_container_width=True)
    
    # Resumo executivo
    if len(df_display) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_receita = df_display["Subtotal"].sum()
            st.metric("💰 Receita Total", f"R$ {total_receita:,.2f}")
        
        with col2:
            total_lucro_liquido = df_display["Lucro Líquido"].sum()
            st.metric("💵 Lucro Líquido", f"R$ {total_lucro_liquido:,.2f}", 
                     delta=f"{(total_lucro_liquido/total_receita)*100:.1f}%" if total_receita > 0 else "0%")
        
        with col3:
            margem_media = df_display["Margem %"].mean()
            st.metric("📊 Margem Média", f"{margem_media:.1f}%")
        
        with col4:
            produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
            st.metric("⚠️ Produtos c/ Prejuízo", produtos_prejuizo)
    
    # Exemplo de cálculo detalhado (primeiro produto)
    if len(resultados) > 0:
        st.markdown("### 🔍 Detalhamento do Cálculo (Primeiro Produto)")
        
        primeiro = resultados.iloc[0]
        produto_nome = df_final.iloc[0]["Descrição"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **📦 {produto_nome}**
            
            **Base de Cálculo:**
            - Preço de Venda: R$ {primeiro['Preço Venda']:.2f}
            - Quantidade: {primeiro['Qtd']:.0f}
            - Subtotal: R$ {primeiro['Subtotal']:.2f}
            
            **ICMS-ST e FCP:**
            - MVA: {df_final.iloc[0]['MVA']:.2%}
            - Base ICMS-ST: R$ {primeiro['Base ICMS-ST']:.2f}
            - ICMS Próprio: R$ {primeiro['ICMS Próprio']:.2f}
            - ICMS-ST: R$ {primeiro['ICMS-ST']:.2f}
            - FCP: R$ {primeiro['FCP']:.2f}
            """)
        
        with col2:
            st.markdown(f"""
            **💰 Resultado Financeiro:**
            
            **Custos e Despesas:**
            - Custo Total: R$ {primeiro['Custo Total']:.2f}
            - Despesas Totais: R$ {primeiro['Total Despesas']:.2f}
            - Frete: R$ {primeiro['Frete Total']:.2f}
            
            **Lucro:**
            - Lucro Antes IR: R$ {primeiro['Lucro Antes IR']:.2f}
            - IRPJ + CSLL: R$ {primeiro['IRPJ'] + primeiro['CSLL']:.2f}
            - **Lucro Líquido: R$ {primeiro['Lucro Líquido']:.2f}**
            - **Margem: {primeiro['Margem Líquida %']:.1f}%**
            """)

# Exportação melhorada
st.markdown("### 📄 Exportar Resultados")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Baixar Resumo Executivo", use_container_width=True):
        # Criar DataFrame consolidado
        df_export = pd.concat([df_final[colunas_edicao], resultados], axis=1)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            # Aba principal
            df_export.to_excel(writer, index=False, sheet_name="Simulacao_Completa")
            
            # Aba resumo
            resumo = pd.DataFrame({
                "Métrica": ["Receita Total", "Lucro Líquido Total", "Margem Média", "Produtos com Prejuízo"],
                "Valor": [
                    f"R$ {df_display['Subtotal'].sum():,.2f}",
                    f"R$ {df_display['Lucro Líquido'].sum():,.2f}",
                    f"{df_display['Margem %'].mean():.1f}%",
                    len(df_display[df_display["Lucro Líquido"] < 0])
                ]
            })
            resumo.to_excel(writer, index=False, sheet_name="Resumo_Executivo")
        
        st.download_button(
            label="📄 Download Excel Completo",
            data=excel_buffer.getvalue(),
            file_name=f"simulacao_sobel_SP_{uf_selecionado}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with col2:
    if st.button("📋 Copiar Resumo", use_container_width=True):
        resumo_texto = f"""
SIMULAÇÃO SOBEL - SP → {uf_selecionado}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

RESUMO EXECUTIVO:
• Receita Total: R$ {df_display['Subtotal'].sum():,.2f}
• Lucro Líquido: R$ {df_display['Lucro Líquido'].sum():,.2f}
• Margem Média: {df_display['Margem %'].mean():.1f}%
• Produtos com Prejuízo: {len(df_display[df_display['Lucro Líquido'] < 0])}

PRODUTOS:
{chr(10).join([f"• {row['Produto']}: R$ {row['Preço Venda']:.2f} | Margem: {row['Margem %']:.1f}%" for _, row in df_display.iterrows()])}
        """
        st.code(resumo_texto)

# Notas técnicas
st.markdown("""
---
### 📚 Simulador Sobel Suprema v2.5 - Código Completo

#### 🎯 **Estados com FCP:**
- **2,0%:** AC, AL, BA, MA, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, SC, SE
- **2,5%:** CE
- **0,0%:** AP, AM, DF, ES, GO, MT, RO, RR, SP, TO

""")