# Configuração da página - DEVE SER A PRIMEIRA COISA!
import streamlit as st

# Configurar página ANTES de qualquer outro comando Streamlit
st.set_page_config(
    page_title="Simulador de Preço de Venda Sobel", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊"
)

import pandas as pd
import pyodbc
import io
import os
import requests
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any
import math
import time
import unicodedata
import locale

# Configurar locale para formatação brasileira
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Fallback se não conseguir configurar

# Carrega chave da API
load_dotenv()

# ==================== FUNÇÕES AUXILIARES ====================

def normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza texto para comparação"""
    if pd.isna(texto) or texto is None:
        return ""
    
    # Converter para string e normalizar
    texto_str = str(texto).strip().upper()
    
    # Remover acentos usando unicodedata
    texto_normalizado = unicodedata.normalize('NFD', texto_str)
    texto_sem_acento = ''.join(char for char in texto_normalizado 
                              if unicodedata.category(char) != 'Mn')
    
    return texto_sem_acento

def formatar_moeda_brasileira(valor: float) -> str:
    """Formata valor monetário no padrão brasileiro"""
    try:
        if pd.isna(valor) or valor is None:
            return "R$ 0,00"
        
        valor_float = float(valor)
        
        # Usar locale se disponível, senão formatação manual
        try:
            return locale.currency(valor_float, grouping=True, symbol='R                "Valor": [
                    "SP", self.uf_selecionado, self.tipo_frete, 
                    # Configuração da página - DEVE SER A PRIMEIRA COISA!
import streamlit as st

# Configurar página ANTES de qualquer outro comando Streamlit
st.set_page_config(
    page_title="Simulador de Preço de Venda Sobel", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊"
)

import pandas as pd
import pyodbc
import io
import os
import requests
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any
import math
import time
import unicodedata
import locale

# Configurar locale para formatação brasileira
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Fallback se não conseguir configurar

# Carrega chave da API
load_dotenv()

# ==================== FUNÇÕES AUXILIARES ====================

def normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza texto para comparação"""
    if pd.isna(texto) or texto is None:
        return ""
    
    # Converter para string e normalizar
    texto_str = str(texto).strip().upper()
    
    # Remover acentos usando unicodedata
    texto_normalizado = unicodedata.normalize('NFD', texto_str)
    texto_sem_acento = ''.join(char for char in texto_normalizado 
                              if unicodedata.category(char) != 'Mn')
    
    return texto_sem_acento

def formatar_moeda_brasileira(valor: float) -> str:
    """Formata valor monetário no padrão brasileiro"""
    try:
        if pd.isna(valor) or valor is None:
            return "R$ 0,00"
        
        valor_float = float(valor)
        
        # Usar locale se disponível, senão formatação manual
        try:
            return locale.currency(valor_float, grouping=True, symbol='R

def obter_faixa_km_exata(distancia_km: float, faixas: list) -> str:
    """Dado a distância, retorna a faixa de KM correspondente (ex: '0-50')"""
    # Primeiro: busca exata
    for ini, fim, label in faixas:
        if ini <= distancia_km <= fim:
            return label

    # Segundo: busca pela faixa mais próxima (menor diferença)
    if faixas:
        melhor_faixa = None
        menor_diferenca = float('inf')

        for ini, fim, label in faixas:
            # Calcular distância até o centro da faixa
            centro_faixa = (ini + fim) / 2 if fim != float('inf') else ini + 50
            diferenca = abs(distancia_km - centro_faixa)

            if diferenca < menor_diferenca:
                menor_diferenca = diferenca
                melhor_faixa = label

        # Se a diferença for razoável (menos de 100km), usar a faixa mais próxima
        if menor_diferenca <= 100:
            return melhor_faixa

    return 'Indefinida'

def buscar_frete_inteligente(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str) -> dict:
    """
    Busca valores de frete de forma inteligente para otimização de veículo
    """
    resultado = {
        'truck': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'carreta': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'capacidades': {'truck': 870, 'carreta': 1740}
    }

    # Buscar ambos os tipos
    for tipo_veiculo in ['truck', 'carreta']:
        valor, faixa_usada, metodo = buscar_frete_por_faixa(df_clientes, cidade_ibge, faixa_km, tipo_veiculo)
        resultado[tipo_veiculo] = {
            'valor': valor,
            'faixa_usada': faixa_usada,
            'metodo': metodo
        }

    return resultado

def calcular_frete_otimizado(resultado_frete: dict, quantidade_total: int) -> dict:
    """
    Calcula o frete otimizado baseado no volume total
    """
    truck_info = resultado_frete['truck']
    carreta_info = resultado_frete['carreta']
    capacidades = resultado_frete['capacidades']

    # Se não encontrou nenhum valor, retornar erro
    if truck_info['valor'] == 0 and carreta_info['valor'] == 0:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhum valor de frete encontrado',
            'detalhes': {}
        }

    # Calcular cenários
    cenarios = {}

    # Cenário Truck (se couber)
    if quantidade_total <= capacidades['truck'] and truck_info['valor'] > 0:
        cenarios['truck'] = {
            'frete_total': truck_info['valor'],
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': 1,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'],
            'ocupacao': (quantidade_total / capacidades['truck']) * 100
        }

    # Cenário Carreta
    if carreta_info['valor'] > 0:
        viagens_carreta = max(1, math.ceil(quantidade_total / capacidades['carreta']))
        cenarios['carreta'] = {
            'frete_total': carreta_info['valor'] * viagens_carreta,
            'frete_por_caixa': carreta_info['valor'] / capacidades['carreta'],
            'viagens': viagens_carreta,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['carreta'] * viagens_carreta,
            'ocupacao': (quantidade_total / (capacidades['carreta'] * viagens_carreta)) * 100
        }

    # Cenário Truck múltiplo (se necessário)
    if quantidade_total > capacidades['truck'] and truck_info['valor'] > 0:
        viagens_truck = math.ceil(quantidade_total / capacidades['truck'])
        cenarios['truck_multiplo'] = {
            'frete_total': truck_info['valor'] * viagens_truck,
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': viagens_truck,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'] * viagens_truck,
            'ocupacao': (quantidade_total / (capacidades['truck'] * viagens_truck)) * 100
        }

    # Encontrar melhor opção (menor custo total)
    if not cenarios:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhuma opção de frete viável',
            'detalhes': {}
        }

    melhor_opcao = min(cenarios.keys(), key=lambda k: cenarios[k]['frete_total'])
    melhor_cenario = cenarios[melhor_opcao]

    # Calcular economia
    economia = 0.0
    if 'carreta' in cenarios and melhor_opcao != 'carreta':
        economia = cenarios['carreta']['frete_total'] - melhor_cenario['frete_total']

    # Gerar alerta
    alerta = ""
    if melhor_opcao == 'truck':
        alerta = f"✅ OTIMIZAÇÃO: Volume de {quantidade_total} caixas cabe em TRUCK! Economia de R$ {economia:.2f}"
    elif melhor_opcao == 'truck_multiplo':
        viagens = melhor_cenario['viagens']
        alerta = f"📦 MÚLTIPLOS TRUCKS: {viagens} viagens necessárias. " + (f"Economia de R$ {economia:.2f}" if economia > 0 else "")
    else:
        alerta = f"🚛 CARRETA RECOMENDADA: Volume de {quantidade_total} caixas otimizado para carreta"

    return {
        'veiculo_otimo': melhor_opcao,
        'frete_total': melhor_cenario['frete_total'],
        'frete_por_caixa': melhor_cenario['frete_por_caixa'],
        'economia': economia,
        'alerta': alerta,
        'detalhes': {
            'cenarios': cenarios,
            'melhor_cenario': melhor_cenario,
            'truck_info': truck_info,
            'carreta_info': carreta_info
        }
    }

def buscar_frete_por_faixa(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str, tipo_veiculo='truck') -> tuple:
    """
    Busca o valor do frete de forma inteligente
    """
    # Primeira tentativa: busca exata por cidade_ibge e faixa
    linha_exata = df_clientes[
        (df_clientes['cidade_ibge'] == cidade_ibge) &
        (df_clientes['FAIXA_KM'] == faixa_km)
    ]

    if not linha_exata.empty:
        if tipo_veiculo == 'truck':
            valor = linha_exata.iloc[0]['TBL_TRCK'] if not pd.isna(linha_exata.iloc[0]['TBL_TRCK']) else 0.0
        elif tipo_veiculo == 'carreta':
            valor = linha_exata.iloc[0]['TBL_CRRT'] if 'TBL_CRRT' in linha_exata.columns and not pd.isna(linha_exata.iloc[0]['TBL_CRRT']) else 0.0
        else:
            valor = 0.0

        if valor > 0:
            return float(valor), faixa_km, "exata"

    # Segunda tentativa: buscar por IBGE e calcular pela faixa mais próxima
    linhas_ibge = df_clientes[df_clientes['cidade_ibge'] == cidade_ibge]

    if not linhas_ibge.empty:
        distancia_solicitada = extrair_distancia_da_faixa(faixa_km)

        if distancia_solicitada is not None:
            melhor_faixa = None
            menor_diferenca = float('inf')
            melhor_linha = None

            for _, linha in linhas_ibge.iterrows():
                faixa_disponivel = linha['FAIXA_KM']
                distancia_disponivel = extrair_distancia_da_faixa(faixa_disponivel)

                if distancia_disponivel is not None:
                    diferenca = abs(distancia_solicitada - distancia_disponivel)
                    if diferenca < menor_diferenca:
                        menor_diferenca = diferenca
                        melhor_faixa = faixa_disponivel
                        melhor_linha = linha

            if melhor_linha is not None:
                if tipo_veiculo == 'truck':
                    valor = melhor_linha['TBL_TRCK'] if not pd.isna(melhor_linha['TBL_TRCK']) else 0.0
                elif tipo_veiculo == 'carreta':
                    valor = melhor_linha['TBL_CRRT'] if 'TBL_CRRT' in melhor_linha and not pd.isna(melhor_linha['TBL_CRRT']) else 0.0
                else:
                    valor = 0.0

                if valor > 0:
                    return float(valor), melhor_faixa, f"aproximada (IBGE {cidade_ibge})"

    return 0.0, "não encontrada", "não encontrado"

def extrair_distancia_da_faixa(faixa: str) -> float:
    """Extrai a distância média de uma faixa"""
    try:
        faixa_str = str(faixa).strip()

        if '+' in faixa_str:
            valor = int(faixa_str.replace('+', '').strip())
            return float(valor + 50)
        elif '-' in faixa_str:
            partes = faixa_str.split('-')
            if len(partes) == 2:
                ini, fim = int(partes[0].strip()), int(partes[1].strip())
                return float((ini + fim) / 2)
        else:
            return float(faixa_str)
    except (ValueError, IndexError):
        return None

# ==================== CLASSES PRINCIPAIS ====================

class ConfiguracaoTributaria:
    """Classe para gerenciar configurações tributárias por UF"""

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
        'RJ': {'interna': 0.22, 'interestadual': 0.12, 'fcp': 0.02}, 
        'RN': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RS': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RO': {'interna': 0.175, 'interestadual': 0.12, 'fcp': 0.0},
        'RR': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
        'SC': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
        'SP': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
        'SE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'TO': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0}
    }

    @classmethod
    def obter_aliquotas(cls, uf: str) -> Dict[str, float]:
        """Retorna as alíquotas para uma UF específica"""
        return cls.ICMS_ALIQUOTAS.get(uf.upper(), {
            'interna': 0.18, 
            'interestadual': 0.12, 
            'fcp': 0.0
        })

class GerenciadorGeolocalizacao:
    """Classe para gerenciar operações de geolocalização"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço ou CEP em coordenadas (lat, lng)"""
        try:
            with st.spinner("🔍 Geocodificando endereço..."):
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return location["lat"], location["lng"]
                return None, None
        except Exception as e:
            st.error(f"❌ Erro na geocodificação: {str(e)}")
            return None, None

    def calcular_distancia(self, origem_coords: Tuple[float, float], 
                          destino_coords: Tuple[float, float]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Consulta a Distance Matrix API e retorna distância e tempo"""
        try:
            with st.spinner("📏 Calculando distância e tempo..."):
                lat_o, lng_o = origem_coords
                lat_d, lng_d = destino_coords

                url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat_o},{lng_o}&destinations={lat_d},{lng_d}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                elemento = data['rows'][0]['elements'][0]
                status = elemento.get("status", "ERRO")

                if status != "OK":
                    return None, None, f"⚠️ API não conseguiu calcular: `{status}`"

                distancia = elemento['distance']['text']
                duracao = elemento['duration']['text']
                return distancia, duracao, None

        except Exception as e:
            return None, None, f"❌ Erro ao processar resposta: {str(e)}"

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas usando a fórmula de Haversine"""
        R = 6371  # Raio da Terra em km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

class GerenciadorBancoDados:
    """Classe para gerenciar conexões e consultas ao banco de dados"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @st.cache_data(ttl=600)
    def carregar_clientes_ou_rede(_self) -> pd.DataFrame:
        """Carrega dados dos clientes do banco de dados"""
        try:
            with st.spinner("🔄 Carregando dados dos clientes..."):
                with pyodbc.connect(_self.connection_string, timeout=30) as conexao:
                    query = """
                        SELECT 
                            SA1.A1_COD, 
                            SA1.A1_LOJA,
                            SA1.A1_ZZLOJA,
                            SA1.A1_NOME,
                            IIF(SA1.A1_ZZREDE = '', LEFT(SA1.A1_NOME, 20), SA1.A1_ZZREDE) AS REDE,
                            SA1.A1_CEP, 
                            SA1.A1_RISCO,
                            SA1.A1_ZZCONTR,
                            SA1.A1_LC,
                            SA1.A1_END,                         
                            SA1.A1_MCOMPRA,
                            SA1.A1_ULTCOM,
                            SA1.A1_EST,
                            SA1.A1_MUN,
                            SA1.A1_BAIRRO,
                            SA1.A1_END,
                            SA1.A1_CGC,
                            cep.longitude,
                            cep.latitude,
                            cep.nome_logradouro_sem_acento,
                            ibge.cidade_ibge,
                            T.CIDADE,
                            T.FAIXA_KM,
                            T.TBL_TRCK,
                            T.TBL_CRRT
                        FROM SA1010 SA1
                        INNER JOIN cep.dbo.tbl_cep_202504_n_logradouro AS cep 
                            ON cep.cep COLLATE Latin1_General_CI_AS = SA1.A1_CEP COLLATE Latin1_General_CI_AS
                        INNER JOIN cep.dbo.tbl_cep_202504_n_cidade_ibge AS ibge 
                            ON ibge.id_cidade = cep.cidade_id
                        INNER JOIN BISOBEL.dbo.TRANSP_TARGET T ON T.COD_IBGE COLLATE Latin1_General_CI_AS = ibge.cidade_ibge 
                        WHERE SA1.A1_MSBLQL = '2'
                          AND SA1.D_E_L_E_T_ = ''
                    """
                    return pd.read_sql(query, conexao)
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados dos clientes: {e}")
            return pd.DataFrame()

class CalculadoraTributaria:
    """Classe para realizar cálculos tributários"""

    @staticmethod
    def arredondar_valor(valor: Any, decimais: int = 2) -> float:
        """Arredonda valores para evitar problemas de precisão"""
        try:
            return round(float(valor), decimais)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def calcular_icms_st_completo(valor_produto: float, ipi_valor: float, mva: float,
                                 icms_interestadual: float, icms_interno_destino: float,
                                 fcp_aliquota: float, frete: float = 0.0,
                                 seguro: float = 0.0, despesas: float = 0.0,
                                 descontos: float = 0.0) -> Tuple[float, float, float, float, float]:
        """
        Cálculo preciso do ICMS-ST conforme a legislação
        """
        # Se MVA for 0, não há ICMS-ST
        if mva <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        # Base sem MVA: inclui valor do produto + IPI
        base_sem_mva = CalculadoraTributaria.arredondar_valor(valor_produto + ipi_valor)

        # Aplica MVA
        base_com_mva = CalculadoraTributaria.arredondar_valor(base_sem_mva * (1 + mva))

        # ICMS origem (interestadual) sobre base sem MVA
        icms_origem = CalculadoraTributaria.arredondar_valor(base_sem_mva * icms_interestadual)

        # ICMS destino (interno) sobre base com MVA
        icms_destino = CalculadoraTributaria.arredondar_valor(base_com_mva * icms_interno_destino)

        # ICMS-ST: diferença entre ICMS destino e ICMS origem
        icms_st = CalculadoraTributaria.arredondar_valor(max(icms_destino - icms_origem, 0.0))

        # FCP somente se a alíquota for maior que zero
        fcp = CalculadoraTributaria.arredondar_valor(base_sem_mva * fcp_aliquota) if fcp_aliquota > 0 else 0.0

        return icms_st, base_com_mva, icms_origem, icms_destino, fcp

class CalculadoraResultados:
    """Classe para calcular resultados financeiros"""

    def __init__(self, tipo_frete: str = "CIF"):
        self.tipo_frete = tipo_frete

    def calcular_resultados_completos(self, row: pd.Series) -> pd.Series:
        """Calcula todos os resultados financeiros para uma linha de produto"""
        try:
            # Valores base
            preco_venda = CalculadoraTributaria.arredondar_valor(row["Preço de Venda"])
            qtd = CalculadoraTributaria.arredondar_valor(row["Quantidade"], 0)
            subtotal = CalculadoraTributaria.arredondar_valor(preco_venda * qtd)

            # Custos
            custo_net = CalculadoraTributaria.arredondar_valor(row.get("Custo NET", 0))
            custo_fixo = CalculadoraTributaria.arredondar_valor(row.get("Custo Fixo", 0))
            custo_total_unit = CalculadoraTributaria.arredondar_valor(custo_net + custo_fixo)
            custo_total = CalculadoraTributaria.arredondar_valor(custo_total_unit * qtd)

            # Frete
            frete_total = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0)) * qtd
            ) if self.tipo_frete == "CIF" else 0.0

            frete_unit = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0))
            ) if self.tipo_frete == "CIF" else 0.0

            # IPI
            ipi_percent = float(row.get("IPI", 0))
            ipi_total = CalculadoraTributaria.arredondar_valor(subtotal * ipi_percent)

            # Parâmetros ICMS-ST
            mva = float(row.get("MVA", 0))
            icms_interestadual = float(row.get("ICMS Interestadual", 0))
            icms_interno_destino = float(row.get("ICMS Interno Destino", 0))
            fcp_aliquota = float(row.get("FCP", 0))

            # Calcular ICMS-ST
            icms_st, base_icms_st, icms_proprio, icms_total_interno, fcp_valor = \
                CalculadoraTributaria.calcular_icms_st_completo(
                    valor_produto=subtotal,
                    ipi_valor=ipi_total,
                    mva=mva,
                    icms_interestadual=icms_interestadual,
                    icms_interno_destino=icms_interno_destino,
                    fcp_aliquota=fcp_aliquota
                )

            # Despesas operacionais
            despesas_operacionais = self._calcular_despesas_operacionais(row, subtotal)
            total_despesas_operacionais = despesas_operacionais

            # Lucro antes dos impostos sobre lucro
            lucro_antes_ir = CalculadoraTributaria.arredondar_valor(
                subtotal - custo_total - total_despesas_operacionais - frete_total
            )

            # Calcular IR e CSLL
            irpj, csll = self._calcular_ir_csll(lucro_antes_ir)

            # Lucro líquido
            lucro_liquido = CalculadoraTributaria.arredondar_valor(lucro_antes_ir - irpj - csll)

            # Margem calculada corretamente
            margem_antes_ir = CalculadoraTributaria.arredondar_valor(
                (lucro_antes_ir / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            margem_liquida = CalculadoraTributaria.arredondar_valor(
                (lucro_liquido / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            # Total NF
            total_nf = CalculadoraTributaria.arredondar_valor(subtotal + ipi_total + icms_st + fcp_valor)

            # Ponto de equilíbrio
            ponto_equilibrio = self._calcular_ponto_equilibrio(row, custo_total_unit, frete_unit)

            return pd.Series({
                "Preço Venda": preco_venda,
                "Qtd": qtd,
                "Custo NET": custo_net,
                "Custo Fixo": custo_fixo,
                "MVA": mva,
                "Comissão": float(row.get("Comissão", 0)),
                "Bonificação": float(row.get("Bonificação", 0)),
                "Subtotal": subtotal,
                "IPI": ipi_total,
                "Base ICMS-ST": base_icms_st,
                "ICMS Próprio": icms_proprio,
                "ICMS-ST": icms_st,
                "FCP": fcp_valor,
                "Total NF": total_nf,
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
            st.error(f"❌ Erro no cálculo do produto {row.get('Descrição', 'N/A')}: {str(e)}")
            return self._retornar_serie_vazia()

    def _calcular_despesas_operacionais(self, row: pd.Series, subtotal: float) -> float:
        """Calcula o total das despesas operacionais"""
        despesas = [
            "ICMS Interestadual", "COFINS", "PIS", "Comissão",
            "Bonificação", "Contigência", "Contrato", "%Estrategico"
        ]

        total = 0.0
        for despesa in despesas:
            percentual = float(row.get(despesa, 0))
            total += CalculadoraTributaria.arredondar_valor(subtotal * percentual)

        return total

    def _calcular_ir_csll(self, lucro_antes_ir: float) -> Tuple[float, float]:
        """Calcula IRPJ e CSLL"""
        if lucro_antes_ir <= 0:
            return 0.0, 0.0

        # IRPJ: 15% + 10% sobre o que exceder R$ 20.000/mês
        irpj = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.15)
        if lucro_antes_ir > 20000:
            adicional_irpj = CalculadoraTributaria.arredondar_valor((lucro_antes_ir - 20000) * 0.10)
            irpj += adicional_irpj

        # CSLL: 9%
        csll = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.09)

        return irpj, csll

    def _calcular_ponto_equilibrio(self, row: pd.Series, custo_total_unit: float, frete_unit: float) -> float:
        """Calcula o ponto de equilíbrio"""
        try:
            # Despesas diretas percentuais
            despesas_diretas = (
                float(row.get("ICMS Interestadual", 0)) +
                float(row.get("COFINS", 0)) +
                float(row.get("PIS", 0)) +
                float(row.get("Comissão", 0)) +
                float(row.get("Bonificação", 0)) +
                float(row.get("Contigência", 0)) +
                float(row.get("Contrato", 0)) +
                float(row.get("%Estrategico", 0))
            )

            if despesas_diretas >= 1.0:
                return 0.0

            # Cálculo básico
            ponto_equilibrio = (custo_total_unit + frete_unit) / (1 - despesas_diretas)
            return CalculadoraTributaria.arredondar_valor(ponto_equilibrio)

        except Exception:
            return 0.0

    def _retornar_serie_vazia(self) -> pd.Series:
        """Retorna uma série com valores zerados em caso de erro"""
        return pd.Series({
            "Preço Venda": 0, "Qtd": 0, "Custo NET": 0, "Custo Fixo": 0, "MVA": 0,
            "Comissão": 0, "Bonificação": 0, "Subtotal": 0, "IPI": 0, "Base ICMS-ST": 0,
            "ICMS Próprio": 0, "ICMS-ST": 0, "FCP": 0, "Total NF": 0, "Custo Total": 0,
            "Frete Total": 0, "Total Despesas": 0, "Lucro Antes IR": 0, "IRPJ": 0,
            "CSLL": 0, "Lucro Líquido": 0, "Margem Antes IR %": 0, "Margem Líquida %": 0,
            "Ponto Equilíbrio": 0
        })

class GerenciadorEstado:
    """Classe para gerenciar o estado da aplicação"""

    def __init__(self):
        self.inicializar_estado()

    def inicializar_estado(self):
        """Inicializa as variáveis de estado"""
        estados_default = {
            'df_atual': None,
            'modo_equilibrio': False,
            'comissao_global_aplicada': False,
            'comissoes_editadas': {},
            'bonificacoes_editadas': {},
            'valores_originais': {},
            'df_edicao_temp': None,
            'resultados_atualizados': False,
            'frete_calculado_automatico': 0.0,
            'distancia_calculada': None,
            'tempo_calculado': None,
            'usar_frete_auto': False,
            'coordenadas_origem': None,
            'coordenadas_destino': None,
            'resultado_frete_completo': None,
            'otimizacao_frete': None,
            'dados_carregados': False
        }

        for key, value in estados_default.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def resetar_estado(self):
        """Reseta o estado da aplicação"""
        for key in ['df_atual', 'modo_equilibrio', 'comissao_global_aplicada', 
                   'comissoes_editadas', 'bonificacoes_editadas', 'valores_originais',
                   'df_edicao_temp', 'resultados_atualizados']:
            if key in st.session_state:
                if key in ['comissoes_editadas', 'bonificacoes_editadas', 'valores_originais']:
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None if key == 'df_atual' or key == 'df_edicao_temp' else False

class SimuladorSobel:
    """Classe principal do simulador"""

    def __init__(self):
        self.config_tributaria = ConfiguracaoTributaria()
        self.gerenciador_estado = GerenciadorEstado()
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if self.api_key:
            self.geolocalizacao = GerenciadorGeolocalizacao(self.api_key)
        else:
            self.geolocalizacao = None
            st.warning("⚠️ Google Maps API não configurada. Funcionalidades de geolocalização desabilitadas.")

        # Configuração do banco de dados
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.0.16;"
            "DATABASE=Protheus_Producao;"
            "UID=sa;"
            "PWD=Totvs@452525!"
        )
        self.db_manager = GerenciadorBancoDados(connection_string)

        # Produtos esperados com normalização para comparação
        self.produtos_esperados = [
            "ÁGUA SANITÁRIA 5L", "ÁGUA SANITÁRIA 2L", "ÁGUA SANITÁRIA 1L",
            "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
            "AMACIANTE 5L", "AMACIANTE 2L",
            "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
            "LAVA LOUÇAS 500ML", "LAVA LOUÇAS 5L",
            "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
            "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
            "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
        ]
        
        # Criar versão normalizada para comparação
        self.produtos_esperados_normalizados = [normalizar_texto(produto) for produto in self.produtos_esperados]

        # Inicializar variáveis
        self.dados_cliente_selecionado = None
        self.frete_padrao_cliente = None
        self.faixas_km_ordenadas = []
        self.df_padrao = pd.DataFrame()
        self.contrato_real = None

    def executar(self):
        """Método principal para executar o simulador"""
        self._configurar_interface()
        
        # Verificar conexão com banco
        if not self._verificar_conexao_banco():
            return
            
        self._carregar_dados_iniciais()
        self._exibir_interface()

    def _configurar_interface(self):
        """Configura a interface do usuário"""
        # CSS customizado para melhorar a aparência
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e7cb8 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2e7cb8;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .success-card {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .warning-card {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-card {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header principal
        st.markdown("""
        <div class="main-header">
            <h1>📊 Simulador de Formação de Preço de Venda - Sobel v3.0</h1>
            <p>Sistema integrado de simulação com otimização de frete e geolocalização</p>
        </div>
        """, unsafe_allow_html=True)

        # Verificar se a imagem existe
        if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
            col_logo, col_space = st.columns([1, 3])
            with col_logo:
                st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=250)

    def _verificar_conexao_banco(self) -> bool:
        """Verifica se a conexão com o banco está funcionando"""
        try:
            with st.spinner("🔄 Verificando conexão com banco de dados..."):
                df_test = self.db_manager.carregar_clientes_ou_rede()
                if df_test.empty:
                    st.error("❌ Nenhum dado encontrado no banco. Verifique a conexão.")
                    return False
                st.success(f"✅ Banco conectado com sucesso! {len(df_test)} registros encontrados.")
                return True
        except Exception as e:
            st.error(f"❌ Erro de conexão com banco: {str(e)}")
            return False

    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais necessários"""
        # Carregar planilha padrão
        arquivo_padrao = "Custo de reposição.xlsx"
        if os.path.exists(arquivo_padrao):
            try:
                with st.spinner("📂 Carregando planilha de custos..."):
                    self.df_padrao = pd.read_excel(arquivo_padrao)
                    self.df_padrao.columns = self.df_padrao.columns.str.strip()
                    st.success(f"✅ Planilha carregada: {len(self.df_padrao)} produtos disponíveis")
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo padrão: {str(e)}")
                self.df_padrao = pd.DataFrame()
        else:
            st.warning("⚠️ Arquivo padrão 'Custo de reposição.xlsx' não encontrado.")
            self.df_padrao = pd.DataFrame()

        # Carregar faixas de KM
        self.faixas_km_ordenadas = self._extrair_faixas_ordenadas()

    def _extrair_faixas_ordenadas(self) -> list:
        """Extrai e ordena as faixas de KM disponíveis da base de clientes"""
        try:
            df_clientes = self.db_manager.carregar_clientes_ou_rede()
            if df_clientes.empty:
                return []
                
            faixas = []
            faixas_unicas = df_clientes['FAIXA_KM'].dropna().unique()

            for faixa in faixas_unicas:
                try:
                    faixa_str = str(faixa).strip()
                    if '+' in faixa_str:
                        ini = int(faixa_str.replace('+', '').strip())
                        faixas.append((ini, float('inf'), faixa_str))
                    elif '-' in faixa_str:
                        partes = faixa_str.split('-')
                        if len(partes) == 2:
                            ini, fim = int(partes[0].strip()), int(partes[1].strip())
                            faixas.append((ini, fim, faixa_str))
                    else:
                        valor = int(faixa_str)
                        faixas.append((valor, valor, faixa_str))
                except (ValueError, IndexError):
                    continue

            faixas.sort(key=lambda x: x[0])

            if faixas:
                st.info(f"🎯 Faixas de KM carregadas: {[f[2] for f in faixas[:5]]}{'...' if len(faixas) > 5 else ''}")

            return faixas
        except Exception as e:
            st.error(f"❌ Erro ao extrair faixas de frete: {e}")
            return []

    def _exibir_interface(self):
        """Exibe a interface principal"""
        # Verificar se há dados para continuar
        if self.df_padrao.empty:
            st.error("❌ Não é possível continuar sem dados. Carregue uma planilha de custos.")
            return

        # Usar tabs para melhor organização
        tab1, tab2, tab3 = st.tabs(["👤 Cliente & Parâmetros", "📊 Simulação", "📄 Relatórios"])

        with tab1:
            self._exibir_secao_cliente()
            st.markdown("---")
            self._exibir_secao_parametros()
            st.markdown("---")
            self._exibir_upload_arquivo()

        with tab2:
            if self._validar_dados():
                self._processar_simulacao()

        with tab3:
            self._exibir_relatorios()

    def _exibir_secao_cliente(self):
        """Exibe a seção de seleção de cliente melhorada"""
        st.markdown("### 👤 Seleção de Cliente")

        # Opção de cliente
        opcao_cliente = st.radio(
            "Como deseja proceder?", 
            ["🔍 Selecionar cliente existente", "➕ Cliente novo (sem histórico)"], 
            horizontal=True
        )

        self.contrato_real = None
        self.dados_cliente_selecionado = None

        if opcao_cliente == "🔍 Selecionar cliente existente":
            clientes_df = self.db_manager.carregar_clientes_ou_rede()
            
            if not clientes_df.empty:
                # Melhor interface de seleção
                col_search, col_filter = st.columns([3, 1])
                
                with col_search:
                    # Busca por nome
                    busca_nome = st.text_input("🔍 Buscar por nome do cliente", placeholder="Digite parte do nome...")
                
                with col_filter:
                    # Filtro por UF
                    ufs_disponiveis = ['Todos'] + sorted(clientes_df['A1_EST'].unique().tolist())
                    uf_filtro = st.selectbox("📍 Filtrar por UF", ufs_disponiveis)

                # Aplicar filtros
                df_filtrado = clientes_df.copy()
                
                if busca_nome:
                    df_filtrado = df_filtrado[
                        df_filtrado['A1_NOME'].str.contains(busca_nome, case=False, na=False)
                    ]
                
                if uf_filtro != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['A1_EST'] == uf_filtro]

                if not df_filtrado.empty:
                    # Criar opções mais informativas
                    opcoes_clientes = []
                    for idx, row in df_filtrado.iterrows():
                        opcao = f"{row['A1_NOME'][:50]} | {row['A1_MUN']}/{row['A1_EST']} | {row['A1_COD']}/{row['A1_LOJA']}"
                        if row['REDE'] and str(row['REDE']) != str(row['A1_NOME'])[:20]:
                            opcao += f" | [{row['REDE']}]"
                        opcoes_clientes.append(opcao)

                    cliente_escolhido_display = st.selectbox(
                        f"📋 Clientes encontrados ({len(df_filtrado)} registros):", 
                        opcoes_clientes,
                        help="Formato: Nome | Cidade/UF | Código/Loja | [Rede]"
                    )

                    # Encontrar o cliente selecionado
                    indice_selecionado = opcoes_clientes.index(cliente_escolhido_display)
                    self.dados_cliente_selecionado = df_filtrado.iloc[indice_selecionado]

                    # Exibir dados do cliente
                    self._exibir_dados_completos_cliente()

                    # Seção de cálculo de frete (se disponível)
                    if self.geolocalizacao:
                        self._exibir_secao_rota_integrada()
                else:
                    st.info("ℹ️ Nenhum cliente encontrado com os filtros aplicados.")
            else:
                st.warning("⚠️ Nenhum cliente encontrado na base de dados.")
        
        else:  # Cliente novo
            self._exibir_secao_cliente_novo()

    def _exibir_secao_cliente_novo(self):
        """Exibe seção para entrada manual de dados de cliente novo"""
        st.markdown("#### ➕ Dados do Cliente Novo")
        
        # Informações básicas
        col1, col2 = st.columns(2)
        
        with col1:
            nome_cliente_novo = st.text_input(
                "🏢 Nome/Razão Social", 
                placeholder="Digite o nome do cliente...",
                help="Nome para identificação nas análises"
            )
            
            uf_cliente_novo = st.selectbox(
                "📍 UF de Destino",
                options=['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
                help="Selecione o estado de destino"
            )
            
        with col2:
            cidade_cliente_novo = st.text_input(
                "🏙️ Cidade",
                placeholder="Nome da cidade...",
                help="Cidade de destino para cálculo de frete"
            )
            
            contrato_cliente_novo = st.number_input(
                "📄 % Contrato",
                min_value=0.0,
                max_value=100.0,
                value=1.00,
                step=0.01,
                help="Percentual de contrato para este cliente"
            )

        # Seção de endereço para frete
        if self.geolocalizacao:
            st.markdown("#### 🗺️ Endereço para Cálculo de Frete")
            
            col_end1, col_end2 = st.columns(2)
            
            with col_end1:
                endereco_cliente_novo = st.text_input(
                    "📍 Endereço Completo",
                    placeholder="Rua, número, bairro...",
                    help="Endereço mais completo possível para melhor precisão"
                )
                
            with col_end2:
                cep_cliente_novo = st.text_input(
                    "📮 CEP",
                    placeholder="00000-000",
                    help="CEP para maior precisão na localização",
                    max_chars=9
                )
            
            # Montar endereço completo
            if nome_cliente_novo and uf_cliente_novo:
                # Criar dados simulados do cliente novo
                endereco_completo_partes = []
                
                if endereco_cliente_novo:
                    endereco_completo_partes.append(endereco_cliente_novo)
                    
                if cidade_cliente_novo:
                    endereco_completo_partes.append(cidade_cliente_novo)
                    
                endereco_completo_partes.append(uf_cliente_novo)
                
                if cep_cliente_novo:
                    endereco_completo_partes.append(f"CEP {cep_cliente_novo}")
                    
                endereco_completo_partes.append("Brasil")
                
                endereco_completo = ", ".join(endereco_completo_partes)
                
                # Exibir endereço montado
                st.text_area(
                    "🎯 Endereço para Geocodificação",
                    endereco_completo,
                    height=80,
                    disabled=True,
                    help="Endereço que será usado para calcular distância e frete"
                )
                
                # Criar dados fictícios do cliente para uso no sistema
                self.dados_cliente_selecionado = pd.Series({
                    'A1_NOME': nome_cliente_novo,
                    'A1_EST': uf_cliente_novo,
                    'A1_MUN': cidade_cliente_novo or 'Não informado',
                    'A1_COD': 'NOVO',
                    'A1_LOJA': '01',
                    'A1_ZZCONTR': contrato_cliente_novo,
                    'A1_END': endereco_cliente_novo or 'Não informado',
                    'A1_CEP': cep_cliente_novo.replace('-', '') if cep_cliente_novo else '00000000',
                    'A1_BAIRRO': 'Não informado',
                    'cidade_ibge': '0000000',  # Será usado valor padrão para frete
                    'REDE': 'Cliente Novo',
                    'latitude': 0.0,
                    'longitude': 0.0
                })
                
                # Aplicar contrato
                self.contrato_real = contrato_cliente_novo
                
                # Exibir dados do cliente novo
                with st.expander("📋 Resumo do Cliente Novo", expanded=True):
                    col_res1, col_res2, col_res3 = st.columns(3)
                    
                    with col_res1:
                        st.metric("🏢 Cliente", nome_cliente_novo)
                        st.metric("📍 UF", uf_cliente_novo)
                        
                    with col_res2:
                        st.metric("🏙️ Cidade", cidade_cliente_novo or "Não informado")
                        st.metric("📄 Contrato", f"{contrato_cliente_novo:.2f}%")
                        
                    with col_res3:
                        st.info("💡 **Dica:** Complete o endereço para cálculo automático de frete")
                
                # Seção de cálculo de frete para cliente novo
                if endereco_cliente_novo or cep_cliente_novo:
                    self._exibir_secao_rota_cliente_novo(endereco_completo)
                else:
                    st.warning("⚠️ Preencha o endereço para habilitar o cálculo automático de frete")

    def _exibir_secao_rota_cliente_novo(self, endereco_destino: str):
        """Exibe seção de cálculo de rota para cliente novo"""
        with st.expander("🗺️ Cálculo de Frete para Cliente Novo", expanded=False):
            st.markdown("#### 🧭 Configuração de Rota")

            # Origens disponíveis
            origens = {
                "📍 Matriz (São Paulo - SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "📍 Filial (Atibaia - SP)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }

            col_origem, col_destino = st.columns(2)

            with col_origem:
                origem_opcao = st.selectbox("🚚 Unidade de Origem", list(origens.keys()), key="origem_cliente_novo")
                origem = origens[origem_opcao]
                st.text_area("📍 Endereço de Origem", origem, height=60, disabled=True)

            with col_destino:
                st.text_input("🎯 Cliente Novo", self.dados_cliente_selecionado['A1_NOME'], disabled=True)
                st.text_area("🎯 Endereço de Destino", endereco_destino, height=60, disabled=True)

            # Configurações de frete
            st.markdown("#### 🚛 Configuração de Frete")
            
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "🚚 Truck (870 caixas)" if x == "truck" else "🚛 Carreta (1.740 caixas)",
                    key="tipo_veiculo_cliente_novo"
                )
                
                if st.button("🗺️ Calcular Rota", type="primary", use_container_width=True, key="calc_rota_novo"):
                    self._calcular_frete_cliente_novo(origem, endereco_destino, tipo_veiculo)

            with col_frete2:
                # Resultados da rota
                if st.session_state.get('distancia_calculada_novo') and st.session_state.get('tempo_calculado_novo'):
                    st.success("✅ Rota Calculada")
                    st.metric("📏 Distância", st.session_state.get('distancia_calculada_novo'))
                    st.metric("⏱️ Tempo", st.session_state.get('tempo_calculado_novo'))
                else:
                    st.info("ℹ️ Clique em 'Calcular' para obter a rota")

            with col_frete3:
                # Frete calculado ou manual
                frete_calculado = st.session_state.get('frete_calculado_cliente_novo', 0.0)
                if frete_calculado > 0:
                    usar_frete_auto = st.checkbox("🤖 Usar frete calculado", value=True, key="usar_frete_auto_novo")
                    if usar_frete_auto:
                        self.frete_padrao_cliente = frete_calculado
                        st.success(f"💰 {formatar_moeda_brasileira(frete_calculado)}/caixa")
                    else:
                        self.frete_padrao_cliente = st.number_input(
                            "✏️ Frete Manual (R$)", 
                            min_value=0.0, 
                            value=1.50, 
                            step=0.01,
                            key="frete_manual_novo"
                        )
                else:
                    self.frete_padrao_cliente = st.number_input(
                        "✏️ Frete Manual (R$)", 
                        min_value=0.0, 
                        value=1.50, 
                        step=0.01,
                        key="frete_manual_novo_default"
                    )

            # Mostrar mapas se disponível
            if (st.session_state.get('coordenadas_origem_novo') and 
                st.session_state.get('coordenadas_destino_novo')):
                self._exibir_mapas_cliente_novo(origem)

    def _calcular_frete_cliente_novo(self, origem: str, endereco_destino: str, tipo_veiculo: str = "truck"):
        """Calcula frete para cliente novo baseado no endereço informado"""
        with st.spinner("🔄 Processando cálculo para cliente novo..."):
            # Geocodificar origem
            origem_coords = self.geolocalizacao.geocode(origem)
            if not origem_coords:
                st.error("❌ Não foi possível localizar o endereço de origem.")
                return

            # Geocodificar destino
            destino_coords = self.geolocalizacao.geocode(endereco_destino)
            if not destino_coords:
                st.error(f"❌ Não foi possível localizar o endereço: {endereco_destino}")
                st.info("💡 **Dicas para melhorar a localização:**")
                st.write("• Use endereços mais específicos (rua, número)")
                st.write("• Inclua o CEP sempre que possível")
                st.write("• Verifique a ortografia da cidade")
                return

            # Calcular distância e tempo
            distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)
            if erro:
                st.error(erro)
                return

            try:
                # Processar distância
                distancia_texto = distancia.replace('km', '').strip()
                
                # Converter para float tratando vírgulas
                if ',' in distancia_texto:
                    if '.' in distancia_texto:
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:
                        partes = distancia_texto.split(',')
                        if len(partes[1]) == 3:
                            distancia_km = float(distancia_texto.replace(',', ''))
                        else:
                            distancia_km = float(distancia_texto.replace(',', '.'))
                else:
                    distancia_km = float(distancia_texto)

                # Armazenar dados específicos para cliente novo
                st.session_state.distancia_calculada_novo = distancia
                st.session_state.tempo_calculado_novo = duracao
                st.session_state.coordenadas_origem_novo = origem_coords
                st.session_state.coordenadas_destino_novo = destino_coords

                # Para cliente novo, usar frete baseado em distância (sem tabela específica)
                # Implementar lógica de frete por distância
                frete_por_km = self._calcular_frete_por_distancia(distancia_km, tipo_veiculo)
                
                st.session_state.frete_calculado_cliente_novo = frete_por_km

                # Exibir resultados
                st.success(f"""
                ✅ **Rota Calculada para Cliente Novo!**
                
                📏 **Distância:** {distancia} ({duracao}) → {distancia_km:.0f} km
                🚛 **Veículo:** {tipo_veiculo.upper()}
                💰 **Frete Estimado:** {formatar_moeda_brasileira(frete_por_km)}/caixa
                """)

                st.info("💡 **Frete Calculado por Distância:** Para clientes novos, o frete é estimado baseado na distância e tipo de veículo")

            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")

    def _calcular_frete_por_distancia(self, distancia_km: float, tipo_veiculo: str) -> float:
        """Calcula frete baseado na distância para clientes novos"""
        
        # Faixas de distância e valores base
        faixas_frete = [
            (0, 50, {"truck": 1.20, "carreta": 0.85}),
            (50, 100, {"truck": 1.50, "carreta": 1.10}),
            (100, 200, {"truck": 1.80, "carreta": 1.35}),
            (200, 300, {"truck": 2.10, "carreta": 1.60}),
            (300, 500, {"truck": 2.40, "carreta": 1.85}),
            (500, 800, {"truck": 2.70, "carreta": 2.10}),
            (800, 1200, {"truck": 3.00, "carreta": 2.35}),
            (1200, float('inf'), {"truck": 3.50, "carreta": 2.80})
        ]
        
        # Encontrar faixa correspondente
        for ini, fim, valores in faixas_frete:
            if ini <= distancia_km < fim:
                frete_base = valores.get(tipo_veiculo, valores["truck"])
                
                # Ajuste progressivo dentro da faixa
                if fim != float('inf'):
                    faixa_size = fim - ini
                    posicao_na_faixa = (distancia_km - ini) / faixa_size
                    
                    # Encontrar próxima faixa para interpolação
                    proximo_valor = frete_base
                    for next_ini, next_fim, next_valores in faixas_frete:
                        if next_ini == fim:
                            proximo_valor = next_valores.get(tipo_veiculo, next_valores["truck"])
                            break
                    
                    # Interpolação linear
                    frete_ajustado = frete_base + (proximo_valor - frete_base) * posicao_na_faixa * 0.3
                    return round(frete_ajustado, 2)
                else:
                    return frete_base
        
        # Fallback para distâncias muito pequenas
        return 1.50 if tipo_veiculo == "truck" else 1.10

    def _exibir_mapas_cliente_novo(self, origem: str):
        """Exibe mapas para cliente novo"""
        origem_coords = st.session_state.get('coordenadas_origem_novo')
        destino_coords = st.session_state.get('coordenadas_destino_novo')

        if not origem_coords or not destino_coords:
            return

        st.markdown("#### 🗺️ Visualização da Rota")
        
        col_mapa, col_street = st.columns(2)

        with col_mapa:
            st.markdown("**📍 Mapa com Rota**")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

        with col_street:
            st.markdown("**🚦 Street View - Destino**")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

    def _exibir_dados_completos_cliente(self):
        """Exibe dados completos do cliente de forma mais organizada"""
        st.markdown("#### 📋 Informações do Cliente Selecionado")

        cliente_dict = self.dados_cliente_selecionado.to_dict()

        # Card principal com informações básicas
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🏢 Razão Social", 
                    value=cliente_dict.get('A1_NOME', 'N/A')[:30] + ('...' if len(str(cliente_dict.get('A1_NOME', ''))) > 30 else ''),
                    help=cliente_dict.get('A1_NOME', 'N/A')
                )
                
            with col2:
                codigo = cliente_dict.get('A1_COD', '')
                loja = cliente_dict.get('A1_LOJA', '')
                st.metric("🏷️ Código/Loja", f"{codigo}/{loja}")
                
            with col3:
                uf = cliente_dict.get('A1_EST', 'N/A')
                cidade = cliente_dict.get('A1_MUN', 'N/A')
                st.metric("📍 Localização", f"{cidade}/{uf}")
                
            with col4:
                try:
                    contrato_valor = float(cliente_dict.get("A1_ZZCONTR", 0) or 0)
                    self.contrato_real = contrato_valor
                except:
                    self.contrato_real = 0.0
                    contrato_valor = 0.0
                st.metric("📄 Contrato", f"{contrato_valor:.2f}%")

        # Informações detalhadas em expander
        with st.expander("📄 Detalhes Completos", expanded=False):
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                # Endereço
                endereco_parts = []
                if cliente_dict.get('A1_END'):
                    endereco_parts.append(cliente_dict['A1_END'])
                if cliente_dict.get('A1_BAIRRO'):
                    endereco_parts.append(cliente_dict['A1_BAIRRO'])
                if cliente_dict.get('A1_MUN') and cliente_dict.get('A1_EST'):
                    endereco_parts.append(f"{cliente_dict['A1_MUN']}/{cliente_dict['A1_EST']}")
                
                cep = cliente_dict.get('A1_CEP', '')
                if cep and len(cep) == 8:
                    cep_formatado = f"{cep[:5]}-{cep[5:]}"
                    endereco_parts.append(f"CEP: {cep_formatado}")
                
                endereco_completo = '\n'.join(endereco_parts) if endereco_parts else "Não informado"
                st.text_area("📍 Endereço Completo", endereco_completo, height=100, disabled=True)
                
            with col_det2:
                # Informações financeiras
                try:
                    lc_value = float(cliente_dict.get('A1_LC', 0) or 0)
                    lc_text = f"R$ {lc_value:,.2f}" if lc_value > 0 else "Não definido"
                except:
                    lc_text = "Não definido"
                
                st.text_input("💳 Limite de Crédito", lc_text, disabled=True)
                st.text_input("⚠️ Classificação de Risco", cliente_dict.get('A1_RISCO', 'N/A'), disabled=True)
                
                # Rede se houver
                rede = cliente_dict.get('REDE', '')
                nome_resumo = str(cliente_dict.get('A1_NOME', ''))[:20]
                if rede and rede != nome_resumo:
                    st.text_input("🏪 Rede", rede, disabled=True)

    def _exibir_secao_rota_integrada(self):
        """Exibe seção de cálculo de rota melhorada"""
        with st.expander("🗺️ Cálculo de Frete e Rota", expanded=False):
            st.markdown("#### 🧭 Configuração de Rota")

            # Origens disponíveis
            origens = {
                "📍 Matriz (São Paulo - SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "📍 Filial (Atibaia - SP)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }

            col_origem, col_destino = st.columns(2)

            with col_origem:
                origem_opcao = st.selectbox("🚚 Unidade de Origem", list(origens.keys()))
                origem = origens[origem_opcao]
                st.text_area("📍 Endereço de Origem", origem, height=60, disabled=True)

            with col_destino:
                # Informações do cliente
                cliente_info = f"{self.dados_cliente_selecionado['A1_NOME'][:30]}..."
                st.text_input("🎯 Cliente Selecionado", cliente_info, disabled=True)
                
                # Endereço para geocodificação
                endereco_destino = self._montar_endereco_completo_para_geocode(
                    self.dados_cliente_selecionado.to_dict()
                )
                st.text_area("🎯 Endereço de Destino", endereco_destino, height=60, disabled=True)

            # Configurações de frete
            st.markdown("#### 🚛 Configuração de Frete")
            
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "🚚 Truck (870 caixas)" if x == "truck" else "🚛 Carreta (1.740 caixas)"
                )
                
                if st.button("🗺️ Calcular Rota e Frete", type="primary", use_container_width=True):
                    self._calcular_frete_automatico(origem, tipo_veiculo)

            with col_frete2:
                # Resultados da rota
                if st.session_state.get('distancia_calculada') and st.session_state.get('tempo_calculado'):
                    st.success("✅ Rota Calculada")
                    st.metric("📏 Distância", st.session_state.get('distancia_calculada'))
                    st.metric("⏱️ Tempo", st.session_state.get('tempo_calculado'))
                else:
                    st.info("ℹ️ Clique em 'Calcular' para obter a rota")

            with col_frete3:
                # Frete calculado ou manual
                frete_calculado = st.session_state.get('frete_calculado_automatico', 0.0)
                if frete_calculado > 0:
                    usar_frete_auto = st.checkbox("🤖 Usar frete calculado", value=True)
                    if usar_frete_auto:
                        self.frete_padrao_cliente = frete_calculado
                        st.success(f"💰 R$ {frete_calculado:.2f}/caixa")
                    else:
                        self.frete_padrao_cliente = st.number_input(
                            "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                        )
                else:
                    self.frete_padrao_cliente = st.number_input(
                        "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                    )

            # Mostrar mapas se disponível
            if (st.session_state.get('coordenadas_origem') and 
                st.session_state.get('coordenadas_destino')):
                self._exibir_mapas_cliente(origem)

    def _montar_endereco_completo_para_geocode(self, cliente_dict: dict) -> str:
        """Monta endereço otimizado para geocodificação"""
        partes_endereco = []

        def safe_str(value):
            if value is None or pd.isna(value):
                return ""
            return str(value).strip()

        # Componentes do endereço
        endereco_rua = safe_str(cliente_dict.get('A1_END', ''))
        if endereco_rua and endereco_rua.lower() != 'não informado':
            partes_endereco.append(endereco_rua)

        bairro = safe_str(cliente_dict.get('A1_BAIRRO', ''))
        if bairro and bairro.lower() not in ['', 'não informado']:
            partes_endereco.append(bairro)

        cidade = safe_str(cliente_dict.get('A1_MUN', ''))
        if cidade:
            partes_endereco.append(cidade)

        uf = safe_str(cliente_dict.get('A1_EST', ''))
        if uf:
            partes_endereco.append(uf)

        cep = safe_str(cliente_dict.get('A1_CEP', ''))
        if cep and cep not in ['N/A', '0'] and len(cep) >= 8:
            if len(cep) == 8 and cep.isdigit():
                cep_formatado = f"{cep[:5]}-{cep[5:]}"
                partes_endereco.append(f"CEP {cep_formatado}")
            else:
                partes_endereco.append(f"CEP {cep}")

        partes_endereco.append("Brasil")
        return ", ".join(partes_endereco)

    def _calcular_frete_automatico(self, origem: str, tipo_veiculo: str = "truck"):
        """Calcula frete automaticamente baseado na distância real"""
        with st.spinner("🔄 Processando cálculo de frete..."):
            # Geocodificar origem
            origem_coords = self.geolocalizacao.geocode(origem)
            if not origem_coords:
                st.error("❌ Não foi possível localizar o endereço de origem.")
                return

            # Geocodificar destino
            cliente_dict = self.dados_cliente_selecionado.to_dict()
            endereco_destino_completo = self._montar_endereco_completo_para_geocode(cliente_dict)
            destino_coords = self.geolocalizacao.geocode(endereco_destino_completo)

            if not destino_coords:
                # Fallback para coordenadas do banco
                try:
                    lat_banco = float(self.dados_cliente_selecionado["latitude"])
                    lng_banco = float(self.dados_cliente_selecionado["longitude"])
                    if lat_banco != 0 and lng_banco != 0:
                        destino_coords = (lat_banco, lng_banco)
                        st.warning("⚠️ Usando coordenadas do banco como fallback.")
                    else:
                        st.error("❌ Não foi possível localizar o endereço de destino.")
                        return
                except:
                    st.error("❌ Endereço não encontrado e coordenadas do banco indisponíveis.")
                    return

            # Calcular distância e tempo
            distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)
            if erro:
                st.error(erro)
                return

            try:
                # Processar distância
                distancia_texto = distancia.replace('km', '').strip()
                
                # Converter para float tratando vírgulas
                if ',' in distancia_texto:
                    if '.' in distancia_texto:
                        # Formato: "1,159.5" - vírgula = milhares, ponto = decimal
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:
                        # Verificar se vírgula é separador de milhares ou decimal
                        partes = distancia_texto.split(',')
                        if len(partes[1]) == 3:  # "1,159" - milhares
                            distancia_km = float(distancia_texto.replace(',', ''))
                        else:  # "1,5" - decimal
                            distancia_km = float(distancia_texto.replace(',', '.'))
                else:
                    distancia_km = float(distancia_texto)

                # Armazenar dados no session state
                st.session_state.distancia_calculada = distancia
                st.session_state.tempo_calculado = duracao
                st.session_state.coordenadas_origem = origem_coords
                st.session_state.coordenadas_destino = destino_coords

                # Obter faixa de KM e código IBGE
                faixa_km = obter_faixa_km_exata(distancia_km, self.faixas_km_ordenadas)
                cidade_ibge = str(self.dados_cliente_selecionado["cidade_ibge"])

                # Buscar valores de frete
                df_clientes_frete = self.db_manager.carregar_clientes_ou_rede()
                resultado_frete = buscar_frete_inteligente(df_clientes_frete, cidade_ibge, faixa_km)

                # Calcular otimização (volume estimado inicial)
                volume_estimado = 500
                otimizacao = calcular_frete_otimizado(resultado_frete, volume_estimado)

                # Armazenar resultados
                st.session_state.frete_calculado_automatico = otimizacao['frete_por_caixa']
                st.session_state.tipo_veiculo_usado = otimizacao['veiculo_otimo']
                st.session_state.resultado_frete_completo = resultado_frete
                st.session_state.otimizacao_frete = otimizacao

                # Exibir resultados
                if otimizacao['frete_por_caixa'] > 0:
                    st.success(f"""
                    ✅ **Cálculo Concluído com Sucesso!**
                    
                    📏 **Rota:** {distancia} ({duracao}) → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💰 **Frete/Caixa:** {formatar_moeda_brasileira(otimizacao['frete_por_caixa'])}
                    🚛 **Veículo Otimizado:** {otimizacao['veiculo_otimo'].upper()}
                    """)

                    # Alerta de otimização
                    if otimizacao['alerta']:
                        if 'OTIMIZAÇÃO' in otimizacao['alerta']:
                            st.success(f"🎯 {otimizacao['alerta']}")
                        elif 'MÚLTIPLOS' in otimizacao['alerta']:
                            st.warning(f"📦 {otimizacao['alerta']}")
                        else:
                            st.info(f"ℹ️ {otimizacao['alerta']}")

                    # Tabela de comparação
                    self._exibir_comparacao_fretes(resultado_frete)
                else:
                    st.warning(f"""
                    ⚠️ **Rota calculada, mas frete não encontrado**
                    
                    📏 **Distância:** {distancia} → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💡 **Sugestão:** Use frete manual
                    """)

            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")

    def _exibir_comparacao_fretes(self, resultado_frete: dict):
        """Exibe tabela de comparação de fretes"""
        st.markdown("#### 📊 Comparação de Fretes Disponíveis")

        truck_info = resultado_frete['truck']
        carreta_info = resultado_frete['carreta']

        comparacao_data = []
        
        if truck_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚚 Truck',
                'Capacidade': '870 caixas',
                'Frete Total': formatar_moeda_brasileira(truck_info['valor']),
                'Frete/Caixa': formatar_moeda_brasileira(truck_info['valor']/870),
                'Método de Busca': truck_info['metodo'],
                'Faixa Utilizada': truck_info['faixa_usada']
            })

        if carreta_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚛 Carreta',
                'Capacidade': '1.740 caixas',
                'Frete Total': formatar_moeda_brasileira(carreta_info['valor']),
                'Frete/Caixa': formatar_moeda_brasileira(carreta_info['valor']/1740),
                'Método de Busca': carreta_info['metodo'],
                'Faixa Utilizada': carreta_info['faixa_usada']
            })

        if comparacao_data:
            df_comparacao = pd.DataFrame(comparacao_data)
            st.dataframe(df_comparacao, use_container_width=True, hide_index=True)
            st.info("💡 **Dica:** O frete será otimizado automaticamente quando você definir as quantidades!")

    def _exibir_mapas_cliente(self, origem: str):
        """Exibe mapas interativos"""
        origem_coords = st.session_state.get('coordenadas_origem')
        destino_coords = st.session_state.get('coordenadas_destino')

        if not origem_coords or not destino_coords:
            return

        st.markdown("#### 🗺️ Visualização da Rota")
        
        col_mapa, col_street = st.columns(2)

        with col_mapa:
            st.markdown("**📍 Mapa com Rota**")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

        with col_street:
            st.markdown("**🚦 Street View - Destino**")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

    def _exibir_secao_parametros(self):
        """Exibe seção de parâmetros melhorada"""
        st.markdown("### ⚙️ Parâmetros de Simulação")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🏭 Origem")
            st.info("**São Paulo - SP** (Fixo)")
            
            # Frete
            if hasattr(self, 'frete_padrao_cliente') and self.frete_padrao_cliente is not None:
                st.success(f"🚛 **Frete:** {formatar_moeda_brasileira(self.frete_padrao_cliente)}/caixa")
                st.caption("Definido pela seleção do cliente")
                self.frete_padrao = self.frete_padrao_cliente
            else:
                self.frete_padrao = st.number_input(
                    "🚛 Frete/Caixa (R$)", 
                    min_value=0.0, 
                    value=1.50, 
                    step=0.01,
                    help="Frete padrão para cliente novo"
                )

            # Tipo de frete
            self.tipo_frete = st.radio(
                "📦 Tipo de Frete", 
                ("CIF", "FOB"),
                help="CIF: Vendedor paga frete | FOB: Comprador paga frete"
            )

        with col2:
            st.markdown("#### 📍 Destino")
            
            # UF de destino
            opcoes_uf = self.df_padrao["UF"].dropna().unique().tolist() if not self.df_padrao.empty else []
            
            if self.dados_cliente_selecionado is not None:
                uf_cliente = self.dados_cliente_selecionado['A1_EST']
                if uf_cliente in opcoes_uf:
                    index_uf = opcoes_uf.index(uf_cliente)
                    self.uf_selecionado = st.selectbox(
                        "🗺️ UF de Destino", 
                        options=opcoes_uf, 
                        index=index_uf,
                        help="UF do cliente selecionado"
                    )
                else:
                    st.error(f"❌ UF do cliente ({uf_cliente}) não encontrada na planilha!")
                    self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)
            else:
                self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)

            # Contrato
            if self.contrato_real is not None:
                st.success(f"📄 **Contrato:** {formatar_percentual_brasileiro(self.contrato_real)}")
                st.caption("Valor real do cliente")
                self.contrato_percentual = self.contrato_real / 100
            else:
                contrato_input = st.number_input(
                    "📄 % Contrato", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=1.00, 
                    step=0.01
                )
                self.contrato_percentual = contrato_input / 100

        with col3:
            st.markdown("#### 💰 Parâmetros Globais")
            
            self.custo_fixo_global = st.number_input(
                "🏗️ Custo Fixo Global (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            
            comissao_input = st.number_input(
                "🤝 % Comissão Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.1,
                help="Se zero, usa valor da planilha"
            )
            self.comissao_padrao = comissao_input / 100

            bonificacao_input = st.number_input(
                "🎁 % Bonificação Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            self.bonificacao_global = bonificacao_input / 100

        # Mostrar informações tributárias
        if self.uf_selecionado:
            st.markdown("#### 📋 Informações Tributárias")
            aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
            aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

            col_trib1, col_trib2, col_trib3 = st.columns(3)
            
            with col_trib1:
                st.metric("🏛️ ICMS Interestadual", formatar_percentual_brasileiro(aliquotas_origem['interestadual'] * 100))
            
            with col_trib2:
                st.metric("🏛️ ICMS Interno", formatar_percentual_brasileiro(aliquotas_destino['interna'] * 100))
            
            with col_trib3:
                if aliquotas_destino['fcp'] > 0:
                    st.metric("📊 FCP", formatar_percentual_brasileiro(aliquotas_destino['fcp'] * 100))
                else:
                    st.metric("📊 FCP", "Não aplicável")

    def _exibir_upload_arquivo(self):
        """Seção de upload melhorada"""
        st.markdown("### 📂 Gestão de Arquivos")
        
        col_upload, col_info = st.columns([2, 1])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "📊 Atualizar planilha de custos (.xlsx)", 
                type="xlsx",
                help="Substitui o arquivo 'Custo de reposição.xlsx'"
            )

            if uploaded_file:
                if st.button("🔄 Confirmar Atualização", type="primary"):
                    try:
                        with st.spinner("📤 Processando upload..."):
                            arquivo_padrao = "Custo de reposição.xlsx"

                            # Criar backup
                            if os.path.exists(arquivo_padrao):
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
                                os.rename(arquivo_padrao, backup_name)
                                st.success(f"✅ Backup criado: {backup_name}")

                            # Salvar novo arquivo
                            with open(arquivo_padrao, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Recarregar dados
                            self.df_padrao = pd.read_excel(arquivo_padrao)
                            self.df_padrao.columns = self.df_padrao.columns.str.strip()

                            # Resetar estado
                            self.gerenciador_estado.resetar_estado()
                            
                            st.success("✅ Arquivo atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        
        with col_info:
            # Informações sobre o arquivo atual
            if not self.df_padrao.empty:
                st.info(f"""
                **📋 Arquivo Atual:**
                - Produtos: {len(self.df_padrao)}
                - UFs: {len(self.df_padrao['UF'].unique()) if 'UF' in self.df_padrao.columns else 0}
                """)
            else:
                st.warning("⚠️ Nenhum arquivo carregado")

    def _validar_dados(self) -> bool:
        """Validação melhorada dos dados"""
        if self.df_padrao.empty:
            st.error("❌ Carregue uma planilha de custos para continuar.")
            return False
            
        if not self.uf_selecionado:
            st.warning("⚠️ Selecione uma UF de destino.")
            return False
            
        return True

    def _processar_simulacao(self):
        """Processa a simulação principal"""
        st.markdown("### 📊 Simulação de Preços")
        
        # Preparar dados base
        df_base = self._preparar_dados_base()

        if df_base.empty:
            st.error(f"❌ Nenhum produto encontrado para a UF {self.uf_selecionado}")
            return

        # Exibir controles
        self._exibir_controles(df_base)

        # Processar edição e resultados
        self._processar_edicao_e_resultados(df_base)

    def _preparar_dados_base(self) -> pd.DataFrame:
        """Prepara dados base com melhor tratamento de acentuação"""
        # Filtrar por UF
        df_base = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado].copy()

        # Resetar se mudou UF
        if (st.session_state.df_atual is not None and 
            "UF" in st.session_state.df_atual.columns):
            ufs_atuais = st.session_state.df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != self.uf_selecionado:
                self.gerenciador_estado.resetar_estado()

        # CORREÇÃO: Filtrar produtos com normalização de acentos
        if not df_base.empty and "Descrição" in df_base.columns:
            # Criar coluna temporária com descrições normalizadas
            df_base['Descricao_Normalizada'] = df_base['Descrição'].apply(normalizar_texto)
            
            # Filtrar usando versões normalizadas
            mask_produtos = df_base['Descricao_Normalizada'].isin(self.produtos_esperados_normalizados)
            df_base = df_base[mask_produtos].copy()
            
            # Remover coluna temporária
            df_base = df_base.drop('Descricao_Normalizada', axis=1)
            
            # Debug: mostrar produtos encontrados
            if not df_base.empty:
                st.success(f"✅ {len(df_base)} produtos encontrados para {self.uf_selecionado}")
                produtos_encontrados = df_base['Descrição'].tolist()
                with st.expander(f"📋 Produtos carregados ({len(produtos_encontrados)})", expanded=False):
                    for produto in produtos_encontrados:
                        st.write(f"• {produto}")
            else:
                st.warning(f"⚠️ Nenhum produto encontrado para {self.uf_selecionado}")
                
                # Debug: mostrar produtos disponíveis na planilha
                if "Descrição" in self.df_padrao.columns:
                    produtos_planilha = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado]["Descrição"].unique()
                    st.info(f"Produtos disponíveis na planilha para {self.uf_selecionado}:")
                    for produto in produtos_planilha[:10]:  # Mostrar apenas os primeiros 10
                        st.write(f"• {produto}")

        # Ajustar colunas e aplicar parâmetros
        df_base = self._ajustar_colunas_necessarias(df_base)
        df_base = self._aplicar_parametros_globais(df_base)

        return df_base

    def _ajustar_colunas_necessarias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta colunas com melhor tratamento de valores padrão"""
        colunas_necessarias = [
            "Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", 
            "ICMS ST", "ICMS", "MVA", "Comissão", "Bonificação", "COFINS", "PIS", 
            "Contigência", "ICMS Interestadual", "ICMS Interno Destino", "FCP"
        ]

        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        for col in colunas_necessarias:
            if col not in df.columns:
                if col == "Quantidade":
                    df[col] = 1
                elif col == "ICMS Interestadual":
                    df[col] = aliquotas_origem['interestadual']
                elif col == "ICMS Interno Destino":
                    df[col] = aliquotas_destino['interna']
                elif col == "FCP":
                    df[col] = aliquotas_destino['fcp']
                else:
                    df[col] = 0.0

        return df

    def _aplicar_parametros_globais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica parâmetros globais com melhor organização"""
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        # Aplicar valores básicos
        df["Frete Caixa"] = self.frete_padrao
        df["Contrato"] = self.contrato_percentual
        df["UF Origem"] = 'SP'
        df["UF Destino"] = self.uf_selecionado
        df["ICMS Interestadual"] = aliquotas_origem['interestadual']
        df["ICMS Interno Destino"] = aliquotas_destino['interna']
        df["FCP"] = aliquotas_destino['fcp']

        # Aplicar parâmetros condicionais
        if self.custo_fixo_global > 0:
            df["Custo Fixo"] = self.custo_fixo_global

        if self.comissao_padrao > 0:
            df["Comissão"] = self.comissao_padrao
            st.session_state.comissao_global_aplicada = True
        else:
            st.session_state.comissao_global_aplicada = False

        if self.bonificacao_global > 0:
            df["Bonificação"] = self.bonificacao_global

        return df

    def _exibir_controles(self, df_base: pd.DataFrame):
        """Controles principais melhorados"""
        st.markdown("#### 🎯 Ações Principais")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⚖️ Calcular Ponto de Equilíbrio", use_container_width=True, type="primary"):
                with st.spinner("⚖️ Calculando pontos de equilíbrio..."):
                    df_equilibrio, alertas = self._calcular_ponto_equilibrio(df_base)

                    if alertas:
                        for alerta in alertas:
                            st.warning(f"⚠️ {alerta}")

                    st.session_state.df_atual = df_equilibrio.copy()
                    st.session_state.modo_equilibrio = True
                    st.success("✅ Pontos de equilíbrio calculados!")

        with col2:
            if st.button("🔄 Resetar Simulação", use_container_width=True):
                self.gerenciador_estado.resetar_estado()
                st.success("✅ Dados resetados.")
                time.sleep(1)
                st.rerun()

        with col3:
            # Informações rápidas
            if not df_base.empty:
                st.metric("📦 Produtos", len(df_base))

    def _calcular_ponto_equilibrio(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """Cálculo melhorado do ponto de equilíbrio"""
        df_resultado = df.copy()
        alertas = []

        for index, row in df_resultado.iterrows():
            try:
                # Custos base
                custo_net = float(row.get("Custo NET", 0))
                custo_fixo = float(row.get("Custo Fixo", 0))
                custo_total_unit = custo_net + custo_fixo
                frete_unit = float(row.get("Frete Caixa", 0)) if self.tipo_frete == "CIF" else 0.0

                # Despesas percentuais
                despesas_diretas = (
                    float(row.get("ICMS Interestadual", 0)) +
                    float(row.get("COFINS", 0)) +
                    float(row.get("PIS", 0)) +
                    float(row.get("Comissão", 0)) +
                    float(row.get("Bonificação", 0)) +
                    float(row.get("Contigência", 0)) +
                    float(row.get("Contrato", 0)) +
                    float(row.get("%Estrategico", 0))
                )

                # Verificar viabilidade
                if despesas_diretas >= 1.0:
                    produto_nome = row.get('Descrição', f'Produto {index}')
                    alertas.append(f"{produto_nome}: Despesas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    custos_totais = custo_total_unit + frete_unit
                    preco_equilibrio = custos_totais / (1 - despesas_diretas)
                    preco_equilibrio = max(0.0, CalculadoraTributaria.arredondar_valor(preco_equilibrio, 2))

                df_resultado.at[index, "Preço de Venda"] = preco_equilibrio

            except Exception as e:
                produto_nome = row.get('Descrição', f'Produto {index}')
                alertas.append(f"Erro em {produto_nome}: {str(e)}")
                df_resultado.at[index, "Preço de Venda"] = 0.0

        return df_resultado, alertas

    def _processar_edicao_e_resultados(self, df_base: pd.DataFrame):
        """Processamento melhorado de edição e resultados"""
        # Determinar DataFrame
        if st.session_state.df_atual is not None:
            df_para_edicao = st.session_state.df_atual.copy()
        else:
            df_para_edicao = df_base.copy()

        # Aplicar lógica de comissão/bonificação
        df_para_edicao = self._aplicar_logica_comissao_bonificacao(df_para_edicao)

        # Exibir status e resumos
        self._exibir_status_melhorado()
        self._exibir_resumo_edicoes()

        # Editor de dados
        df_editado = self._exibir_editor_dados_melhorado(df_para_edicao)

        # Processar edições
        df_final = self._processar_dados_editados(df_editado, df_para_edicao)

        # Calcular e exibir resultados
        self._calcular_e_exibir_resultados(df_final)

    def _aplicar_logica_comissao_bonificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica lógica melhorada de comissão e bonificação"""
        df_temp = df.copy()

        # Garantir colunas numéricas
        for col in ["Comissão", "Bonificação"]:
            if col not in df_temp.columns:
                df_temp[col] = 0.0
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0.0)

        # Armazenar valores originais
        if not st.session_state.valores_originais:
            for index in df_temp.index:
                produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
                st.session_state.valores_originais[produto] = {
                    'comissao': float(df_temp.at[index, "Comissão"]),
                    'bonificacao': float(df_temp.at[index, "Bonificação"])
                }

        # Aplicar valores globais se não editados individualmente
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)

            # Comissão global
            if (st.session_state.comissao_global_aplicada and 
                self.comissao_padrao > 0 and 
                produto not in st.session_state.comissoes_editadas):
                df_temp.at[index, "Comissão"] = float(self.comissao_padrao)

            # Bonificação global
            if (self.bonificacao_global > 0 and 
                produto not in st.session_state.bonificacoes_editadas):
                df_temp.at[index, "Bonificação"] = float(self.bonificacao_global)

        # Aplicar edições individuais (prioridade máxima)
        for produto, valor in st.session_state.comissoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Comissão"] = float(valor)

        for produto, valor in st.session_state.bonificacoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Bonificação"] = float(valor)

        return df_temp

    def _exibir_status_melhorado(self):
        """Status melhorado da simulação"""
        # Card de status principal
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.metric("🗺️ Rota", f"SP → {self.uf_selecionado}")
            
        with col_status2:
            modo = "🔒 Equilíbrio" if st.session_state.modo_equilibrio else "📋 Normal"
            st.metric("⚙️ Modo", modo)
            
        with col_status3:
            frete_info = f"R$ {self.frete_padrao:.2f}" if hasattr(self, 'frete_padrao') else "N/A"
            st.metric("🚛 Frete/Caixa", frete_info)

        # Parâmetros ativos
        parametros_ativos = []
        if st.session_state.comissao_global_aplicada and self.comissao_padrao > 0:
            parametros_ativos.append(f"Comissão Global: {self.comissao_padrao:.1%}")
        if self.bonificacao_global > 0:
            parametros_ativos.append(f"Bonificação Global: {self.bonificacao_global:.1%}")

        if parametros_ativos:
            st.info(f"🎯 **Parâmetros Ativos:** {' | '.join(parametros_ativos)}")

        # Edições individuais
        edicoes = []
        if st.session_state.comissoes_editadas:
            edicoes.append(f"Comissões editadas: {len(st.session_state.comissoes_editadas)}")
        if st.session_state.bonificacoes_editadas:
            edicoes.append(f"Bonificações editadas: {len(st.session_state.bonificacoes_editadas)}")

        if edicoes:
            st.success(f"✏️ **Edições Individuais:** {' | '.join(edicoes)}")

    def _exibir_resumo_edicoes(self):
        """Resumo melhorado das edições"""
        if st.session_state.comissoes_editadas or st.session_state.bonificacoes_editadas:
            with st.expander("🎯 Detalhes das Edições Individuais", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🤝 Comissões Personalizadas:**")
                    if st.session_state.comissoes_editadas:
                        for produto, valor in st.session_state.comissoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('comissao', 0)
                            global_val = self.comissao_padrao if self.comissao_padrao > 0 else original
                            st.write(f"• {produto}: {formatar_percentual_brasileiro(valor * 100)} (era {formatar_percentual_brasileiro(global_val * 100)})")
                        
                        if st.button("🗑️ Limpar Comissões", key="clear_comissoes"):
                            st.session_state.comissoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma comissão editada")

                with col2:
                    st.markdown("**🎁 Bonificações Personalizadas:**")
                    if st.session_state.bonificacoes_editadas:
                        for produto, valor in st.session_state.bonificacoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('bonificacao', 0)
                            global_val = self.bonificacao_global if self.bonificacao_global > 0 else original
                            st.write(f"• {produto}: {formatar_percentual_brasileiro(valor * 100)} (era {formatar_percentual_brasileiro(global_val * 100)})")
                        
                        if st.button("🗑️ Limpar Bonificações", key="clear_bonificacoes"):
                            st.session_state.bonificacoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma bonificação editada")

    def _exibir_editor_dados_melhorado(self, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Editor de dados melhorado"""
        st.markdown("#### 📊 Editor de Dados da Simulação")

        # Preparar dados para edição
        colunas_edicao = [
            "Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
            "MVA", "Comissão", "Bonificação", "Contrato"
        ]

        df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()

        # Converter valores numéricos
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_para_edicao_clean.columns:
                df_para_edicao_clean[col] = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)

        # Converter percentuais para formato 0-100
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_para_edicao_clean.columns:
                valores = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = (valores * 100).round(2)

        # Editor com melhor configuração
        df_editado = st.data_editor(
            df_para_edicao_clean,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_principal",
            column_config={
                "Descrição": st.column_config.TextColumn(
                    "📦 Produto", 
                    disabled=True, 
                    width="medium"
                ),
                "Preço de Venda": st.column_config.NumberColumn(
                    "💰 Preço Venda", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "📦 Qtd", 
                    format="%.0f", 
                    min_value=1, 
                    step=1,
                    width="small"
                ),
                "Custo NET": st.column_config.NumberColumn(
                    "💵 Custo NET", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Custo Fixo": st.column_config.NumberColumn(
                    "🏗️ Custo Fixo", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "MVA": st.column_config.NumberColumn(
                    "📈 MVA (%)", 
                    format="%.1f%%", 
                    min_value=0.0, 
                    max_value=500.0, 
                    step=0.1,
                    width="small"
                ),
                "Comissão": st.column_config.NumberColumn(
                    "🤝 Comissão (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Bonificação": st.column_config.NumberColumn(
                    "🎁 Bonificação (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Contrato": st.column_config.NumberColumn(
                    "📄 Contrato (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                )
            },
            hide_index=True
        )

        # Dicas de uso
        st.info("💡 **Dicas:** Use ⭐ para editar valores individualmente. Clique duas vezes nas células para editar.")

        return df_editado

    def _processar_dados_editados(self, df_editado: pd.DataFrame, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Processamento melhorado dos dados editados"""
        df_processado = df_editado.copy()

        # Converter percentuais de volta para decimal
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_processado.columns:
                df_processado[col] = pd.to_numeric(df_processado[col], errors='coerce').fillna(0.0) / 100

        # Arredondar valores
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_processado.columns:
                df_processado[col] = df_processado[col].round(2)

        # Detectar mudanças com melhor feedback
        produtos_com_mudancas = []

        for index in df_processado.index:
            if index < len(df_para_edicao):
                produto = df_processado.at[index, "Descrição"]

                # Verificar comissão
                try:
                    comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
                    comissao_editada = float(df_processado.at[index, "Comissão"])

                    if abs(comissao_original - comissao_editada) > 0.001:
                        st.session_state.comissoes_editadas[produto] = comissao_editada
                        produtos_com_mudancas.append(f"Comissão {produto}: {comissao_editada:.2%}")
                except:
                    pass

                # Verificar bonificação
                try:
                    bonificacao_original = float(df_para_edicao.iloc[index]["Bonificação"])
                    bonificacao_editada = float(df_processado.at[index, "Bonificação"])

                    if abs(bonificacao_original - bonificacao_editada) > 0.001:
                        st.session_state.bonificacoes_editadas[produto] = bonificacao_editada
                        produtos_com_mudancas.append(f"Bonificação {produto}: {bonificacao_editada:.2%}")
                except:
                    pass

            if produtos_com_mudancas:
                mudancas_texto = ', '.join(produtos_com_mudancas[:3])
                if len(produtos_com_mudancas) > 3:
                    mudancas_texto += f" e mais {len(produtos_com_mudancas) - 3}"
                st.success(f"✏️ **Mudanças detectadas:** {mudancas_texto}")

        # Criar DataFrame final
        df_final = df_para_edicao.copy()
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                         "Custo Fixo", "MVA", "Comissão", "Bonificação", "Contrato"]

        for col in colunas_edicao:
            if col in df_processado.columns:
                df_final[col] = df_processado[col]

        st.session_state.df_edicao_temp = df_final.copy()
        return df_final

    def _calcular_e_exibir_resultados(self, df_final: pd.DataFrame):
        """Cálculo e exibição melhorados dos resultados"""
        st.markdown("#### 🚀 Resultados da Simulação")
        
        # Botão principal de cálculo
        col_calc, col_space = st.columns([2, 3])
        with col_calc:
            calcular_clicked = st.button(
                "🚀 Calcular Resultados Finais", 
                type="primary", 
                use_container_width=True
            )

        if calcular_clicked:
            with st.spinner("🔄 Processando cálculos..."):
                # Otimização de frete se disponível
                self._otimizar_frete_por_volume(df_final)

                # Armazenar dados
                st.session_state.df_atual = st.session_state.df_edicao_temp.copy()
                st.session_state.resultados_atualizados = True
                
                time.sleep(1)  # UX melhor
                st.rerun()

        # Mostrar resultados se disponível
        if st.session_state.get("resultados_atualizados", False):
            self._exibir_resultados_completos(df_final)

    def _otimizar_frete_por_volume(self, df_final: pd.DataFrame):
        """Otimização inteligente de frete por volume"""
        if (hasattr(st.session_state, 'resultado_frete_completo') and 
            st.session_state.resultado_frete_completo):

            volume_total = df_final["Quantidade"].sum()
            
            # Reavalia otimização
            nova_otimizacao = calcular_frete_otimizado(
                st.session_state.resultado_frete_completo, 
                volume_total
            )

            # Verificar mudanças
            otimizacao_anterior = st.session_state.get('otimizacao_frete', {})
            veiculo_anterior = otimizacao_anterior.get('veiculo_otimo', 'desconhecido')
            veiculo_novo = nova_otimizacao['veiculo_otimo']

            # Atualizar frete se necessário
            if veiculo_novo != veiculo_anterior and nova_otimizacao['frete_por_caixa'] > 0:
                df_final["Frete Caixa"] = nova_otimizacao['frete_por_caixa']

                # Alertar sobre otimização
                if nova_otimizacao['economia'] > 0:
                    st.success(f"""
                    🎯 **FRETE OTIMIZADO AUTOMATICAMENTE!**
                    
                    📦 Volume total: {volume_total} caixas
                    {nova_otimizacao['alerta']}
                    💰 Novo frete/caixa: R$ {nova_otimizacao['frete_por_caixa']:.2f}
                    """)
                else:
                    st.info(f"ℹ️ {nova_otimizacao['alerta']}")

            st.session_state.otimizacao_frete = nova_otimizacao

    def _exibir_resultados_completos(self, df_final: pd.DataFrame):
        """Exibição completa e melhorada dos resultados"""
        # Calcular resultados
        calculadora = CalculadoraResultados(self.tipo_frete)
        resultados = df_final.apply(calculadora.calcular_resultados_completos, axis=1)

        # Criar DataFrame para exibição
        df_display = self._criar_dataframe_display_melhorado(df_final, resultados)

        # Informações de otimização
        self._exibir_info_otimizacao(df_final)

        # Tabela principal de resultados
        self._exibir_tabela_resultados_melhorada(df_display)

        # Resumo executivo
        self._exibir_resumo_executivo_melhorado(df_display)

        # Análises detalhadas
        self._exibir_analises_detalhadas(df_final, resultados, df_display)

        # Seção de exportação
        self._exibir_secao_exportacao_melhorada(df_final, resultados, df_display)

    def _criar_dataframe_display_melhorado(self, df_final: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame melhorado para exibição"""
        df_display = pd.DataFrame({
            "Produto": df_final["Descrição"].values,
            "Preço Venda": resultados["Preço Venda"].values,
            "Qtd": resultados["Qtd"].values.astype(int),
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

        # Arredondamento melhorado
        colunas_monetarias = [
            "Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
            "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
            "Lucro Líquido", "Equilíbrio"
        ]

        for col in colunas_monetarias:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: CalculadoraTributaria.arredondar_valor(x, 2)
                )

        df_display["Margem %"] = df_display["Margem %"].apply(
            lambda x: CalculadoraTributaria.arredondar_valor(x, 1)
        )

        return df_display

    def _exibir_info_otimizacao(self, df_final: pd.DataFrame):
        """Exibe informações de otimização de frete"""
        if hasattr(st.session_state, 'otimizacao_frete') and st.session_state.otimizacao_frete:
            otimizacao = st.session_state.otimizacao_frete

            if otimizacao['veiculo_otimo'] != 'nenhum':
                col_opt1, col_opt2, col_opt3, col_opt4 = st.columns(4)

                with col_opt1:
                    volume_total = df_final["Quantidade"].sum()
                    st.metric("📦 Volume Total", f"{volume_total} caixas")

                with col_opt2:
                    veiculo_label = otimizacao['veiculo_otimo'].replace('_', ' ').upper()
                    st.metric("🚛 Veículo Otimizado", veiculo_label)

                with col_opt3:
                    st.metric("💰 Frete Total", f"R$ {otimizacao['frete_total']:.2f}")

                with col_opt4:
                    if otimizacao['economia'] > 0:
                        st.metric("💰 Economia", f"R$ {otimizacao['economia']:.2f}", delta="Positiva")
                    else:
                        st.metric("📊 Status", "Otimizado")

    def _exibir_tabela_resultados_melhorada(self, df_display: pd.DataFrame):
        """Tabela de resultados com melhor formatação"""
        st.markdown("#### 📊 Resultados Detalhados")

        # Função de coloração melhorada
        def colorir_valores(val):
            try:
                if isinstance(val, (int, float)):
                    if val < 0:
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                    elif val > 0:
                        return 'background-color: #e8f5e8; color: #2e7d32'
                    else:
                        return 'color: #666666'
                return ''
            except:
                return ''

        # Formatação aprimorada com padrão brasileiro
        styled_display = df_display.style.format({
            "Preço Venda": lambda x: formatar_moeda_brasileira(x),
            "Subtotal": lambda x: formatar_moeda_brasileira(x),
            "IPI": lambda x: formatar_moeda_brasileira(x),
            "ICMS-ST": lambda x: formatar_moeda_brasileira(x),
            "FCP": lambda x: formatar_moeda_brasileira(x),
            "Total NF": lambda x: formatar_moeda_brasileira(x),
            "Custo Total": lambda x: formatar_moeda_brasileira(x),
            "Despesas": lambda x: formatar_moeda_brasileira(x),
            "Lucro Antes IR": lambda x: formatar_moeda_brasileira(x),
            "IRPJ+CSLL": lambda x: formatar_moeda_brasileira(x),
            "Lucro Líquido": lambda x: formatar_moeda_brasileira(x),
            "Margem %": lambda x: formatar_percentual_brasileiro(x),
            "Equilíbrio": lambda x: formatar_moeda_brasileira(x)
        }).applymap(
            colorir_valores, 
            subset=["Lucro Antes IR", "Lucro Líquido", "Margem %"]
        ).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f0f2f6'), ('color', '#262730'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '8px'), ('text-align', 'right')]},
            {'selector': 'td:first-child', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}
        ])

        st.dataframe(styled_display, use_container_width=True, height=400)

    def _exibir_resumo_executivo_melhorado(self, df_display: pd.DataFrame):
        """Resumo executivo melhorado"""
        st.markdown("#### 📈 Resumo Executivo")

        if len(df_display) > 0:
            # Métricas principais
            col1, col2, col3, col4, col5 = st.columns(5)

            total_receita = df_display["Subtotal"].sum()
            total_lucro_liquido = df_display["Lucro Líquido"].sum()
            margem_ponderada = (total_lucro_liquido / total_receita) * 100 if total_receita > 0 else 0.0
            produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
            total_nf = df_display["Total NF"].sum()

            with col1:
                st.metric("💰 Receita Total", formatar_moeda_brasileira(total_receita))

            with col2:
                delta_lucro = formatar_percentual_brasileiro(margem_ponderada) if total_receita > 0 else "0,0%"
                st.metric("💵 Lucro Líquido", formatar_moeda_brasileira(total_lucro_liquido), delta=delta_lucro)

            with col3:
                cor_margem = "🟢" if margem_ponderada > 10 else "🟡" if margem_ponderada > 5 else "🔴"
                st.metric("📊 Margem Ponderada", f"{cor_margem} {formatar_percentual_brasileiro(margem_ponderada)}")

            with col4:
                cor_produtos = "🔴" if produtos_prejuizo > 0 else "🟢"
                st.metric("⚠️ Produtos c/ Prejuízo", f"{cor_produtos} {produtos_prejuizo}")

            with col5:
                st.metric("📄 Total NF", formatar_moeda_brasileira(total_nf))

            # Alertas inteligentes
            self._exibir_alertas_inteligentes(df_display, margem_ponderada, produtos_prejuizo)

    def _exibir_alertas_inteligentes(self, df_display: pd.DataFrame, margem_ponderada: float, produtos_prejuizo: int):
        """Sistema de alertas inteligentes"""
        alertas = []

        # Análise de margem
        if margem_ponderada < 5:
            alertas.append("🔴 **ATENÇÃO:** Margem muito baixa (< 5%). Revisar preços ou custos.")
        elif margem_ponderada < 10:
            alertas.append("🟡 **CUIDADO:** Margem baixa (< 10%). Monitorar competitividade.")
        elif margem_ponderada > 25:
            alertas.append("🟢 **EXCELENTE:** Margem alta (> 25%). Ótima rentabilidade!")

        # Análise de produtos
        if produtos_prejuizo > 0:
            produtos_negativos = df_display[df_display["Lucro Líquido"] < 0]
            maior_prejuizo = produtos_negativos.nlargest(1, "Lucro Líquido")
            if not maior_prejuizo.empty:
                produto_problema = maior_prejuizo.iloc[0]["Produto"]
                prejuizo_valor = maior_prejuizo.iloc[0]["Lucro Líquido"]
                alertas.append(f"🚨 **PRODUTO CRÍTICO:** {produto_problema} com prejuízo de R$ {abs(prejuizo_valor):.2f}")

        # Análise de concentração
        receita_por_produto = df_display["Subtotal"]
        produto_principal = df_display.loc[receita_por_produto.idxmax(), "Produto"]
        concentracao = (receita_por_produto.max() / receita_por_produto.sum()) * 100
        if concentracao > 50:
            alertas.append(f"📊 **CONCENTRAÇÃO:** {concentracao:.1f}% da receita vem de '{produto_principal}'")

        # Exibir alertas
        for alerta in alertas:
            if "🔴" in alerta or "🚨" in alerta:
                st.error(alerta)
            elif "🟡" in alerta:
                st.warning(alerta)
            else:
                st.success(alerta)

    def _exibir_analises_detalhadas(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Análises detalhadas melhoradas"""
        with st.expander("🔍 Análises Detalhadas", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📊 Composição", "🎯 Top Produtos", "📋 Breakdown"])

            with tab1:
                self._exibir_analise_composicao(df_display)

            with tab2:
                self._exibir_top_produtos(df_display)

            with tab3:
                self._exibir_breakdown_calculo(df_final, resultados)

    def _exibir_analise_composicao(self, df_display: pd.DataFrame):
        """Análise de composição dos resultados"""
        st.markdown("**📊 Composição dos Resultados**")

        # Análise de receita por produto
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Contribuição por Receita**")
            receita_sorted = df_display.nlargest(5, "Subtotal")[["Produto", "Subtotal", "Margem %"]]
            for idx, row in receita_sorted.iterrows():
                participacao = (row["Subtotal"] / df_display["Subtotal"].sum()) * 100
                st.write(f"• {row['Produto']}: {formatar_moeda_brasileira(row['Subtotal'])} ({formatar_percentual_brasileiro(participacao)}) - Margem: {formatar_percentual_brasileiro(row['Margem %'])}")

        with col2:
            st.markdown("**🎯 Contribuição por Lucro**")
            lucro_sorted = df_display.nlargest(5, "Lucro Líquido")[["Produto", "Lucro Líquido", "Margem %"]]
            for idx, row in lucro_sorted.iterrows():
                if df_display["Lucro Líquido"].sum() > 0:
                    participacao = (row["Lucro Líquido"] / df_display["Lucro Líquido"].sum()) * 100
                else:
                    participacao = 0
                st.write(f"• {row['Produto']}: {formatar_moeda_brasileira(row['Lucro Líquido'])} ({formatar_percentual_brasileiro(participacao)}) - Margem: {formatar_percentual_brasileiro(row['Margem %'])}")

    def _exibir_top_produtos(self, df_display: pd.DataFrame):
        """Análise dos top produtos"""
        st.markdown("**🏆 Rankings de Produtos**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🥇 Maiores Receitas**")
            top_receita = df_display.nlargest(3, "Subtotal")[["Produto", "Subtotal"]]
            for i, (idx, row) in enumerate(top_receita.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {formatar_moeda_brasileira(row['Subtotal'])}")

        with col2:
            st.markdown("**💰 Maiores Lucros**")
            top_lucro = df_display.nlargest(3, "Lucro Líquido")[["Produto", "Lucro Líquido"]]
            for i, (idx, row) in enumerate(top_lucro.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {formatar_moeda_brasileira(row['Lucro Líquido'])}")

        with col3:
            st.markdown("**📈 Maiores Margens**")
            top_margem = df_display.nlargest(3, "Margem %")[["Produto", "Margem %"]]
            for i, (idx, row) in enumerate(top_margem.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {formatar_percentual_brasileiro(row['Margem %'])}")

        # Produtos que precisam de atenção
        produtos_atencao = df_display[df_display["Margem %"] < 5]
        if not produtos_atencao.empty:
            st.markdown("**⚠️ Produtos que Precisam de Atenção (Margem < 5%)**")
            for idx, row in produtos_atencao.iterrows():
                st.write(f"🔴 {row['Produto']}: Margem {formatar_percentual_brasileiro(row['Margem %'])} - Lucro {formatar_moeda_brasileira(row['Lucro Líquido'])}")

    def _exibir_breakdown_calculo(self, df_final: pd.DataFrame, resultados: pd.DataFrame):
        """Breakdown detalhado do cálculo"""
        st.markdown("**🔍 Breakdown do Cálculo (Primeiro Produto)**")

        if len(resultados) > 0:
            primeiro = resultados.iloc[0]
            produto_nome = df_final.iloc[0]["Descrição"]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**📦 Base do Produto**")
                st.write(f"• Produto: {produto_nome}")
                st.write(f"• Preço Unitário: {formatar_moeda_brasileira(primeiro['Preço Venda'])}")
                st.write(f"• Quantidade: {primeiro['Qtd']:.0f}")
                st.write(f"• **Subtotal: {formatar_moeda_brasileira(primeiro['Subtotal'])}**")
                st.write(f"• IPI: {formatar_moeda_brasileira(primeiro['IPI'])}")

            with col2:
                st.markdown("**🏛️ Impostos e Contribuições**")
                st.write(f"• Base ICMS-ST: {formatar_moeda_brasileira(primeiro['Base ICMS-ST'])}")
                st.write(f"• ICMS Próprio: {formatar_moeda_brasileira(primeiro['ICMS Próprio'])}")
                st.write(f"• ICMS-ST: {formatar_moeda_brasileira(primeiro['ICMS-ST'])}")
                st.write(f"• FCP: {formatar_moeda_brasileira(primeiro['FCP'])}")
                st.write(f"• **Total NF: {formatar_moeda_brasileira(primeiro['Total NF'])}**")

            with col3:
                st.markdown("**💰 Resultado Financeiro**")
                st.write(f"• Custo Total: {formatar_moeda_brasileira(primeiro['Custo Total'])}")
                st.write(f"• Despesas: {formatar_moeda_brasileira(primeiro['Total Despesas'])}")
                st.write(f"• Frete: {formatar_moeda_brasileira(primeiro['Frete Total'])}")
                st.write(f"• Lucro Antes IR: {formatar_moeda_brasileira(primeiro['Lucro Antes IR'])}")
                st.write(f"• IRPJ + CSLL: {formatar_moeda_brasileira(primeiro['IRPJ'] + primeiro['CSLL'])}")
                st.write(f"• **Lucro Líquido: {formatar_moeda_brasileira(primeiro['Lucro Líquido'])}**")
                st.write(f"• **Margem: {formatar_percentual_brasileiro(primeiro['Margem Líquida %'])}**")

            # Fórmulas utilizadas
            st.markdown("**📐 Fórmulas Principais**")
            st.code("""
            Subtotal = Preço × Quantidade
            ICMS-ST = max(0, (Subtotal × (1 + MVA) × ICMS_Destino) - (Subtotal × ICMS_Origem))
            Lucro Antes IR = Subtotal - Custos - Despesas - Frete
            Lucro Líquido = Lucro Antes IR - IRPJ - CSLL
            Margem = (Lucro Líquido / Subtotal) × 100
            """)

    def _exibir_secao_exportacao_melhorada(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Seção de exportação melhorada"""
        st.markdown("#### 📄 Exportar e Compartilhar")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Excel Completo", use_container_width=True, type="primary"):
                excel_buffer = self._gerar_excel_completo(df_final, resultados, df_display)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"simulacao_sobel_SP_{self.uf_selecionado}_{timestamp}.xlsx"
                
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=excel_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with col2:
            if st.button("📋 Relatório PDF", use_container_width=True):
                st.info("🚧 Funcionalidade em desenvolvimento")

        with col3:
            if st.button("📱 Resumo para WhatsApp", use_container_width=True):
                resumo_whatsapp = self._gerar_resumo_whatsapp(df_display)
                st.text_area("📱 Copie e cole no WhatsApp:", resumo_whatsapp, height=200)

    def _gerar_excel_completo(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame) -> io.BytesIO:
        """Gera Excel completo com múltiplas abas"""
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            # Aba 1: Resultados principais
            df_display.to_excel(writer, index=False, sheet_name="Resultados")
            
            # Aba 2: Dados de entrada
            colunas_entrada = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                              "Custo Fixo", "MVA", "Comissão", "Bonificação"]
            df_entrada = df_final[colunas_entrada]
            df_entrada.to_excel(writer, index=False, sheet_name="Dados_Entrada")
            
            # Aba 3: Cálculos detalhados
            df_completo = pd.concat([df_final[colunas_entrada], resultados], axis=1)
            df_completo.to_excel(writer, index=False, sheet_name="Calculos_Completos")
            
            # Aba 4: Resumo executivo
            resumo_data = {
                "Métrica": [
                    "Receita Total", "Lucro Líquido Total", "Margem Ponderada", 
                    "Produtos com Prejuízo", "Total da Nota Fiscal", "Quantidade Total"
                ],
                "Valor": [
                    formatar_moeda_brasileira(df_display['Subtotal'].sum()),
                    formatar_moeda_brasileira(df_display['Lucro Líquido'].sum()),
                    formatar_percentual_brasileiro((df_display['Lucro Líquido'].sum()/df_display['Subtotal'].sum()*100)),
                    len(df_display[df_display["Lucro Líquido"] < 0]),
                    formatar_moeda_brasileira(df_display['Total NF'].sum()),
                    f"{df_display['Qtd'].sum():,.0f} caixas".replace(",", ".")
                ]
            }
            resumo_df = pd.DataFrame(resumo_data)
            resumo_df.to_excel(writer, index=False, sheet_name="Resumo_Executivo")
            
            # Aba 5: Parâmetros utilizados
            parametros_data = {
                "Parâmetro": [
                    "UF Origem", "UF Destino", "Tipo de Frete", "Frete por Caixa",
                    "% Contrato", "% Comissão Global", "% Bonificação Global"
                ],
                "Valor": [
                    "SP", self.uf_selecionado, self.tipo_frete, 
                    formatar_moeda_brasileira(self.frete_padrao),
                    formatar_percentual_brasileiro(self.contrato_percentual * 100),
                    formatar_percentual_brasileiro(self.comissao_padrao * 100) if self.comissao_padrao > 0 else "N/A",
                    formatar_percentual_brasileiro(self.bonificacao_global * 100) if self.bonificacao_global > 0 else "N/A"
                ]
            }
            parametros_df = pd.DataFrame(parametros_data)
            parametros_df.to_excel(writer, index=False, sheet_name="Parametros")

        return excel_buffer

    def _gerar_resumo_whatsapp(self, df_display: pd.DataFrame) -> str:
        """Gera resumo formatado para WhatsApp"""
        total_receita = df_display["Subtotal"].sum()
        total_lucro = df_display["Lucro Líquido"].sum()
        margem = (total_lucro / total_receita * 100) if total_receita > 0 else 0
        produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
        
        resumo = f"""
🏢 *SIMULAÇÃO SOBEL - RESUMO EXECUTIVO*
📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🗺️ *Rota:* SP → {self.uf_selecionado}
📦 *Produtos:* {len(df_display)} itens

💰 *RESULTADOS FINANCEIROS:*
• Receita Total: {formatar_moeda_brasileira(total_receita)}
• Lucro Líquido: {formatar_moeda_brasileira(total_lucro)}
• Margem Ponderada: {formatar_percentual_brasileiro(margem)}
• Produtos c/ Prejuízo: {produtos_prejuizo}

🏆 *TOP 3 PRODUTOS POR RECEITA:*
"""
        
        top3_receita = df_display.nlargest(3, "Subtotal")
        for i, (_, row) in enumerate(top3_receita.iterrows(), 1):
            resumo += f"{i}. {row['Produto']}: {formatar_moeda_brasileira(row['Subtotal'])} (Margem: {formatar_percentual_brasileiro(row['Margem %'])})\n"
        
        resumo += f"""
⚠️ *ALERTAS:*
"""
        if margem < 5:
            resumo += "🔴 Margem muito baixa - Revisar preços\n"
        elif margem < 10:
            resumo += "🟡 Margem baixa - Monitorar\n"
        else:
            resumo += "🟢 Margem adequada\n"
            
        if produtos_prejuizo > 0:
            resumo += f"🚨 {produtos_prejuizo} produtos com prejuízo\n"
        
        resumo += "\n🤖 _Gerado pelo Simulador Sobel v3.0_"
        
        return resumo

    def _exibir_relatorios(self):
        """Seção de relatórios e análises históricas"""
        st.markdown("### 📈 Relatórios e Análises")
        
        if not st.session_state.get("resultados_atualizados", False):
            st.info("ℹ️ Execute uma simulação primeiro para gerar relatórios.")
            return
        
        # Placeholder para funcionalidades futuras
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📊 Relatórios Disponíveis
            - 📈 Análise de margem por produto
            - 🎯 Comparativo de cenários
            - 📋 Histórico de simulações
            - 🏆 Ranking de produtos
            """)
            
        with col2:
            st.markdown("""
            #### 🚧 Em Desenvolvimento
            - 📅 Análise temporal
            - 🔄 Comparativo com concorrência
            - 📊 Dashboard executivo
            - 📱 Relatórios mobile
            """)
        
        st.info("💡 **Sugestão:** Use a funcionalidade de exportação para análises externas detalhadas.")

# Função principal melhorada
def main():
    """Função principal com melhor tratamento de erros"""
    try:
        # Verificações iniciais
        if 'inicializado' not in st.session_state:
            st.session_state.inicializado = True
            st.balloons()  # Feedback visual de carregamento
        
        # Executar simulador
        simulador = SimuladorSobel()
        simulador.executar()
        
        # Notas técnicas no final
        st.markdown("---")
        st.markdown("""
        ### 📚 Notas Técnicas - Simulador Sobel v3.0

        #### 🎯 **Estados com FCP (Fundo de Combate à Pobreza):**
        - **2,0%:** AC, AL, BA, MA, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, SC, SE
        - **2,5%:** CE
        - **0,0%:** AP, AM, DF, ES, GO, MT, RO, RR, SP, TO

        #### 🔧 **Funcionalidades Principais:**
        - ✅ Cálculo automático de ICMS-ST por UF
        - ✅ Otimização inteligente de frete por volume
        - ✅ Geolocalização e cálculo de rotas
        - ✅ Edição individual de comissões e bonificações
        - ✅ Exportação completa para Excel
        - ✅ Análises detalhadas e alertas inteligentes

        #### 📊 **Melhorias v3.0:**
        - Interface redesenhada com melhor UX/UI
        - Sistema de alertas inteligentes
        - Otimização automática de frete
        - Análises detalhadas por produto
        - Exportação aprimorada
        - Tratamento de erros melhorado

        ---
        *Desenvolvido para Sobel Suprema - Sistema integrado de simulação de preços*
        """)
        
    except Exception as e:
        st.error(f"""
        🚨 **Erro Crítico na Aplicação**
        
        **Detalhes do erro:** {str(e)}
        
        **Ações recomendadas:**
        1. 🔄 Recarregue a página (F5)
        2. 🧹 Limpe o cache do navegador
        3. 📞 Entre em contato com o suporte técnico
        
        **Informações técnicas:**
        - Versão: Simulador Sobel v3.0
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        # Log de erro para debug
        import traceback
        st.expander("🔧 Detalhes Técnicos (Para Suporte)", expanded=False).code(
            traceback.format_exc()
        )

# Executar aplicação
if __name__ == "__main__":
    main())
        except:
            # Formatação manual no padrão brasileiro
            if valor_float < 0:
                sinal = "-"
                valor_abs = abs(valor_float)
            else:
                sinal = ""
                valor_abs = valor_float
            
            # Separar parte inteira e decimal
            parte_inteira = int(valor_abs)
            parte_decimal = int((valor_abs - parte_inteira) * 100)
            
            # Formatação com pontos para milhares
            parte_inteira_str = f"{parte_inteira:,}".replace(",", ".")
            
            return f"{sinal}R$ {parte_inteira_str},{parte_decimal:02d}"
    except:
        return "R$ 0,00"

def formatar_percentual_brasileiro(valor: float) -> str:
    """Formata percentual no padrão brasileiro"""
    try:
        if pd.isna(valor) or valor is None:
            return "0,0%"
        
        valor_float = float(valor)
        return f"{valor_float:.1f}%".replace(".", ",")
    except:
        return "0,0%"

def obter_faixa_km_exata(distancia_km: float, faixas: list) -> str:
    """Dado a distância, retorna a faixa de KM correspondente (ex: '0-50')"""
    # Primeiro: busca exata
    for ini, fim, label in faixas:
        if ini <= distancia_km <= fim:
            return label

    # Segundo: busca pela faixa mais próxima (menor diferença)
    if faixas:
        melhor_faixa = None
        menor_diferenca = float('inf')

        for ini, fim, label in faixas:
            # Calcular distância até o centro da faixa
            centro_faixa = (ini + fim) / 2 if fim != float('inf') else ini + 50
            diferenca = abs(distancia_km - centro_faixa)

            if diferenca < menor_diferenca:
                menor_diferenca = diferenca
                melhor_faixa = label

        # Se a diferença for razoável (menos de 100km), usar a faixa mais próxima
        if menor_diferenca <= 100:
            return melhor_faixa

    return 'Indefinida'

def buscar_frete_inteligente(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str) -> dict:
    """
    Busca valores de frete de forma inteligente para otimização de veículo
    """
    resultado = {
        'truck': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'carreta': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'capacidades': {'truck': 870, 'carreta': 1740}
    }

    # Buscar ambos os tipos
    for tipo_veiculo in ['truck', 'carreta']:
        valor, faixa_usada, metodo = buscar_frete_por_faixa(df_clientes, cidade_ibge, faixa_km, tipo_veiculo)
        resultado[tipo_veiculo] = {
            'valor': valor,
            'faixa_usada': faixa_usada,
            'metodo': metodo
        }

    return resultado

def calcular_frete_otimizado(resultado_frete: dict, quantidade_total: int) -> dict:
    """
    Calcula o frete otimizado baseado no volume total
    """
    truck_info = resultado_frete['truck']
    carreta_info = resultado_frete['carreta']
    capacidades = resultado_frete['capacidades']

    # Se não encontrou nenhum valor, retornar erro
    if truck_info['valor'] == 0 and carreta_info['valor'] == 0:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhum valor de frete encontrado',
            'detalhes': {}
        }

    # Calcular cenários
    cenarios = {}

    # Cenário Truck (se couber)
    if quantidade_total <= capacidades['truck'] and truck_info['valor'] > 0:
        cenarios['truck'] = {
            'frete_total': truck_info['valor'],
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': 1,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'],
            'ocupacao': (quantidade_total / capacidades['truck']) * 100
        }

    # Cenário Carreta
    if carreta_info['valor'] > 0:
        viagens_carreta = max(1, math.ceil(quantidade_total / capacidades['carreta']))
        cenarios['carreta'] = {
            'frete_total': carreta_info['valor'] * viagens_carreta,
            'frete_por_caixa': carreta_info['valor'] / capacidades['carreta'],
            'viagens': viagens_carreta,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['carreta'] * viagens_carreta,
            'ocupacao': (quantidade_total / (capacidades['carreta'] * viagens_carreta)) * 100
        }

    # Cenário Truck múltiplo (se necessário)
    if quantidade_total > capacidades['truck'] and truck_info['valor'] > 0:
        viagens_truck = math.ceil(quantidade_total / capacidades['truck'])
        cenarios['truck_multiplo'] = {
            'frete_total': truck_info['valor'] * viagens_truck,
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': viagens_truck,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'] * viagens_truck,
            'ocupacao': (quantidade_total / (capacidades['truck'] * viagens_truck)) * 100
        }

    # Encontrar melhor opção (menor custo total)
    if not cenarios:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhuma opção de frete viável',
            'detalhes': {}
        }

    melhor_opcao = min(cenarios.keys(), key=lambda k: cenarios[k]['frete_total'])
    melhor_cenario = cenarios[melhor_opcao]

    # Calcular economia
    economia = 0.0
    if 'carreta' in cenarios and melhor_opcao != 'carreta':
        economia = cenarios['carreta']['frete_total'] - melhor_cenario['frete_total']

    # Gerar alerta
    alerta = ""
    if melhor_opcao == 'truck':
        alerta = f"✅ OTIMIZAÇÃO: Volume de {quantidade_total} caixas cabe em TRUCK! Economia de R$ {economia:.2f}"
    elif melhor_opcao == 'truck_multiplo':
        viagens = melhor_cenario['viagens']
        alerta = f"📦 MÚLTIPLOS TRUCKS: {viagens} viagens necessárias. " + (f"Economia de R$ {economia:.2f}" if economia > 0 else "")
    else:
        alerta = f"🚛 CARRETA RECOMENDADA: Volume de {quantidade_total} caixas otimizado para carreta"

    return {
        'veiculo_otimo': melhor_opcao,
        'frete_total': melhor_cenario['frete_total'],
        'frete_por_caixa': melhor_cenario['frete_por_caixa'],
        'economia': economia,
        'alerta': alerta,
        'detalhes': {
            'cenarios': cenarios,
            'melhor_cenario': melhor_cenario,
            'truck_info': truck_info,
            'carreta_info': carreta_info
        }
    }

def buscar_frete_por_faixa(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str, tipo_veiculo='truck') -> tuple:
    """
    Busca o valor do frete de forma inteligente
    """
    # Primeira tentativa: busca exata por cidade_ibge e faixa
    linha_exata = df_clientes[
        (df_clientes['cidade_ibge'] == cidade_ibge) &
        (df_clientes['FAIXA_KM'] == faixa_km)
    ]

    if not linha_exata.empty:
        if tipo_veiculo == 'truck':
            valor = linha_exata.iloc[0]['TBL_TRCK'] if not pd.isna(linha_exata.iloc[0]['TBL_TRCK']) else 0.0
        elif tipo_veiculo == 'carreta':
            valor = linha_exata.iloc[0]['TBL_CRRT'] if 'TBL_CRRT' in linha_exata.columns and not pd.isna(linha_exata.iloc[0]['TBL_CRRT']) else 0.0
        else:
            valor = 0.0

        if valor > 0:
            return float(valor), faixa_km, "exata"

    # Segunda tentativa: buscar por IBGE e calcular pela faixa mais próxima
    linhas_ibge = df_clientes[df_clientes['cidade_ibge'] == cidade_ibge]

    if not linhas_ibge.empty:
        distancia_solicitada = extrair_distancia_da_faixa(faixa_km)

        if distancia_solicitada is not None:
            melhor_faixa = None
            menor_diferenca = float('inf')
            melhor_linha = None

            for _, linha in linhas_ibge.iterrows():
                faixa_disponivel = linha['FAIXA_KM']
                distancia_disponivel = extrair_distancia_da_faixa(faixa_disponivel)

                if distancia_disponivel is not None:
                    diferenca = abs(distancia_solicitada - distancia_disponivel)
                    if diferenca < menor_diferenca:
                        menor_diferenca = diferenca
                        melhor_faixa = faixa_disponivel
                        melhor_linha = linha

            if melhor_linha is not None:
                if tipo_veiculo == 'truck':
                    valor = melhor_linha['TBL_TRCK'] if not pd.isna(melhor_linha['TBL_TRCK']) else 0.0
                elif tipo_veiculo == 'carreta':
                    valor = melhor_linha['TBL_CRRT'] if 'TBL_CRRT' in melhor_linha and not pd.isna(melhor_linha['TBL_CRRT']) else 0.0
                else:
                    valor = 0.0

                if valor > 0:
                    return float(valor), melhor_faixa, f"aproximada (IBGE {cidade_ibge})"

    return 0.0, "não encontrada", "não encontrado"

def extrair_distancia_da_faixa(faixa: str) -> float:
    """Extrai a distância média de uma faixa"""
    try:
        faixa_str = str(faixa).strip()

        if '+' in faixa_str:
            valor = int(faixa_str.replace('+', '').strip())
            return float(valor + 50)
        elif '-' in faixa_str:
            partes = faixa_str.split('-')
            if len(partes) == 2:
                ini, fim = int(partes[0].strip()), int(partes[1].strip())
                return float((ini + fim) / 2)
        else:
            return float(faixa_str)
    except (ValueError, IndexError):
        return None

# ==================== CLASSES PRINCIPAIS ====================

class ConfiguracaoTributaria:
    """Classe para gerenciar configurações tributárias por UF"""

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
        'RJ': {'interna': 0.22, 'interestadual': 0.12, 'fcp': 0.02}, 
        'RN': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RS': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RO': {'interna': 0.175, 'interestadual': 0.12, 'fcp': 0.0},
        'RR': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
        'SC': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
        'SP': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
        'SE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'TO': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0}
    }

    @classmethod
    def obter_aliquotas(cls, uf: str) -> Dict[str, float]:
        """Retorna as alíquotas para uma UF específica"""
        return cls.ICMS_ALIQUOTAS.get(uf.upper(), {
            'interna': 0.18, 
            'interestadual': 0.12, 
            'fcp': 0.0
        })

class GerenciadorGeolocalizacao:
    """Classe para gerenciar operações de geolocalização"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço ou CEP em coordenadas (lat, lng)"""
        try:
            with st.spinner("🔍 Geocodificando endereço..."):
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return location["lat"], location["lng"]
                return None, None
        except Exception as e:
            st.error(f"❌ Erro na geocodificação: {str(e)}")
            return None, None

    def calcular_distancia(self, origem_coords: Tuple[float, float], 
                          destino_coords: Tuple[float, float]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Consulta a Distance Matrix API e retorna distância e tempo"""
        try:
            with st.spinner("📏 Calculando distância e tempo..."):
                lat_o, lng_o = origem_coords
                lat_d, lng_d = destino_coords

                url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat_o},{lng_o}&destinations={lat_d},{lng_d}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                elemento = data['rows'][0]['elements'][0]
                status = elemento.get("status", "ERRO")

                if status != "OK":
                    return None, None, f"⚠️ API não conseguiu calcular: `{status}`"

                distancia = elemento['distance']['text']
                duracao = elemento['duration']['text']
                return distancia, duracao, None

        except Exception as e:
            return None, None, f"❌ Erro ao processar resposta: {str(e)}"

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas usando a fórmula de Haversine"""
        R = 6371  # Raio da Terra em km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

class GerenciadorBancoDados:
    """Classe para gerenciar conexões e consultas ao banco de dados"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @st.cache_data(ttl=600)
    def carregar_clientes_ou_rede(_self) -> pd.DataFrame:
        """Carrega dados dos clientes do banco de dados"""
        try:
            with st.spinner("🔄 Carregando dados dos clientes..."):
                with pyodbc.connect(_self.connection_string, timeout=30) as conexao:
                    query = """
                        SELECT 
                            SA1.A1_COD, 
                            SA1.A1_LOJA,
                            SA1.A1_ZZLOJA,
                            SA1.A1_NOME,
                            IIF(SA1.A1_ZZREDE = '', LEFT(SA1.A1_NOME, 20), SA1.A1_ZZREDE) AS REDE,
                            SA1.A1_CEP, 
                            SA1.A1_RISCO,
                            SA1.A1_ZZCONTR,
                            SA1.A1_LC,
                            SA1.A1_END,                         
                            SA1.A1_MCOMPRA,
                            SA1.A1_ULTCOM,
                            SA1.A1_EST,
                            SA1.A1_MUN,
                            SA1.A1_BAIRRO,
                            SA1.A1_END,
                            SA1.A1_CGC,
                            cep.longitude,
                            cep.latitude,
                            cep.nome_logradouro_sem_acento,
                            ibge.cidade_ibge,
                            T.CIDADE,
                            T.FAIXA_KM,
                            T.TBL_TRCK,
                            T.TBL_CRRT
                        FROM SA1010 SA1
                        INNER JOIN cep.dbo.tbl_cep_202504_n_logradouro AS cep 
                            ON cep.cep COLLATE Latin1_General_CI_AS = SA1.A1_CEP COLLATE Latin1_General_CI_AS
                        INNER JOIN cep.dbo.tbl_cep_202504_n_cidade_ibge AS ibge 
                            ON ibge.id_cidade = cep.cidade_id
                        INNER JOIN BISOBEL.dbo.TRANSP_TARGET T ON T.COD_IBGE COLLATE Latin1_General_CI_AS = ibge.cidade_ibge 
                        WHERE SA1.A1_MSBLQL = '2'
                          AND SA1.D_E_L_E_T_ = ''
                    """
                    return pd.read_sql(query, conexao)
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados dos clientes: {e}")
            return pd.DataFrame()

class CalculadoraTributaria:
    """Classe para realizar cálculos tributários"""

    @staticmethod
    def arredondar_valor(valor: Any, decimais: int = 2) -> float:
        """Arredonda valores para evitar problemas de precisão"""
        try:
            return round(float(valor), decimais)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def calcular_icms_st_completo(valor_produto: float, ipi_valor: float, mva: float,
                                 icms_interestadual: float, icms_interno_destino: float,
                                 fcp_aliquota: float, frete: float = 0.0,
                                 seguro: float = 0.0, despesas: float = 0.0,
                                 descontos: float = 0.0) -> Tuple[float, float, float, float, float]:
        """
        Cálculo preciso do ICMS-ST conforme a legislação
        """
        # Se MVA for 0, não há ICMS-ST
        if mva <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        # Base sem MVA: inclui valor do produto + IPI
        base_sem_mva = CalculadoraTributaria.arredondar_valor(valor_produto + ipi_valor)

        # Aplica MVA
        base_com_mva = CalculadoraTributaria.arredondar_valor(base_sem_mva * (1 + mva))

        # ICMS origem (interestadual) sobre base sem MVA
        icms_origem = CalculadoraTributaria.arredondar_valor(base_sem_mva * icms_interestadual)

        # ICMS destino (interno) sobre base com MVA
        icms_destino = CalculadoraTributaria.arredondar_valor(base_com_mva * icms_interno_destino)

        # ICMS-ST: diferença entre ICMS destino e ICMS origem
        icms_st = CalculadoraTributaria.arredondar_valor(max(icms_destino - icms_origem, 0.0))

        # FCP somente se a alíquota for maior que zero
        fcp = CalculadoraTributaria.arredondar_valor(base_sem_mva * fcp_aliquota) if fcp_aliquota > 0 else 0.0

        return icms_st, base_com_mva, icms_origem, icms_destino, fcp

class CalculadoraResultados:
    """Classe para calcular resultados financeiros"""

    def __init__(self, tipo_frete: str = "CIF"):
        self.tipo_frete = tipo_frete

    def calcular_resultados_completos(self, row: pd.Series) -> pd.Series:
        """Calcula todos os resultados financeiros para uma linha de produto"""
        try:
            # Valores base
            preco_venda = CalculadoraTributaria.arredondar_valor(row["Preço de Venda"])
            qtd = CalculadoraTributaria.arredondar_valor(row["Quantidade"], 0)
            subtotal = CalculadoraTributaria.arredondar_valor(preco_venda * qtd)

            # Custos
            custo_net = CalculadoraTributaria.arredondar_valor(row.get("Custo NET", 0))
            custo_fixo = CalculadoraTributaria.arredondar_valor(row.get("Custo Fixo", 0))
            custo_total_unit = CalculadoraTributaria.arredondar_valor(custo_net + custo_fixo)
            custo_total = CalculadoraTributaria.arredondar_valor(custo_total_unit * qtd)

            # Frete
            frete_total = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0)) * qtd
            ) if self.tipo_frete == "CIF" else 0.0

            frete_unit = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0))
            ) if self.tipo_frete == "CIF" else 0.0

            # IPI
            ipi_percent = float(row.get("IPI", 0))
            ipi_total = CalculadoraTributaria.arredondar_valor(subtotal * ipi_percent)

            # Parâmetros ICMS-ST
            mva = float(row.get("MVA", 0))
            icms_interestadual = float(row.get("ICMS Interestadual", 0))
            icms_interno_destino = float(row.get("ICMS Interno Destino", 0))
            fcp_aliquota = float(row.get("FCP", 0))

            # Calcular ICMS-ST
            icms_st, base_icms_st, icms_proprio, icms_total_interno, fcp_valor = \
                CalculadoraTributaria.calcular_icms_st_completo(
                    valor_produto=subtotal,
                    ipi_valor=ipi_total,
                    mva=mva,
                    icms_interestadual=icms_interestadual,
                    icms_interno_destino=icms_interno_destino,
                    fcp_aliquota=fcp_aliquota
                )

            # Despesas operacionais
            despesas_operacionais = self._calcular_despesas_operacionais(row, subtotal)
            total_despesas_operacionais = despesas_operacionais

            # Lucro antes dos impostos sobre lucro
            lucro_antes_ir = CalculadoraTributaria.arredondar_valor(
                subtotal - custo_total - total_despesas_operacionais - frete_total
            )

            # Calcular IR e CSLL
            irpj, csll = self._calcular_ir_csll(lucro_antes_ir)

            # Lucro líquido
            lucro_liquido = CalculadoraTributaria.arredondar_valor(lucro_antes_ir - irpj - csll)

            # Margem calculada corretamente
            margem_antes_ir = CalculadoraTributaria.arredondar_valor(
                (lucro_antes_ir / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            margem_liquida = CalculadoraTributaria.arredondar_valor(
                (lucro_liquido / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            # Total NF
            total_nf = CalculadoraTributaria.arredondar_valor(subtotal + ipi_total + icms_st + fcp_valor)

            # Ponto de equilíbrio
            ponto_equilibrio = self._calcular_ponto_equilibrio(row, custo_total_unit, frete_unit)

            return pd.Series({
                "Preço Venda": preco_venda,
                "Qtd": qtd,
                "Custo NET": custo_net,
                "Custo Fixo": custo_fixo,
                "MVA": mva,
                "Comissão": float(row.get("Comissão", 0)),
                "Bonificação": float(row.get("Bonificação", 0)),
                "Subtotal": subtotal,
                "IPI": ipi_total,
                "Base ICMS-ST": base_icms_st,
                "ICMS Próprio": icms_proprio,
                "ICMS-ST": icms_st,
                "FCP": fcp_valor,
                "Total NF": total_nf,
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
            st.error(f"❌ Erro no cálculo do produto {row.get('Descrição', 'N/A')}: {str(e)}")
            return self._retornar_serie_vazia()

    def _calcular_despesas_operacionais(self, row: pd.Series, subtotal: float) -> float:
        """Calcula o total das despesas operacionais"""
        despesas = [
            "ICMS Interestadual", "COFINS", "PIS", "Comissão",
            "Bonificação", "Contigência", "Contrato", "%Estrategico"
        ]

        total = 0.0
        for despesa in despesas:
            percentual = float(row.get(despesa, 0))
            total += CalculadoraTributaria.arredondar_valor(subtotal * percentual)

        return total

    def _calcular_ir_csll(self, lucro_antes_ir: float) -> Tuple[float, float]:
        """Calcula IRPJ e CSLL"""
        if lucro_antes_ir <= 0:
            return 0.0, 0.0

        # IRPJ: 15% + 10% sobre o que exceder R$ 20.000/mês
        irpj = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.15)
        if lucro_antes_ir > 20000:
            adicional_irpj = CalculadoraTributaria.arredondar_valor((lucro_antes_ir - 20000) * 0.10)
            irpj += adicional_irpj

        # CSLL: 9%
        csll = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.09)

        return irpj, csll

    def _calcular_ponto_equilibrio(self, row: pd.Series, custo_total_unit: float, frete_unit: float) -> float:
        """Calcula o ponto de equilíbrio"""
        try:
            # Despesas diretas percentuais
            despesas_diretas = (
                float(row.get("ICMS Interestadual", 0)) +
                float(row.get("COFINS", 0)) +
                float(row.get("PIS", 0)) +
                float(row.get("Comissão", 0)) +
                float(row.get("Bonificação", 0)) +
                float(row.get("Contigência", 0)) +
                float(row.get("Contrato", 0)) +
                float(row.get("%Estrategico", 0))
            )

            if despesas_diretas >= 1.0:
                return 0.0

            # Cálculo básico
            ponto_equilibrio = (custo_total_unit + frete_unit) / (1 - despesas_diretas)
            return CalculadoraTributaria.arredondar_valor(ponto_equilibrio)

        except Exception:
            return 0.0

    def _retornar_serie_vazia(self) -> pd.Series:
        """Retorna uma série com valores zerados em caso de erro"""
        return pd.Series({
            "Preço Venda": 0, "Qtd": 0, "Custo NET": 0, "Custo Fixo": 0, "MVA": 0,
            "Comissão": 0, "Bonificação": 0, "Subtotal": 0, "IPI": 0, "Base ICMS-ST": 0,
            "ICMS Próprio": 0, "ICMS-ST": 0, "FCP": 0, "Total NF": 0, "Custo Total": 0,
            "Frete Total": 0, "Total Despesas": 0, "Lucro Antes IR": 0, "IRPJ": 0,
            "CSLL": 0, "Lucro Líquido": 0, "Margem Antes IR %": 0, "Margem Líquida %": 0,
            "Ponto Equilíbrio": 0
        })

class GerenciadorEstado:
    """Classe para gerenciar o estado da aplicação"""

    def __init__(self):
        self.inicializar_estado()

    def inicializar_estado(self):
        """Inicializa as variáveis de estado"""
        estados_default = {
            'df_atual': None,
            'modo_equilibrio': False,
            'comissao_global_aplicada': False,
            'comissoes_editadas': {},
            'bonificacoes_editadas': {},
            'valores_originais': {},
            'df_edicao_temp': None,
            'resultados_atualizados': False,
            'frete_calculado_automatico': 0.0,
            'distancia_calculada': None,
            'tempo_calculado': None,
            'usar_frete_auto': False,
            'coordenadas_origem': None,
            'coordenadas_destino': None,
            'resultado_frete_completo': None,
            'otimizacao_frete': None,
            'dados_carregados': False
        }

        for key, value in estados_default.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def resetar_estado(self):
        """Reseta o estado da aplicação"""
        for key in ['df_atual', 'modo_equilibrio', 'comissao_global_aplicada', 
                   'comissoes_editadas', 'bonificacoes_editadas', 'valores_originais',
                   'df_edicao_temp', 'resultados_atualizados']:
            if key in st.session_state:
                if key in ['comissoes_editadas', 'bonificacoes_editadas', 'valores_originais']:
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None if key == 'df_atual' or key == 'df_edicao_temp' else False

class SimuladorSobel:
    """Classe principal do simulador"""

    def __init__(self):
        self.config_tributaria = ConfiguracaoTributaria()
        self.gerenciador_estado = GerenciadorEstado()
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if self.api_key:
            self.geolocalizacao = GerenciadorGeolocalizacao(self.api_key)
        else:
            self.geolocalizacao = None
            st.warning("⚠️ Google Maps API não configurada. Funcionalidades de geolocalização desabilitadas.")

        # Configuração do banco de dados
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.0.16;"
            "DATABASE=Protheus_Producao;"
            "UID=sa;"
            "PWD=Totvs@452525!"
        )
        self.db_manager = GerenciadorBancoDados(connection_string)

        # Produtos esperados
        self.produtos_esperados = [
            "ÁGUA SANITÁRIA 5L", "ÁGUA SANITÁRIA 2L", "ÁGUA SANITÁRIA 1L",
            "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
            "AMACIANTE 5L", "AMACIANTE 2L",
            "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
            "LAVA LOUÇAS 500ML", "LAVA LOUÇAS 5L",
            "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
            "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
            "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
        ]

        # Inicializar variáveis
        self.dados_cliente_selecionado = None
        self.frete_padrao_cliente = None
        self.faixas_km_ordenadas = []
        self.df_padrao = pd.DataFrame()
        self.contrato_real = None

    def executar(self):
        """Método principal para executar o simulador"""
        self._configurar_interface()
        
        # Verificar conexão com banco
        if not self._verificar_conexao_banco():
            return
            
        self._carregar_dados_iniciais()
        self._exibir_interface()

    def _configurar_interface(self):
        """Configura a interface do usuário"""
        # CSS customizado para melhorar a aparência
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e7cb8 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2e7cb8;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .success-card {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .warning-card {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-card {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header principal
        st.markdown("""
        <div class="main-header">
            <h1>📊 Simulador de Formação de Preço de Venda - Sobel v3.0</h1>
            <p>Sistema integrado de simulação com otimização de frete e geolocalização</p>
        </div>
        """, unsafe_allow_html=True)

        # Verificar se a imagem existe
        if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
            col_logo, col_space = st.columns([1, 3])
            with col_logo:
                st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=250)

    def _verificar_conexao_banco(self) -> bool:
        """Verifica se a conexão com o banco está funcionando"""
        try:
            with st.spinner("🔄 Verificando conexão com banco de dados..."):
                df_test = self.db_manager.carregar_clientes_ou_rede()
                if df_test.empty:
                    st.error("❌ Nenhum dado encontrado no banco. Verifique a conexão.")
                    return False
                st.success(f"✅ Banco conectado com sucesso! {len(df_test)} registros encontrados.")
                return True
        except Exception as e:
            st.error(f"❌ Erro de conexão com banco: {str(e)}")
            return False

    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais necessários"""
        # Carregar planilha padrão
        arquivo_padrao = "Custo de reposição.xlsx"
        if os.path.exists(arquivo_padrao):
            try:
                with st.spinner("📂 Carregando planilha de custos..."):
                    self.df_padrao = pd.read_excel(arquivo_padrao)
                    self.df_padrao.columns = self.df_padrao.columns.str.strip()
                    st.success(f"✅ Planilha carregada: {len(self.df_padrao)} produtos disponíveis")
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo padrão: {str(e)}")
                self.df_padrao = pd.DataFrame()
        else:
            st.warning("⚠️ Arquivo padrão 'Custo de reposição.xlsx' não encontrado.")
            self.df_padrao = pd.DataFrame()

        # Carregar faixas de KM
        self.faixas_km_ordenadas = self._extrair_faixas_ordenadas()

    def _extrair_faixas_ordenadas(self) -> list:
        """Extrai e ordena as faixas de KM disponíveis da base de clientes"""
        try:
            df_clientes = self.db_manager.carregar_clientes_ou_rede()
            if df_clientes.empty:
                return []
                
            faixas = []
            faixas_unicas = df_clientes['FAIXA_KM'].dropna().unique()

            for faixa in faixas_unicas:
                try:
                    faixa_str = str(faixa).strip()
                    if '+' in faixa_str:
                        ini = int(faixa_str.replace('+', '').strip())
                        faixas.append((ini, float('inf'), faixa_str))
                    elif '-' in faixa_str:
                        partes = faixa_str.split('-')
                        if len(partes) == 2:
                            ini, fim = int(partes[0].strip()), int(partes[1].strip())
                            faixas.append((ini, fim, faixa_str))
                    else:
                        valor = int(faixa_str)
                        faixas.append((valor, valor, faixa_str))
                except (ValueError, IndexError):
                    continue

            faixas.sort(key=lambda x: x[0])

            if faixas:
                st.info(f"🎯 Faixas de KM carregadas: {[f[2] for f in faixas[:5]]}{'...' if len(faixas) > 5 else ''}")

            return faixas
        except Exception as e:
            st.error(f"❌ Erro ao extrair faixas de frete: {e}")
            return []

    def _exibir_interface(self):
        """Exibe a interface principal"""
        # Verificar se há dados para continuar
        if self.df_padrao.empty:
            st.error("❌ Não é possível continuar sem dados. Carregue uma planilha de custos.")
            return

        # Usar tabs para melhor organização
        tab1, tab2, tab3 = st.tabs(["👤 Cliente & Parâmetros", "📊 Simulação", "📄 Relatórios"])

        with tab1:
            self._exibir_secao_cliente()
            st.markdown("---")
            self._exibir_secao_parametros()
            st.markdown("---")
            self._exibir_upload_arquivo()

        with tab2:
            if self._validar_dados():
                self._processar_simulacao()

        with tab3:
            self._exibir_relatorios()

    def _exibir_secao_cliente(self):
        """Exibe a seção de seleção de cliente melhorada"""
        st.markdown("### 👤 Seleção de Cliente")

        # Opção de cliente
        opcao_cliente = st.radio(
            "Como deseja proceder?", 
            ["🔍 Selecionar cliente existente", "➕ Cliente novo (sem histórico)"], 
            horizontal=True
        )

        self.contrato_real = None
        self.dados_cliente_selecionado = None

        if opcao_cliente == "🔍 Selecionar cliente existente":
            clientes_df = self.db_manager.carregar_clientes_ou_rede()
            
            if not clientes_df.empty:
                # Melhor interface de seleção
                col_search, col_filter = st.columns([3, 1])
                
                with col_search:
                    # Busca por nome
                    busca_nome = st.text_input("🔍 Buscar por nome do cliente", placeholder="Digite parte do nome...")
                
                with col_filter:
                    # Filtro por UF
                    ufs_disponiveis = ['Todos'] + sorted(clientes_df['A1_EST'].unique().tolist())
                    uf_filtro = st.selectbox("📍 Filtrar por UF", ufs_disponiveis)

                # Aplicar filtros
                df_filtrado = clientes_df.copy()
                
                if busca_nome:
                    df_filtrado = df_filtrado[
                        df_filtrado['A1_NOME'].str.contains(busca_nome, case=False, na=False)
                    ]
                
                if uf_filtro != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['A1_EST'] == uf_filtro]

                if not df_filtrado.empty:
                    # Criar opções mais informativas
                    opcoes_clientes = []
                    for idx, row in df_filtrado.iterrows():
                        opcao = f"{row['A1_NOME'][:50]} | {row['A1_MUN']}/{row['A1_EST']} | {row['A1_COD']}/{row['A1_LOJA']}"
                        if row['REDE'] and str(row['REDE']) != str(row['A1_NOME'])[:20]:
                            opcao += f" | [{row['REDE']}]"
                        opcoes_clientes.append(opcao)

                    cliente_escolhido_display = st.selectbox(
                        f"📋 Clientes encontrados ({len(df_filtrado)} registros):", 
                        opcoes_clientes,
                        help="Formato: Nome | Cidade/UF | Código/Loja | [Rede]"
                    )

                    # Encontrar o cliente selecionado
                    indice_selecionado = opcoes_clientes.index(cliente_escolhido_display)
                    self.dados_cliente_selecionado = df_filtrado.iloc[indice_selecionado]

                    # Exibir dados do cliente
                    self._exibir_dados_completos_cliente()

                    # Seção de cálculo de frete (se disponível)
                    if self.geolocalizacao:
                        self._exibir_secao_rota_integrada()
                else:
                    st.info("ℹ️ Nenhum cliente encontrado com os filtros aplicados.")
            else:
                st.warning("⚠️ Nenhum cliente encontrado na base de dados.")

    def _exibir_dados_completos_cliente(self):
        """Exibe dados completos do cliente de forma mais organizada"""
        st.markdown("#### 📋 Informações do Cliente Selecionado")

        cliente_dict = self.dados_cliente_selecionado.to_dict()

        # Card principal com informações básicas
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🏢 Razão Social", 
                    value=cliente_dict.get('A1_NOME', 'N/A')[:30] + ('...' if len(str(cliente_dict.get('A1_NOME', ''))) > 30 else ''),
                    help=cliente_dict.get('A1_NOME', 'N/A')
                )
                
            with col2:
                codigo = cliente_dict.get('A1_COD', '')
                loja = cliente_dict.get('A1_LOJA', '')
                st.metric("🏷️ Código/Loja", f"{codigo}/{loja}")
                
            with col3:
                uf = cliente_dict.get('A1_EST', 'N/A')
                cidade = cliente_dict.get('A1_MUN', 'N/A')
                st.metric("📍 Localização", f"{cidade}/{uf}")
                
            with col4:
                try:
                    contrato_valor = float(cliente_dict.get("A1_ZZCONTR", 0) or 0)
                    self.contrato_real = contrato_valor
                except:
                    self.contrato_real = 0.0
                    contrato_valor = 0.0
                st.metric("📄 Contrato", f"{contrato_valor:.2f}%")

        # Informações detalhadas em expander
        with st.expander("📄 Detalhes Completos", expanded=False):
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                # Endereço
                endereco_parts = []
                if cliente_dict.get('A1_END'):
                    endereco_parts.append(cliente_dict['A1_END'])
                if cliente_dict.get('A1_BAIRRO'):
                    endereco_parts.append(cliente_dict['A1_BAIRRO'])
                if cliente_dict.get('A1_MUN') and cliente_dict.get('A1_EST'):
                    endereco_parts.append(f"{cliente_dict['A1_MUN']}/{cliente_dict['A1_EST']}")
                
                cep = cliente_dict.get('A1_CEP', '')
                if cep and len(cep) == 8:
                    cep_formatado = f"{cep[:5]}-{cep[5:]}"
                    endereco_parts.append(f"CEP: {cep_formatado}")
                
                endereco_completo = '\n'.join(endereco_parts) if endereco_parts else "Não informado"
                st.text_area("📍 Endereço Completo", endereco_completo, height=100, disabled=True)
                
            with col_det2:
                # Informações financeiras
                try:
                    lc_value = float(cliente_dict.get('A1_LC', 0) or 0)
                    lc_text = f"R$ {lc_value:,.2f}" if lc_value > 0 else "Não definido"
                except:
                    lc_text = "Não definido"
                
                st.text_input("💳 Limite de Crédito", lc_text, disabled=True)
                st.text_input("⚠️ Classificação de Risco", cliente_dict.get('A1_RISCO', 'N/A'), disabled=True)
                
                # Rede se houver
                rede = cliente_dict.get('REDE', '')
                nome_resumo = str(cliente_dict.get('A1_NOME', ''))[:20]
                if rede and rede != nome_resumo:
                    st.text_input("🏪 Rede", rede, disabled=True)

    def _exibir_secao_rota_integrada(self):
        """Exibe seção de cálculo de rota melhorada"""
        with st.expander("🗺️ Cálculo de Frete e Rota", expanded=False):
            st.markdown("#### 🧭 Configuração de Rota")

            # Origens disponíveis
            origens = {
                "📍 Matriz (São Paulo - SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "📍 Filial (Atibaia - SP)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }

            col_origem, col_destino = st.columns(2)

            with col_origem:
                origem_opcao = st.selectbox("🚚 Unidade de Origem", list(origens.keys()))
                origem = origens[origem_opcao]
                st.text_area("📍 Endereço de Origem", origem, height=60, disabled=True)

            with col_destino:
                # Informações do cliente
                cliente_info = f"{self.dados_cliente_selecionado['A1_NOME'][:30]}..."
                st.text_input("🎯 Cliente Selecionado", cliente_info, disabled=True)
                
                # Endereço para geocodificação
                endereco_destino = self._montar_endereco_completo_para_geocode(
                    self.dados_cliente_selecionado.to_dict()
                )
                st.text_area("🎯 Endereço de Destino", endereco_destino, height=60, disabled=True)

            # Configurações de frete
            st.markdown("#### 🚛 Configuração de Frete")
            
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "🚚 Truck (870 caixas)" if x == "truck" else "🚛 Carreta (1.740 caixas)"
                )
                
                if st.button("🗺️ Calcular Rota e Frete", type="primary", use_container_width=True):
                    self._calcular_frete_automatico(origem, tipo_veiculo)

            with col_frete2:
                # Resultados da rota
                if st.session_state.get('distancia_calculada') and st.session_state.get('tempo_calculado'):
                    st.success("✅ Rota Calculada")
                    st.metric("📏 Distância", st.session_state.get('distancia_calculada'))
                    st.metric("⏱️ Tempo", st.session_state.get('tempo_calculado'))
                else:
                    st.info("ℹ️ Clique em 'Calcular' para obter a rota")

            with col_frete3:
                # Frete calculado ou manual
                frete_calculado = st.session_state.get('frete_calculado_automatico', 0.0)
                if frete_calculado > 0:
                    usar_frete_auto = st.checkbox("🤖 Usar frete calculado", value=True)
                    if usar_frete_auto:
                        self.frete_padrao_cliente = frete_calculado
                        st.success(f"💰 R$ {frete_calculado:.2f}/caixa")
                    else:
                        self.frete_padrao_cliente = st.number_input(
                            "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                        )
                else:
                    self.frete_padrao_cliente = st.number_input(
                        "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                    )

            # Mostrar mapas se disponível
            if (st.session_state.get('coordenadas_origem') and 
                st.session_state.get('coordenadas_destino')):
                self._exibir_mapas_cliente(origem)

    def _montar_endereco_completo_para_geocode(self, cliente_dict: dict) -> str:
        """Monta endereço otimizado para geocodificação"""
        partes_endereco = []

        def safe_str(value):
            if value is None or pd.isna(value):
                return ""
            return str(value).strip()

        # Componentes do endereço
        endereco_rua = safe_str(cliente_dict.get('A1_END', ''))
        if endereco_rua and endereco_rua.lower() != 'não informado':
            partes_endereco.append(endereco_rua)

        bairro = safe_str(cliente_dict.get('A1_BAIRRO', ''))
        if bairro and bairro.lower() not in ['', 'não informado']:
            partes_endereco.append(bairro)

        cidade = safe_str(cliente_dict.get('A1_MUN', ''))
        if cidade:
            partes_endereco.append(cidade)

        uf = safe_str(cliente_dict.get('A1_EST', ''))
        if uf:
            partes_endereco.append(uf)

        cep = safe_str(cliente_dict.get('A1_CEP', ''))
        if cep and cep not in ['N/A', '0'] and len(cep) >= 8:
            if len(cep) == 8 and cep.isdigit():
                cep_formatado = f"{cep[:5]}-{cep[5:]}"
                partes_endereco.append(f"CEP {cep_formatado}")
            else:
                partes_endereco.append(f"CEP {cep}")

        partes_endereco.append("Brasil")
        return ", ".join(partes_endereco)

    def _calcular_frete_automatico(self, origem: str, tipo_veiculo: str = "truck"):
        """Calcula frete automaticamente baseado na distância real"""
        with st.spinner("🔄 Processando cálculo de frete..."):
            # Geocodificar origem
            origem_coords = self.geolocalizacao.geocode(origem)
            if not origem_coords:
                st.error("❌ Não foi possível localizar o endereço de origem.")
                return

            # Geocodificar destino
            cliente_dict = self.dados_cliente_selecionado.to_dict()
            endereco_destino_completo = self._montar_endereco_completo_para_geocode(cliente_dict)
            destino_coords = self.geolocalizacao.geocode(endereco_destino_completo)

            if not destino_coords:
                # Fallback para coordenadas do banco
                try:
                    lat_banco = float(self.dados_cliente_selecionado["latitude"])
                    lng_banco = float(self.dados_cliente_selecionado["longitude"])
                    if lat_banco != 0 and lng_banco != 0:
                        destino_coords = (lat_banco, lng_banco)
                        st.warning("⚠️ Usando coordenadas do banco como fallback.")
                    else:
                        st.error("❌ Não foi possível localizar o endereço de destino.")
                        return
                except:
                    st.error("❌ Endereço não encontrado e coordenadas do banco indisponíveis.")
                    return

            # Calcular distância e tempo
            distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)
            if erro:
                st.error(erro)
                return

            try:
                # Processar distância
                distancia_texto = distancia.replace('km', '').strip()
                
                # Converter para float tratando vírgulas
                if ',' in distancia_texto:
                    if '.' in distancia_texto:
                        # Formato: "1,159.5" - vírgula = milhares, ponto = decimal
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:
                        # Verificar se vírgula é separador de milhares ou decimal
                        partes = distancia_texto.split(',')
                        if len(partes[1]) == 3:  # "1,159" - milhares
                            distancia_km = float(distancia_texto.replace(',', ''))
                        else:  # "1,5" - decimal
                            distancia_km = float(distancia_texto.replace(',', '.'))
                else:
                    distancia_km = float(distancia_texto)

                # Armazenar dados no session state
                st.session_state.distancia_calculada = distancia
                st.session_state.tempo_calculado = duracao
                st.session_state.coordenadas_origem = origem_coords
                st.session_state.coordenadas_destino = destino_coords

                # Obter faixa de KM e código IBGE
                faixa_km = obter_faixa_km_exata(distancia_km, self.faixas_km_ordenadas)
                cidade_ibge = str(self.dados_cliente_selecionado["cidade_ibge"])

                # Buscar valores de frete
                df_clientes_frete = self.db_manager.carregar_clientes_ou_rede()
                resultado_frete = buscar_frete_inteligente(df_clientes_frete, cidade_ibge, faixa_km)

                # Calcular otimização (volume estimado inicial)
                volume_estimado = 500
                otimizacao = calcular_frete_otimizado(resultado_frete, volume_estimado)

                # Armazenar resultados
                st.session_state.frete_calculado_automatico = otimizacao['frete_por_caixa']
                st.session_state.tipo_veiculo_usado = otimizacao['veiculo_otimo']
                st.session_state.resultado_frete_completo = resultado_frete
                st.session_state.otimizacao_frete = otimizacao

                # Exibir resultados
                if otimizacao['frete_por_caixa'] > 0:
                    st.success(f"""
                    ✅ **Cálculo Concluído com Sucesso!**
                    
                    📏 **Rota:** {distancia} ({duracao}) → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💰 **Frete/Caixa:** R$ {otimizacao['frete_por_caixa']:.2f}
                    🚛 **Veículo Otimizado:** {otimizacao['veiculo_otimo'].upper()}
                    """)

                    # Alerta de otimização
                    if otimizacao['alerta']:
                        if 'OTIMIZAÇÃO' in otimizacao['alerta']:
                            st.success(f"🎯 {otimizacao['alerta']}")
                        elif 'MÚLTIPLOS' in otimizacao['alerta']:
                            st.warning(f"📦 {otimizacao['alerta']}")
                        else:
                            st.info(f"ℹ️ {otimizacao['alerta']}")

                    # Tabela de comparação
                    self._exibir_comparacao_fretes(resultado_frete)
                else:
                    st.warning(f"""
                    ⚠️ **Rota calculada, mas frete não encontrado**
                    
                    📏 **Distância:** {distancia} → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💡 **Sugestão:** Use frete manual
                    """)

            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")

    def _exibir_comparacao_fretes(self, resultado_frete: dict):
        """Exibe tabela de comparação de fretes"""
        st.markdown("#### 📊 Comparação de Fretes Disponíveis")

        truck_info = resultado_frete['truck']
        carreta_info = resultado_frete['carreta']

        comparacao_data = []
        
        if truck_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚚 Truck',
                'Capacidade': '870 caixas',
                'Frete Total': f"R$ {truck_info['valor']:,.2f}",
                'Frete/Caixa': f"R$ {truck_info['valor']/870:.2f}",
                'Método de Busca': truck_info['metodo'],
                'Faixa Utilizada': truck_info['faixa_usada']
            })

        if carreta_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚛 Carreta',
                'Capacidade': '1.740 caixas',
                'Frete Total': f"R$ {carreta_info['valor']:,.2f}",
                'Frete/Caixa': f"R$ {carreta_info['valor']/1740:.2f}",
                'Método de Busca': carreta_info['metodo'],
                'Faixa Utilizada': carreta_info['faixa_usada']
            })

        if comparacao_data:
            df_comparacao = pd.DataFrame(comparacao_data)
            st.dataframe(df_comparacao, use_container_width=True, hide_index=True)
            st.info("💡 **Dica:** O frete será otimizado automaticamente quando você definir as quantidades!")

    def _exibir_mapas_cliente(self, origem: str):
        """Exibe mapas interativos"""
        origem_coords = st.session_state.get('coordenadas_origem')
        destino_coords = st.session_state.get('coordenadas_destino')

        if not origem_coords or not destino_coords:
            return

        st.markdown("#### 🗺️ Visualização da Rota")
        
        col_mapa, col_street = st.columns(2)

        with col_mapa:
            st.markdown("**📍 Mapa com Rota**")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

        with col_street:
            st.markdown("**🚦 Street View - Destino**")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

    def _exibir_secao_parametros(self):
        """Exibe seção de parâmetros melhorada"""
        st.markdown("### ⚙️ Parâmetros de Simulação")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🏭 Origem")
            st.info("**São Paulo - SP** (Fixo)")
            
            # Frete
            if hasattr(self, 'frete_padrao_cliente') and self.frete_padrao_cliente is not None:
                st.success(f"🚛 **Frete:** R$ {self.frete_padrao_cliente:.2f}/caixa")
                st.caption("Definido pela seleção do cliente")
                self.frete_padrao = self.frete_padrao_cliente
            else:
                self.frete_padrao = st.number_input(
                    "🚛 Frete/Caixa (R$)", 
                    min_value=0.0, 
                    value=1.50, 
                    step=0.01,
                    help="Frete padrão para cliente novo"
                )

            # Tipo de frete
            self.tipo_frete = st.radio(
                "📦 Tipo de Frete", 
                ("CIF", "FOB"),
                help="CIF: Vendedor paga frete | FOB: Comprador paga frete"
            )

        with col2:
            st.markdown("#### 📍 Destino")
            
            # UF de destino
            opcoes_uf = self.df_padrao["UF"].dropna().unique().tolist() if not self.df_padrao.empty else []
            
            if self.dados_cliente_selecionado is not None:
                uf_cliente = self.dados_cliente_selecionado['A1_EST']
                if uf_cliente in opcoes_uf:
                    index_uf = opcoes_uf.index(uf_cliente)
                    self.uf_selecionado = st.selectbox(
                        "🗺️ UF de Destino", 
                        options=opcoes_uf, 
                        index=index_uf,
                        help="UF do cliente selecionado"
                    )
                else:
                    st.error(f"❌ UF do cliente ({uf_cliente}) não encontrada na planilha!")
                    self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)
            else:
                self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)

            # Contrato
            if self.contrato_real is not None:
                st.success(f"📄 **Contrato:** {self.contrato_real:.2f}%")
                st.caption("Valor real do cliente")
                self.contrato_percentual = self.contrato_real / 100
            else:
                contrato_input = st.number_input(
                    "📄 % Contrato", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=1.00, 
                    step=0.01
                )
                self.contrato_percentual = contrato_input / 100

        with col3:
            st.markdown("#### 💰 Parâmetros Globais")
            
            self.custo_fixo_global = st.number_input(
                "🏗️ Custo Fixo Global (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            
            comissao_input = st.number_input(
                "🤝 % Comissão Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.1,
                help="Se zero, usa valor da planilha"
            )
            self.comissao_padrao = comissao_input / 100

            bonificacao_input = st.number_input(
                "🎁 % Bonificação Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            self.bonificacao_global = bonificacao_input / 100

        # Mostrar informações tributárias
        if self.uf_selecionado:
            st.markdown("#### 📋 Informações Tributárias")
            aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
            aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

            col_trib1, col_trib2, col_trib3 = st.columns(3)
            
            with col_trib1:
                st.metric("🏛️ ICMS Interestadual", f"{aliquotas_origem['interestadual']:.1%}")
            
            with col_trib2:
                st.metric("🏛️ ICMS Interno", f"{aliquotas_destino['interna']:.1%}")
            
            with col_trib3:
                if aliquotas_destino['fcp'] > 0:
                    st.metric("📊 FCP", f"{aliquotas_destino['fcp']:.1%}")
                else:
                    st.metric("📊 FCP", "Não aplicável")

    def _exibir_upload_arquivo(self):
        """Seção de upload melhorada"""
        st.markdown("### 📂 Gestão de Arquivos")
        
        col_upload, col_info = st.columns([2, 1])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "📊 Atualizar planilha de custos (.xlsx)", 
                type="xlsx",
                help="Substitui o arquivo 'Custo de reposição.xlsx'"
            )

            if uploaded_file:
                if st.button("🔄 Confirmar Atualização", type="primary"):
                    try:
                        with st.spinner("📤 Processando upload..."):
                            arquivo_padrao = "Custo de reposição.xlsx"

                            # Criar backup
                            if os.path.exists(arquivo_padrao):
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
                                os.rename(arquivo_padrao, backup_name)
                                st.success(f"✅ Backup criado: {backup_name}")

                            # Salvar novo arquivo
                            with open(arquivo_padrao, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Recarregar dados
                            self.df_padrao = pd.read_excel(arquivo_padrao)
                            self.df_padrao.columns = self.df_padrao.columns.str.strip()

                            # Resetar estado
                            self.gerenciador_estado.resetar_estado()
                            
                            st.success("✅ Arquivo atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        
        with col_info:
            # Informações sobre o arquivo atual
            if not self.df_padrao.empty:
                st.info(f"""
                **📋 Arquivo Atual:**
                - Produtos: {len(self.df_padrao)}
                - UFs: {len(self.df_padrao['UF'].unique()) if 'UF' in self.df_padrao.columns else 0}
                """)
            else:
                st.warning("⚠️ Nenhum arquivo carregado")

    def _validar_dados(self) -> bool:
        """Validação melhorada dos dados"""
        if self.df_padrao.empty:
            st.error("❌ Carregue uma planilha de custos para continuar.")
            return False
            
        if not self.uf_selecionado:
            st.warning("⚠️ Selecione uma UF de destino.")
            return False
            
        return True

    def _processar_simulacao(self):
        """Processa a simulação principal"""
        st.markdown("### 📊 Simulação de Preços")
        
        # Preparar dados base
        df_base = self._preparar_dados_base()

        if df_base.empty:
            st.error(f"❌ Nenhum produto encontrado para a UF {self.uf_selecionado}")
            return

        # Exibir controles
        self._exibir_controles(df_base)

        # Processar edição e resultados
        self._processar_edicao_e_resultados(df_base)

    def _preparar_dados_base(self) -> pd.DataFrame:
        """Prepara dados base com melhor tratamento"""
        # Filtrar por UF
        df_base = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado].copy()

        # Resetar se mudou UF
        if (st.session_state.df_atual is not None and 
            "UF" in st.session_state.df_atual.columns):
            ufs_atuais = st.session_state.df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != self.uf_selecionado:
                self.gerenciador_estado.resetar_estado()

        # Filtrar produtos esperados
        df_base = df_base[df_base["Descrição"].isin(self.produtos_esperados)].copy()

        # Ajustar colunas e aplicar parâmetros
        df_base = self._ajustar_colunas_necessarias(df_base)
        df_base = self._aplicar_parametros_globais(df_base)

        return df_base

    def _ajustar_colunas_necessarias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta colunas com melhor tratamento de valores padrão"""
        colunas_necessarias = [
            "Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", 
            "ICMS ST", "ICMS", "MVA", "Comissão", "Bonificação", "COFINS", "PIS", 
            "Contigência", "ICMS Interestadual", "ICMS Interno Destino", "FCP"
        ]

        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        for col in colunas_necessarias:
            if col not in df.columns:
                if col == "Quantidade":
                    df[col] = 1
                elif col == "ICMS Interestadual":
                    df[col] = aliquotas_origem['interestadual']
                elif col == "ICMS Interno Destino":
                    df[col] = aliquotas_destino['interna']
                elif col == "FCP":
                    df[col] = aliquotas_destino['fcp']
                else:
                    df[col] = 0.0

        return df

    def _aplicar_parametros_globais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica parâmetros globais com melhor organização"""
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        # Aplicar valores básicos
        df["Frete Caixa"] = self.frete_padrao
        df["Contrato"] = self.contrato_percentual
        df["UF Origem"] = 'SP'
        df["UF Destino"] = self.uf_selecionado
        df["ICMS Interestadual"] = aliquotas_origem['interestadual']
        df["ICMS Interno Destino"] = aliquotas_destino['interna']
        df["FCP"] = aliquotas_destino['fcp']

        # Aplicar parâmetros condicionais
        if self.custo_fixo_global > 0:
            df["Custo Fixo"] = self.custo_fixo_global

        if self.comissao_padrao > 0:
            df["Comissão"] = self.comissao_padrao
            st.session_state.comissao_global_aplicada = True
        else:
            st.session_state.comissao_global_aplicada = False

        if self.bonificacao_global > 0:
            df["Bonificação"] = self.bonificacao_global

        return df

    def _exibir_controles(self, df_base: pd.DataFrame):
        """Controles principais melhorados"""
        st.markdown("#### 🎯 Ações Principais")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⚖️ Calcular Ponto de Equilíbrio", use_container_width=True, type="primary"):
                with st.spinner("⚖️ Calculando pontos de equilíbrio..."):
                    df_equilibrio, alertas = self._calcular_ponto_equilibrio(df_base)

                    if alertas:
                        for alerta in alertas:
                            st.warning(f"⚠️ {alerta}")

                    st.session_state.df_atual = df_equilibrio.copy()
                    st.session_state.modo_equilibrio = True
                    st.success("✅ Pontos de equilíbrio calculados!")

        with col2:
            if st.button("🔄 Resetar Simulação", use_container_width=True):
                self.gerenciador_estado.resetar_estado()
                st.success("✅ Dados resetados.")
                time.sleep(1)
                st.rerun()

        with col3:
            # Informações rápidas
            if not df_base.empty:
                st.metric("📦 Produtos", len(df_base))

    def _calcular_ponto_equilibrio(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """Cálculo melhorado do ponto de equilíbrio"""
        df_resultado = df.copy()
        alertas = []

        for index, row in df_resultado.iterrows():
            try:
                # Custos base
                custo_net = float(row.get("Custo NET", 0))
                custo_fixo = float(row.get("Custo Fixo", 0))
                custo_total_unit = custo_net + custo_fixo
                frete_unit = float(row.get("Frete Caixa", 0)) if self.tipo_frete == "CIF" else 0.0

                # Despesas percentuais
                despesas_diretas = (
                    float(row.get("ICMS Interestadual", 0)) +
                    float(row.get("COFINS", 0)) +
                    float(row.get("PIS", 0)) +
                    float(row.get("Comissão", 0)) +
                    float(row.get("Bonificação", 0)) +
                    float(row.get("Contigência", 0)) +
                    float(row.get("Contrato", 0)) +
                    float(row.get("%Estrategico", 0))
                )

                # Verificar viabilidade
                if despesas_diretas >= 1.0:
                    produto_nome = row.get('Descrição', f'Produto {index}')
                    alertas.append(f"{produto_nome}: Despesas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    custos_totais = custo_total_unit + frete_unit
                    preco_equilibrio = custos_totais / (1 - despesas_diretas)
                    preco_equilibrio = max(0.0, CalculadoraTributaria.arredondar_valor(preco_equilibrio, 2))

                df_resultado.at[index, "Preço de Venda"] = preco_equilibrio

            except Exception as e:
                produto_nome = row.get('Descrição', f'Produto {index}')
                alertas.append(f"Erro em {produto_nome}: {str(e)}")
                df_resultado.at[index, "Preço de Venda"] = 0.0

        return df_resultado, alertas

    def _processar_edicao_e_resultados(self, df_base: pd.DataFrame):
        """Processamento melhorado de edição e resultados"""
        # Determinar DataFrame
        if st.session_state.df_atual is not None:
            df_para_edicao = st.session_state.df_atual.copy()
        else:
            df_para_edicao = df_base.copy()

        # Aplicar lógica de comissão/bonificação
        df_para_edicao = self._aplicar_logica_comissao_bonificacao(df_para_edicao)

        # Exibir status e resumos
        self._exibir_status_melhorado()
        self._exibir_resumo_edicoes()

        # Editor de dados
        df_editado = self._exibir_editor_dados_melhorado(df_para_edicao)

        # Processar edições
        df_final = self._processar_dados_editados(df_editado, df_para_edicao)

        # Calcular e exibir resultados
        self._calcular_e_exibir_resultados(df_final)

    def _aplicar_logica_comissao_bonificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica lógica melhorada de comissão e bonificação"""
        df_temp = df.copy()

        # Garantir colunas numéricas
        for col in ["Comissão", "Bonificação"]:
            if col not in df_temp.columns:
                df_temp[col] = 0.0
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0.0)

        # Armazenar valores originais
        if not st.session_state.valores_originais:
            for index in df_temp.index:
                produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
                st.session_state.valores_originais[produto] = {
                    'comissao': float(df_temp.at[index, "Comissão"]),
                    'bonificacao': float(df_temp.at[index, "Bonificação"])
                }

        # Aplicar valores globais se não editados individualmente
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)

            # Comissão global
            if (st.session_state.comissao_global_aplicada and 
                self.comissao_padrao > 0 and 
                produto not in st.session_state.comissoes_editadas):
                df_temp.at[index, "Comissão"] = float(self.comissao_padrao)

            # Bonificação global
            if (self.bonificacao_global > 0 and 
                produto not in st.session_state.bonificacoes_editadas):
                df_temp.at[index, "Bonificação"] = float(self.bonificacao_global)

        # Aplicar edições individuais (prioridade máxima)
        for produto, valor in st.session_state.comissoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Comissão"] = float(valor)

        for produto, valor in st.session_state.bonificacoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Bonificação"] = float(valor)

        return df_temp

    def _exibir_status_melhorado(self):
        """Status melhorado da simulação"""
        # Card de status principal
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.metric("🗺️ Rota", f"SP → {self.uf_selecionado}")
            
        with col_status2:
            modo = "🔒 Equilíbrio" if st.session_state.modo_equilibrio else "📋 Normal"
            st.metric("⚙️ Modo", modo)
            
        with col_status3:
            frete_info = f"R$ {self.frete_padrao:.2f}" if hasattr(self, 'frete_padrao') else "N/A"
            st.metric("🚛 Frete/Caixa", frete_info)

        # Parâmetros ativos
        parametros_ativos = []
        if st.session_state.comissao_global_aplicada and self.comissao_padrao > 0:
            parametros_ativos.append(f"Comissão Global: {self.comissao_padrao:.1%}")
        if self.bonificacao_global > 0:
            parametros_ativos.append(f"Bonificação Global: {self.bonificacao_global:.1%}")

        if parametros_ativos:
            st.info(f"🎯 **Parâmetros Ativos:** {' | '.join(parametros_ativos)}")

        # Edições individuais
        edicoes = []
        if st.session_state.comissoes_editadas:
            edicoes.append(f"Comissões editadas: {len(st.session_state.comissoes_editadas)}")
        if st.session_state.bonificacoes_editadas:
            edicoes.append(f"Bonificações editadas: {len(st.session_state.bonificacoes_editadas)}")

        if edicoes:
            st.success(f"✏️ **Edições Individuais:** {' | '.join(edicoes)}")

    def _exibir_resumo_edicoes(self):
        """Resumo melhorado das edições"""
        if st.session_state.comissoes_editadas or st.session_state.bonificacoes_editadas:
            with st.expander("🎯 Detalhes das Edições Individuais", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🤝 Comissões Personalizadas:**")
                    if st.session_state.comissoes_editadas:
                        for produto, valor in st.session_state.comissoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('comissao', 0)
                            global_val = self.comissao_padrao if self.comissao_padrao > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                        
                        if st.button("🗑️ Limpar Comissões", key="clear_comissoes"):
                            st.session_state.comissoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma comissão editada")

                with col2:
                    st.markdown("**🎁 Bonificações Personalizadas:**")
                    if st.session_state.bonificacoes_editadas:
                        for produto, valor in st.session_state.bonificacoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('bonificacao', 0)
                            global_val = self.bonificacao_global if self.bonificacao_global > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                        
                        if st.button("🗑️ Limpar Bonificações", key="clear_bonificacoes"):
                            st.session_state.bonificacoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma bonificação editada")

    def _exibir_editor_dados_melhorado(self, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Editor de dados melhorado"""
        st.markdown("#### 📊 Editor de Dados da Simulação")

        # Preparar dados para edição
        colunas_edicao = [
            "Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
            "MVA", "Comissão", "Bonificação", "Contrato"
        ]

        df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()

        # Converter valores numéricos
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_para_edicao_clean.columns:
                df_para_edicao_clean[col] = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)

        # Converter percentuais para formato 0-100
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_para_edicao_clean.columns:
                valores = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = (valores * 100).round(2)

        # Editor com melhor configuração
        df_editado = st.data_editor(
            df_para_edicao_clean,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_principal",
            column_config={
                "Descrição": st.column_config.TextColumn(
                    "📦 Produto", 
                    disabled=True, 
                    width="medium"
                ),
                "Preço de Venda": st.column_config.NumberColumn(
                    "💰 Preço Venda", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "📦 Qtd", 
                    format="%.0f", 
                    min_value=1, 
                    step=1,
                    width="small"
                ),
                "Custo NET": st.column_config.NumberColumn(
                    "💵 Custo NET", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Custo Fixo": st.column_config.NumberColumn(
                    "🏗️ Custo Fixo", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "MVA": st.column_config.NumberColumn(
                    "📈 MVA (%)", 
                    format="%.1f%%", 
                    min_value=0.0, 
                    max_value=500.0, 
                    step=0.1,
                    width="small"
                ),
                "Comissão": st.column_config.NumberColumn(
                    "🤝 Comissão (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Bonificação": st.column_config.NumberColumn(
                    "🎁 Bonificação (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Contrato": st.column_config.NumberColumn(
                    "📄 Contrato (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                )
            },
            hide_index=True
        )

        # Dicas de uso
        st.info("💡 **Dicas:** Use ⭐ para editar valores individualmente. Clique duas vezes nas células para editar.")

        return df_editado

    def _processar_dados_editados(self, df_editado: pd.DataFrame, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Processamento melhorado dos dados editados"""
        df_processado = df_editado.copy()

        # Converter percentuais de volta para decimal
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_processado.columns:
                df_processado[col] = pd.to_numeric(df_processado[col], errors='coerce').fillna(0.0) / 100

        # Arredondar valores
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_processado.columns:
                df_processado[col] = df_processado[col].round(2)

        # Detectar mudanças com melhor feedback
        produtos_com_mudancas = []

        for index in df_processado.index:
            if index < len(df_para_edicao):
                produto = df_processado.at[index, "Descrição"]

                # Verificar comissão
                try:
                    comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
                    comissao_editada = float(df_processado.at[index, "Comissão"])

                    if abs(comissao_original - comissao_editada) > 0.001:
                        st.session_state.comissoes_editadas[produto] = comissao_editada
                        produtos_com_mudancas.append(f"Comissão {produto}: {formatar_percentual_brasileiro(comissao_editada * 100)}")
                except:
                    pass

                # Verificar bonificação
                try:
                    bonificacao_original = float(df_para_edicao.iloc[index]["Bonificação"])
                    bonificacao_editada = float(df_processado.at[index, "Bonificação"])

                    if abs(bonificacao_original - bonificacao_editada) > 0.001:
                        st.session_state.bonificacoes_editadas[produto] = bonificacao_editada
                        produtos_com_mudancas.append(f"Bonificação {produto}: {formatar_percentual_brasileiro(bonificacao_editada * 100)}")
                except:
                    pass

        # Feedback sobre mudanças
        if produtos_com_mudancas:
            mudancas_texto = ', '.join(produtos_com_mudancas[:3])
            if len(produtos_com_mudancas) > 3:
                mudancas_texto += f" e mais {len(produtos_com_mudancas) - 3}"
            st.success(f"✏️ **Mudanças detectadas:** {mudancas_texto}")

        # Criar DataFrame final
        df_final = df_para_edicao.copy()
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                         "Custo Fixo", "MVA", "Comissão", "Bonificação", "Contrato"]

        for col in colunas_edicao:
            if col in df_processado.columns:
                df_final[col] = df_processado[col]

        st.session_state.df_edicao_temp = df_final.copy()
        return df_final

    def _calcular_e_exibir_resultados(self, df_final: pd.DataFrame):
        """Cálculo e exibição melhorados dos resultados"""
        st.markdown("#### 🚀 Resultados da Simulação")
        
        # Botão principal de cálculo
        col_calc, col_space = st.columns([2, 3])
        with col_calc:
            calcular_clicked = st.button(
                "🚀 Calcular Resultados Finais", 
                type="primary", 
                use_container_width=True
            )

        if calcular_clicked:
            with st.spinner("🔄 Processando cálculos..."):
                # Otimização de frete se disponível
                self._otimizar_frete_por_volume(df_final)

                # Armazenar dados
                st.session_state.df_atual = st.session_state.df_edicao_temp.copy()
                st.session_state.resultados_atualizados = True
                
                time.sleep(1)  # UX melhor
                st.rerun()

        # Mostrar resultados se disponível
        if st.session_state.get("resultados_atualizados", False):
            self._exibir_resultados_completos(df_final)

    def _otimizar_frete_por_volume(self, df_final: pd.DataFrame):
        """Otimização inteligente de frete por volume"""
        if (hasattr(st.session_state, 'resultado_frete_completo') and 
            st.session_state.resultado_frete_completo):

            volume_total = df_final["Quantidade"].sum()
            
            # Reavalia otimização
            nova_otimizacao = calcular_frete_otimizado(
                st.session_state.resultado_frete_completo, 
                volume_total
            )

            # Verificar mudanças
            otimizacao_anterior = st.session_state.get('otimizacao_frete', {})
            veiculo_anterior = otimizacao_anterior.get('veiculo_otimo', 'desconhecido')
            veiculo_novo = nova_otimizacao['veiculo_otimo']

            # Atualizar frete se necessário
            if veiculo_novo != veiculo_anterior and nova_otimizacao['frete_por_caixa'] > 0:
                df_final["Frete Caixa"] = nova_otimizacao['frete_por_caixa']

                # Alertar sobre otimização
                if nova_otimizacao['economia'] > 0:
                    st.success(f"""
                    🎯 **FRETE OTIMIZADO AUTOMATICAMENTE!**
                    
                    📦 Volume total: {volume_total} caixas
                    {nova_otimizacao['alerta']}
                    💰 Novo frete/caixa: R$ {nova_otimizacao['frete_por_caixa']:.2f}
                    """)
                else:
                    st.info(f"ℹ️ {nova_otimizacao['alerta']}")

            st.session_state.otimizacao_frete = nova_otimizacao

    def _exibir_resultados_completos(self, df_final: pd.DataFrame):
        """Exibição completa e melhorada dos resultados"""
        # Calcular resultados
        calculadora = CalculadoraResultados(self.tipo_frete)
        resultados = df_final.apply(calculadora.calcular_resultados_completos, axis=1)

        # Criar DataFrame para exibição
        df_display = self._criar_dataframe_display_melhorado(df_final, resultados)

        # Informações de otimização
        self._exibir_info_otimizacao(df_final)

        # Tabela principal de resultados
        self._exibir_tabela_resultados_melhorada(df_display)

        # Resumo executivo
        self._exibir_resumo_executivo_melhorado(df_display)

        # Análises detalhadas
        self._exibir_analises_detalhadas(df_final, resultados, df_display)

        # Seção de exportação
        self._exibir_secao_exportacao_melhorada(df_final, resultados, df_display)

    def _criar_dataframe_display_melhorado(self, df_final: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame melhorado para exibição"""
        df_display = pd.DataFrame({
            "Produto": df_final["Descrição"].values,
            "Preço Venda": resultados["Preço Venda"].values,
            "Qtd": resultados["Qtd"].values.astype(int),
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

        # Arredondamento melhorado
        colunas_monetarias = [
            "Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
            "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
            "Lucro Líquido", "Equilíbrio"
        ]

        for col in colunas_monetarias:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: CalculadoraTributaria.arredondar_valor(x, 2)
                )

        df_display["Margem %"] = df_display["Margem %"].apply(
            lambda x: CalculadoraTributaria.arredondar_valor(x, 1)
        )

        return df_display

    def _exibir_info_otimizacao(self, df_final: pd.DataFrame):
        """Exibe informações de otimização de frete"""
        if hasattr(st.session_state, 'otimizacao_frete') and st.session_state.otimizacao_frete:
            otimizacao = st.session_state.otimizacao_frete

            if otimizacao['veiculo_otimo'] != 'nenhum':
                col_opt1, col_opt2, col_opt3, col_opt4 = st.columns(4)

                with col_opt1:
                    volume_total = df_final["Quantidade"].sum()
                    st.metric("📦 Volume Total", f"{volume_total} caixas")

                with col_opt2:
                    veiculo_label = otimizacao['veiculo_otimo'].replace('_', ' ').upper()
                    st.metric("🚛 Veículo Otimizado", veiculo_label)

                with col_opt3:
                    st.metric("💰 Frete Total", f"R$ {otimizacao['frete_total']:.2f}")

                with col_opt4:
                    if otimizacao['economia'] > 0:
                        st.metric("💰 Economia", f"R$ {otimizacao['economia']:.2f}", delta="Positiva")
                    else:
                        st.metric("📊 Status", "Otimizado")

    def _exibir_tabela_resultados_melhorada(self, df_display: pd.DataFrame):
        """Tabela de resultados com melhor formatação"""
        st.markdown("#### 📊 Resultados Detalhados")

        # Função de coloração melhorada
        def colorir_valores(val):
            try:
                if isinstance(val, (int, float)):
                    if val < 0:
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                    elif val > 0:
                        return 'background-color: #e8f5e8; color: #2e7d32'
                    else:
                        return 'color: #666666'
                return ''
            except:
                return ''

        # Formatação aprimorada
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
        }).applymap(
            colorir_valores, 
            subset=["Lucro Antes IR", "Lucro Líquido", "Margem %"]
        ).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f0f2f6'), ('color', '#262730'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '8px'), ('text-align', 'right')]},
            {'selector': 'td:first-child', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}
        ])

        st.dataframe(styled_display, use_container_width=True, height=400)

    def _exibir_resumo_executivo_melhorado(self, df_display: pd.DataFrame):
        """Resumo executivo melhorado"""
        st.markdown("#### 📈 Resumo Executivo")

        if len(df_display) > 0:
            # Métricas principais
            col1, col2, col3, col4, col5 = st.columns(5)

            total_receita = df_display["Subtotal"].sum()
            total_lucro_liquido = df_display["Lucro Líquido"].sum()
            margem_ponderada = (total_lucro_liquido / total_receita) * 100 if total_receita > 0 else 0.0
            produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
            total_nf = df_display["Total NF"].sum()

            with col1:
                st.metric("💰 Receita Total", f"R$ {total_receita:,.2f}")

            with col2:
                delta_lucro = f"{margem_ponderada:.1f}%" if total_receita > 0 else "0%"
                delta_color = "normal" if total_lucro_liquido >= 0 else "inverse"
                st.metric("💵 Lucro Líquido", f"R$ {total_lucro_liquido:,.2f}", delta=delta_lucro)

            with col3:
                cor_margem = "🟢" if margem_ponderada > 10 else "🟡" if margem_ponderada > 5 else "🔴"
                st.metric("📊 Margem Ponderada", f"{cor_margem} {margem_ponderada:.1f}%")

            with col4:
                cor_produtos = "🔴" if produtos_prejuizo > 0 else "🟢"
                st.metric("⚠️ Produtos c/ Prejuízo", f"{cor_produtos} {produtos_prejuizo}")

            with col5:
                st.metric("📄 Total NF", f"R$ {total_nf:,.2f}")

            # Alertas inteligentes
            self._exibir_alertas_inteligentes(df_display, margem_ponderada, produtos_prejuizo)

    def _exibir_alertas_inteligentes(self, df_display: pd.DataFrame, margem_ponderada: float, produtos_prejuizo: int):
        """Sistema de alertas inteligentes"""
        alertas = []

        # Análise de margem
        if margem_ponderada < 5:
            alertas.append("🔴 **ATENÇÃO:** Margem muito baixa (< 5%). Revisar preços ou custos.")
        elif margem_ponderada < 10:
            alertas.append("🟡 **CUIDADO:** Margem baixa (< 10%). Monitorar competitividade.")
        elif margem_ponderada > 25:
            alertas.append("🟢 **EXCELENTE:** Margem alta (> 25%). Ótima rentabilidade!")

        # Análise de produtos
        if produtos_prejuizo > 0:
            produtos_negativos = df_display[df_display["Lucro Líquido"] < 0]
            maior_prejuizo = produtos_negativos.nlargest(1, "Lucro Líquido")
            if not maior_prejuizo.empty:
                produto_problema = maior_prejuizo.iloc[0]["Produto"]
                prejuizo_valor = maior_prejuizo.iloc[0]["Lucro Líquido"]
                alertas.append(f"🚨 **PRODUTO CRÍTICO:** {produto_problema} com prejuízo de R$ {abs(prejuizo_valor):.2f}")

        # Análise de concentração
        receita_por_produto = df_display["Subtotal"]
        produto_principal = df_display.loc[receita_por_produto.idxmax(), "Produto"]
        concentracao = (receita_por_produto.max() / receita_por_produto.sum()) * 100
        if concentracao > 50:
            alertas.append(f"📊 **CONCENTRAÇÃO:** {concentracao:.1f}% da receita vem de '{produto_principal}'")

        # Exibir alertas
        for alerta in alertas:
            if "🔴" in alerta or "🚨" in alerta:
                st.error(alerta)
            elif "🟡" in alerta:
                st.warning(alerta)
            else:
                st.success(alerta)

    def _exibir_analises_detalhadas(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Análises detalhadas melhoradas"""
        with st.expander("🔍 Análises Detalhadas", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📊 Composição", "🎯 Top Produtos", "📋 Breakdown"])

            with tab1:
                self._exibir_analise_composicao(df_display)

            with tab2:
                self._exibir_top_produtos(df_display)

            with tab3:
                self._exibir_breakdown_calculo(df_final, resultados)

    def _exibir_analise_composicao(self, df_display: pd.DataFrame):
        """Análise de composição dos resultados"""
        st.markdown("**📊 Composição dos Resultados**")

        # Análise de receita por produto
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Contribuição por Receita**")
            receita_sorted = df_display.nlargest(5, "Subtotal")[["Produto", "Subtotal", "Margem %"]]
            for idx, row in receita_sorted.iterrows():
                participacao = (row["Subtotal"] / df_display["Subtotal"].sum()) * 100
                st.write(f"• {row['Produto']}: R$ {row['Subtotal']:,.2f} ({participacao:.1f}%) - Margem: {row['Margem %']:.1f}%")

        with col2:
            st.markdown("**🎯 Contribuição por Lucro**")
            lucro_sorted = df_display.nlargest(5, "Lucro Líquido")[["Produto", "Lucro Líquido", "Margem %"]]
            for idx, row in lucro_sorted.iterrows():
                if df_display["Lucro Líquido"].sum() > 0:
                    participacao = (row["Lucro Líquido"] / df_display["Lucro Líquido"].sum()) * 100
                else:
                    participacao = 0
                st.write(f"• {row['Produto']}: R$ {row['Lucro Líquido']:,.2f} ({participacao:.1f}%) - Margem: {row['Margem %']:.1f}%")

    def _exibir_top_produtos(self, df_display: pd.DataFrame):
        """Análise dos top produtos"""
        st.markdown("**🏆 Rankings de Produtos**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🥇 Maiores Receitas**")
            top_receita = df_display.nlargest(3, "Subtotal")[["Produto", "Subtotal"]]
            for i, (idx, row) in enumerate(top_receita.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: R$ {row['Subtotal']:,.2f}")

        with col2:
            st.markdown("**💰 Maiores Lucros**")
            top_lucro = df_display.nlargest(3, "Lucro Líquido")[["Produto", "Lucro Líquido"]]
            for i, (idx, row) in enumerate(top_lucro.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: R$ {row['Lucro Líquido']:,.2f}")

        with col3:
            st.markdown("**📈 Maiores Margens**")
            top_margem = df_display.nlargest(3, "Margem %")[["Produto", "Margem %"]]
            for i, (idx, row) in enumerate(top_margem.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {row['Margem %']:.1f}%")

        # Produtos que precisam de atenção
        produtos_atencao = df_display[df_display["Margem %"] < 5]
        if not produtos_atencao.empty:
            st.markdown("**⚠️ Produtos que Precisam de Atenção (Margem < 5%)**")
            for idx, row in produtos_atencao.iterrows():
                st.write(f"🔴 {row['Produto']}: Margem {row['Margem %']:.1f}% - Lucro R$ {row['Lucro Líquido']:,.2f}")

    def _exibir_breakdown_calculo(self, df_final: pd.DataFrame, resultados: pd.DataFrame):
        """Breakdown detalhado do cálculo"""
        st.markdown("**🔍 Breakdown do Cálculo (Primeiro Produto)**")

        if len(resultados) > 0:
            primeiro = resultados.iloc[0]
            produto_nome = df_final.iloc[0]["Descrição"]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**📦 Base do Produto**")
                st.write(f"• Produto: {produto_nome}")
                st.write(f"• Preço Unitário: R$ {primeiro['Preço Venda']:.2f}")
                st.write(f"• Quantidade: {primeiro['Qtd']:.0f}")
                st.write(f"• **Subtotal: R$ {primeiro['Subtotal']:.2f}**")
                st.write(f"• IPI: R$ {primeiro['IPI']:.2f}")

            with col2:
                st.markdown("**🏛️ Impostos e Contribuições**")
                st.write(f"• Base ICMS-ST: R$ {primeiro['Base ICMS-ST']:.2f}")
                st.write(f"• ICMS Próprio: R$ {primeiro['ICMS Próprio']:.2f}")
                st.write(f"• ICMS-ST: R$ {primeiro['ICMS-ST']:.2f}")
                st.write(f"• FCP: R$ {primeiro['FCP']:.2f}")
                st.write(f"• **Total NF: R$ {primeiro['Total NF']:.2f}**")

            with col3:
                st.markdown("**💰 Resultado Financeiro**")
                st.write(f"• Custo Total: R$ {primeiro['Custo Total']:.2f}")
                st.write(f"• Despesas: R$ {primeiro['Total Despesas']:.2f}")
                st.write(f"• Frete: R$ {primeiro['Frete Total']:.2f}")
                st.write(f"• Lucro Antes IR: R$ {primeiro['Lucro Antes IR']:.2f}")
                st.write(f"• IRPJ + CSLL: R$ {primeiro['IRPJ'] + primeiro['CSLL']:.2f}")
                st.write(f"• **Lucro Líquido: R$ {primeiro['Lucro Líquido']:.2f}**")
                st.write(f"• **Margem: {primeiro['Margem Líquida %']:.1f}%**")

            # Fórmulas utilizadas
            st.markdown("**📐 Fórmulas Principais**")
            st.code("""
            Subtotal = Preço × Quantidade
            ICMS-ST = max(0, (Subtotal × (1 + MVA) × ICMS_Destino) - (Subtotal × ICMS_Origem))
            Lucro Antes IR = Subtotal - Custos - Despesas - Frete
            Lucro Líquido = Lucro Antes IR - IRPJ - CSLL
            Margem = (Lucro Líquido / Subtotal) × 100
            """)

    def _exibir_secao_exportacao_melhorada(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Seção de exportação melhorada"""
        st.markdown("#### 📄 Exportar e Compartilhar")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Excel Completo", use_container_width=True, type="primary"):
                excel_buffer = self._gerar_excel_completo(df_final, resultados, df_display)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"simulacao_sobel_SP_{self.uf_selecionado}_{timestamp}.xlsx"
                
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=excel_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with col2:
            if st.button("📋 Relatório PDF", use_container_width=True):
                st.info("🚧 Funcionalidade em desenvolvimento")

        with col3:
            if st.button("📱 Resumo para WhatsApp", use_container_width=True):
                resumo_whatsapp = self._gerar_resumo_whatsapp(df_display)
                st.text_area("📱 Copie e cole no WhatsApp:", resumo_whatsapp, height=200)

    def _gerar_excel_completo(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame) -> io.BytesIO:
        """Gera Excel completo com múltiplas abas"""
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            # Aba 1: Resultados principais
            df_display.to_excel(writer, index=False, sheet_name="Resultados")
            
            # Aba 2: Dados de entrada
            colunas_entrada = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                              "Custo Fixo", "MVA", "Comissão", "Bonificação"]
            df_entrada = df_final[colunas_entrada]
            df_entrada.to_excel(writer, index=False, sheet_name="Dados_Entrada")
            
            # Aba 3: Cálculos detalhados
            df_completo = pd.concat([df_final[colunas_entrada], resultados], axis=1)
            df_completo.to_excel(writer, index=False, sheet_name="Calculos_Completos")
            
            # Aba 4: Resumo executivo
            resumo_data = {
                "Métrica": [
                    "Receita Total", "Lucro Líquido Total", "Margem Ponderada", 
                    "Produtos com Prejuízo", "Total da Nota Fiscal", "Quantidade Total"
                ],
                "Valor": [
                    f"R$ {df_display['Subtotal'].sum():,.2f}",
                    f"R$ {df_display['Lucro Líquido'].sum():,.2f}",
                    f"{(df_display['Lucro Líquido'].sum()/df_display['Subtotal'].sum()*100):.1f}%",
                    len(df_display[df_display["Lucro Líquido"] < 0]),
                    f"R$ {df_display['Total NF'].sum():,.2f}",
                    f"{df_display['Qtd'].sum():,.0f} caixas"
                ]
            }
            resumo_df = pd.DataFrame(resumo_data)
            resumo_df.to_excel(writer, index=False, sheet_name="Resumo_Executivo")
            
            # Aba 5: Parâmetros utilizados
            parametros_data = {
                "Parâmetro": [
                    "UF Origem", "UF Destino", "Tipo de Frete", "Frete por Caixa",
                    "% Contrato", "% Comissão Global", "% Bonificação Global"
                ],
                "Valor": [
                    "SP", self.uf_selecionado, self.tipo_frete, 
                    f"R$ {self.frete_padrao:.2f}",
                    f"{self.contrato_percentual:.2%}",
                    f"{self.comissao_padrao:.2%}" if self.comissao_padrao > 0 else "N/A",
                    f"{self.bonificacao_global:.2%}" if self.bonificacao_global > 0 else "N/A"
                ]
            }
            parametros_df = pd.DataFrame(parametros_data)
            parametros_df.to_excel(writer, index=False, sheet_name="Parametros")

        return excel_buffer

    def _gerar_resumo_whatsapp(self, df_display: pd.DataFrame) -> str:
        """Gera resumo formatado para WhatsApp"""
        total_receita = df_display["Subtotal"].sum()
        total_lucro = df_display["Lucro Líquido"].sum()
        margem = (total_lucro / total_receita * 100) if total_receita > 0 else 0
        produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
        
        resumo = f"""
🏢 *SIMULAÇÃO SOBEL - RESUMO EXECUTIVO*
📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🗺️ *Rota:* SP → {self.uf_selecionado}
📦 *Produtos:* {len(df_display)} itens

💰 *RESULTADOS FINANCEIROS:*
• Receita Total: R$ {total_receita:,.2f}
• Lucro Líquido: R$ {total_lucro:,.2f}
• Margem Ponderada: {margem:.1f}%
• Produtos c/ Prejuízo: {produtos_prejuizo}

🏆 *TOP 3 PRODUTOS POR RECEITA:*
"""
        
        top3_receita = df_display.nlargest(3, "Subtotal")
        for i, (_, row) in enumerate(top3_receita.iterrows(), 1):
            resumo += f"{i}. {row['Produto']}: R$ {row['Subtotal']:,.2f} (Margem: {row['Margem %']:.1f}%)\n"
        
        resumo += f"""
⚠️ *ALERTAS:*
"""
        if margem < 5:
            resumo += "🔴 Margem muito baixa - Revisar preços\n"
        elif margem < 10:
            resumo += "🟡 Margem baixa - Monitorar\n"
        else:
            resumo += "🟢 Margem adequada\n"
            
        if produtos_prejuizo > 0:
            resumo += f"🚨 {produtos_prejuizo} produtos com prejuízo\n"
        
        resumo += "\n🤖 _Gerado pelo Simulador Sobel v3.0_"
        
        return resumo

    def _exibir_relatorios(self):
        """Seção de relatórios e análises históricas"""
        st.markdown("### 📈 Relatórios e Análises")
        
        if not st.session_state.get("resultados_atualizados", False):
            st.info("ℹ️ Execute uma simulação primeiro para gerar relatórios.")
            return
        
        # Placeholder para funcionalidades futuras
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📊 Relatórios Disponíveis
            - 📈 Análise de margem por produto
            - 🎯 Comparativo de cenários
            - 📋 Histórico de simulações
            - 🏆 Ranking de produtos
            """)
            
        with col2:
            st.markdown("""
            #### 🚧 Em Desenvolvimento
            - 📅 Análise temporal
            - 🔄 Comparativo com concorrência
            - 📊 Dashboard executivo
            - 📱 Relatórios mobile
            """)
        
        st.info("💡 **Sugestão:** Use a funcionalidade de exportação para análises externas detalhadas.")

# Função principal melhorada
def main():
    """Função principal com melhor tratamento de erros"""
    try:
        # Verificações iniciais
        if 'inicializado' not in st.session_state:
            st.session_state.inicializado = True
            st.balloons()  # Feedback visual de carregamento
        
        # Executar simulador
        simulador = SimuladorSobel()
        simulador.executar()
        
        # Notas técnicas no final
        st.markdown("---")
        st.markdown("""
        ### 📚 Notas Técnicas - Simulador Sobel v3.0

        #### 🎯 **Estados com FCP (Fundo de Combate à Pobreza):**
        - **2,0%:** AC, AL, BA, MA, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, SC, SE
        - **2,5%:** CE
        - **0,0%:** AP, AM, DF, ES, GO, MT, RO, RR, SP, TO

        #### 🔧 **Funcionalidades Principais:**
        - ✅ Cálculo automático de ICMS-ST por UF
        - ✅ Otimização inteligente de frete por volume
        - ✅ Geolocalização e cálculo de rotas
        - ✅ Edição individual de comissões e bonificações
        - ✅ Exportação completa para Excel
        - ✅ Análises detalhadas e alertas inteligentes

        #### 📊 **Melhorias v3.0:**
        - Interface redesenhada com melhor UX/UI
        - Sistema de alertas inteligentes
        - Otimização automática de frete
        - Análises detalhadas por produto
        - Exportação aprimorada
        - Tratamento de erros melhorado

        ---
        *Desenvolvido para Sobel Suprema - Sistema integrado de simulação de preços*
        """)
        
    except Exception as e:
        st.error(f"""
        🚨 **Erro Crítico na Aplicação**
        
        **Detalhes do erro:** {str(e)}
        
        **Ações recomendadas:**
        1. 🔄 Recarregue a página (F5)
        2. 🧹 Limpe o cache do navegador
        3. 📞 Entre em contato com o suporte técnico
        
        **Informações técnicas:**
        - Versão: Simulador Sobel v3.0
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        # Log de erro para debug
        import traceback
        st.expander("🔧 Detalhes Técnicos (Para Suporte)", expanded=False).code(
            traceback.format_exc()
        )

# Executar aplicação
if __name__ == "__main__":
    main())
        except:
            # Formatação manual no                "Valor": [
                    "SP", self.uf_selecionado, self.tipo_frete, 
                    # Configuração da página - DEVE SER A PRIMEIRA COISA!
import streamlit as st

# Configurar página ANTES de qualquer outro comando Streamlit
st.set_page_config(
    page_title="Simulador de Preço de Venda Sobel", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊"
)

import pandas as pd
import pyodbc
import io
import os
import requests
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any
import math
import time
import unicodedata
import locale

# Configurar locale para formatação brasileira
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Fallback se não conseguir configurar

# Carrega chave da API
load_dotenv()

# ==================== FUNÇÕES AUXILIARES ====================

def normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza texto para comparação"""
    if pd.isna(texto) or texto is None:
        return ""
    
    # Converter para string e normalizar
    texto_str = str(texto).strip().upper()
    
    # Remover acentos usando unicodedata
    texto_normalizado = unicodedata.normalize('NFD', texto_str)
    texto_sem_acento = ''.join(char for char in texto_normalizado 
                              if unicodedata.category(char) != 'Mn')
    
    return texto_sem_acento

def formatar_moeda_brasileira(valor: float) -> str:
    """Formata valor monetário no padrão brasileiro"""
    try:
        if pd.isna(valor) or valor is None:
            return "R$ 0,00"
        
        valor_float = float(valor)
        
        # Usar locale se disponível, senão formatação manual
        try:
            return locale.currency(valor_float, grouping=True, symbol='R

def obter_faixa_km_exata(distancia_km: float, faixas: list) -> str:
    """Dado a distância, retorna a faixa de KM correspondente (ex: '0-50')"""
    # Primeiro: busca exata
    for ini, fim, label in faixas:
        if ini <= distancia_km <= fim:
            return label

    # Segundo: busca pela faixa mais próxima (menor diferença)
    if faixas:
        melhor_faixa = None
        menor_diferenca = float('inf')

        for ini, fim, label in faixas:
            # Calcular distância até o centro da faixa
            centro_faixa = (ini + fim) / 2 if fim != float('inf') else ini + 50
            diferenca = abs(distancia_km - centro_faixa)

            if diferenca < menor_diferenca:
                menor_diferenca = diferenca
                melhor_faixa = label

        # Se a diferença for razoável (menos de 100km), usar a faixa mais próxima
        if menor_diferenca <= 100:
            return melhor_faixa

    return 'Indefinida'

def buscar_frete_inteligente(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str) -> dict:
    """
    Busca valores de frete de forma inteligente para otimização de veículo
    """
    resultado = {
        'truck': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'carreta': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'capacidades': {'truck': 870, 'carreta': 1740}
    }

    # Buscar ambos os tipos
    for tipo_veiculo in ['truck', 'carreta']:
        valor, faixa_usada, metodo = buscar_frete_por_faixa(df_clientes, cidade_ibge, faixa_km, tipo_veiculo)
        resultado[tipo_veiculo] = {
            'valor': valor,
            'faixa_usada': faixa_usada,
            'metodo': metodo
        }

    return resultado

def calcular_frete_otimizado(resultado_frete: dict, quantidade_total: int) -> dict:
    """
    Calcula o frete otimizado baseado no volume total
    """
    truck_info = resultado_frete['truck']
    carreta_info = resultado_frete['carreta']
    capacidades = resultado_frete['capacidades']

    # Se não encontrou nenhum valor, retornar erro
    if truck_info['valor'] == 0 and carreta_info['valor'] == 0:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhum valor de frete encontrado',
            'detalhes': {}
        }

    # Calcular cenários
    cenarios = {}

    # Cenário Truck (se couber)
    if quantidade_total <= capacidades['truck'] and truck_info['valor'] > 0:
        cenarios['truck'] = {
            'frete_total': truck_info['valor'],
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': 1,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'],
            'ocupacao': (quantidade_total / capacidades['truck']) * 100
        }

    # Cenário Carreta
    if carreta_info['valor'] > 0:
        viagens_carreta = max(1, math.ceil(quantidade_total / capacidades['carreta']))
        cenarios['carreta'] = {
            'frete_total': carreta_info['valor'] * viagens_carreta,
            'frete_por_caixa': carreta_info['valor'] / capacidades['carreta'],
            'viagens': viagens_carreta,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['carreta'] * viagens_carreta,
            'ocupacao': (quantidade_total / (capacidades['carreta'] * viagens_carreta)) * 100
        }

    # Cenário Truck múltiplo (se necessário)
    if quantidade_total > capacidades['truck'] and truck_info['valor'] > 0:
        viagens_truck = math.ceil(quantidade_total / capacidades['truck'])
        cenarios['truck_multiplo'] = {
            'frete_total': truck_info['valor'] * viagens_truck,
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': viagens_truck,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'] * viagens_truck,
            'ocupacao': (quantidade_total / (capacidades['truck'] * viagens_truck)) * 100
        }

    # Encontrar melhor opção (menor custo total)
    if not cenarios:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhuma opção de frete viável',
            'detalhes': {}
        }

    melhor_opcao = min(cenarios.keys(), key=lambda k: cenarios[k]['frete_total'])
    melhor_cenario = cenarios[melhor_opcao]

    # Calcular economia
    economia = 0.0
    if 'carreta' in cenarios and melhor_opcao != 'carreta':
        economia = cenarios['carreta']['frete_total'] - melhor_cenario['frete_total']

    # Gerar alerta
    alerta = ""
    if melhor_opcao == 'truck':
        alerta = f"✅ OTIMIZAÇÃO: Volume de {quantidade_total} caixas cabe em TRUCK! Economia de R$ {economia:.2f}"
    elif melhor_opcao == 'truck_multiplo':
        viagens = melhor_cenario['viagens']
        alerta = f"📦 MÚLTIPLOS TRUCKS: {viagens} viagens necessárias. " + (f"Economia de R$ {economia:.2f}" if economia > 0 else "")
    else:
        alerta = f"🚛 CARRETA RECOMENDADA: Volume de {quantidade_total} caixas otimizado para carreta"

    return {
        'veiculo_otimo': melhor_opcao,
        'frete_total': melhor_cenario['frete_total'],
        'frete_por_caixa': melhor_cenario['frete_por_caixa'],
        'economia': economia,
        'alerta': alerta,
        'detalhes': {
            'cenarios': cenarios,
            'melhor_cenario': melhor_cenario,
            'truck_info': truck_info,
            'carreta_info': carreta_info
        }
    }

def buscar_frete_por_faixa(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str, tipo_veiculo='truck') -> tuple:
    """
    Busca o valor do frete de forma inteligente
    """
    # Primeira tentativa: busca exata por cidade_ibge e faixa
    linha_exata = df_clientes[
        (df_clientes['cidade_ibge'] == cidade_ibge) &
        (df_clientes['FAIXA_KM'] == faixa_km)
    ]

    if not linha_exata.empty:
        if tipo_veiculo == 'truck':
            valor = linha_exata.iloc[0]['TBL_TRCK'] if not pd.isna(linha_exata.iloc[0]['TBL_TRCK']) else 0.0
        elif tipo_veiculo == 'carreta':
            valor = linha_exata.iloc[0]['TBL_CRRT'] if 'TBL_CRRT' in linha_exata.columns and not pd.isna(linha_exata.iloc[0]['TBL_CRRT']) else 0.0
        else:
            valor = 0.0

        if valor > 0:
            return float(valor), faixa_km, "exata"

    # Segunda tentativa: buscar por IBGE e calcular pela faixa mais próxima
    linhas_ibge = df_clientes[df_clientes['cidade_ibge'] == cidade_ibge]

    if not linhas_ibge.empty:
        distancia_solicitada = extrair_distancia_da_faixa(faixa_km)

        if distancia_solicitada is not None:
            melhor_faixa = None
            menor_diferenca = float('inf')
            melhor_linha = None

            for _, linha in linhas_ibge.iterrows():
                faixa_disponivel = linha['FAIXA_KM']
                distancia_disponivel = extrair_distancia_da_faixa(faixa_disponivel)

                if distancia_disponivel is not None:
                    diferenca = abs(distancia_solicitada - distancia_disponivel)
                    if diferenca < menor_diferenca:
                        menor_diferenca = diferenca
                        melhor_faixa = faixa_disponivel
                        melhor_linha = linha

            if melhor_linha is not None:
                if tipo_veiculo == 'truck':
                    valor = melhor_linha['TBL_TRCK'] if not pd.isna(melhor_linha['TBL_TRCK']) else 0.0
                elif tipo_veiculo == 'carreta':
                    valor = melhor_linha['TBL_CRRT'] if 'TBL_CRRT' in melhor_linha and not pd.isna(melhor_linha['TBL_CRRT']) else 0.0
                else:
                    valor = 0.0

                if valor > 0:
                    return float(valor), melhor_faixa, f"aproximada (IBGE {cidade_ibge})"

    return 0.0, "não encontrada", "não encontrado"

def extrair_distancia_da_faixa(faixa: str) -> float:
    """Extrai a distância média de uma faixa"""
    try:
        faixa_str = str(faixa).strip()

        if '+' in faixa_str:
            valor = int(faixa_str.replace('+', '').strip())
            return float(valor + 50)
        elif '-' in faixa_str:
            partes = faixa_str.split('-')
            if len(partes) == 2:
                ini, fim = int(partes[0].strip()), int(partes[1].strip())
                return float((ini + fim) / 2)
        else:
            return float(faixa_str)
    except (ValueError, IndexError):
        return None

# ==================== CLASSES PRINCIPAIS ====================

class ConfiguracaoTributaria:
    """Classe para gerenciar configurações tributárias por UF"""

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
        'RJ': {'interna': 0.22, 'interestadual': 0.12, 'fcp': 0.02}, 
        'RN': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RS': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RO': {'interna': 0.175, 'interestadual': 0.12, 'fcp': 0.0},
        'RR': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
        'SC': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
        'SP': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
        'SE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'TO': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0}
    }

    @classmethod
    def obter_aliquotas(cls, uf: str) -> Dict[str, float]:
        """Retorna as alíquotas para uma UF específica"""
        return cls.ICMS_ALIQUOTAS.get(uf.upper(), {
            'interna': 0.18, 
            'interestadual': 0.12, 
            'fcp': 0.0
        })

class GerenciadorGeolocalizacao:
    """Classe para gerenciar operações de geolocalização"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço ou CEP em coordenadas (lat, lng)"""
        try:
            with st.spinner("🔍 Geocodificando endereço..."):
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return location["lat"], location["lng"]
                return None, None
        except Exception as e:
            st.error(f"❌ Erro na geocodificação: {str(e)}")
            return None, None

    def calcular_distancia(self, origem_coords: Tuple[float, float], 
                          destino_coords: Tuple[float, float]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Consulta a Distance Matrix API e retorna distância e tempo"""
        try:
            with st.spinner("📏 Calculando distância e tempo..."):
                lat_o, lng_o = origem_coords
                lat_d, lng_d = destino_coords

                url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat_o},{lng_o}&destinations={lat_d},{lng_d}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                elemento = data['rows'][0]['elements'][0]
                status = elemento.get("status", "ERRO")

                if status != "OK":
                    return None, None, f"⚠️ API não conseguiu calcular: `{status}`"

                distancia = elemento['distance']['text']
                duracao = elemento['duration']['text']
                return distancia, duracao, None

        except Exception as e:
            return None, None, f"❌ Erro ao processar resposta: {str(e)}"

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas usando a fórmula de Haversine"""
        R = 6371  # Raio da Terra em km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

class GerenciadorBancoDados:
    """Classe para gerenciar conexões e consultas ao banco de dados"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @st.cache_data(ttl=600)
    def carregar_clientes_ou_rede(_self) -> pd.DataFrame:
        """Carrega dados dos clientes do banco de dados"""
        try:
            with st.spinner("🔄 Carregando dados dos clientes..."):
                with pyodbc.connect(_self.connection_string, timeout=30) as conexao:
                    query = """
                        SELECT 
                            SA1.A1_COD, 
                            SA1.A1_LOJA,
                            SA1.A1_ZZLOJA,
                            SA1.A1_NOME,
                            IIF(SA1.A1_ZZREDE = '', LEFT(SA1.A1_NOME, 20), SA1.A1_ZZREDE) AS REDE,
                            SA1.A1_CEP, 
                            SA1.A1_RISCO,
                            SA1.A1_ZZCONTR,
                            SA1.A1_LC,
                            SA1.A1_END,                         
                            SA1.A1_MCOMPRA,
                            SA1.A1_ULTCOM,
                            SA1.A1_EST,
                            SA1.A1_MUN,
                            SA1.A1_BAIRRO,
                            SA1.A1_END,
                            SA1.A1_CGC,
                            cep.longitude,
                            cep.latitude,
                            cep.nome_logradouro_sem_acento,
                            ibge.cidade_ibge,
                            T.CIDADE,
                            T.FAIXA_KM,
                            T.TBL_TRCK,
                            T.TBL_CRRT
                        FROM SA1010 SA1
                        INNER JOIN cep.dbo.tbl_cep_202504_n_logradouro AS cep 
                            ON cep.cep COLLATE Latin1_General_CI_AS = SA1.A1_CEP COLLATE Latin1_General_CI_AS
                        INNER JOIN cep.dbo.tbl_cep_202504_n_cidade_ibge AS ibge 
                            ON ibge.id_cidade = cep.cidade_id
                        INNER JOIN BISOBEL.dbo.TRANSP_TARGET T ON T.COD_IBGE COLLATE Latin1_General_CI_AS = ibge.cidade_ibge 
                        WHERE SA1.A1_MSBLQL = '2'
                          AND SA1.D_E_L_E_T_ = ''
                    """
                    return pd.read_sql(query, conexao)
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados dos clientes: {e}")
            return pd.DataFrame()

class CalculadoraTributaria:
    """Classe para realizar cálculos tributários"""

    @staticmethod
    def arredondar_valor(valor: Any, decimais: int = 2) -> float:
        """Arredonda valores para evitar problemas de precisão"""
        try:
            return round(float(valor), decimais)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def calcular_icms_st_completo(valor_produto: float, ipi_valor: float, mva: float,
                                 icms_interestadual: float, icms_interno_destino: float,
                                 fcp_aliquota: float, frete: float = 0.0,
                                 seguro: float = 0.0, despesas: float = 0.0,
                                 descontos: float = 0.0) -> Tuple[float, float, float, float, float]:
        """
        Cálculo preciso do ICMS-ST conforme a legislação
        """
        # Se MVA for 0, não há ICMS-ST
        if mva <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        # Base sem MVA: inclui valor do produto + IPI
        base_sem_mva = CalculadoraTributaria.arredondar_valor(valor_produto + ipi_valor)

        # Aplica MVA
        base_com_mva = CalculadoraTributaria.arredondar_valor(base_sem_mva * (1 + mva))

        # ICMS origem (interestadual) sobre base sem MVA
        icms_origem = CalculadoraTributaria.arredondar_valor(base_sem_mva * icms_interestadual)

        # ICMS destino (interno) sobre base com MVA
        icms_destino = CalculadoraTributaria.arredondar_valor(base_com_mva * icms_interno_destino)

        # ICMS-ST: diferença entre ICMS destino e ICMS origem
        icms_st = CalculadoraTributaria.arredondar_valor(max(icms_destino - icms_origem, 0.0))

        # FCP somente se a alíquota for maior que zero
        fcp = CalculadoraTributaria.arredondar_valor(base_sem_mva * fcp_aliquota) if fcp_aliquota > 0 else 0.0

        return icms_st, base_com_mva, icms_origem, icms_destino, fcp

class CalculadoraResultados:
    """Classe para calcular resultados financeiros"""

    def __init__(self, tipo_frete: str = "CIF"):
        self.tipo_frete = tipo_frete

    def calcular_resultados_completos(self, row: pd.Series) -> pd.Series:
        """Calcula todos os resultados financeiros para uma linha de produto"""
        try:
            # Valores base
            preco_venda = CalculadoraTributaria.arredondar_valor(row["Preço de Venda"])
            qtd = CalculadoraTributaria.arredondar_valor(row["Quantidade"], 0)
            subtotal = CalculadoraTributaria.arredondar_valor(preco_venda * qtd)

            # Custos
            custo_net = CalculadoraTributaria.arredondar_valor(row.get("Custo NET", 0))
            custo_fixo = CalculadoraTributaria.arredondar_valor(row.get("Custo Fixo", 0))
            custo_total_unit = CalculadoraTributaria.arredondar_valor(custo_net + custo_fixo)
            custo_total = CalculadoraTributaria.arredondar_valor(custo_total_unit * qtd)

            # Frete
            frete_total = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0)) * qtd
            ) if self.tipo_frete == "CIF" else 0.0

            frete_unit = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0))
            ) if self.tipo_frete == "CIF" else 0.0

            # IPI
            ipi_percent = float(row.get("IPI", 0))
            ipi_total = CalculadoraTributaria.arredondar_valor(subtotal * ipi_percent)

            # Parâmetros ICMS-ST
            mva = float(row.get("MVA", 0))
            icms_interestadual = float(row.get("ICMS Interestadual", 0))
            icms_interno_destino = float(row.get("ICMS Interno Destino", 0))
            fcp_aliquota = float(row.get("FCP", 0))

            # Calcular ICMS-ST
            icms_st, base_icms_st, icms_proprio, icms_total_interno, fcp_valor = \
                CalculadoraTributaria.calcular_icms_st_completo(
                    valor_produto=subtotal,
                    ipi_valor=ipi_total,
                    mva=mva,
                    icms_interestadual=icms_interestadual,
                    icms_interno_destino=icms_interno_destino,
                    fcp_aliquota=fcp_aliquota
                )

            # Despesas operacionais
            despesas_operacionais = self._calcular_despesas_operacionais(row, subtotal)
            total_despesas_operacionais = despesas_operacionais

            # Lucro antes dos impostos sobre lucro
            lucro_antes_ir = CalculadoraTributaria.arredondar_valor(
                subtotal - custo_total - total_despesas_operacionais - frete_total
            )

            # Calcular IR e CSLL
            irpj, csll = self._calcular_ir_csll(lucro_antes_ir)

            # Lucro líquido
            lucro_liquido = CalculadoraTributaria.arredondar_valor(lucro_antes_ir - irpj - csll)

            # Margem calculada corretamente
            margem_antes_ir = CalculadoraTributaria.arredondar_valor(
                (lucro_antes_ir / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            margem_liquida = CalculadoraTributaria.arredondar_valor(
                (lucro_liquido / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            # Total NF
            total_nf = CalculadoraTributaria.arredondar_valor(subtotal + ipi_total + icms_st + fcp_valor)

            # Ponto de equilíbrio
            ponto_equilibrio = self._calcular_ponto_equilibrio(row, custo_total_unit, frete_unit)

            return pd.Series({
                "Preço Venda": preco_venda,
                "Qtd": qtd,
                "Custo NET": custo_net,
                "Custo Fixo": custo_fixo,
                "MVA": mva,
                "Comissão": float(row.get("Comissão", 0)),
                "Bonificação": float(row.get("Bonificação", 0)),
                "Subtotal": subtotal,
                "IPI": ipi_total,
                "Base ICMS-ST": base_icms_st,
                "ICMS Próprio": icms_proprio,
                "ICMS-ST": icms_st,
                "FCP": fcp_valor,
                "Total NF": total_nf,
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
            st.error(f"❌ Erro no cálculo do produto {row.get('Descrição', 'N/A')}: {str(e)}")
            return self._retornar_serie_vazia()

    def _calcular_despesas_operacionais(self, row: pd.Series, subtotal: float) -> float:
        """Calcula o total das despesas operacionais"""
        despesas = [
            "ICMS Interestadual", "COFINS", "PIS", "Comissão",
            "Bonificação", "Contigência", "Contrato", "%Estrategico"
        ]

        total = 0.0
        for despesa in despesas:
            percentual = float(row.get(despesa, 0))
            total += CalculadoraTributaria.arredondar_valor(subtotal * percentual)

        return total

    def _calcular_ir_csll(self, lucro_antes_ir: float) -> Tuple[float, float]:
        """Calcula IRPJ e CSLL"""
        if lucro_antes_ir <= 0:
            return 0.0, 0.0

        # IRPJ: 15% + 10% sobre o que exceder R$ 20.000/mês
        irpj = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.15)
        if lucro_antes_ir > 20000:
            adicional_irpj = CalculadoraTributaria.arredondar_valor((lucro_antes_ir - 20000) * 0.10)
            irpj += adicional_irpj

        # CSLL: 9%
        csll = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.09)

        return irpj, csll

    def _calcular_ponto_equilibrio(self, row: pd.Series, custo_total_unit: float, frete_unit: float) -> float:
        """Calcula o ponto de equilíbrio"""
        try:
            # Despesas diretas percentuais
            despesas_diretas = (
                float(row.get("ICMS Interestadual", 0)) +
                float(row.get("COFINS", 0)) +
                float(row.get("PIS", 0)) +
                float(row.get("Comissão", 0)) +
                float(row.get("Bonificação", 0)) +
                float(row.get("Contigência", 0)) +
                float(row.get("Contrato", 0)) +
                float(row.get("%Estrategico", 0))
            )

            if despesas_diretas >= 1.0:
                return 0.0

            # Cálculo básico
            ponto_equilibrio = (custo_total_unit + frete_unit) / (1 - despesas_diretas)
            return CalculadoraTributaria.arredondar_valor(ponto_equilibrio)

        except Exception:
            return 0.0

    def _retornar_serie_vazia(self) -> pd.Series:
        """Retorna uma série com valores zerados em caso de erro"""
        return pd.Series({
            "Preço Venda": 0, "Qtd": 0, "Custo NET": 0, "Custo Fixo": 0, "MVA": 0,
            "Comissão": 0, "Bonificação": 0, "Subtotal": 0, "IPI": 0, "Base ICMS-ST": 0,
            "ICMS Próprio": 0, "ICMS-ST": 0, "FCP": 0, "Total NF": 0, "Custo Total": 0,
            "Frete Total": 0, "Total Despesas": 0, "Lucro Antes IR": 0, "IRPJ": 0,
            "CSLL": 0, "Lucro Líquido": 0, "Margem Antes IR %": 0, "Margem Líquida %": 0,
            "Ponto Equilíbrio": 0
        })

class GerenciadorEstado:
    """Classe para gerenciar o estado da aplicação"""

    def __init__(self):
        self.inicializar_estado()

    def inicializar_estado(self):
        """Inicializa as variáveis de estado"""
        estados_default = {
            'df_atual': None,
            'modo_equilibrio': False,
            'comissao_global_aplicada': False,
            'comissoes_editadas': {},
            'bonificacoes_editadas': {},
            'valores_originais': {},
            'df_edicao_temp': None,
            'resultados_atualizados': False,
            'frete_calculado_automatico': 0.0,
            'distancia_calculada': None,
            'tempo_calculado': None,
            'usar_frete_auto': False,
            'coordenadas_origem': None,
            'coordenadas_destino': None,
            'resultado_frete_completo': None,
            'otimizacao_frete': None,
            'dados_carregados': False
        }

        for key, value in estados_default.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def resetar_estado(self):
        """Reseta o estado da aplicação"""
        for key in ['df_atual', 'modo_equilibrio', 'comissao_global_aplicada', 
                   'comissoes_editadas', 'bonificacoes_editadas', 'valores_originais',
                   'df_edicao_temp', 'resultados_atualizados']:
            if key in st.session_state:
                if key in ['comissoes_editadas', 'bonificacoes_editadas', 'valores_originais']:
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None if key == 'df_atual' or key == 'df_edicao_temp' else False

class SimuladorSobel:
    """Classe principal do simulador"""

    def __init__(self):
        self.config_tributaria = ConfiguracaoTributaria()
        self.gerenciador_estado = GerenciadorEstado()
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if self.api_key:
            self.geolocalizacao = GerenciadorGeolocalizacao(self.api_key)
        else:
            self.geolocalizacao = None
            st.warning("⚠️ Google Maps API não configurada. Funcionalidades de geolocalização desabilitadas.")

        # Configuração do banco de dados
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.0.16;"
            "DATABASE=Protheus_Producao;"
            "UID=sa;"
            "PWD=Totvs@452525!"
        )
        self.db_manager = GerenciadorBancoDados(connection_string)

        # Produtos esperados com normalização para comparação
        self.produtos_esperados = [
            "ÁGUA SANITÁRIA 5L", "ÁGUA SANITÁRIA 2L", "ÁGUA SANITÁRIA 1L",
            "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
            "AMACIANTE 5L", "AMACIANTE 2L",
            "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
            "LAVA LOUÇAS 500ML", "LAVA LOUÇAS 5L",
            "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
            "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
            "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
        ]
        
        # Criar versão normalizada para comparação
        self.produtos_esperados_normalizados = [normalizar_texto(produto) for produto in self.produtos_esperados]

        # Inicializar variáveis
        self.dados_cliente_selecionado = None
        self.frete_padrao_cliente = None
        self.faixas_km_ordenadas = []
        self.df_padrao = pd.DataFrame()
        self.contrato_real = None

    def executar(self):
        """Método principal para executar o simulador"""
        self._configurar_interface()
        
        # Verificar conexão com banco
        if not self._verificar_conexao_banco():
            return
            
        self._carregar_dados_iniciais()
        self._exibir_interface()

    def _configurar_interface(self):
        """Configura a interface do usuário"""
        # CSS customizado para melhorar a aparência
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e7cb8 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2e7cb8;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .success-card {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .warning-card {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-card {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header principal
        st.markdown("""
        <div class="main-header">
            <h1>📊 Simulador de Formação de Preço de Venda - Sobel v3.0</h1>
            <p>Sistema integrado de simulação com otimização de frete e geolocalização</p>
        </div>
        """, unsafe_allow_html=True)

        # Verificar se a imagem existe
        if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
            col_logo, col_space = st.columns([1, 3])
            with col_logo:
                st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=250)

    def _verificar_conexao_banco(self) -> bool:
        """Verifica se a conexão com o banco está funcionando"""
        try:
            with st.spinner("🔄 Verificando conexão com banco de dados..."):
                df_test = self.db_manager.carregar_clientes_ou_rede()
                if df_test.empty:
                    st.error("❌ Nenhum dado encontrado no banco. Verifique a conexão.")
                    return False
                st.success(f"✅ Banco conectado com sucesso! {len(df_test)} registros encontrados.")
                return True
        except Exception as e:
            st.error(f"❌ Erro de conexão com banco: {str(e)}")
            return False

    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais necessários"""
        # Carregar planilha padrão
        arquivo_padrao = "Custo de reposição.xlsx"
        if os.path.exists(arquivo_padrao):
            try:
                with st.spinner("📂 Carregando planilha de custos..."):
                    self.df_padrao = pd.read_excel(arquivo_padrao)
                    self.df_padrao.columns = self.df_padrao.columns.str.strip()
                    st.success(f"✅ Planilha carregada: {len(self.df_padrao)} produtos disponíveis")
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo padrão: {str(e)}")
                self.df_padrao = pd.DataFrame()
        else:
            st.warning("⚠️ Arquivo padrão 'Custo de reposição.xlsx' não encontrado.")
            self.df_padrao = pd.DataFrame()

        # Carregar faixas de KM
        self.faixas_km_ordenadas = self._extrair_faixas_ordenadas()

    def _extrair_faixas_ordenadas(self) -> list:
        """Extrai e ordena as faixas de KM disponíveis da base de clientes"""
        try:
            df_clientes = self.db_manager.carregar_clientes_ou_rede()
            if df_clientes.empty:
                return []
                
            faixas = []
            faixas_unicas = df_clientes['FAIXA_KM'].dropna().unique()

            for faixa in faixas_unicas:
                try:
                    faixa_str = str(faixa).strip()
                    if '+' in faixa_str:
                        ini = int(faixa_str.replace('+', '').strip())
                        faixas.append((ini, float('inf'), faixa_str))
                    elif '-' in faixa_str:
                        partes = faixa_str.split('-')
                        if len(partes) == 2:
                            ini, fim = int(partes[0].strip()), int(partes[1].strip())
                            faixas.append((ini, fim, faixa_str))
                    else:
                        valor = int(faixa_str)
                        faixas.append((valor, valor, faixa_str))
                except (ValueError, IndexError):
                    continue

            faixas.sort(key=lambda x: x[0])

            if faixas:
                st.info(f"🎯 Faixas de KM carregadas: {[f[2] for f in faixas[:5]]}{'...' if len(faixas) > 5 else ''}")

            return faixas
        except Exception as e:
            st.error(f"❌ Erro ao extrair faixas de frete: {e}")
            return []

    def _exibir_interface(self):
        """Exibe a interface principal"""
        # Verificar se há dados para continuar
        if self.df_padrao.empty:
            st.error("❌ Não é possível continuar sem dados. Carregue uma planilha de custos.")
            return

        # Usar tabs para melhor organização
        tab1, tab2, tab3 = st.tabs(["👤 Cliente & Parâmetros", "📊 Simulação", "📄 Relatórios"])

        with tab1:
            self._exibir_secao_cliente()
            st.markdown("---")
            self._exibir_secao_parametros()
            st.markdown("---")
            self._exibir_upload_arquivo()

        with tab2:
            if self._validar_dados():
                self._processar_simulacao()

        with tab3:
            self._exibir_relatorios()

    def _exibir_secao_cliente(self):
        """Exibe a seção de seleção de cliente melhorada"""
        st.markdown("### 👤 Seleção de Cliente")

        # Opção de cliente
        opcao_cliente = st.radio(
            "Como deseja proceder?", 
            ["🔍 Selecionar cliente existente", "➕ Cliente novo (sem histórico)"], 
            horizontal=True
        )

        self.contrato_real = None
        self.dados_cliente_selecionado = None

        if opcao_cliente == "🔍 Selecionar cliente existente":
            clientes_df = self.db_manager.carregar_clientes_ou_rede()
            
            if not clientes_df.empty:
                # Melhor interface de seleção
                col_search, col_filter = st.columns([3, 1])
                
                with col_search:
                    # Busca por nome
                    busca_nome = st.text_input("🔍 Buscar por nome do cliente", placeholder="Digite parte do nome...")
                
                with col_filter:
                    # Filtro por UF
                    ufs_disponiveis = ['Todos'] + sorted(clientes_df['A1_EST'].unique().tolist())
                    uf_filtro = st.selectbox("📍 Filtrar por UF", ufs_disponiveis)

                # Aplicar filtros
                df_filtrado = clientes_df.copy()
                
                if busca_nome:
                    df_filtrado = df_filtrado[
                        df_filtrado['A1_NOME'].str.contains(busca_nome, case=False, na=False)
                    ]
                
                if uf_filtro != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['A1_EST'] == uf_filtro]

                if not df_filtrado.empty:
                    # Criar opções mais informativas
                    opcoes_clientes = []
                    for idx, row in df_filtrado.iterrows():
                        opcao = f"{row['A1_NOME'][:50]} | {row['A1_MUN']}/{row['A1_EST']} | {row['A1_COD']}/{row['A1_LOJA']}"
                        if row['REDE'] and str(row['REDE']) != str(row['A1_NOME'])[:20]:
                            opcao += f" | [{row['REDE']}]"
                        opcoes_clientes.append(opcao)

                    cliente_escolhido_display = st.selectbox(
                        f"📋 Clientes encontrados ({len(df_filtrado)} registros):", 
                        opcoes_clientes,
                        help="Formato: Nome | Cidade/UF | Código/Loja | [Rede]"
                    )

                    # Encontrar o cliente selecionado
                    indice_selecionado = opcoes_clientes.index(cliente_escolhido_display)
                    self.dados_cliente_selecionado = df_filtrado.iloc[indice_selecionado]

                    # Exibir dados do cliente
                    self._exibir_dados_completos_cliente()

                    # Seção de cálculo de frete (se disponível)
                    if self.geolocalizacao:
                        self._exibir_secao_rota_integrada()
                else:
                    st.info("ℹ️ Nenhum cliente encontrado com os filtros aplicados.")
            else:
                st.warning("⚠️ Nenhum cliente encontrado na base de dados.")
        
        else:  # Cliente novo
            self._exibir_secao_cliente_novo()

    def _exibir_secao_cliente_novo(self):
        """Exibe seção para entrada manual de dados de cliente novo"""
        st.markdown("#### ➕ Dados do Cliente Novo")
        
        # Informações básicas
        col1, col2 = st.columns(2)
        
        with col1:
            nome_cliente_novo = st.text_input(
                "🏢 Nome/Razão Social", 
                placeholder="Digite o nome do cliente...",
                help="Nome para identificação nas análises"
            )
            
            uf_cliente_novo = st.selectbox(
                "📍 UF de Destino",
                options=['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
                help="Selecione o estado de destino"
            )
            
        with col2:
            cidade_cliente_novo = st.text_input(
                "🏙️ Cidade",
                placeholder="Nome da cidade...",
                help="Cidade de destino para cálculo de frete"
            )
            
            contrato_cliente_novo = st.number_input(
                "📄 % Contrato",
                min_value=0.0,
                max_value=100.0,
                value=1.00,
                step=0.01,
                help="Percentual de contrato para este cliente"
            )

        # Seção de endereço para frete
        if self.geolocalizacao:
            st.markdown("#### 🗺️ Endereço para Cálculo de Frete")
            
            col_end1, col_end2 = st.columns(2)
            
            with col_end1:
                endereco_cliente_novo = st.text_input(
                    "📍 Endereço Completo",
                    placeholder="Rua, número, bairro...",
                    help="Endereço mais completo possível para melhor precisão"
                )
                
            with col_end2:
                cep_cliente_novo = st.text_input(
                    "📮 CEP",
                    placeholder="00000-000",
                    help="CEP para maior precisão na localização",
                    max_chars=9
                )
            
            # Montar endereço completo
            if nome_cliente_novo and uf_cliente_novo:
                # Criar dados simulados do cliente novo
                endereco_completo_partes = []
                
                if endereco_cliente_novo:
                    endereco_completo_partes.append(endereco_cliente_novo)
                    
                if cidade_cliente_novo:
                    endereco_completo_partes.append(cidade_cliente_novo)
                    
                endereco_completo_partes.append(uf_cliente_novo)
                
                if cep_cliente_novo:
                    endereco_completo_partes.append(f"CEP {cep_cliente_novo}")
                    
                endereco_completo_partes.append("Brasil")
                
                endereco_completo = ", ".join(endereco_completo_partes)
                
                # Exibir endereço montado
                st.text_area(
                    "🎯 Endereço para Geocodificação",
                    endereco_completo,
                    height=80,
                    disabled=True,
                    help="Endereço que será usado para calcular distância e frete"
                )
                
                # Criar dados fictícios do cliente para uso no sistema
                self.dados_cliente_selecionado = pd.Series({
                    'A1_NOME': nome_cliente_novo,
                    'A1_EST': uf_cliente_novo,
                    'A1_MUN': cidade_cliente_novo or 'Não informado',
                    'A1_COD': 'NOVO',
                    'A1_LOJA': '01',
                    'A1_ZZCONTR': contrato_cliente_novo,
                    'A1_END': endereco_cliente_novo or 'Não informado',
                    'A1_CEP': cep_cliente_novo.replace('-', '') if cep_cliente_novo else '00000000',
                    'A1_BAIRRO': 'Não informado',
                    'cidade_ibge': '0000000',  # Será usado valor padrão para frete
                    'REDE': 'Cliente Novo',
                    'latitude': 0.0,
                    'longitude': 0.0
                })
                
                # Aplicar contrato
                self.contrato_real = contrato_cliente_novo
                
                # Exibir dados do cliente novo
                with st.expander("📋 Resumo do Cliente Novo", expanded=True):
                    col_res1, col_res2, col_res3 = st.columns(3)
                    
                    with col_res1:
                        st.metric("🏢 Cliente", nome_cliente_novo)
                        st.metric("📍 UF", uf_cliente_novo)
                        
                    with col_res2:
                        st.metric("🏙️ Cidade", cidade_cliente_novo or "Não informado")
                        st.metric("📄 Contrato", f"{contrato_cliente_novo:.2f}%")
                        
                    with col_res3:
                        st.info("💡 **Dica:** Complete o endereço para cálculo automático de frete")
                
                # Seção de cálculo de frete para cliente novo
                if endereco_cliente_novo or cep_cliente_novo:
                    self._exibir_secao_rota_cliente_novo(endereco_completo)
                else:
                    st.warning("⚠️ Preencha o endereço para habilitar o cálculo automático de frete")

    def _exibir_secao_rota_cliente_novo(self, endereco_destino: str):
        """Exibe seção de cálculo de rota para cliente novo"""
        with st.expander("🗺️ Cálculo de Frete para Cliente Novo", expanded=False):
            st.markdown("#### 🧭 Configuração de Rota")

            # Origens disponíveis
            origens = {
                "📍 Matriz (São Paulo - SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "📍 Filial (Atibaia - SP)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }

            col_origem, col_destino = st.columns(2)

            with col_origem:
                origem_opcao = st.selectbox("🚚 Unidade de Origem", list(origens.keys()), key="origem_cliente_novo")
                origem = origens[origem_opcao]
                st.text_area("📍 Endereço de Origem", origem, height=60, disabled=True)

            with col_destino:
                st.text_input("🎯 Cliente Novo", self.dados_cliente_selecionado['A1_NOME'], disabled=True)
                st.text_area("🎯 Endereço de Destino", endereco_destino, height=60, disabled=True)

            # Configurações de frete
            st.markdown("#### 🚛 Configuração de Frete")
            
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "🚚 Truck (870 caixas)" if x == "truck" else "🚛 Carreta (1.740 caixas)",
                    key="tipo_veiculo_cliente_novo"
                )
                
                if st.button("🗺️ Calcular Rota", type="primary", use_container_width=True, key="calc_rota_novo"):
                    self._calcular_frete_cliente_novo(origem, endereco_destino, tipo_veiculo)

            with col_frete2:
                # Resultados da rota
                if st.session_state.get('distancia_calculada_novo') and st.session_state.get('tempo_calculado_novo'):
                    st.success("✅ Rota Calculada")
                    st.metric("📏 Distância", st.session_state.get('distancia_calculada_novo'))
                    st.metric("⏱️ Tempo", st.session_state.get('tempo_calculado_novo'))
                else:
                    st.info("ℹ️ Clique em 'Calcular' para obter a rota")

            with col_frete3:
                # Frete calculado ou manual
                frete_calculado = st.session_state.get('frete_calculado_cliente_novo', 0.0)
                if frete_calculado > 0:
                    usar_frete_auto = st.checkbox("🤖 Usar frete calculado", value=True, key="usar_frete_auto_novo")
                    if usar_frete_auto:
                        self.frete_padrao_cliente = frete_calculado
                        st.success(f"💰 {formatar_moeda_brasileira(frete_calculado)}/caixa")
                    else:
                        self.frete_padrao_cliente = st.number_input(
                            "✏️ Frete Manual (R$)", 
                            min_value=0.0, 
                            value=1.50, 
                            step=0.01,
                            key="frete_manual_novo"
                        )
                else:
                    self.frete_padrao_cliente = st.number_input(
                        "✏️ Frete Manual (R$)", 
                        min_value=0.0, 
                        value=1.50, 
                        step=0.01,
                        key="frete_manual_novo_default"
                    )

            # Mostrar mapas se disponível
            if (st.session_state.get('coordenadas_origem_novo') and 
                st.session_state.get('coordenadas_destino_novo')):
                self._exibir_mapas_cliente_novo(origem)

    def _calcular_frete_cliente_novo(self, origem: str, endereco_destino: str, tipo_veiculo: str = "truck"):
        """Calcula frete para cliente novo baseado no endereço informado"""
        with st.spinner("🔄 Processando cálculo para cliente novo..."):
            # Geocodificar origem
            origem_coords = self.geolocalizacao.geocode(origem)
            if not origem_coords:
                st.error("❌ Não foi possível localizar o endereço de origem.")
                return

            # Geocodificar destino
            destino_coords = self.geolocalizacao.geocode(endereco_destino)
            if not destino_coords:
                st.error(f"❌ Não foi possível localizar o endereço: {endereco_destino}")
                st.info("💡 **Dicas para melhorar a localização:**")
                st.write("• Use endereços mais específicos (rua, número)")
                st.write("• Inclua o CEP sempre que possível")
                st.write("• Verifique a ortografia da cidade")
                return

            # Calcular distância e tempo
            distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)
            if erro:
                st.error(erro)
                return

            try:
                # Processar distância
                distancia_texto = distancia.replace('km', '').strip()
                
                # Converter para float tratando vírgulas
                if ',' in distancia_texto:
                    if '.' in distancia_texto:
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:
                        partes = distancia_texto.split(',')
                        if len(partes[1]) == 3:
                            distancia_km = float(distancia_texto.replace(',', ''))
                        else:
                            distancia_km = float(distancia_texto.replace(',', '.'))
                else:
                    distancia_km = float(distancia_texto)

                # Armazenar dados específicos para cliente novo
                st.session_state.distancia_calculada_novo = distancia
                st.session_state.tempo_calculado_novo = duracao
                st.session_state.coordenadas_origem_novo = origem_coords
                st.session_state.coordenadas_destino_novo = destino_coords

                # Para cliente novo, usar frete baseado em distância (sem tabela específica)
                # Implementar lógica de frete por distância
                frete_por_km = self._calcular_frete_por_distancia(distancia_km, tipo_veiculo)
                
                st.session_state.frete_calculado_cliente_novo = frete_por_km

                # Exibir resultados
                st.success(f"""
                ✅ **Rota Calculada para Cliente Novo!**
                
                📏 **Distância:** {distancia} ({duracao}) → {distancia_km:.0f} km
                🚛 **Veículo:** {tipo_veiculo.upper()}
                💰 **Frete Estimado:** {formatar_moeda_brasileira(frete_por_km)}/caixa
                """)

                st.info("💡 **Frete Calculado por Distância:** Para clientes novos, o frete é estimado baseado na distância e tipo de veículo")

            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")

    def _calcular_frete_por_distancia(self, distancia_km: float, tipo_veiculo: str) -> float:
        """Calcula frete baseado na distância para clientes novos"""
        
        # Faixas de distância e valores base
        faixas_frete = [
            (0, 50, {"truck": 1.20, "carreta": 0.85}),
            (50, 100, {"truck": 1.50, "carreta": 1.10}),
            (100, 200, {"truck": 1.80, "carreta": 1.35}),
            (200, 300, {"truck": 2.10, "carreta": 1.60}),
            (300, 500, {"truck": 2.40, "carreta": 1.85}),
            (500, 800, {"truck": 2.70, "carreta": 2.10}),
            (800, 1200, {"truck": 3.00, "carreta": 2.35}),
            (1200, float('inf'), {"truck": 3.50, "carreta": 2.80})
        ]
        
        # Encontrar faixa correspondente
        for ini, fim, valores in faixas_frete:
            if ini <= distancia_km < fim:
                frete_base = valores.get(tipo_veiculo, valores["truck"])
                
                # Ajuste progressivo dentro da faixa
                if fim != float('inf'):
                    faixa_size = fim - ini
                    posicao_na_faixa = (distancia_km - ini) / faixa_size
                    
                    # Encontrar próxima faixa para interpolação
                    proximo_valor = frete_base
                    for next_ini, next_fim, next_valores in faixas_frete:
                        if next_ini == fim:
                            proximo_valor = next_valores.get(tipo_veiculo, next_valores["truck"])
                            break
                    
                    # Interpolação linear
                    frete_ajustado = frete_base + (proximo_valor - frete_base) * posicao_na_faixa * 0.3
                    return round(frete_ajustado, 2)
                else:
                    return frete_base
        
        # Fallback para distâncias muito pequenas
        return 1.50 if tipo_veiculo == "truck" else 1.10

    def _exibir_mapas_cliente_novo(self, origem: str):
        """Exibe mapas para cliente novo"""
        origem_coords = st.session_state.get('coordenadas_origem_novo')
        destino_coords = st.session_state.get('coordenadas_destino_novo')

        if not origem_coords or not destino_coords:
            return

        st.markdown("#### 🗺️ Visualização da Rota")
        
        col_mapa, col_street = st.columns(2)

        with col_mapa:
            st.markdown("**📍 Mapa com Rota**")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

        with col_street:
            st.markdown("**🚦 Street View - Destino**")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

    def _exibir_dados_completos_cliente(self):
        """Exibe dados completos do cliente de forma mais organizada"""
        st.markdown("#### 📋 Informações do Cliente Selecionado")

        cliente_dict = self.dados_cliente_selecionado.to_dict()

        # Card principal com informações básicas
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🏢 Razão Social", 
                    value=cliente_dict.get('A1_NOME', 'N/A')[:30] + ('...' if len(str(cliente_dict.get('A1_NOME', ''))) > 30 else ''),
                    help=cliente_dict.get('A1_NOME', 'N/A')
                )
                
            with col2:
                codigo = cliente_dict.get('A1_COD', '')
                loja = cliente_dict.get('A1_LOJA', '')
                st.metric("🏷️ Código/Loja", f"{codigo}/{loja}")
                
            with col3:
                uf = cliente_dict.get('A1_EST', 'N/A')
                cidade = cliente_dict.get('A1_MUN', 'N/A')
                st.metric("📍 Localização", f"{cidade}/{uf}")
                
            with col4:
                try:
                    contrato_valor = float(cliente_dict.get("A1_ZZCONTR", 0) or 0)
                    self.contrato_real = contrato_valor
                except:
                    self.contrato_real = 0.0
                    contrato_valor = 0.0
                st.metric("📄 Contrato", f"{contrato_valor:.2f}%")

        # Informações detalhadas em expander
        with st.expander("📄 Detalhes Completos", expanded=False):
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                # Endereço
                endereco_parts = []
                if cliente_dict.get('A1_END'):
                    endereco_parts.append(cliente_dict['A1_END'])
                if cliente_dict.get('A1_BAIRRO'):
                    endereco_parts.append(cliente_dict['A1_BAIRRO'])
                if cliente_dict.get('A1_MUN') and cliente_dict.get('A1_EST'):
                    endereco_parts.append(f"{cliente_dict['A1_MUN']}/{cliente_dict['A1_EST']}")
                
                cep = cliente_dict.get('A1_CEP', '')
                if cep and len(cep) == 8:
                    cep_formatado = f"{cep[:5]}-{cep[5:]}"
                    endereco_parts.append(f"CEP: {cep_formatado}")
                
                endereco_completo = '\n'.join(endereco_parts) if endereco_parts else "Não informado"
                st.text_area("📍 Endereço Completo", endereco_completo, height=100, disabled=True)
                
            with col_det2:
                # Informações financeiras
                try:
                    lc_value = float(cliente_dict.get('A1_LC', 0) or 0)
                    lc_text = f"R$ {lc_value:,.2f}" if lc_value > 0 else "Não definido"
                except:
                    lc_text = "Não definido"
                
                st.text_input("💳 Limite de Crédito", lc_text, disabled=True)
                st.text_input("⚠️ Classificação de Risco", cliente_dict.get('A1_RISCO', 'N/A'), disabled=True)
                
                # Rede se houver
                rede = cliente_dict.get('REDE', '')
                nome_resumo = str(cliente_dict.get('A1_NOME', ''))[:20]
                if rede and rede != nome_resumo:
                    st.text_input("🏪 Rede", rede, disabled=True)

    def _exibir_secao_rota_integrada(self):
        """Exibe seção de cálculo de rota melhorada"""
        with st.expander("🗺️ Cálculo de Frete e Rota", expanded=False):
            st.markdown("#### 🧭 Configuração de Rota")

            # Origens disponíveis
            origens = {
                "📍 Matriz (São Paulo - SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "📍 Filial (Atibaia - SP)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }

            col_origem, col_destino = st.columns(2)

            with col_origem:
                origem_opcao = st.selectbox("🚚 Unidade de Origem", list(origens.keys()))
                origem = origens[origem_opcao]
                st.text_area("📍 Endereço de Origem", origem, height=60, disabled=True)

            with col_destino:
                # Informações do cliente
                cliente_info = f"{self.dados_cliente_selecionado['A1_NOME'][:30]}..."
                st.text_input("🎯 Cliente Selecionado", cliente_info, disabled=True)
                
                # Endereço para geocodificação
                endereco_destino = self._montar_endereco_completo_para_geocode(
                    self.dados_cliente_selecionado.to_dict()
                )
                st.text_area("🎯 Endereço de Destino", endereco_destino, height=60, disabled=True)

            # Configurações de frete
            st.markdown("#### 🚛 Configuração de Frete")
            
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "🚚 Truck (870 caixas)" if x == "truck" else "🚛 Carreta (1.740 caixas)"
                )
                
                if st.button("🗺️ Calcular Rota e Frete", type="primary", use_container_width=True):
                    self._calcular_frete_automatico(origem, tipo_veiculo)

            with col_frete2:
                # Resultados da rota
                if st.session_state.get('distancia_calculada') and st.session_state.get('tempo_calculado'):
                    st.success("✅ Rota Calculada")
                    st.metric("📏 Distância", st.session_state.get('distancia_calculada'))
                    st.metric("⏱️ Tempo", st.session_state.get('tempo_calculado'))
                else:
                    st.info("ℹ️ Clique em 'Calcular' para obter a rota")

            with col_frete3:
                # Frete calculado ou manual
                frete_calculado = st.session_state.get('frete_calculado_automatico', 0.0)
                if frete_calculado > 0:
                    usar_frete_auto = st.checkbox("🤖 Usar frete calculado", value=True)
                    if usar_frete_auto:
                        self.frete_padrao_cliente = frete_calculado
                        st.success(f"💰 R$ {frete_calculado:.2f}/caixa")
                    else:
                        self.frete_padrao_cliente = st.number_input(
                            "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                        )
                else:
                    self.frete_padrao_cliente = st.number_input(
                        "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                    )

            # Mostrar mapas se disponível
            if (st.session_state.get('coordenadas_origem') and 
                st.session_state.get('coordenadas_destino')):
                self._exibir_mapas_cliente(origem)

    def _montar_endereco_completo_para_geocode(self, cliente_dict: dict) -> str:
        """Monta endereço otimizado para geocodificação"""
        partes_endereco = []

        def safe_str(value):
            if value is None or pd.isna(value):
                return ""
            return str(value).strip()

        # Componentes do endereço
        endereco_rua = safe_str(cliente_dict.get('A1_END', ''))
        if endereco_rua and endereco_rua.lower() != 'não informado':
            partes_endereco.append(endereco_rua)

        bairro = safe_str(cliente_dict.get('A1_BAIRRO', ''))
        if bairro and bairro.lower() not in ['', 'não informado']:
            partes_endereco.append(bairro)

        cidade = safe_str(cliente_dict.get('A1_MUN', ''))
        if cidade:
            partes_endereco.append(cidade)

        uf = safe_str(cliente_dict.get('A1_EST', ''))
        if uf:
            partes_endereco.append(uf)

        cep = safe_str(cliente_dict.get('A1_CEP', ''))
        if cep and cep not in ['N/A', '0'] and len(cep) >= 8:
            if len(cep) == 8 and cep.isdigit():
                cep_formatado = f"{cep[:5]}-{cep[5:]}"
                partes_endereco.append(f"CEP {cep_formatado}")
            else:
                partes_endereco.append(f"CEP {cep}")

        partes_endereco.append("Brasil")
        return ", ".join(partes_endereco)

    def _calcular_frete_automatico(self, origem: str, tipo_veiculo: str = "truck"):
        """Calcula frete automaticamente baseado na distância real"""
        with st.spinner("🔄 Processando cálculo de frete..."):
            # Geocodificar origem
            origem_coords = self.geolocalizacao.geocode(origem)
            if not origem_coords:
                st.error("❌ Não foi possível localizar o endereço de origem.")
                return

            # Geocodificar destino
            cliente_dict = self.dados_cliente_selecionado.to_dict()
            endereco_destino_completo = self._montar_endereco_completo_para_geocode(cliente_dict)
            destino_coords = self.geolocalizacao.geocode(endereco_destino_completo)

            if not destino_coords:
                # Fallback para coordenadas do banco
                try:
                    lat_banco = float(self.dados_cliente_selecionado["latitude"])
                    lng_banco = float(self.dados_cliente_selecionado["longitude"])
                    if lat_banco != 0 and lng_banco != 0:
                        destino_coords = (lat_banco, lng_banco)
                        st.warning("⚠️ Usando coordenadas do banco como fallback.")
                    else:
                        st.error("❌ Não foi possível localizar o endereço de destino.")
                        return
                except:
                    st.error("❌ Endereço não encontrado e coordenadas do banco indisponíveis.")
                    return

            # Calcular distância e tempo
            distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)
            if erro:
                st.error(erro)
                return

            try:
                # Processar distância
                distancia_texto = distancia.replace('km', '').strip()
                
                # Converter para float tratando vírgulas
                if ',' in distancia_texto:
                    if '.' in distancia_texto:
                        # Formato: "1,159.5" - vírgula = milhares, ponto = decimal
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:
                        # Verificar se vírgula é separador de milhares ou decimal
                        partes = distancia_texto.split(',')
                        if len(partes[1]) == 3:  # "1,159" - milhares
                            distancia_km = float(distancia_texto.replace(',', ''))
                        else:  # "1,5" - decimal
                            distancia_km = float(distancia_texto.replace(',', '.'))
                else:
                    distancia_km = float(distancia_texto)

                # Armazenar dados no session state
                st.session_state.distancia_calculada = distancia
                st.session_state.tempo_calculado = duracao
                st.session_state.coordenadas_origem = origem_coords
                st.session_state.coordenadas_destino = destino_coords

                # Obter faixa de KM e código IBGE
                faixa_km = obter_faixa_km_exata(distancia_km, self.faixas_km_ordenadas)
                cidade_ibge = str(self.dados_cliente_selecionado["cidade_ibge"])

                # Buscar valores de frete
                df_clientes_frete = self.db_manager.carregar_clientes_ou_rede()
                resultado_frete = buscar_frete_inteligente(df_clientes_frete, cidade_ibge, faixa_km)

                # Calcular otimização (volume estimado inicial)
                volume_estimado = 500
                otimizacao = calcular_frete_otimizado(resultado_frete, volume_estimado)

                # Armazenar resultados
                st.session_state.frete_calculado_automatico = otimizacao['frete_por_caixa']
                st.session_state.tipo_veiculo_usado = otimizacao['veiculo_otimo']
                st.session_state.resultado_frete_completo = resultado_frete
                st.session_state.otimizacao_frete = otimizacao

                # Exibir resultados
                if otimizacao['frete_por_caixa'] > 0:
                    st.success(f"""
                    ✅ **Cálculo Concluído com Sucesso!**
                    
                    📏 **Rota:** {distancia} ({duracao}) → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💰 **Frete/Caixa:** {formatar_moeda_brasileira(otimizacao['frete_por_caixa'])}
                    🚛 **Veículo Otimizado:** {otimizacao['veiculo_otimo'].upper()}
                    """)

                    # Alerta de otimização
                    if otimizacao['alerta']:
                        if 'OTIMIZAÇÃO' in otimizacao['alerta']:
                            st.success(f"🎯 {otimizacao['alerta']}")
                        elif 'MÚLTIPLOS' in otimizacao['alerta']:
                            st.warning(f"📦 {otimizacao['alerta']}")
                        else:
                            st.info(f"ℹ️ {otimizacao['alerta']}")

                    # Tabela de comparação
                    self._exibir_comparacao_fretes(resultado_frete)
                else:
                    st.warning(f"""
                    ⚠️ **Rota calculada, mas frete não encontrado**
                    
                    📏 **Distância:** {distancia} → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💡 **Sugestão:** Use frete manual
                    """)

            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")

    def _exibir_comparacao_fretes(self, resultado_frete: dict):
        """Exibe tabela de comparação de fretes"""
        st.markdown("#### 📊 Comparação de Fretes Disponíveis")

        truck_info = resultado_frete['truck']
        carreta_info = resultado_frete['carreta']

        comparacao_data = []
        
        if truck_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚚 Truck',
                'Capacidade': '870 caixas',
                'Frete Total': formatar_moeda_brasileira(truck_info['valor']),
                'Frete/Caixa': formatar_moeda_brasileira(truck_info['valor']/870),
                'Método de Busca': truck_info['metodo'],
                'Faixa Utilizada': truck_info['faixa_usada']
            })

        if carreta_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚛 Carreta',
                'Capacidade': '1.740 caixas',
                'Frete Total': formatar_moeda_brasileira(carreta_info['valor']),
                'Frete/Caixa': formatar_moeda_brasileira(carreta_info['valor']/1740),
                'Método de Busca': carreta_info['metodo'],
                'Faixa Utilizada': carreta_info['faixa_usada']
            })

        if comparacao_data:
            df_comparacao = pd.DataFrame(comparacao_data)
            st.dataframe(df_comparacao, use_container_width=True, hide_index=True)
            st.info("💡 **Dica:** O frete será otimizado automaticamente quando você definir as quantidades!")

    def _exibir_mapas_cliente(self, origem: str):
        """Exibe mapas interativos"""
        origem_coords = st.session_state.get('coordenadas_origem')
        destino_coords = st.session_state.get('coordenadas_destino')

        if not origem_coords or not destino_coords:
            return

        st.markdown("#### 🗺️ Visualização da Rota")
        
        col_mapa, col_street = st.columns(2)

        with col_mapa:
            st.markdown("**📍 Mapa com Rota**")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

        with col_street:
            st.markdown("**🚦 Street View - Destino**")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

    def _exibir_secao_parametros(self):
        """Exibe seção de parâmetros melhorada"""
        st.markdown("### ⚙️ Parâmetros de Simulação")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🏭 Origem")
            st.info("**São Paulo - SP** (Fixo)")
            
            # Frete
            if hasattr(self, 'frete_padrao_cliente') and self.frete_padrao_cliente is not None:
                st.success(f"🚛 **Frete:** {formatar_moeda_brasileira(self.frete_padrao_cliente)}/caixa")
                st.caption("Definido pela seleção do cliente")
                self.frete_padrao = self.frete_padrao_cliente
            else:
                self.frete_padrao = st.number_input(
                    "🚛 Frete/Caixa (R$)", 
                    min_value=0.0, 
                    value=1.50, 
                    step=0.01,
                    help="Frete padrão para cliente novo"
                )

            # Tipo de frete
            self.tipo_frete = st.radio(
                "📦 Tipo de Frete", 
                ("CIF", "FOB"),
                help="CIF: Vendedor paga frete | FOB: Comprador paga frete"
            )

        with col2:
            st.markdown("#### 📍 Destino")
            
            # UF de destino
            opcoes_uf = self.df_padrao["UF"].dropna().unique().tolist() if not self.df_padrao.empty else []
            
            if self.dados_cliente_selecionado is not None:
                uf_cliente = self.dados_cliente_selecionado['A1_EST']
                if uf_cliente in opcoes_uf:
                    index_uf = opcoes_uf.index(uf_cliente)
                    self.uf_selecionado = st.selectbox(
                        "🗺️ UF de Destino", 
                        options=opcoes_uf, 
                        index=index_uf,
                        help="UF do cliente selecionado"
                    )
                else:
                    st.error(f"❌ UF do cliente ({uf_cliente}) não encontrada na planilha!")
                    self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)
            else:
                self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)

            # Contrato
            if self.contrato_real is not None:
                st.success(f"📄 **Contrato:** {formatar_percentual_brasileiro(self.contrato_real)}")
                st.caption("Valor real do cliente")
                self.contrato_percentual = self.contrato_real / 100
            else:
                contrato_input = st.number_input(
                    "📄 % Contrato", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=1.00, 
                    step=0.01
                )
                self.contrato_percentual = contrato_input / 100

        with col3:
            st.markdown("#### 💰 Parâmetros Globais")
            
            self.custo_fixo_global = st.number_input(
                "🏗️ Custo Fixo Global (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            
            comissao_input = st.number_input(
                "🤝 % Comissão Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.1,
                help="Se zero, usa valor da planilha"
            )
            self.comissao_padrao = comissao_input / 100

            bonificacao_input = st.number_input(
                "🎁 % Bonificação Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            self.bonificacao_global = bonificacao_input / 100

        # Mostrar informações tributárias
        if self.uf_selecionado:
            st.markdown("#### 📋 Informações Tributárias")
            aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
            aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

            col_trib1, col_trib2, col_trib3 = st.columns(3)
            
            with col_trib1:
                st.metric("🏛️ ICMS Interestadual", formatar_percentual_brasileiro(aliquotas_origem['interestadual'] * 100))
            
            with col_trib2:
                st.metric("🏛️ ICMS Interno", formatar_percentual_brasileiro(aliquotas_destino['interna'] * 100))
            
            with col_trib3:
                if aliquotas_destino['fcp'] > 0:
                    st.metric("📊 FCP", formatar_percentual_brasileiro(aliquotas_destino['fcp'] * 100))
                else:
                    st.metric("📊 FCP", "Não aplicável")

    def _exibir_upload_arquivo(self):
        """Seção de upload melhorada"""
        st.markdown("### 📂 Gestão de Arquivos")
        
        col_upload, col_info = st.columns([2, 1])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "📊 Atualizar planilha de custos (.xlsx)", 
                type="xlsx",
                help="Substitui o arquivo 'Custo de reposição.xlsx'"
            )

            if uploaded_file:
                if st.button("🔄 Confirmar Atualização", type="primary"):
                    try:
                        with st.spinner("📤 Processando upload..."):
                            arquivo_padrao = "Custo de reposição.xlsx"

                            # Criar backup
                            if os.path.exists(arquivo_padrao):
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
                                os.rename(arquivo_padrao, backup_name)
                                st.success(f"✅ Backup criado: {backup_name}")

                            # Salvar novo arquivo
                            with open(arquivo_padrao, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Recarregar dados
                            self.df_padrao = pd.read_excel(arquivo_padrao)
                            self.df_padrao.columns = self.df_padrao.columns.str.strip()

                            # Resetar estado
                            self.gerenciador_estado.resetar_estado()
                            
                            st.success("✅ Arquivo atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        
        with col_info:
            # Informações sobre o arquivo atual
            if not self.df_padrao.empty:
                st.info(f"""
                **📋 Arquivo Atual:**
                - Produtos: {len(self.df_padrao)}
                - UFs: {len(self.df_padrao['UF'].unique()) if 'UF' in self.df_padrao.columns else 0}
                """)
            else:
                st.warning("⚠️ Nenhum arquivo carregado")

    def _validar_dados(self) -> bool:
        """Validação melhorada dos dados"""
        if self.df_padrao.empty:
            st.error("❌ Carregue uma planilha de custos para continuar.")
            return False
            
        if not self.uf_selecionado:
            st.warning("⚠️ Selecione uma UF de destino.")
            return False
            
        return True

    def _processar_simulacao(self):
        """Processa a simulação principal"""
        st.markdown("### 📊 Simulação de Preços")
        
        # Preparar dados base
        df_base = self._preparar_dados_base()

        if df_base.empty:
            st.error(f"❌ Nenhum produto encontrado para a UF {self.uf_selecionado}")
            return

        # Exibir controles
        self._exibir_controles(df_base)

        # Processar edição e resultados
        self._processar_edicao_e_resultados(df_base)

    def _preparar_dados_base(self) -> pd.DataFrame:
        """Prepara dados base com melhor tratamento de acentuação"""
        # Filtrar por UF
        df_base = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado].copy()

        # Resetar se mudou UF
        if (st.session_state.df_atual is not None and 
            "UF" in st.session_state.df_atual.columns):
            ufs_atuais = st.session_state.df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != self.uf_selecionado:
                self.gerenciador_estado.resetar_estado()

        # CORREÇÃO: Filtrar produtos com normalização de acentos
        if not df_base.empty and "Descrição" in df_base.columns:
            # Criar coluna temporária com descrições normalizadas
            df_base['Descricao_Normalizada'] = df_base['Descrição'].apply(normalizar_texto)
            
            # Filtrar usando versões normalizadas
            mask_produtos = df_base['Descricao_Normalizada'].isin(self.produtos_esperados_normalizados)
            df_base = df_base[mask_produtos].copy()
            
            # Remover coluna temporária
            df_base = df_base.drop('Descricao_Normalizada', axis=1)
            
            # Debug: mostrar produtos encontrados
            if not df_base.empty:
                st.success(f"✅ {len(df_base)} produtos encontrados para {self.uf_selecionado}")
                produtos_encontrados = df_base['Descrição'].tolist()
                with st.expander(f"📋 Produtos carregados ({len(produtos_encontrados)})", expanded=False):
                    for produto in produtos_encontrados:
                        st.write(f"• {produto}")
            else:
                st.warning(f"⚠️ Nenhum produto encontrado para {self.uf_selecionado}")
                
                # Debug: mostrar produtos disponíveis na planilha
                if "Descrição" in self.df_padrao.columns:
                    produtos_planilha = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado]["Descrição"].unique()
                    st.info(f"Produtos disponíveis na planilha para {self.uf_selecionado}:")
                    for produto in produtos_planilha[:10]:  # Mostrar apenas os primeiros 10
                        st.write(f"• {produto}")

        # Ajustar colunas e aplicar parâmetros
        df_base = self._ajustar_colunas_necessarias(df_base)
        df_base = self._aplicar_parametros_globais(df_base)

        return df_base

    def _ajustar_colunas_necessarias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta colunas com melhor tratamento de valores padrão"""
        colunas_necessarias = [
            "Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", 
            "ICMS ST", "ICMS", "MVA", "Comissão", "Bonificação", "COFINS", "PIS", 
            "Contigência", "ICMS Interestadual", "ICMS Interno Destino", "FCP"
        ]

        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        for col in colunas_necessarias:
            if col not in df.columns:
                if col == "Quantidade":
                    df[col] = 1
                elif col == "ICMS Interestadual":
                    df[col] = aliquotas_origem['interestadual']
                elif col == "ICMS Interno Destino":
                    df[col] = aliquotas_destino['interna']
                elif col == "FCP":
                    df[col] = aliquotas_destino['fcp']
                else:
                    df[col] = 0.0

        return df

    def _aplicar_parametros_globais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica parâmetros globais com melhor organização"""
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        # Aplicar valores básicos
        df["Frete Caixa"] = self.frete_padrao
        df["Contrato"] = self.contrato_percentual
        df["UF Origem"] = 'SP'
        df["UF Destino"] = self.uf_selecionado
        df["ICMS Interestadual"] = aliquotas_origem['interestadual']
        df["ICMS Interno Destino"] = aliquotas_destino['interna']
        df["FCP"] = aliquotas_destino['fcp']

        # Aplicar parâmetros condicionais
        if self.custo_fixo_global > 0:
            df["Custo Fixo"] = self.custo_fixo_global

        if self.comissao_padrao > 0:
            df["Comissão"] = self.comissao_padrao
            st.session_state.comissao_global_aplicada = True
        else:
            st.session_state.comissao_global_aplicada = False

        if self.bonificacao_global > 0:
            df["Bonificação"] = self.bonificacao_global

        return df

    def _exibir_controles(self, df_base: pd.DataFrame):
        """Controles principais melhorados"""
        st.markdown("#### 🎯 Ações Principais")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⚖️ Calcular Ponto de Equilíbrio", use_container_width=True, type="primary"):
                with st.spinner("⚖️ Calculando pontos de equilíbrio..."):
                    df_equilibrio, alertas = self._calcular_ponto_equilibrio(df_base)

                    if alertas:
                        for alerta in alertas:
                            st.warning(f"⚠️ {alerta}")

                    st.session_state.df_atual = df_equilibrio.copy()
                    st.session_state.modo_equilibrio = True
                    st.success("✅ Pontos de equilíbrio calculados!")

        with col2:
            if st.button("🔄 Resetar Simulação", use_container_width=True):
                self.gerenciador_estado.resetar_estado()
                st.success("✅ Dados resetados.")
                time.sleep(1)
                st.rerun()

        with col3:
            # Informações rápidas
            if not df_base.empty:
                st.metric("📦 Produtos", len(df_base))

    def _calcular_ponto_equilibrio(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """Cálculo melhorado do ponto de equilíbrio"""
        df_resultado = df.copy()
        alertas = []

        for index, row in df_resultado.iterrows():
            try:
                # Custos base
                custo_net = float(row.get("Custo NET", 0))
                custo_fixo = float(row.get("Custo Fixo", 0))
                custo_total_unit = custo_net + custo_fixo
                frete_unit = float(row.get("Frete Caixa", 0)) if self.tipo_frete == "CIF" else 0.0

                # Despesas percentuais
                despesas_diretas = (
                    float(row.get("ICMS Interestadual", 0)) +
                    float(row.get("COFINS", 0)) +
                    float(row.get("PIS", 0)) +
                    float(row.get("Comissão", 0)) +
                    float(row.get("Bonificação", 0)) +
                    float(row.get("Contigência", 0)) +
                    float(row.get("Contrato", 0)) +
                    float(row.get("%Estrategico", 0))
                )

                # Verificar viabilidade
                if despesas_diretas >= 1.0:
                    produto_nome = row.get('Descrição', f'Produto {index}')
                    alertas.append(f"{produto_nome}: Despesas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    custos_totais = custo_total_unit + frete_unit
                    preco_equilibrio = custos_totais / (1 - despesas_diretas)
                    preco_equilibrio = max(0.0, CalculadoraTributaria.arredondar_valor(preco_equilibrio, 2))

                df_resultado.at[index, "Preço de Venda"] = preco_equilibrio

            except Exception as e:
                produto_nome = row.get('Descrição', f'Produto {index}')
                alertas.append(f"Erro em {produto_nome}: {str(e)}")
                df_resultado.at[index, "Preço de Venda"] = 0.0

        return df_resultado, alertas

    def _processar_edicao_e_resultados(self, df_base: pd.DataFrame):
        """Processamento melhorado de edição e resultados"""
        # Determinar DataFrame
        if st.session_state.df_atual is not None:
            df_para_edicao = st.session_state.df_atual.copy()
        else:
            df_para_edicao = df_base.copy()

        # Aplicar lógica de comissão/bonificação
        df_para_edicao = self._aplicar_logica_comissao_bonificacao(df_para_edicao)

        # Exibir status e resumos
        self._exibir_status_melhorado()
        self._exibir_resumo_edicoes()

        # Editor de dados
        df_editado = self._exibir_editor_dados_melhorado(df_para_edicao)

        # Processar edições
        df_final = self._processar_dados_editados(df_editado, df_para_edicao)

        # Calcular e exibir resultados
        self._calcular_e_exibir_resultados(df_final)

    def _aplicar_logica_comissao_bonificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica lógica melhorada de comissão e bonificação"""
        df_temp = df.copy()

        # Garantir colunas numéricas
        for col in ["Comissão", "Bonificação"]:
            if col not in df_temp.columns:
                df_temp[col] = 0.0
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0.0)

        # Armazenar valores originais
        if not st.session_state.valores_originais:
            for index in df_temp.index:
                produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
                st.session_state.valores_originais[produto] = {
                    'comissao': float(df_temp.at[index, "Comissão"]),
                    'bonificacao': float(df_temp.at[index, "Bonificação"])
                }

        # Aplicar valores globais se não editados individualmente
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)

            # Comissão global
            if (st.session_state.comissao_global_aplicada and 
                self.comissao_padrao > 0 and 
                produto not in st.session_state.comissoes_editadas):
                df_temp.at[index, "Comissão"] = float(self.comissao_padrao)

            # Bonificação global
            if (self.bonificacao_global > 0 and 
                produto not in st.session_state.bonificacoes_editadas):
                df_temp.at[index, "Bonificação"] = float(self.bonificacao_global)

        # Aplicar edições individuais (prioridade máxima)
        for produto, valor in st.session_state.comissoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Comissão"] = float(valor)

        for produto, valor in st.session_state.bonificacoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Bonificação"] = float(valor)

        return df_temp

    def _exibir_status_melhorado(self):
        """Status melhorado da simulação"""
        # Card de status principal
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.metric("🗺️ Rota", f"SP → {self.uf_selecionado}")
            
        with col_status2:
            modo = "🔒 Equilíbrio" if st.session_state.modo_equilibrio else "📋 Normal"
            st.metric("⚙️ Modo", modo)
            
        with col_status3:
            frete_info = f"R$ {self.frete_padrao:.2f}" if hasattr(self, 'frete_padrao') else "N/A"
            st.metric("🚛 Frete/Caixa", frete_info)

        # Parâmetros ativos
        parametros_ativos = []
        if st.session_state.comissao_global_aplicada and self.comissao_padrao > 0:
            parametros_ativos.append(f"Comissão Global: {self.comissao_padrao:.1%}")
        if self.bonificacao_global > 0:
            parametros_ativos.append(f"Bonificação Global: {self.bonificacao_global:.1%}")

        if parametros_ativos:
            st.info(f"🎯 **Parâmetros Ativos:** {' | '.join(parametros_ativos)}")

        # Edições individuais
        edicoes = []
        if st.session_state.comissoes_editadas:
            edicoes.append(f"Comissões editadas: {len(st.session_state.comissoes_editadas)}")
        if st.session_state.bonificacoes_editadas:
            edicoes.append(f"Bonificações editadas: {len(st.session_state.bonificacoes_editadas)}")

        if edicoes:
            st.success(f"✏️ **Edições Individuais:** {' | '.join(edicoes)}")

    def _exibir_resumo_edicoes(self):
        """Resumo melhorado das edições"""
        if st.session_state.comissoes_editadas or st.session_state.bonificacoes_editadas:
            with st.expander("🎯 Detalhes das Edições Individuais", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🤝 Comissões Personalizadas:**")
                    if st.session_state.comissoes_editadas:
                        for produto, valor in st.session_state.comissoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('comissao', 0)
                            global_val = self.comissao_padrao if self.comissao_padrao > 0 else original
                            st.write(f"• {produto}: {formatar_percentual_brasileiro(valor * 100)} (era {formatar_percentual_brasileiro(global_val * 100)})")
                        
                        if st.button("🗑️ Limpar Comissões", key="clear_comissoes"):
                            st.session_state.comissoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma comissão editada")

                with col2:
                    st.markdown("**🎁 Bonificações Personalizadas:**")
                    if st.session_state.bonificacoes_editadas:
                        for produto, valor in st.session_state.bonificacoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('bonificacao', 0)
                            global_val = self.bonificacao_global if self.bonificacao_global > 0 else original
                            st.write(f"• {produto}: {formatar_percentual_brasileiro(valor * 100)} (era {formatar_percentual_brasileiro(global_val * 100)})")
                        
                        if st.button("🗑️ Limpar Bonificações", key="clear_bonificacoes"):
                            st.session_state.bonificacoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma bonificação editada")

    def _exibir_editor_dados_melhorado(self, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Editor de dados melhorado"""
        st.markdown("#### 📊 Editor de Dados da Simulação")

        # Preparar dados para edição
        colunas_edicao = [
            "Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
            "MVA", "Comissão", "Bonificação", "Contrato"
        ]

        df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()

        # Converter valores numéricos
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_para_edicao_clean.columns:
                df_para_edicao_clean[col] = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)

        # Converter percentuais para formato 0-100
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_para_edicao_clean.columns:
                valores = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = (valores * 100).round(2)

        # Editor com melhor configuração
        df_editado = st.data_editor(
            df_para_edicao_clean,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_principal",
            column_config={
                "Descrição": st.column_config.TextColumn(
                    "📦 Produto", 
                    disabled=True, 
                    width="medium"
                ),
                "Preço de Venda": st.column_config.NumberColumn(
                    "💰 Preço Venda", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "📦 Qtd", 
                    format="%.0f", 
                    min_value=1, 
                    step=1,
                    width="small"
                ),
                "Custo NET": st.column_config.NumberColumn(
                    "💵 Custo NET", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Custo Fixo": st.column_config.NumberColumn(
                    "🏗️ Custo Fixo", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "MVA": st.column_config.NumberColumn(
                    "📈 MVA (%)", 
                    format="%.1f%%", 
                    min_value=0.0, 
                    max_value=500.0, 
                    step=0.1,
                    width="small"
                ),
                "Comissão": st.column_config.NumberColumn(
                    "🤝 Comissão (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Bonificação": st.column_config.NumberColumn(
                    "🎁 Bonificação (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Contrato": st.column_config.NumberColumn(
                    "📄 Contrato (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                )
            },
            hide_index=True
        )

        # Dicas de uso
        st.info("💡 **Dicas:** Use ⭐ para editar valores individualmente. Clique duas vezes nas células para editar.")

        return df_editado

    def _processar_dados_editados(self, df_editado: pd.DataFrame, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Processamento melhorado dos dados editados"""
        df_processado = df_editado.copy()

        # Converter percentuais de volta para decimal
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_processado.columns:
                df_processado[col] = pd.to_numeric(df_processado[col], errors='coerce').fillna(0.0) / 100

        # Arredondar valores
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_processado.columns:
                df_processado[col] = df_processado[col].round(2)

        # Detectar mudanças com melhor feedback
        produtos_com_mudancas = []

        for index in df_processado.index:
            if index < len(df_para_edicao):
                produto = df_processado.at[index, "Descrição"]

                # Verificar comissão
                try:
                    comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
                    comissao_editada = float(df_processado.at[index, "Comissão"])

                    if abs(comissao_original - comissao_editada) > 0.001:
                        st.session_state.comissoes_editadas[produto] = comissao_editada
                        produtos_com_mudancas.append(f"Comissão {produto}: {comissao_editada:.2%}")
                except:
                    pass

                # Verificar bonificação
                try:
                    bonificacao_original = float(df_para_edicao.iloc[index]["Bonificação"])
                    bonificacao_editada = float(df_processado.at[index, "Bonificação"])

                    if abs(bonificacao_original - bonificacao_editada) > 0.001:
                        st.session_state.bonificacoes_editadas[produto] = bonificacao_editada
                        produtos_com_mudancas.append(f"Bonificação {produto}: {bonificacao_editada:.2%}")
                except:
                    pass

            if produtos_com_mudancas:
                mudancas_texto = ', '.join(produtos_com_mudancas[:3])
                if len(produtos_com_mudancas) > 3:
                    mudancas_texto += f" e mais {len(produtos_com_mudancas) - 3}"
                st.success(f"✏️ **Mudanças detectadas:** {mudancas_texto}")

        # Criar DataFrame final
        df_final = df_para_edicao.copy()
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                         "Custo Fixo", "MVA", "Comissão", "Bonificação", "Contrato"]

        for col in colunas_edicao:
            if col in df_processado.columns:
                df_final[col] = df_processado[col]

        st.session_state.df_edicao_temp = df_final.copy()
        return df_final

    def _calcular_e_exibir_resultados(self, df_final: pd.DataFrame):
        """Cálculo e exibição melhorados dos resultados"""
        st.markdown("#### 🚀 Resultados da Simulação")
        
        # Botão principal de cálculo
        col_calc, col_space = st.columns([2, 3])
        with col_calc:
            calcular_clicked = st.button(
                "🚀 Calcular Resultados Finais", 
                type="primary", 
                use_container_width=True
            )

        if calcular_clicked:
            with st.spinner("🔄 Processando cálculos..."):
                # Otimização de frete se disponível
                self._otimizar_frete_por_volume(df_final)

                # Armazenar dados
                st.session_state.df_atual = st.session_state.df_edicao_temp.copy()
                st.session_state.resultados_atualizados = True
                
                time.sleep(1)  # UX melhor
                st.rerun()

        # Mostrar resultados se disponível
        if st.session_state.get("resultados_atualizados", False):
            self._exibir_resultados_completos(df_final)

    def _otimizar_frete_por_volume(self, df_final: pd.DataFrame):
        """Otimização inteligente de frete por volume"""
        if (hasattr(st.session_state, 'resultado_frete_completo') and 
            st.session_state.resultado_frete_completo):

            volume_total = df_final["Quantidade"].sum()
            
            # Reavalia otimização
            nova_otimizacao = calcular_frete_otimizado(
                st.session_state.resultado_frete_completo, 
                volume_total
            )

            # Verificar mudanças
            otimizacao_anterior = st.session_state.get('otimizacao_frete', {})
            veiculo_anterior = otimizacao_anterior.get('veiculo_otimo', 'desconhecido')
            veiculo_novo = nova_otimizacao['veiculo_otimo']

            # Atualizar frete se necessário
            if veiculo_novo != veiculo_anterior and nova_otimizacao['frete_por_caixa'] > 0:
                df_final["Frete Caixa"] = nova_otimizacao['frete_por_caixa']

                # Alertar sobre otimização
                if nova_otimizacao['economia'] > 0:
                    st.success(f"""
                    🎯 **FRETE OTIMIZADO AUTOMATICAMENTE!**
                    
                    📦 Volume total: {volume_total} caixas
                    {nova_otimizacao['alerta']}
                    💰 Novo frete/caixa: R$ {nova_otimizacao['frete_por_caixa']:.2f}
                    """)
                else:
                    st.info(f"ℹ️ {nova_otimizacao['alerta']}")

            st.session_state.otimizacao_frete = nova_otimizacao

    def _exibir_resultados_completos(self, df_final: pd.DataFrame):
        """Exibição completa e melhorada dos resultados"""
        # Calcular resultados
        calculadora = CalculadoraResultados(self.tipo_frete)
        resultados = df_final.apply(calculadora.calcular_resultados_completos, axis=1)

        # Criar DataFrame para exibição
        df_display = self._criar_dataframe_display_melhorado(df_final, resultados)

        # Informações de otimização
        self._exibir_info_otimizacao(df_final)

        # Tabela principal de resultados
        self._exibir_tabela_resultados_melhorada(df_display)

        # Resumo executivo
        self._exibir_resumo_executivo_melhorado(df_display)

        # Análises detalhadas
        self._exibir_analises_detalhadas(df_final, resultados, df_display)

        # Seção de exportação
        self._exibir_secao_exportacao_melhorada(df_final, resultados, df_display)

    def _criar_dataframe_display_melhorado(self, df_final: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame melhorado para exibição"""
        df_display = pd.DataFrame({
            "Produto": df_final["Descrição"].values,
            "Preço Venda": resultados["Preço Venda"].values,
            "Qtd": resultados["Qtd"].values.astype(int),
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

        # Arredondamento melhorado
        colunas_monetarias = [
            "Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
            "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
            "Lucro Líquido", "Equilíbrio"
        ]

        for col in colunas_monetarias:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: CalculadoraTributaria.arredondar_valor(x, 2)
                )

        df_display["Margem %"] = df_display["Margem %"].apply(
            lambda x: CalculadoraTributaria.arredondar_valor(x, 1)
        )

        return df_display

    def _exibir_info_otimizacao(self, df_final: pd.DataFrame):
        """Exibe informações de otimização de frete"""
        if hasattr(st.session_state, 'otimizacao_frete') and st.session_state.otimizacao_frete:
            otimizacao = st.session_state.otimizacao_frete

            if otimizacao['veiculo_otimo'] != 'nenhum':
                col_opt1, col_opt2, col_opt3, col_opt4 = st.columns(4)

                with col_opt1:
                    volume_total = df_final["Quantidade"].sum()
                    st.metric("📦 Volume Total", f"{volume_total} caixas")

                with col_opt2:
                    veiculo_label = otimizacao['veiculo_otimo'].replace('_', ' ').upper()
                    st.metric("🚛 Veículo Otimizado", veiculo_label)

                with col_opt3:
                    st.metric("💰 Frete Total", f"R$ {otimizacao['frete_total']:.2f}")

                with col_opt4:
                    if otimizacao['economia'] > 0:
                        st.metric("💰 Economia", f"R$ {otimizacao['economia']:.2f}", delta="Positiva")
                    else:
                        st.metric("📊 Status", "Otimizado")

    def _exibir_tabela_resultados_melhorada(self, df_display: pd.DataFrame):
        """Tabela de resultados com melhor formatação"""
        st.markdown("#### 📊 Resultados Detalhados")

        # Função de coloração melhorada
        def colorir_valores(val):
            try:
                if isinstance(val, (int, float)):
                    if val < 0:
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                    elif val > 0:
                        return 'background-color: #e8f5e8; color: #2e7d32'
                    else:
                        return 'color: #666666'
                return ''
            except:
                return ''

        # Formatação aprimorada com padrão brasileiro
        styled_display = df_display.style.format({
            "Preço Venda": lambda x: formatar_moeda_brasileira(x),
            "Subtotal": lambda x: formatar_moeda_brasileira(x),
            "IPI": lambda x: formatar_moeda_brasileira(x),
            "ICMS-ST": lambda x: formatar_moeda_brasileira(x),
            "FCP": lambda x: formatar_moeda_brasileira(x),
            "Total NF": lambda x: formatar_moeda_brasileira(x),
            "Custo Total": lambda x: formatar_moeda_brasileira(x),
            "Despesas": lambda x: formatar_moeda_brasileira(x),
            "Lucro Antes IR": lambda x: formatar_moeda_brasileira(x),
            "IRPJ+CSLL": lambda x: formatar_moeda_brasileira(x),
            "Lucro Líquido": lambda x: formatar_moeda_brasileira(x),
            "Margem %": lambda x: formatar_percentual_brasileiro(x),
            "Equilíbrio": lambda x: formatar_moeda_brasileira(x)
        }).applymap(
            colorir_valores, 
            subset=["Lucro Antes IR", "Lucro Líquido", "Margem %"]
        ).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f0f2f6'), ('color', '#262730'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '8px'), ('text-align', 'right')]},
            {'selector': 'td:first-child', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}
        ])

        st.dataframe(styled_display, use_container_width=True, height=400)

    def _exibir_resumo_executivo_melhorado(self, df_display: pd.DataFrame):
        """Resumo executivo melhorado"""
        st.markdown("#### 📈 Resumo Executivo")

        if len(df_display) > 0:
            # Métricas principais
            col1, col2, col3, col4, col5 = st.columns(5)

            total_receita = df_display["Subtotal"].sum()
            total_lucro_liquido = df_display["Lucro Líquido"].sum()
            margem_ponderada = (total_lucro_liquido / total_receita) * 100 if total_receita > 0 else 0.0
            produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
            total_nf = df_display["Total NF"].sum()

            with col1:
                st.metric("💰 Receita Total", formatar_moeda_brasileira(total_receita))

            with col2:
                delta_lucro = formatar_percentual_brasileiro(margem_ponderada) if total_receita > 0 else "0,0%"
                st.metric("💵 Lucro Líquido", formatar_moeda_brasileira(total_lucro_liquido), delta=delta_lucro)

            with col3:
                cor_margem = "🟢" if margem_ponderada > 10 else "🟡" if margem_ponderada > 5 else "🔴"
                st.metric("📊 Margem Ponderada", f"{cor_margem} {formatar_percentual_brasileiro(margem_ponderada)}")

            with col4:
                cor_produtos = "🔴" if produtos_prejuizo > 0 else "🟢"
                st.metric("⚠️ Produtos c/ Prejuízo", f"{cor_produtos} {produtos_prejuizo}")

            with col5:
                st.metric("📄 Total NF", formatar_moeda_brasileira(total_nf))

            # Alertas inteligentes
            self._exibir_alertas_inteligentes(df_display, margem_ponderada, produtos_prejuizo)

    def _exibir_alertas_inteligentes(self, df_display: pd.DataFrame, margem_ponderada: float, produtos_prejuizo: int):
        """Sistema de alertas inteligentes"""
        alertas = []

        # Análise de margem
        if margem_ponderada < 5:
            alertas.append("🔴 **ATENÇÃO:** Margem muito baixa (< 5%). Revisar preços ou custos.")
        elif margem_ponderada < 10:
            alertas.append("🟡 **CUIDADO:** Margem baixa (< 10%). Monitorar competitividade.")
        elif margem_ponderada > 25:
            alertas.append("🟢 **EXCELENTE:** Margem alta (> 25%). Ótima rentabilidade!")

        # Análise de produtos
        if produtos_prejuizo > 0:
            produtos_negativos = df_display[df_display["Lucro Líquido"] < 0]
            maior_prejuizo = produtos_negativos.nlargest(1, "Lucro Líquido")
            if not maior_prejuizo.empty:
                produto_problema = maior_prejuizo.iloc[0]["Produto"]
                prejuizo_valor = maior_prejuizo.iloc[0]["Lucro Líquido"]
                alertas.append(f"🚨 **PRODUTO CRÍTICO:** {produto_problema} com prejuízo de R$ {abs(prejuizo_valor):.2f}")

        # Análise de concentração
        receita_por_produto = df_display["Subtotal"]
        produto_principal = df_display.loc[receita_por_produto.idxmax(), "Produto"]
        concentracao = (receita_por_produto.max() / receita_por_produto.sum()) * 100
        if concentracao > 50:
            alertas.append(f"📊 **CONCENTRAÇÃO:** {concentracao:.1f}% da receita vem de '{produto_principal}'")

        # Exibir alertas
        for alerta in alertas:
            if "🔴" in alerta or "🚨" in alerta:
                st.error(alerta)
            elif "🟡" in alerta:
                st.warning(alerta)
            else:
                st.success(alerta)

    def _exibir_analises_detalhadas(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Análises detalhadas melhoradas"""
        with st.expander("🔍 Análises Detalhadas", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📊 Composição", "🎯 Top Produtos", "📋 Breakdown"])

            with tab1:
                self._exibir_analise_composicao(df_display)

            with tab2:
                self._exibir_top_produtos(df_display)

            with tab3:
                self._exibir_breakdown_calculo(df_final, resultados)

    def _exibir_analise_composicao(self, df_display: pd.DataFrame):
        """Análise de composição dos resultados"""
        st.markdown("**📊 Composição dos Resultados**")

        # Análise de receita por produto
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Contribuição por Receita**")
            receita_sorted = df_display.nlargest(5, "Subtotal")[["Produto", "Subtotal", "Margem %"]]
            for idx, row in receita_sorted.iterrows():
                participacao = (row["Subtotal"] / df_display["Subtotal"].sum()) * 100
                st.write(f"• {row['Produto']}: {formatar_moeda_brasileira(row['Subtotal'])} ({formatar_percentual_brasileiro(participacao)}) - Margem: {formatar_percentual_brasileiro(row['Margem %'])}")

        with col2:
            st.markdown("**🎯 Contribuição por Lucro**")
            lucro_sorted = df_display.nlargest(5, "Lucro Líquido")[["Produto", "Lucro Líquido", "Margem %"]]
            for idx, row in lucro_sorted.iterrows():
                if df_display["Lucro Líquido"].sum() > 0:
                    participacao = (row["Lucro Líquido"] / df_display["Lucro Líquido"].sum()) * 100
                else:
                    participacao = 0
                st.write(f"• {row['Produto']}: {formatar_moeda_brasileira(row['Lucro Líquido'])} ({formatar_percentual_brasileiro(participacao)}) - Margem: {formatar_percentual_brasileiro(row['Margem %'])}")

    def _exibir_top_produtos(self, df_display: pd.DataFrame):
        """Análise dos top produtos"""
        st.markdown("**🏆 Rankings de Produtos**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🥇 Maiores Receitas**")
            top_receita = df_display.nlargest(3, "Subtotal")[["Produto", "Subtotal"]]
            for i, (idx, row) in enumerate(top_receita.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {formatar_moeda_brasileira(row['Subtotal'])}")

        with col2:
            st.markdown("**💰 Maiores Lucros**")
            top_lucro = df_display.nlargest(3, "Lucro Líquido")[["Produto", "Lucro Líquido"]]
            for i, (idx, row) in enumerate(top_lucro.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {formatar_moeda_brasileira(row['Lucro Líquido'])}")

        with col3:
            st.markdown("**📈 Maiores Margens**")
            top_margem = df_display.nlargest(3, "Margem %")[["Produto", "Margem %"]]
            for i, (idx, row) in enumerate(top_margem.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {formatar_percentual_brasileiro(row['Margem %'])}")

        # Produtos que precisam de atenção
        produtos_atencao = df_display[df_display["Margem %"] < 5]
        if not produtos_atencao.empty:
            st.markdown("**⚠️ Produtos que Precisam de Atenção (Margem < 5%)**")
            for idx, row in produtos_atencao.iterrows():
                st.write(f"🔴 {row['Produto']}: Margem {formatar_percentual_brasileiro(row['Margem %'])} - Lucro {formatar_moeda_brasileira(row['Lucro Líquido'])}")

    def _exibir_breakdown_calculo(self, df_final: pd.DataFrame, resultados: pd.DataFrame):
        """Breakdown detalhado do cálculo"""
        st.markdown("**🔍 Breakdown do Cálculo (Primeiro Produto)**")

        if len(resultados) > 0:
            primeiro = resultados.iloc[0]
            produto_nome = df_final.iloc[0]["Descrição"]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**📦 Base do Produto**")
                st.write(f"• Produto: {produto_nome}")
                st.write(f"• Preço Unitário: {formatar_moeda_brasileira(primeiro['Preço Venda'])}")
                st.write(f"• Quantidade: {primeiro['Qtd']:.0f}")
                st.write(f"• **Subtotal: {formatar_moeda_brasileira(primeiro['Subtotal'])}**")
                st.write(f"• IPI: {formatar_moeda_brasileira(primeiro['IPI'])}")

            with col2:
                st.markdown("**🏛️ Impostos e Contribuições**")
                st.write(f"• Base ICMS-ST: {formatar_moeda_brasileira(primeiro['Base ICMS-ST'])}")
                st.write(f"• ICMS Próprio: {formatar_moeda_brasileira(primeiro['ICMS Próprio'])}")
                st.write(f"• ICMS-ST: {formatar_moeda_brasileira(primeiro['ICMS-ST'])}")
                st.write(f"• FCP: {formatar_moeda_brasileira(primeiro['FCP'])}")
                st.write(f"• **Total NF: {formatar_moeda_brasileira(primeiro['Total NF'])}**")

            with col3:
                st.markdown("**💰 Resultado Financeiro**")
                st.write(f"• Custo Total: {formatar_moeda_brasileira(primeiro['Custo Total'])}")
                st.write(f"• Despesas: {formatar_moeda_brasileira(primeiro['Total Despesas'])}")
                st.write(f"• Frete: {formatar_moeda_brasileira(primeiro['Frete Total'])}")
                st.write(f"• Lucro Antes IR: {formatar_moeda_brasileira(primeiro['Lucro Antes IR'])}")
                st.write(f"• IRPJ + CSLL: {formatar_moeda_brasileira(primeiro['IRPJ'] + primeiro['CSLL'])}")
                st.write(f"• **Lucro Líquido: {formatar_moeda_brasileira(primeiro['Lucro Líquido'])}**")
                st.write(f"• **Margem: {formatar_percentual_brasileiro(primeiro['Margem Líquida %'])}**")

            # Fórmulas utilizadas
            st.markdown("**📐 Fórmulas Principais**")
            st.code("""
            Subtotal = Preço × Quantidade
            ICMS-ST = max(0, (Subtotal × (1 + MVA) × ICMS_Destino) - (Subtotal × ICMS_Origem))
            Lucro Antes IR = Subtotal - Custos - Despesas - Frete
            Lucro Líquido = Lucro Antes IR - IRPJ - CSLL
            Margem = (Lucro Líquido / Subtotal) × 100
            """)

    def _exibir_secao_exportacao_melhorada(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Seção de exportação melhorada"""
        st.markdown("#### 📄 Exportar e Compartilhar")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Excel Completo", use_container_width=True, type="primary"):
                excel_buffer = self._gerar_excel_completo(df_final, resultados, df_display)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"simulacao_sobel_SP_{self.uf_selecionado}_{timestamp}.xlsx"
                
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=excel_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with col2:
            if st.button("📋 Relatório PDF", use_container_width=True):
                st.info("🚧 Funcionalidade em desenvolvimento")

        with col3:
            if st.button("📱 Resumo para WhatsApp", use_container_width=True):
                resumo_whatsapp = self._gerar_resumo_whatsapp(df_display)
                st.text_area("📱 Copie e cole no WhatsApp:", resumo_whatsapp, height=200)

    def _gerar_excel_completo(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame) -> io.BytesIO:
        """Gera Excel completo com múltiplas abas"""
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            # Aba 1: Resultados principais
            df_display.to_excel(writer, index=False, sheet_name="Resultados")
            
            # Aba 2: Dados de entrada
            colunas_entrada = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                              "Custo Fixo", "MVA", "Comissão", "Bonificação"]
            df_entrada = df_final[colunas_entrada]
            df_entrada.to_excel(writer, index=False, sheet_name="Dados_Entrada")
            
            # Aba 3: Cálculos detalhados
            df_completo = pd.concat([df_final[colunas_entrada], resultados], axis=1)
            df_completo.to_excel(writer, index=False, sheet_name="Calculos_Completos")
            
            # Aba 4: Resumo executivo
            resumo_data = {
                "Métrica": [
                    "Receita Total", "Lucro Líquido Total", "Margem Ponderada", 
                    "Produtos com Prejuízo", "Total da Nota Fiscal", "Quantidade Total"
                ],
                "Valor": [
                    formatar_moeda_brasileira(df_display['Subtotal'].sum()),
                    formatar_moeda_brasileira(df_display['Lucro Líquido'].sum()),
                    formatar_percentual_brasileiro((df_display['Lucro Líquido'].sum()/df_display['Subtotal'].sum()*100)),
                    len(df_display[df_display["Lucro Líquido"] < 0]),
                    formatar_moeda_brasileira(df_display['Total NF'].sum()),
                    f"{df_display['Qtd'].sum():,.0f} caixas".replace(",", ".")
                ]
            }
            resumo_df = pd.DataFrame(resumo_data)
            resumo_df.to_excel(writer, index=False, sheet_name="Resumo_Executivo")
            
            # Aba 5: Parâmetros utilizados
            parametros_data = {
                "Parâmetro": [
                    "UF Origem", "UF Destino", "Tipo de Frete", "Frete por Caixa",
                    "% Contrato", "% Comissão Global", "% Bonificação Global"
                ],
                "Valor": [
                    "SP", self.uf_selecionado, self.tipo_frete, 
                    formatar_moeda_brasileira(self.frete_padrao),
                    formatar_percentual_brasileiro(self.contrato_percentual * 100),
                    formatar_percentual_brasileiro(self.comissao_padrao * 100) if self.comissao_padrao > 0 else "N/A",
                    formatar_percentual_brasileiro(self.bonificacao_global * 100) if self.bonificacao_global > 0 else "N/A"
                ]
            }
            parametros_df = pd.DataFrame(parametros_data)
            parametros_df.to_excel(writer, index=False, sheet_name="Parametros")

        return excel_buffer

    def _gerar_resumo_whatsapp(self, df_display: pd.DataFrame) -> str:
        """Gera resumo formatado para WhatsApp"""
        total_receita = df_display["Subtotal"].sum()
        total_lucro = df_display["Lucro Líquido"].sum()
        margem = (total_lucro / total_receita * 100) if total_receita > 0 else 0
        produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
        
        resumo = f"""
🏢 *SIMULAÇÃO SOBEL - RESUMO EXECUTIVO*
📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🗺️ *Rota:* SP → {self.uf_selecionado}
📦 *Produtos:* {len(df_display)} itens

💰 *RESULTADOS FINANCEIROS:*
• Receita Total: {formatar_moeda_brasileira(total_receita)}
• Lucro Líquido: {formatar_moeda_brasileira(total_lucro)}
• Margem Ponderada: {formatar_percentual_brasileiro(margem)}
• Produtos c/ Prejuízo: {produtos_prejuizo}

🏆 *TOP 3 PRODUTOS POR RECEITA:*
"""
        
        top3_receita = df_display.nlargest(3, "Subtotal")
        for i, (_, row) in enumerate(top3_receita.iterrows(), 1):
            resumo += f"{i}. {row['Produto']}: {formatar_moeda_brasileira(row['Subtotal'])} (Margem: {formatar_percentual_brasileiro(row['Margem %'])})\n"
        
        resumo += f"""
⚠️ *ALERTAS:*
"""
        if margem < 5:
            resumo += "🔴 Margem muito baixa - Revisar preços\n"
        elif margem < 10:
            resumo += "🟡 Margem baixa - Monitorar\n"
        else:
            resumo += "🟢 Margem adequada\n"
            
        if produtos_prejuizo > 0:
            resumo += f"🚨 {produtos_prejuizo} produtos com prejuízo\n"
        
        resumo += "\n🤖 _Gerado pelo Simulador Sobel v3.0_"
        
        return resumo

    def _exibir_relatorios(self):
        """Seção de relatórios e análises históricas"""
        st.markdown("### 📈 Relatórios e Análises")
        
        if not st.session_state.get("resultados_atualizados", False):
            st.info("ℹ️ Execute uma simulação primeiro para gerar relatórios.")
            return
        
        # Placeholder para funcionalidades futuras
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📊 Relatórios Disponíveis
            - 📈 Análise de margem por produto
            - 🎯 Comparativo de cenários
            - 📋 Histórico de simulações
            - 🏆 Ranking de produtos
            """)
            
        with col2:
            st.markdown("""
            #### 🚧 Em Desenvolvimento
            - 📅 Análise temporal
            - 🔄 Comparativo com concorrência
            - 📊 Dashboard executivo
            - 📱 Relatórios mobile
            """)
        
        st.info("💡 **Sugestão:** Use a funcionalidade de exportação para análises externas detalhadas.")

# Função principal melhorada
def main():
    """Função principal com melhor tratamento de erros"""
    try:
        # Verificações iniciais
        if 'inicializado' not in st.session_state:
            st.session_state.inicializado = True
            st.balloons()  # Feedback visual de carregamento
        
        # Executar simulador
        simulador = SimuladorSobel()
        simulador.executar()
        
        # Notas técnicas no final
        st.markdown("---")
        st.markdown("""
        ### 📚 Notas Técnicas - Simulador Sobel v3.0

        #### 🎯 **Estados com FCP (Fundo de Combate à Pobreza):**
        - **2,0%:** AC, AL, BA, MA, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, SC, SE
        - **2,5%:** CE
        - **0,0%:** AP, AM, DF, ES, GO, MT, RO, RR, SP, TO

        #### 🔧 **Funcionalidades Principais:**
        - ✅ Cálculo automático de ICMS-ST por UF
        - ✅ Otimização inteligente de frete por volume
        - ✅ Geolocalização e cálculo de rotas
        - ✅ Edição individual de comissões e bonificações
        - ✅ Exportação completa para Excel
        - ✅ Análises detalhadas e alertas inteligentes

        #### 📊 **Melhorias v3.0:**
        - Interface redesenhada com melhor UX/UI
        - Sistema de alertas inteligentes
        - Otimização automática de frete
        - Análises detalhadas por produto
        - Exportação aprimorada
        - Tratamento de erros melhorado

        ---
        *Desenvolvido para Sobel Suprema - Sistema integrado de simulação de preços*
        """)
        
    except Exception as e:
        st.error(f"""
        🚨 **Erro Crítico na Aplicação**
        
        **Detalhes do erro:** {str(e)}
        
        **Ações recomendadas:**
        1. 🔄 Recarregue a página (F5)
        2. 🧹 Limpe o cache do navegador
        3. 📞 Entre em contato com o suporte técnico
        
        **Informações técnicas:**
        - Versão: Simulador Sobel v3.0
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        # Log de erro para debug
        import traceback
        st.expander("🔧 Detalhes Técnicos (Para Suporte)", expanded=False).code(
            traceback.format_exc()
        )

# Executar aplicação
if __name__ == "__main__":
    main())
        except:
            # Formatação manual no padrão brasileiro
            if valor_float < 0:
                sinal = "-"
                valor_abs = abs(valor_float)
            else:
                sinal = ""
                valor_abs = valor_float
            
            # Separar parte inteira e decimal
            parte_inteira = int(valor_abs)
            parte_decimal = int((valor_abs - parte_inteira) * 100)
            
            # Formatação com pontos para milhares
            parte_inteira_str = f"{parte_inteira:,}".replace(",", ".")
            
            return f"{sinal}R$ {parte_inteira_str},{parte_decimal:02d}"
    except:
        return "R$ 0,00"

def formatar_percentual_brasileiro(valor: float) -> str:
    """Formata percentual no padrão brasileiro"""
    try:
        if pd.isna(valor) or valor is None:
            return "0,0%"
        
        valor_float = float(valor)
        return f"{valor_float:.1f}%".replace(".", ",")
    except:
        return "0,0%"

def obter_faixa_km_exata(distancia_km: float, faixas: list) -> str:
    """Dado a distância, retorna a faixa de KM correspondente (ex: '0-50')"""
    # Primeiro: busca exata
    for ini, fim, label in faixas:
        if ini <= distancia_km <= fim:
            return label

    # Segundo: busca pela faixa mais próxima (menor diferença)
    if faixas:
        melhor_faixa = None
        menor_diferenca = float('inf')

        for ini, fim, label in faixas:
            # Calcular distância até o centro da faixa
            centro_faixa = (ini + fim) / 2 if fim != float('inf') else ini + 50
            diferenca = abs(distancia_km - centro_faixa)

            if diferenca < menor_diferenca:
                menor_diferenca = diferenca
                melhor_faixa = label

        # Se a diferença for razoável (menos de 100km), usar a faixa mais próxima
        if menor_diferenca <= 100:
            return melhor_faixa

    return 'Indefinida'

def buscar_frete_inteligente(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str) -> dict:
    """
    Busca valores de frete de forma inteligente para otimização de veículo
    """
    resultado = {
        'truck': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'carreta': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'capacidades': {'truck': 870, 'carreta': 1740}
    }

    # Buscar ambos os tipos
    for tipo_veiculo in ['truck', 'carreta']:
        valor, faixa_usada, metodo = buscar_frete_por_faixa(df_clientes, cidade_ibge, faixa_km, tipo_veiculo)
        resultado[tipo_veiculo] = {
            'valor': valor,
            'faixa_usada': faixa_usada,
            'metodo': metodo
        }

    return resultado

def calcular_frete_otimizado(resultado_frete: dict, quantidade_total: int) -> dict:
    """
    Calcula o frete otimizado baseado no volume total
    """
    truck_info = resultado_frete['truck']
    carreta_info = resultado_frete['carreta']
    capacidades = resultado_frete['capacidades']

    # Se não encontrou nenhum valor, retornar erro
    if truck_info['valor'] == 0 and carreta_info['valor'] == 0:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhum valor de frete encontrado',
            'detalhes': {}
        }

    # Calcular cenários
    cenarios = {}

    # Cenário Truck (se couber)
    if quantidade_total <= capacidades['truck'] and truck_info['valor'] > 0:
        cenarios['truck'] = {
            'frete_total': truck_info['valor'],
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': 1,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'],
            'ocupacao': (quantidade_total / capacidades['truck']) * 100
        }

    # Cenário Carreta
    if carreta_info['valor'] > 0:
        viagens_carreta = max(1, math.ceil(quantidade_total / capacidades['carreta']))
        cenarios['carreta'] = {
            'frete_total': carreta_info['valor'] * viagens_carreta,
            'frete_por_caixa': carreta_info['valor'] / capacidades['carreta'],
            'viagens': viagens_carreta,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['carreta'] * viagens_carreta,
            'ocupacao': (quantidade_total / (capacidades['carreta'] * viagens_carreta)) * 100
        }

    # Cenário Truck múltiplo (se necessário)
    if quantidade_total > capacidades['truck'] and truck_info['valor'] > 0:
        viagens_truck = math.ceil(quantidade_total / capacidades['truck'])
        cenarios['truck_multiplo'] = {
            'frete_total': truck_info['valor'] * viagens_truck,
            'frete_por_caixa': truck_info['valor'] / capacidades['truck'],
            'viagens': viagens_truck,
            'capacidade_usada': quantidade_total,
            'capacidade_total': capacidades['truck'] * viagens_truck,
            'ocupacao': (quantidade_total / (capacidades['truck'] * viagens_truck)) * 100
        }

    # Encontrar melhor opção (menor custo total)
    if not cenarios:
        return {
            'veiculo_otimo': 'nenhum',
            'frete_total': 0.0,
            'frete_por_caixa': 0.0,
            'economia': 0.0,
            'alerta': 'Nenhuma opção de frete viável',
            'detalhes': {}
        }

    melhor_opcao = min(cenarios.keys(), key=lambda k: cenarios[k]['frete_total'])
    melhor_cenario = cenarios[melhor_opcao]

    # Calcular economia
    economia = 0.0
    if 'carreta' in cenarios and melhor_opcao != 'carreta':
        economia = cenarios['carreta']['frete_total'] - melhor_cenario['frete_total']

    # Gerar alerta
    alerta = ""
    if melhor_opcao == 'truck':
        alerta = f"✅ OTIMIZAÇÃO: Volume de {quantidade_total} caixas cabe em TRUCK! Economia de R$ {economia:.2f}"
    elif melhor_opcao == 'truck_multiplo':
        viagens = melhor_cenario['viagens']
        alerta = f"📦 MÚLTIPLOS TRUCKS: {viagens} viagens necessárias. " + (f"Economia de R$ {economia:.2f}" if economia > 0 else "")
    else:
        alerta = f"🚛 CARRETA RECOMENDADA: Volume de {quantidade_total} caixas otimizado para carreta"

    return {
        'veiculo_otimo': melhor_opcao,
        'frete_total': melhor_cenario['frete_total'],
        'frete_por_caixa': melhor_cenario['frete_por_caixa'],
        'economia': economia,
        'alerta': alerta,
        'detalhes': {
            'cenarios': cenarios,
            'melhor_cenario': melhor_cenario,
            'truck_info': truck_info,
            'carreta_info': carreta_info
        }
    }

def buscar_frete_por_faixa(df_clientes: pd.DataFrame, cidade_ibge: str, faixa_km: str, tipo_veiculo='truck') -> tuple:
    """
    Busca o valor do frete de forma inteligente
    """
    # Primeira tentativa: busca exata por cidade_ibge e faixa
    linha_exata = df_clientes[
        (df_clientes['cidade_ibge'] == cidade_ibge) &
        (df_clientes['FAIXA_KM'] == faixa_km)
    ]

    if not linha_exata.empty:
        if tipo_veiculo == 'truck':
            valor = linha_exata.iloc[0]['TBL_TRCK'] if not pd.isna(linha_exata.iloc[0]['TBL_TRCK']) else 0.0
        elif tipo_veiculo == 'carreta':
            valor = linha_exata.iloc[0]['TBL_CRRT'] if 'TBL_CRRT' in linha_exata.columns and not pd.isna(linha_exata.iloc[0]['TBL_CRRT']) else 0.0
        else:
            valor = 0.0

        if valor > 0:
            return float(valor), faixa_km, "exata"

    # Segunda tentativa: buscar por IBGE e calcular pela faixa mais próxima
    linhas_ibge = df_clientes[df_clientes['cidade_ibge'] == cidade_ibge]

    if not linhas_ibge.empty:
        distancia_solicitada = extrair_distancia_da_faixa(faixa_km)

        if distancia_solicitada is not None:
            melhor_faixa = None
            menor_diferenca = float('inf')
            melhor_linha = None

            for _, linha in linhas_ibge.iterrows():
                faixa_disponivel = linha['FAIXA_KM']
                distancia_disponivel = extrair_distancia_da_faixa(faixa_disponivel)

                if distancia_disponivel is not None:
                    diferenca = abs(distancia_solicitada - distancia_disponivel)
                    if diferenca < menor_diferenca:
                        menor_diferenca = diferenca
                        melhor_faixa = faixa_disponivel
                        melhor_linha = linha

            if melhor_linha is not None:
                if tipo_veiculo == 'truck':
                    valor = melhor_linha['TBL_TRCK'] if not pd.isna(melhor_linha['TBL_TRCK']) else 0.0
                elif tipo_veiculo == 'carreta':
                    valor = melhor_linha['TBL_CRRT'] if 'TBL_CRRT' in melhor_linha and not pd.isna(melhor_linha['TBL_CRRT']) else 0.0
                else:
                    valor = 0.0

                if valor > 0:
                    return float(valor), melhor_faixa, f"aproximada (IBGE {cidade_ibge})"

    return 0.0, "não encontrada", "não encontrado"

def extrair_distancia_da_faixa(faixa: str) -> float:
    """Extrai a distância média de uma faixa"""
    try:
        faixa_str = str(faixa).strip()

        if '+' in faixa_str:
            valor = int(faixa_str.replace('+', '').strip())
            return float(valor + 50)
        elif '-' in faixa_str:
            partes = faixa_str.split('-')
            if len(partes) == 2:
                ini, fim = int(partes[0].strip()), int(partes[1].strip())
                return float((ini + fim) / 2)
        else:
            return float(faixa_str)
    except (ValueError, IndexError):
        return None

# ==================== CLASSES PRINCIPAIS ====================

class ConfiguracaoTributaria:
    """Classe para gerenciar configurações tributárias por UF"""

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
        'RJ': {'interna': 0.22, 'interestadual': 0.12, 'fcp': 0.02}, 
        'RN': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RS': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'RO': {'interna': 0.175, 'interestadual': 0.12, 'fcp': 0.0},
        'RR': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.0},
        'SC': {'interna': 0.17, 'interestadual': 0.12, 'fcp': 0.02},
        'SP': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0},
        'SE': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.02},
        'TO': {'interna': 0.18, 'interestadual': 0.12, 'fcp': 0.0}
    }

    @classmethod
    def obter_aliquotas(cls, uf: str) -> Dict[str, float]:
        """Retorna as alíquotas para uma UF específica"""
        return cls.ICMS_ALIQUOTAS.get(uf.upper(), {
            'interna': 0.18, 
            'interestadual': 0.12, 
            'fcp': 0.0
        })

class GerenciadorGeolocalizacao:
    """Classe para gerenciar operações de geolocalização"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço ou CEP em coordenadas (lat, lng)"""
        try:
            with st.spinner("🔍 Geocodificando endereço..."):
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return location["lat"], location["lng"]
                return None, None
        except Exception as e:
            st.error(f"❌ Erro na geocodificação: {str(e)}")
            return None, None

    def calcular_distancia(self, origem_coords: Tuple[float, float], 
                          destino_coords: Tuple[float, float]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Consulta a Distance Matrix API e retorna distância e tempo"""
        try:
            with st.spinner("📏 Calculando distância e tempo..."):
                lat_o, lng_o = origem_coords
                lat_d, lng_d = destino_coords

                url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat_o},{lng_o}&destinations={lat_d},{lng_d}&key={self.api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                elemento = data['rows'][0]['elements'][0]
                status = elemento.get("status", "ERRO")

                if status != "OK":
                    return None, None, f"⚠️ API não conseguiu calcular: `{status}`"

                distancia = elemento['distance']['text']
                duracao = elemento['duration']['text']
                return distancia, duracao, None

        except Exception as e:
            return None, None, f"❌ Erro ao processar resposta: {str(e)}"

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas usando a fórmula de Haversine"""
        R = 6371  # Raio da Terra em km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

class GerenciadorBancoDados:
    """Classe para gerenciar conexões e consultas ao banco de dados"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @st.cache_data(ttl=600)
    def carregar_clientes_ou_rede(_self) -> pd.DataFrame:
        """Carrega dados dos clientes do banco de dados"""
        try:
            with st.spinner("🔄 Carregando dados dos clientes..."):
                with pyodbc.connect(_self.connection_string, timeout=30) as conexao:
                    query = """
                        SELECT 
                            SA1.A1_COD, 
                            SA1.A1_LOJA,
                            SA1.A1_ZZLOJA,
                            SA1.A1_NOME,
                            IIF(SA1.A1_ZZREDE = '', LEFT(SA1.A1_NOME, 20), SA1.A1_ZZREDE) AS REDE,
                            SA1.A1_CEP, 
                            SA1.A1_RISCO,
                            SA1.A1_ZZCONTR,
                            SA1.A1_LC,
                            SA1.A1_END,                         
                            SA1.A1_MCOMPRA,
                            SA1.A1_ULTCOM,
                            SA1.A1_EST,
                            SA1.A1_MUN,
                            SA1.A1_BAIRRO,
                            SA1.A1_END,
                            SA1.A1_CGC,
                            cep.longitude,
                            cep.latitude,
                            cep.nome_logradouro_sem_acento,
                            ibge.cidade_ibge,
                            T.CIDADE,
                            T.FAIXA_KM,
                            T.TBL_TRCK,
                            T.TBL_CRRT
                        FROM SA1010 SA1
                        INNER JOIN cep.dbo.tbl_cep_202504_n_logradouro AS cep 
                            ON cep.cep COLLATE Latin1_General_CI_AS = SA1.A1_CEP COLLATE Latin1_General_CI_AS
                        INNER JOIN cep.dbo.tbl_cep_202504_n_cidade_ibge AS ibge 
                            ON ibge.id_cidade = cep.cidade_id
                        INNER JOIN BISOBEL.dbo.TRANSP_TARGET T ON T.COD_IBGE COLLATE Latin1_General_CI_AS = ibge.cidade_ibge 
                        WHERE SA1.A1_MSBLQL = '2'
                          AND SA1.D_E_L_E_T_ = ''
                    """
                    return pd.read_sql(query, conexao)
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados dos clientes: {e}")
            return pd.DataFrame()

class CalculadoraTributaria:
    """Classe para realizar cálculos tributários"""

    @staticmethod
    def arredondar_valor(valor: Any, decimais: int = 2) -> float:
        """Arredonda valores para evitar problemas de precisão"""
        try:
            return round(float(valor), decimais)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def calcular_icms_st_completo(valor_produto: float, ipi_valor: float, mva: float,
                                 icms_interestadual: float, icms_interno_destino: float,
                                 fcp_aliquota: float, frete: float = 0.0,
                                 seguro: float = 0.0, despesas: float = 0.0,
                                 descontos: float = 0.0) -> Tuple[float, float, float, float, float]:
        """
        Cálculo preciso do ICMS-ST conforme a legislação
        """
        # Se MVA for 0, não há ICMS-ST
        if mva <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        # Base sem MVA: inclui valor do produto + IPI
        base_sem_mva = CalculadoraTributaria.arredondar_valor(valor_produto + ipi_valor)

        # Aplica MVA
        base_com_mva = CalculadoraTributaria.arredondar_valor(base_sem_mva * (1 + mva))

        # ICMS origem (interestadual) sobre base sem MVA
        icms_origem = CalculadoraTributaria.arredondar_valor(base_sem_mva * icms_interestadual)

        # ICMS destino (interno) sobre base com MVA
        icms_destino = CalculadoraTributaria.arredondar_valor(base_com_mva * icms_interno_destino)

        # ICMS-ST: diferença entre ICMS destino e ICMS origem
        icms_st = CalculadoraTributaria.arredondar_valor(max(icms_destino - icms_origem, 0.0))

        # FCP somente se a alíquota for maior que zero
        fcp = CalculadoraTributaria.arredondar_valor(base_sem_mva * fcp_aliquota) if fcp_aliquota > 0 else 0.0

        return icms_st, base_com_mva, icms_origem, icms_destino, fcp

class CalculadoraResultados:
    """Classe para calcular resultados financeiros"""

    def __init__(self, tipo_frete: str = "CIF"):
        self.tipo_frete = tipo_frete

    def calcular_resultados_completos(self, row: pd.Series) -> pd.Series:
        """Calcula todos os resultados financeiros para uma linha de produto"""
        try:
            # Valores base
            preco_venda = CalculadoraTributaria.arredondar_valor(row["Preço de Venda"])
            qtd = CalculadoraTributaria.arredondar_valor(row["Quantidade"], 0)
            subtotal = CalculadoraTributaria.arredondar_valor(preco_venda * qtd)

            # Custos
            custo_net = CalculadoraTributaria.arredondar_valor(row.get("Custo NET", 0))
            custo_fixo = CalculadoraTributaria.arredondar_valor(row.get("Custo Fixo", 0))
            custo_total_unit = CalculadoraTributaria.arredondar_valor(custo_net + custo_fixo)
            custo_total = CalculadoraTributaria.arredondar_valor(custo_total_unit * qtd)

            # Frete
            frete_total = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0)) * qtd
            ) if self.tipo_frete == "CIF" else 0.0

            frete_unit = CalculadoraTributaria.arredondar_valor(
                float(row.get("Frete Caixa", 0))
            ) if self.tipo_frete == "CIF" else 0.0

            # IPI
            ipi_percent = float(row.get("IPI", 0))
            ipi_total = CalculadoraTributaria.arredondar_valor(subtotal * ipi_percent)

            # Parâmetros ICMS-ST
            mva = float(row.get("MVA", 0))
            icms_interestadual = float(row.get("ICMS Interestadual", 0))
            icms_interno_destino = float(row.get("ICMS Interno Destino", 0))
            fcp_aliquota = float(row.get("FCP", 0))

            # Calcular ICMS-ST
            icms_st, base_icms_st, icms_proprio, icms_total_interno, fcp_valor = \
                CalculadoraTributaria.calcular_icms_st_completo(
                    valor_produto=subtotal,
                    ipi_valor=ipi_total,
                    mva=mva,
                    icms_interestadual=icms_interestadual,
                    icms_interno_destino=icms_interno_destino,
                    fcp_aliquota=fcp_aliquota
                )

            # Despesas operacionais
            despesas_operacionais = self._calcular_despesas_operacionais(row, subtotal)
            total_despesas_operacionais = despesas_operacionais

            # Lucro antes dos impostos sobre lucro
            lucro_antes_ir = CalculadoraTributaria.arredondar_valor(
                subtotal - custo_total - total_despesas_operacionais - frete_total
            )

            # Calcular IR e CSLL
            irpj, csll = self._calcular_ir_csll(lucro_antes_ir)

            # Lucro líquido
            lucro_liquido = CalculadoraTributaria.arredondar_valor(lucro_antes_ir - irpj - csll)

            # Margem calculada corretamente
            margem_antes_ir = CalculadoraTributaria.arredondar_valor(
                (lucro_antes_ir / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            margem_liquida = CalculadoraTributaria.arredondar_valor(
                (lucro_liquido / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            # Total NF
            total_nf = CalculadoraTributaria.arredondar_valor(subtotal + ipi_total + icms_st + fcp_valor)

            # Ponto de equilíbrio
            ponto_equilibrio = self._calcular_ponto_equilibrio(row, custo_total_unit, frete_unit)

            return pd.Series({
                "Preço Venda": preco_venda,
                "Qtd": qtd,
                "Custo NET": custo_net,
                "Custo Fixo": custo_fixo,
                "MVA": mva,
                "Comissão": float(row.get("Comissão", 0)),
                "Bonificação": float(row.get("Bonificação", 0)),
                "Subtotal": subtotal,
                "IPI": ipi_total,
                "Base ICMS-ST": base_icms_st,
                "ICMS Próprio": icms_proprio,
                "ICMS-ST": icms_st,
                "FCP": fcp_valor,
                "Total NF": total_nf,
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
            st.error(f"❌ Erro no cálculo do produto {row.get('Descrição', 'N/A')}: {str(e)}")
            return self._retornar_serie_vazia()

    def _calcular_despesas_operacionais(self, row: pd.Series, subtotal: float) -> float:
        """Calcula o total das despesas operacionais"""
        despesas = [
            "ICMS Interestadual", "COFINS", "PIS", "Comissão",
            "Bonificação", "Contigência", "Contrato", "%Estrategico"
        ]

        total = 0.0
        for despesa in despesas:
            percentual = float(row.get(despesa, 0))
            total += CalculadoraTributaria.arredondar_valor(subtotal * percentual)

        return total

    def _calcular_ir_csll(self, lucro_antes_ir: float) -> Tuple[float, float]:
        """Calcula IRPJ e CSLL"""
        if lucro_antes_ir <= 0:
            return 0.0, 0.0

        # IRPJ: 15% + 10% sobre o que exceder R$ 20.000/mês
        irpj = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.15)
        if lucro_antes_ir > 20000:
            adicional_irpj = CalculadoraTributaria.arredondar_valor((lucro_antes_ir - 20000) * 0.10)
            irpj += adicional_irpj

        # CSLL: 9%
        csll = CalculadoraTributaria.arredondar_valor(lucro_antes_ir * 0.09)

        return irpj, csll

    def _calcular_ponto_equilibrio(self, row: pd.Series, custo_total_unit: float, frete_unit: float) -> float:
        """Calcula o ponto de equilíbrio"""
        try:
            # Despesas diretas percentuais
            despesas_diretas = (
                float(row.get("ICMS Interestadual", 0)) +
                float(row.get("COFINS", 0)) +
                float(row.get("PIS", 0)) +
                float(row.get("Comissão", 0)) +
                float(row.get("Bonificação", 0)) +
                float(row.get("Contigência", 0)) +
                float(row.get("Contrato", 0)) +
                float(row.get("%Estrategico", 0))
            )

            if despesas_diretas >= 1.0:
                return 0.0

            # Cálculo básico
            ponto_equilibrio = (custo_total_unit + frete_unit) / (1 - despesas_diretas)
            return CalculadoraTributaria.arredondar_valor(ponto_equilibrio)

        except Exception:
            return 0.0

    def _retornar_serie_vazia(self) -> pd.Series:
        """Retorna uma série com valores zerados em caso de erro"""
        return pd.Series({
            "Preço Venda": 0, "Qtd": 0, "Custo NET": 0, "Custo Fixo": 0, "MVA": 0,
            "Comissão": 0, "Bonificação": 0, "Subtotal": 0, "IPI": 0, "Base ICMS-ST": 0,
            "ICMS Próprio": 0, "ICMS-ST": 0, "FCP": 0, "Total NF": 0, "Custo Total": 0,
            "Frete Total": 0, "Total Despesas": 0, "Lucro Antes IR": 0, "IRPJ": 0,
            "CSLL": 0, "Lucro Líquido": 0, "Margem Antes IR %": 0, "Margem Líquida %": 0,
            "Ponto Equilíbrio": 0
        })

class GerenciadorEstado:
    """Classe para gerenciar o estado da aplicação"""

    def __init__(self):
        self.inicializar_estado()

    def inicializar_estado(self):
        """Inicializa as variáveis de estado"""
        estados_default = {
            'df_atual': None,
            'modo_equilibrio': False,
            'comissao_global_aplicada': False,
            'comissoes_editadas': {},
            'bonificacoes_editadas': {},
            'valores_originais': {},
            'df_edicao_temp': None,
            'resultados_atualizados': False,
            'frete_calculado_automatico': 0.0,
            'distancia_calculada': None,
            'tempo_calculado': None,
            'usar_frete_auto': False,
            'coordenadas_origem': None,
            'coordenadas_destino': None,
            'resultado_frete_completo': None,
            'otimizacao_frete': None,
            'dados_carregados': False
        }

        for key, value in estados_default.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def resetar_estado(self):
        """Reseta o estado da aplicação"""
        for key in ['df_atual', 'modo_equilibrio', 'comissao_global_aplicada', 
                   'comissoes_editadas', 'bonificacoes_editadas', 'valores_originais',
                   'df_edicao_temp', 'resultados_atualizados']:
            if key in st.session_state:
                if key in ['comissoes_editadas', 'bonificacoes_editadas', 'valores_originais']:
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None if key == 'df_atual' or key == 'df_edicao_temp' else False

class SimuladorSobel:
    """Classe principal do simulador"""

    def __init__(self):
        self.config_tributaria = ConfiguracaoTributaria()
        self.gerenciador_estado = GerenciadorEstado()
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if self.api_key:
            self.geolocalizacao = GerenciadorGeolocalizacao(self.api_key)
        else:
            self.geolocalizacao = None
            st.warning("⚠️ Google Maps API não configurada. Funcionalidades de geolocalização desabilitadas.")

        # Configuração do banco de dados
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.0.16;"
            "DATABASE=Protheus_Producao;"
            "UID=sa;"
            "PWD=Totvs@452525!"
        )
        self.db_manager = GerenciadorBancoDados(connection_string)

        # Produtos esperados
        self.produtos_esperados = [
            "ÁGUA SANITÁRIA 5L", "ÁGUA SANITÁRIA 2L", "ÁGUA SANITÁRIA 1L",
            "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
            "AMACIANTE 5L", "AMACIANTE 2L",
            "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
            "LAVA LOUÇAS 500ML", "LAVA LOUÇAS 5L",
            "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
            "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
            "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
        ]

        # Inicializar variáveis
        self.dados_cliente_selecionado = None
        self.frete_padrao_cliente = None
        self.faixas_km_ordenadas = []
        self.df_padrao = pd.DataFrame()
        self.contrato_real = None

    def executar(self):
        """Método principal para executar o simulador"""
        self._configurar_interface()
        
        # Verificar conexão com banco
        if not self._verificar_conexao_banco():
            return
            
        self._carregar_dados_iniciais()
        self._exibir_interface()

    def _configurar_interface(self):
        """Configura a interface do usuário"""
        # CSS customizado para melhorar a aparência
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e7cb8 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2e7cb8;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .success-card {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .warning-card {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-card {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header principal
        st.markdown("""
        <div class="main-header">
            <h1>📊 Simulador de Formação de Preço de Venda - Sobel v3.0</h1>
            <p>Sistema integrado de simulação com otimização de frete e geolocalização</p>
        </div>
        """, unsafe_allow_html=True)

        # Verificar se a imagem existe
        if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
            col_logo, col_space = st.columns([1, 3])
            with col_logo:
                st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=250)

    def _verificar_conexao_banco(self) -> bool:
        """Verifica se a conexão com o banco está funcionando"""
        try:
            with st.spinner("🔄 Verificando conexão com banco de dados..."):
                df_test = self.db_manager.carregar_clientes_ou_rede()
                if df_test.empty:
                    st.error("❌ Nenhum dado encontrado no banco. Verifique a conexão.")
                    return False
                st.success(f"✅ Banco conectado com sucesso! {len(df_test)} registros encontrados.")
                return True
        except Exception as e:
            st.error(f"❌ Erro de conexão com banco: {str(e)}")
            return False

    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais necessários"""
        # Carregar planilha padrão
        arquivo_padrao = "Custo de reposição.xlsx"
        if os.path.exists(arquivo_padrao):
            try:
                with st.spinner("📂 Carregando planilha de custos..."):
                    self.df_padrao = pd.read_excel(arquivo_padrao)
                    self.df_padrao.columns = self.df_padrao.columns.str.strip()
                    st.success(f"✅ Planilha carregada: {len(self.df_padrao)} produtos disponíveis")
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo padrão: {str(e)}")
                self.df_padrao = pd.DataFrame()
        else:
            st.warning("⚠️ Arquivo padrão 'Custo de reposição.xlsx' não encontrado.")
            self.df_padrao = pd.DataFrame()

        # Carregar faixas de KM
        self.faixas_km_ordenadas = self._extrair_faixas_ordenadas()

    def _extrair_faixas_ordenadas(self) -> list:
        """Extrai e ordena as faixas de KM disponíveis da base de clientes"""
        try:
            df_clientes = self.db_manager.carregar_clientes_ou_rede()
            if df_clientes.empty:
                return []
                
            faixas = []
            faixas_unicas = df_clientes['FAIXA_KM'].dropna().unique()

            for faixa in faixas_unicas:
                try:
                    faixa_str = str(faixa).strip()
                    if '+' in faixa_str:
                        ini = int(faixa_str.replace('+', '').strip())
                        faixas.append((ini, float('inf'), faixa_str))
                    elif '-' in faixa_str:
                        partes = faixa_str.split('-')
                        if len(partes) == 2:
                            ini, fim = int(partes[0].strip()), int(partes[1].strip())
                            faixas.append((ini, fim, faixa_str))
                    else:
                        valor = int(faixa_str)
                        faixas.append((valor, valor, faixa_str))
                except (ValueError, IndexError):
                    continue

            faixas.sort(key=lambda x: x[0])

            if faixas:
                st.info(f"🎯 Faixas de KM carregadas: {[f[2] for f in faixas[:5]]}{'...' if len(faixas) > 5 else ''}")

            return faixas
        except Exception as e:
            st.error(f"❌ Erro ao extrair faixas de frete: {e}")
            return []

    def _exibir_interface(self):
        """Exibe a interface principal"""
        # Verificar se há dados para continuar
        if self.df_padrao.empty:
            st.error("❌ Não é possível continuar sem dados. Carregue uma planilha de custos.")
            return

        # Usar tabs para melhor organização
        tab1, tab2, tab3 = st.tabs(["👤 Cliente & Parâmetros", "📊 Simulação", "📄 Relatórios"])

        with tab1:
            self._exibir_secao_cliente()
            st.markdown("---")
            self._exibir_secao_parametros()
            st.markdown("---")
            self._exibir_upload_arquivo()

        with tab2:
            if self._validar_dados():
                self._processar_simulacao()

        with tab3:
            self._exibir_relatorios()

    def _exibir_secao_cliente(self):
        """Exibe a seção de seleção de cliente melhorada"""
        st.markdown("### 👤 Seleção de Cliente")

        # Opção de cliente
        opcao_cliente = st.radio(
            "Como deseja proceder?", 
            ["🔍 Selecionar cliente existente", "➕ Cliente novo (sem histórico)"], 
            horizontal=True
        )

        self.contrato_real = None
        self.dados_cliente_selecionado = None

        if opcao_cliente == "🔍 Selecionar cliente existente":
            clientes_df = self.db_manager.carregar_clientes_ou_rede()
            
            if not clientes_df.empty:
                # Melhor interface de seleção
                col_search, col_filter = st.columns([3, 1])
                
                with col_search:
                    # Busca por nome
                    busca_nome = st.text_input("🔍 Buscar por nome do cliente", placeholder="Digite parte do nome...")
                
                with col_filter:
                    # Filtro por UF
                    ufs_disponiveis = ['Todos'] + sorted(clientes_df['A1_EST'].unique().tolist())
                    uf_filtro = st.selectbox("📍 Filtrar por UF", ufs_disponiveis)

                # Aplicar filtros
                df_filtrado = clientes_df.copy()
                
                if busca_nome:
                    df_filtrado = df_filtrado[
                        df_filtrado['A1_NOME'].str.contains(busca_nome, case=False, na=False)
                    ]
                
                if uf_filtro != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['A1_EST'] == uf_filtro]

                if not df_filtrado.empty:
                    # Criar opções mais informativas
                    opcoes_clientes = []
                    for idx, row in df_filtrado.iterrows():
                        opcao = f"{row['A1_NOME'][:50]} | {row['A1_MUN']}/{row['A1_EST']} | {row['A1_COD']}/{row['A1_LOJA']}"
                        if row['REDE'] and str(row['REDE']) != str(row['A1_NOME'])[:20]:
                            opcao += f" | [{row['REDE']}]"
                        opcoes_clientes.append(opcao)

                    cliente_escolhido_display = st.selectbox(
                        f"📋 Clientes encontrados ({len(df_filtrado)} registros):", 
                        opcoes_clientes,
                        help="Formato: Nome | Cidade/UF | Código/Loja | [Rede]"
                    )

                    # Encontrar o cliente selecionado
                    indice_selecionado = opcoes_clientes.index(cliente_escolhido_display)
                    self.dados_cliente_selecionado = df_filtrado.iloc[indice_selecionado]

                    # Exibir dados do cliente
                    self._exibir_dados_completos_cliente()

                    # Seção de cálculo de frete (se disponível)
                    if self.geolocalizacao:
                        self._exibir_secao_rota_integrada()
                else:
                    st.info("ℹ️ Nenhum cliente encontrado com os filtros aplicados.")
            else:
                st.warning("⚠️ Nenhum cliente encontrado na base de dados.")

    def _exibir_dados_completos_cliente(self):
        """Exibe dados completos do cliente de forma mais organizada"""
        st.markdown("#### 📋 Informações do Cliente Selecionado")

        cliente_dict = self.dados_cliente_selecionado.to_dict()

        # Card principal com informações básicas
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🏢 Razão Social", 
                    value=cliente_dict.get('A1_NOME', 'N/A')[:30] + ('...' if len(str(cliente_dict.get('A1_NOME', ''))) > 30 else ''),
                    help=cliente_dict.get('A1_NOME', 'N/A')
                )
                
            with col2:
                codigo = cliente_dict.get('A1_COD', '')
                loja = cliente_dict.get('A1_LOJA', '')
                st.metric("🏷️ Código/Loja", f"{codigo}/{loja}")
                
            with col3:
                uf = cliente_dict.get('A1_EST', 'N/A')
                cidade = cliente_dict.get('A1_MUN', 'N/A')
                st.metric("📍 Localização", f"{cidade}/{uf}")
                
            with col4:
                try:
                    contrato_valor = float(cliente_dict.get("A1_ZZCONTR", 0) or 0)
                    self.contrato_real = contrato_valor
                except:
                    self.contrato_real = 0.0
                    contrato_valor = 0.0
                st.metric("📄 Contrato", f"{contrato_valor:.2f}%")

        # Informações detalhadas em expander
        with st.expander("📄 Detalhes Completos", expanded=False):
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                # Endereço
                endereco_parts = []
                if cliente_dict.get('A1_END'):
                    endereco_parts.append(cliente_dict['A1_END'])
                if cliente_dict.get('A1_BAIRRO'):
                    endereco_parts.append(cliente_dict['A1_BAIRRO'])
                if cliente_dict.get('A1_MUN') and cliente_dict.get('A1_EST'):
                    endereco_parts.append(f"{cliente_dict['A1_MUN']}/{cliente_dict['A1_EST']}")
                
                cep = cliente_dict.get('A1_CEP', '')
                if cep and len(cep) == 8:
                    cep_formatado = f"{cep[:5]}-{cep[5:]}"
                    endereco_parts.append(f"CEP: {cep_formatado}")
                
                endereco_completo = '\n'.join(endereco_parts) if endereco_parts else "Não informado"
                st.text_area("📍 Endereço Completo", endereco_completo, height=100, disabled=True)
                
            with col_det2:
                # Informações financeiras
                try:
                    lc_value = float(cliente_dict.get('A1_LC', 0) or 0)
                    lc_text = f"R$ {lc_value:,.2f}" if lc_value > 0 else "Não definido"
                except:
                    lc_text = "Não definido"
                
                st.text_input("💳 Limite de Crédito", lc_text, disabled=True)
                st.text_input("⚠️ Classificação de Risco", cliente_dict.get('A1_RISCO', 'N/A'), disabled=True)
                
                # Rede se houver
                rede = cliente_dict.get('REDE', '')
                nome_resumo = str(cliente_dict.get('A1_NOME', ''))[:20]
                if rede and rede != nome_resumo:
                    st.text_input("🏪 Rede", rede, disabled=True)

    def _exibir_secao_rota_integrada(self):
        """Exibe seção de cálculo de rota melhorada"""
        with st.expander("🗺️ Cálculo de Frete e Rota", expanded=False):
            st.markdown("#### 🧭 Configuração de Rota")

            # Origens disponíveis
            origens = {
                "📍 Matriz (São Paulo - SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "📍 Filial (Atibaia - SP)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }

            col_origem, col_destino = st.columns(2)

            with col_origem:
                origem_opcao = st.selectbox("🚚 Unidade de Origem", list(origens.keys()))
                origem = origens[origem_opcao]
                st.text_area("📍 Endereço de Origem", origem, height=60, disabled=True)

            with col_destino:
                # Informações do cliente
                cliente_info = f"{self.dados_cliente_selecionado['A1_NOME'][:30]}..."
                st.text_input("🎯 Cliente Selecionado", cliente_info, disabled=True)
                
                # Endereço para geocodificação
                endereco_destino = self._montar_endereco_completo_para_geocode(
                    self.dados_cliente_selecionado.to_dict()
                )
                st.text_area("🎯 Endereço de Destino", endereco_destino, height=60, disabled=True)

            # Configurações de frete
            st.markdown("#### 🚛 Configuração de Frete")
            
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "🚚 Truck (870 caixas)" if x == "truck" else "🚛 Carreta (1.740 caixas)"
                )
                
                if st.button("🗺️ Calcular Rota e Frete", type="primary", use_container_width=True):
                    self._calcular_frete_automatico(origem, tipo_veiculo)

            with col_frete2:
                # Resultados da rota
                if st.session_state.get('distancia_calculada') and st.session_state.get('tempo_calculado'):
                    st.success("✅ Rota Calculada")
                    st.metric("📏 Distância", st.session_state.get('distancia_calculada'))
                    st.metric("⏱️ Tempo", st.session_state.get('tempo_calculado'))
                else:
                    st.info("ℹ️ Clique em 'Calcular' para obter a rota")

            with col_frete3:
                # Frete calculado ou manual
                frete_calculado = st.session_state.get('frete_calculado_automatico', 0.0)
                if frete_calculado > 0:
                    usar_frete_auto = st.checkbox("🤖 Usar frete calculado", value=True)
                    if usar_frete_auto:
                        self.frete_padrao_cliente = frete_calculado
                        st.success(f"💰 R$ {frete_calculado:.2f}/caixa")
                    else:
                        self.frete_padrao_cliente = st.number_input(
                            "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                        )
                else:
                    self.frete_padrao_cliente = st.number_input(
                        "✏️ Frete Manual (R$)", min_value=0.0, value=1.50, step=0.01
                    )

            # Mostrar mapas se disponível
            if (st.session_state.get('coordenadas_origem') and 
                st.session_state.get('coordenadas_destino')):
                self._exibir_mapas_cliente(origem)

    def _montar_endereco_completo_para_geocode(self, cliente_dict: dict) -> str:
        """Monta endereço otimizado para geocodificação"""
        partes_endereco = []

        def safe_str(value):
            if value is None or pd.isna(value):
                return ""
            return str(value).strip()

        # Componentes do endereço
        endereco_rua = safe_str(cliente_dict.get('A1_END', ''))
        if endereco_rua and endereco_rua.lower() != 'não informado':
            partes_endereco.append(endereco_rua)

        bairro = safe_str(cliente_dict.get('A1_BAIRRO', ''))
        if bairro and bairro.lower() not in ['', 'não informado']:
            partes_endereco.append(bairro)

        cidade = safe_str(cliente_dict.get('A1_MUN', ''))
        if cidade:
            partes_endereco.append(cidade)

        uf = safe_str(cliente_dict.get('A1_EST', ''))
        if uf:
            partes_endereco.append(uf)

        cep = safe_str(cliente_dict.get('A1_CEP', ''))
        if cep and cep not in ['N/A', '0'] and len(cep) >= 8:
            if len(cep) == 8 and cep.isdigit():
                cep_formatado = f"{cep[:5]}-{cep[5:]}"
                partes_endereco.append(f"CEP {cep_formatado}")
            else:
                partes_endereco.append(f"CEP {cep}")

        partes_endereco.append("Brasil")
        return ", ".join(partes_endereco)

    def _calcular_frete_automatico(self, origem: str, tipo_veiculo: str = "truck"):
        """Calcula frete automaticamente baseado na distância real"""
        with st.spinner("🔄 Processando cálculo de frete..."):
            # Geocodificar origem
            origem_coords = self.geolocalizacao.geocode(origem)
            if not origem_coords:
                st.error("❌ Não foi possível localizar o endereço de origem.")
                return

            # Geocodificar destino
            cliente_dict = self.dados_cliente_selecionado.to_dict()
            endereco_destino_completo = self._montar_endereco_completo_para_geocode(cliente_dict)
            destino_coords = self.geolocalizacao.geocode(endereco_destino_completo)

            if not destino_coords:
                # Fallback para coordenadas do banco
                try:
                    lat_banco = float(self.dados_cliente_selecionado["latitude"])
                    lng_banco = float(self.dados_cliente_selecionado["longitude"])
                    if lat_banco != 0 and lng_banco != 0:
                        destino_coords = (lat_banco, lng_banco)
                        st.warning("⚠️ Usando coordenadas do banco como fallback.")
                    else:
                        st.error("❌ Não foi possível localizar o endereço de destino.")
                        return
                except:
                    st.error("❌ Endereço não encontrado e coordenadas do banco indisponíveis.")
                    return

            # Calcular distância e tempo
            distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)
            if erro:
                st.error(erro)
                return

            try:
                # Processar distância
                distancia_texto = distancia.replace('km', '').strip()
                
                # Converter para float tratando vírgulas
                if ',' in distancia_texto:
                    if '.' in distancia_texto:
                        # Formato: "1,159.5" - vírgula = milhares, ponto = decimal
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:
                        # Verificar se vírgula é separador de milhares ou decimal
                        partes = distancia_texto.split(',')
                        if len(partes[1]) == 3:  # "1,159" - milhares
                            distancia_km = float(distancia_texto.replace(',', ''))
                        else:  # "1,5" - decimal
                            distancia_km = float(distancia_texto.replace(',', '.'))
                else:
                    distancia_km = float(distancia_texto)

                # Armazenar dados no session state
                st.session_state.distancia_calculada = distancia
                st.session_state.tempo_calculado = duracao
                st.session_state.coordenadas_origem = origem_coords
                st.session_state.coordenadas_destino = destino_coords

                # Obter faixa de KM e código IBGE
                faixa_km = obter_faixa_km_exata(distancia_km, self.faixas_km_ordenadas)
                cidade_ibge = str(self.dados_cliente_selecionado["cidade_ibge"])

                # Buscar valores de frete
                df_clientes_frete = self.db_manager.carregar_clientes_ou_rede()
                resultado_frete = buscar_frete_inteligente(df_clientes_frete, cidade_ibge, faixa_km)

                # Calcular otimização (volume estimado inicial)
                volume_estimado = 500
                otimizacao = calcular_frete_otimizado(resultado_frete, volume_estimado)

                # Armazenar resultados
                st.session_state.frete_calculado_automatico = otimizacao['frete_por_caixa']
                st.session_state.tipo_veiculo_usado = otimizacao['veiculo_otimo']
                st.session_state.resultado_frete_completo = resultado_frete
                st.session_state.otimizacao_frete = otimizacao

                # Exibir resultados
                if otimizacao['frete_por_caixa'] > 0:
                    st.success(f"""
                    ✅ **Cálculo Concluído com Sucesso!**
                    
                    📏 **Rota:** {distancia} ({duracao}) → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💰 **Frete/Caixa:** R$ {otimizacao['frete_por_caixa']:.2f}
                    🚛 **Veículo Otimizado:** {otimizacao['veiculo_otimo'].upper()}
                    """)

                    # Alerta de otimização
                    if otimizacao['alerta']:
                        if 'OTIMIZAÇÃO' in otimizacao['alerta']:
                            st.success(f"🎯 {otimizacao['alerta']}")
                        elif 'MÚLTIPLOS' in otimizacao['alerta']:
                            st.warning(f"📦 {otimizacao['alerta']}")
                        else:
                            st.info(f"ℹ️ {otimizacao['alerta']}")

                    # Tabela de comparação
                    self._exibir_comparacao_fretes(resultado_frete)
                else:
                    st.warning(f"""
                    ⚠️ **Rota calculada, mas frete não encontrado**
                    
                    📏 **Distância:** {distancia} → {distancia_km:.0f} km
                    📍 **IBGE:** {cidade_ibge} | **Faixa:** {faixa_km}
                    💡 **Sugestão:** Use frete manual
                    """)

            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")

    def _exibir_comparacao_fretes(self, resultado_frete: dict):
        """Exibe tabela de comparação de fretes"""
        st.markdown("#### 📊 Comparação de Fretes Disponíveis")

        truck_info = resultado_frete['truck']
        carreta_info = resultado_frete['carreta']

        comparacao_data = []
        
        if truck_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚚 Truck',
                'Capacidade': '870 caixas',
                'Frete Total': f"R$ {truck_info['valor']:,.2f}",
                'Frete/Caixa': f"R$ {truck_info['valor']/870:.2f}",
                'Método de Busca': truck_info['metodo'],
                'Faixa Utilizada': truck_info['faixa_usada']
            })

        if carreta_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚛 Carreta',
                'Capacidade': '1.740 caixas',
                'Frete Total': f"R$ {carreta_info['valor']:,.2f}",
                'Frete/Caixa': f"R$ {carreta_info['valor']/1740:.2f}",
                'Método de Busca': carreta_info['metodo'],
                'Faixa Utilizada': carreta_info['faixa_usada']
            })

        if comparacao_data:
            df_comparacao = pd.DataFrame(comparacao_data)
            st.dataframe(df_comparacao, use_container_width=True, hide_index=True)
            st.info("💡 **Dica:** O frete será otimizado automaticamente quando você definir as quantidades!")

    def _exibir_mapas_cliente(self, origem: str):
        """Exibe mapas interativos"""
        origem_coords = st.session_state.get('coordenadas_origem')
        destino_coords = st.session_state.get('coordenadas_destino')

        if not origem_coords or not destino_coords:
            return

        st.markdown("#### 🗺️ Visualização da Rota")
        
        col_mapa, col_street = st.columns(2)

        with col_mapa:
            st.markdown("**📍 Mapa com Rota**")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

        with col_street:
            st.markdown("**🚦 Street View - Destino**")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)

    def _exibir_secao_parametros(self):
        """Exibe seção de parâmetros melhorada"""
        st.markdown("### ⚙️ Parâmetros de Simulação")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🏭 Origem")
            st.info("**São Paulo - SP** (Fixo)")
            
            # Frete
            if hasattr(self, 'frete_padrao_cliente') and self.frete_padrao_cliente is not None:
                st.success(f"🚛 **Frete:** R$ {self.frete_padrao_cliente:.2f}/caixa")
                st.caption("Definido pela seleção do cliente")
                self.frete_padrao = self.frete_padrao_cliente
            else:
                self.frete_padrao = st.number_input(
                    "🚛 Frete/Caixa (R$)", 
                    min_value=0.0, 
                    value=1.50, 
                    step=0.01,
                    help="Frete padrão para cliente novo"
                )

            # Tipo de frete
            self.tipo_frete = st.radio(
                "📦 Tipo de Frete", 
                ("CIF", "FOB"),
                help="CIF: Vendedor paga frete | FOB: Comprador paga frete"
            )

        with col2:
            st.markdown("#### 📍 Destino")
            
            # UF de destino
            opcoes_uf = self.df_padrao["UF"].dropna().unique().tolist() if not self.df_padrao.empty else []
            
            if self.dados_cliente_selecionado is not None:
                uf_cliente = self.dados_cliente_selecionado['A1_EST']
                if uf_cliente in opcoes_uf:
                    index_uf = opcoes_uf.index(uf_cliente)
                    self.uf_selecionado = st.selectbox(
                        "🗺️ UF de Destino", 
                        options=opcoes_uf, 
                        index=index_uf,
                        help="UF do cliente selecionado"
                    )
                else:
                    st.error(f"❌ UF do cliente ({uf_cliente}) não encontrada na planilha!")
                    self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)
            else:
                self.uf_selecionado = st.selectbox("🗺️ UF de Destino", options=opcoes_uf)

            # Contrato
            if self.contrato_real is not None:
                st.success(f"📄 **Contrato:** {self.contrato_real:.2f}%")
                st.caption("Valor real do cliente")
                self.contrato_percentual = self.contrato_real / 100
            else:
                contrato_input = st.number_input(
                    "📄 % Contrato", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=1.00, 
                    step=0.01
                )
                self.contrato_percentual = contrato_input / 100

        with col3:
            st.markdown("#### 💰 Parâmetros Globais")
            
            self.custo_fixo_global = st.number_input(
                "🏗️ Custo Fixo Global (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            
            comissao_input = st.number_input(
                "🤝 % Comissão Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.1,
                help="Se zero, usa valor da planilha"
            )
            self.comissao_padrao = comissao_input / 100

            bonificacao_input = st.number_input(
                "🎁 % Bonificação Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha"
            )
            self.bonificacao_global = bonificacao_input / 100

        # Mostrar informações tributárias
        if self.uf_selecionado:
            st.markdown("#### 📋 Informações Tributárias")
            aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
            aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

            col_trib1, col_trib2, col_trib3 = st.columns(3)
            
            with col_trib1:
                st.metric("🏛️ ICMS Interestadual", f"{aliquotas_origem['interestadual']:.1%}")
            
            with col_trib2:
                st.metric("🏛️ ICMS Interno", f"{aliquotas_destino['interna']:.1%}")
            
            with col_trib3:
                if aliquotas_destino['fcp'] > 0:
                    st.metric("📊 FCP", f"{aliquotas_destino['fcp']:.1%}")
                else:
                    st.metric("📊 FCP", "Não aplicável")

    def _exibir_upload_arquivo(self):
        """Seção de upload melhorada"""
        st.markdown("### 📂 Gestão de Arquivos")
        
        col_upload, col_info = st.columns([2, 1])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "📊 Atualizar planilha de custos (.xlsx)", 
                type="xlsx",
                help="Substitui o arquivo 'Custo de reposição.xlsx'"
            )

            if uploaded_file:
                if st.button("🔄 Confirmar Atualização", type="primary"):
                    try:
                        with st.spinner("📤 Processando upload..."):
                            arquivo_padrao = "Custo de reposição.xlsx"

                            # Criar backup
                            if os.path.exists(arquivo_padrao):
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
                                os.rename(arquivo_padrao, backup_name)
                                st.success(f"✅ Backup criado: {backup_name}")

                            # Salvar novo arquivo
                            with open(arquivo_padrao, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Recarregar dados
                            self.df_padrao = pd.read_excel(arquivo_padrao)
                            self.df_padrao.columns = self.df_padrao.columns.str.strip()

                            # Resetar estado
                            self.gerenciador_estado.resetar_estado()
                            
                            st.success("✅ Arquivo atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        
        with col_info:
            # Informações sobre o arquivo atual
            if not self.df_padrao.empty:
                st.info(f"""
                **📋 Arquivo Atual:**
                - Produtos: {len(self.df_padrao)}
                - UFs: {len(self.df_padrao['UF'].unique()) if 'UF' in self.df_padrao.columns else 0}
                """)
            else:
                st.warning("⚠️ Nenhum arquivo carregado")

    def _validar_dados(self) -> bool:
        """Validação melhorada dos dados"""
        if self.df_padrao.empty:
            st.error("❌ Carregue uma planilha de custos para continuar.")
            return False
            
        if not self.uf_selecionado:
            st.warning("⚠️ Selecione uma UF de destino.")
            return False
            
        return True

    def _processar_simulacao(self):
        """Processa a simulação principal"""
        st.markdown("### 📊 Simulação de Preços")
        
        # Preparar dados base
        df_base = self._preparar_dados_base()

        if df_base.empty:
            st.error(f"❌ Nenhum produto encontrado para a UF {self.uf_selecionado}")
            return

        # Exibir controles
        self._exibir_controles(df_base)

        # Processar edição e resultados
        self._processar_edicao_e_resultados(df_base)

    def _preparar_dados_base(self) -> pd.DataFrame:
        """Prepara dados base com melhor tratamento"""
        # Filtrar por UF
        df_base = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado].copy()

        # Resetar se mudou UF
        if (st.session_state.df_atual is not None and 
            "UF" in st.session_state.df_atual.columns):
            ufs_atuais = st.session_state.df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != self.uf_selecionado:
                self.gerenciador_estado.resetar_estado()

        # Filtrar produtos esperados
        df_base = df_base[df_base["Descrição"].isin(self.produtos_esperados)].copy()

        # Ajustar colunas e aplicar parâmetros
        df_base = self._ajustar_colunas_necessarias(df_base)
        df_base = self._aplicar_parametros_globais(df_base)

        return df_base

    def _ajustar_colunas_necessarias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta colunas com melhor tratamento de valores padrão"""
        colunas_necessarias = [
            "Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", 
            "ICMS ST", "ICMS", "MVA", "Comissão", "Bonificação", "COFINS", "PIS", 
            "Contigência", "ICMS Interestadual", "ICMS Interno Destino", "FCP"
        ]

        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        for col in colunas_necessarias:
            if col not in df.columns:
                if col == "Quantidade":
                    df[col] = 1
                elif col == "ICMS Interestadual":
                    df[col] = aliquotas_origem['interestadual']
                elif col == "ICMS Interno Destino":
                    df[col] = aliquotas_destino['interna']
                elif col == "FCP":
                    df[col] = aliquotas_destino['fcp']
                else:
                    df[col] = 0.0

        return df

    def _aplicar_parametros_globais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica parâmetros globais com melhor organização"""
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)

        # Aplicar valores básicos
        df["Frete Caixa"] = self.frete_padrao
        df["Contrato"] = self.contrato_percentual
        df["UF Origem"] = 'SP'
        df["UF Destino"] = self.uf_selecionado
        df["ICMS Interestadual"] = aliquotas_origem['interestadual']
        df["ICMS Interno Destino"] = aliquotas_destino['interna']
        df["FCP"] = aliquotas_destino['fcp']

        # Aplicar parâmetros condicionais
        if self.custo_fixo_global > 0:
            df["Custo Fixo"] = self.custo_fixo_global

        if self.comissao_padrao > 0:
            df["Comissão"] = self.comissao_padrao
            st.session_state.comissao_global_aplicada = True
        else:
            st.session_state.comissao_global_aplicada = False

        if self.bonificacao_global > 0:
            df["Bonificação"] = self.bonificacao_global

        return df

    def _exibir_controles(self, df_base: pd.DataFrame):
        """Controles principais melhorados"""
        st.markdown("#### 🎯 Ações Principais")
        
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⚖️ Calcular Ponto de Equilíbrio", use_container_width=True, type="primary"):
                with st.spinner("⚖️ Calculando pontos de equilíbrio..."):
                    df_equilibrio, alertas = self._calcular_ponto_equilibrio(df_base)

                    if alertas:
                        for alerta in alertas:
                            st.warning(f"⚠️ {alerta}")

                    st.session_state.df_atual = df_equilibrio.copy()
                    st.session_state.modo_equilibrio = True
                    st.success("✅ Pontos de equilíbrio calculados!")

        with col2:
            if st.button("🔄 Resetar Simulação", use_container_width=True):
                self.gerenciador_estado.resetar_estado()
                st.success("✅ Dados resetados.")
                time.sleep(1)
                st.rerun()

        with col3:
            # Informações rápidas
            if not df_base.empty:
                st.metric("📦 Produtos", len(df_base))

    def _calcular_ponto_equilibrio(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """Cálculo melhorado do ponto de equilíbrio"""
        df_resultado = df.copy()
        alertas = []

        for index, row in df_resultado.iterrows():
            try:
                # Custos base
                custo_net = float(row.get("Custo NET", 0))
                custo_fixo = float(row.get("Custo Fixo", 0))
                custo_total_unit = custo_net + custo_fixo
                frete_unit = float(row.get("Frete Caixa", 0)) if self.tipo_frete == "CIF" else 0.0

                # Despesas percentuais
                despesas_diretas = (
                    float(row.get("ICMS Interestadual", 0)) +
                    float(row.get("COFINS", 0)) +
                    float(row.get("PIS", 0)) +
                    float(row.get("Comissão", 0)) +
                    float(row.get("Bonificação", 0)) +
                    float(row.get("Contigência", 0)) +
                    float(row.get("Contrato", 0)) +
                    float(row.get("%Estrategico", 0))
                )

                # Verificar viabilidade
                if despesas_diretas >= 1.0:
                    produto_nome = row.get('Descrição', f'Produto {index}')
                    alertas.append(f"{produto_nome}: Despesas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    custos_totais = custo_total_unit + frete_unit
                    preco_equilibrio = custos_totais / (1 - despesas_diretas)
                    preco_equilibrio = max(0.0, CalculadoraTributaria.arredondar_valor(preco_equilibrio, 2))

                df_resultado.at[index, "Preço de Venda"] = preco_equilibrio

            except Exception as e:
                produto_nome = row.get('Descrição', f'Produto {index}')
                alertas.append(f"Erro em {produto_nome}: {str(e)}")
                df_resultado.at[index, "Preço de Venda"] = 0.0

        return df_resultado, alertas

    def _processar_edicao_e_resultados(self, df_base: pd.DataFrame):
        """Processamento melhorado de edição e resultados"""
        # Determinar DataFrame
        if st.session_state.df_atual is not None:
            df_para_edicao = st.session_state.df_atual.copy()
        else:
            df_para_edicao = df_base.copy()

        # Aplicar lógica de comissão/bonificação
        df_para_edicao = self._aplicar_logica_comissao_bonificacao(df_para_edicao)

        # Exibir status e resumos
        self._exibir_status_melhorado()
        self._exibir_resumo_edicoes()

        # Editor de dados
        df_editado = self._exibir_editor_dados_melhorado(df_para_edicao)

        # Processar edições
        df_final = self._processar_dados_editados(df_editado, df_para_edicao)

        # Calcular e exibir resultados
        self._calcular_e_exibir_resultados(df_final)

    def _aplicar_logica_comissao_bonificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica lógica melhorada de comissão e bonificação"""
        df_temp = df.copy()

        # Garantir colunas numéricas
        for col in ["Comissão", "Bonificação"]:
            if col not in df_temp.columns:
                df_temp[col] = 0.0
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0.0)

        # Armazenar valores originais
        if not st.session_state.valores_originais:
            for index in df_temp.index:
                produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
                st.session_state.valores_originais[produto] = {
                    'comissao': float(df_temp.at[index, "Comissão"]),
                    'bonificacao': float(df_temp.at[index, "Bonificação"])
                }

        # Aplicar valores globais se não editados individualmente
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)

            # Comissão global
            if (st.session_state.comissao_global_aplicada and 
                self.comissao_padrao > 0 and 
                produto not in st.session_state.comissoes_editadas):
                df_temp.at[index, "Comissão"] = float(self.comissao_padrao)

            # Bonificação global
            if (self.bonificacao_global > 0 and 
                produto not in st.session_state.bonificacoes_editadas):
                df_temp.at[index, "Bonificação"] = float(self.bonificacao_global)

        # Aplicar edições individuais (prioridade máxima)
        for produto, valor in st.session_state.comissoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Comissão"] = float(valor)

        for produto, valor in st.session_state.bonificacoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Bonificação"] = float(valor)

        return df_temp

    def _exibir_status_melhorado(self):
        """Status melhorado da simulação"""
        # Card de status principal
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.metric("🗺️ Rota", f"SP → {self.uf_selecionado}")
            
        with col_status2:
            modo = "🔒 Equilíbrio" if st.session_state.modo_equilibrio else "📋 Normal"
            st.metric("⚙️ Modo", modo)
            
        with col_status3:
            frete_info = f"R$ {self.frete_padrao:.2f}" if hasattr(self, 'frete_padrao') else "N/A"
            st.metric("🚛 Frete/Caixa", frete_info)

        # Parâmetros ativos
        parametros_ativos = []
        if st.session_state.comissao_global_aplicada and self.comissao_padrao > 0:
            parametros_ativos.append(f"Comissão Global: {self.comissao_padrao:.1%}")
        if self.bonificacao_global > 0:
            parametros_ativos.append(f"Bonificação Global: {self.bonificacao_global:.1%}")

        if parametros_ativos:
            st.info(f"🎯 **Parâmetros Ativos:** {' | '.join(parametros_ativos)}")

        # Edições individuais
        edicoes = []
        if st.session_state.comissoes_editadas:
            edicoes.append(f"Comissões editadas: {len(st.session_state.comissoes_editadas)}")
        if st.session_state.bonificacoes_editadas:
            edicoes.append(f"Bonificações editadas: {len(st.session_state.bonificacoes_editadas)}")

        if edicoes:
            st.success(f"✏️ **Edições Individuais:** {' | '.join(edicoes)}")

    def _exibir_resumo_edicoes(self):
        """Resumo melhorado das edições"""
        if st.session_state.comissoes_editadas or st.session_state.bonificacoes_editadas:
            with st.expander("🎯 Detalhes das Edições Individuais", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🤝 Comissões Personalizadas:**")
                    if st.session_state.comissoes_editadas:
                        for produto, valor in st.session_state.comissoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('comissao', 0)
                            global_val = self.comissao_padrao if self.comissao_padrao > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                        
                        if st.button("🗑️ Limpar Comissões", key="clear_comissoes"):
                            st.session_state.comissoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma comissão editada")

                with col2:
                    st.markdown("**🎁 Bonificações Personalizadas:**")
                    if st.session_state.bonificacoes_editadas:
                        for produto, valor in st.session_state.bonificacoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('bonificacao', 0)
                            global_val = self.bonificacao_global if self.bonificacao_global > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                        
                        if st.button("🗑️ Limpar Bonificações", key="clear_bonificacoes"):
                            st.session_state.bonificacoes_editadas = {}
                            st.rerun()
                    else:
                        st.write("Nenhuma bonificação editada")

    def _exibir_editor_dados_melhorado(self, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Editor de dados melhorado"""
        st.markdown("#### 📊 Editor de Dados da Simulação")

        # Preparar dados para edição
        colunas_edicao = [
            "Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
            "MVA", "Comissão", "Bonificação", "Contrato"
        ]

        df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()

        # Converter valores numéricos
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_para_edicao_clean.columns:
                df_para_edicao_clean[col] = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)

        # Converter percentuais para formato 0-100
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_para_edicao_clean.columns:
                valores = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = (valores * 100).round(2)

        # Editor com melhor configuração
        df_editado = st.data_editor(
            df_para_edicao_clean,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_principal",
            column_config={
                "Descrição": st.column_config.TextColumn(
                    "📦 Produto", 
                    disabled=True, 
                    width="medium"
                ),
                "Preço de Venda": st.column_config.NumberColumn(
                    "💰 Preço Venda", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "📦 Qtd", 
                    format="%.0f", 
                    min_value=1, 
                    step=1,
                    width="small"
                ),
                "Custo NET": st.column_config.NumberColumn(
                    "💵 Custo NET", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "Custo Fixo": st.column_config.NumberColumn(
                    "🏗️ Custo Fixo", 
                    format="R$ %.2f", 
                    min_value=0.0, 
                    step=0.01,
                    width="small"
                ),
                "MVA": st.column_config.NumberColumn(
                    "📈 MVA (%)", 
                    format="%.1f%%", 
                    min_value=0.0, 
                    max_value=500.0, 
                    step=0.1,
                    width="small"
                ),
                "Comissão": st.column_config.NumberColumn(
                    "🤝 Comissão (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Bonificação": st.column_config.NumberColumn(
                    "🎁 Bonificação (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                ),
                "Contrato": st.column_config.NumberColumn(
                    "📄 Contrato (%) ⭐", 
                    format="%.2f%%", 
                    min_value=0.0, 
                    max_value=50.0, 
                    step=0.1,
                    help="⭐ Editável individualmente",
                    width="small"
                )
            },
            hide_index=True
        )

        # Dicas de uso
        st.info("💡 **Dicas:** Use ⭐ para editar valores individualmente. Clique duas vezes nas células para editar.")

        return df_editado

    def _processar_dados_editados(self, df_editado: pd.DataFrame, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Processamento melhorado dos dados editados"""
        df_processado = df_editado.copy()

        # Converter percentuais de volta para decimal
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_processado.columns:
                df_processado[col] = pd.to_numeric(df_processado[col], errors='coerce').fillna(0.0) / 100

        # Arredondar valores
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_processado.columns:
                df_processado[col] = df_processado[col].round(2)

        # Detectar mudanças com melhor feedback
        produtos_com_mudancas = []

        for index in df_processado.index:
            if index < len(df_para_edicao):
                produto = df_processado.at[index, "Descrição"]

                # Verificar comissão
                try:
                    comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
                    comissao_editada = float(df_processado.at[index, "Comissão"])

                    if abs(comissao_original - comissao_editada) > 0.001:
                        st.session_state.comissoes_editadas[produto] = comissao_editada
                        produtos_com_mudancas.append(f"Comissão {produto}: {formatar_percentual_brasileiro(comissao_editada * 100)}")
                except:
                    pass

                # Verificar bonificação
                try:
                    bonificacao_original = float(df_para_edicao.iloc[index]["Bonificação"])
                    bonificacao_editada = float(df_processado.at[index, "Bonificação"])

                    if abs(bonificacao_original - bonificacao_editada) > 0.001:
                        st.session_state.bonificacoes_editadas[produto] = bonificacao_editada
                        produtos_com_mudancas.append(f"Bonificação {produto}: {formatar_percentual_brasileiro(bonificacao_editada * 100)}")
                except:
                    pass

        # Feedback sobre mudanças
        if produtos_com_mudancas:
            mudancas_texto = ', '.join(produtos_com_mudancas[:3])
            if len(produtos_com_mudancas) > 3:
                mudancas_texto += f" e mais {len(produtos_com_mudancas) - 3}"
            st.success(f"✏️ **Mudanças detectadas:** {mudancas_texto}")

        # Criar DataFrame final
        df_final = df_para_edicao.copy()
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                         "Custo Fixo", "MVA", "Comissão", "Bonificação", "Contrato"]

        for col in colunas_edicao:
            if col in df_processado.columns:
                df_final[col] = df_processado[col]

        st.session_state.df_edicao_temp = df_final.copy()
        return df_final

    def _calcular_e_exibir_resultados(self, df_final: pd.DataFrame):
        """Cálculo e exibição melhorados dos resultados"""
        st.markdown("#### 🚀 Resultados da Simulação")
        
        # Botão principal de cálculo
        col_calc, col_space = st.columns([2, 3])
        with col_calc:
            calcular_clicked = st.button(
                "🚀 Calcular Resultados Finais", 
                type="primary", 
                use_container_width=True
            )

        if calcular_clicked:
            with st.spinner("🔄 Processando cálculos..."):
                # Otimização de frete se disponível
                self._otimizar_frete_por_volume(df_final)

                # Armazenar dados
                st.session_state.df_atual = st.session_state.df_edicao_temp.copy()
                st.session_state.resultados_atualizados = True
                
                time.sleep(1)  # UX melhor
                st.rerun()

        # Mostrar resultados se disponível
        if st.session_state.get("resultados_atualizados", False):
            self._exibir_resultados_completos(df_final)

    def _otimizar_frete_por_volume(self, df_final: pd.DataFrame):
        """Otimização inteligente de frete por volume"""
        if (hasattr(st.session_state, 'resultado_frete_completo') and 
            st.session_state.resultado_frete_completo):

            volume_total = df_final["Quantidade"].sum()
            
            # Reavalia otimização
            nova_otimizacao = calcular_frete_otimizado(
                st.session_state.resultado_frete_completo, 
                volume_total
            )

            # Verificar mudanças
            otimizacao_anterior = st.session_state.get('otimizacao_frete', {})
            veiculo_anterior = otimizacao_anterior.get('veiculo_otimo', 'desconhecido')
            veiculo_novo = nova_otimizacao['veiculo_otimo']

            # Atualizar frete se necessário
            if veiculo_novo != veiculo_anterior and nova_otimizacao['frete_por_caixa'] > 0:
                df_final["Frete Caixa"] = nova_otimizacao['frete_por_caixa']

                # Alertar sobre otimização
                if nova_otimizacao['economia'] > 0:
                    st.success(f"""
                    🎯 **FRETE OTIMIZADO AUTOMATICAMENTE!**
                    
                    📦 Volume total: {volume_total} caixas
                    {nova_otimizacao['alerta']}
                    💰 Novo frete/caixa: R$ {nova_otimizacao['frete_por_caixa']:.2f}
                    """)
                else:
                    st.info(f"ℹ️ {nova_otimizacao['alerta']}")

            st.session_state.otimizacao_frete = nova_otimizacao

    def _exibir_resultados_completos(self, df_final: pd.DataFrame):
        """Exibição completa e melhorada dos resultados"""
        # Calcular resultados
        calculadora = CalculadoraResultados(self.tipo_frete)
        resultados = df_final.apply(calculadora.calcular_resultados_completos, axis=1)

        # Criar DataFrame para exibição
        df_display = self._criar_dataframe_display_melhorado(df_final, resultados)

        # Informações de otimização
        self._exibir_info_otimizacao(df_final)

        # Tabela principal de resultados
        self._exibir_tabela_resultados_melhorada(df_display)

        # Resumo executivo
        self._exibir_resumo_executivo_melhorado(df_display)

        # Análises detalhadas
        self._exibir_analises_detalhadas(df_final, resultados, df_display)

        # Seção de exportação
        self._exibir_secao_exportacao_melhorada(df_final, resultados, df_display)

    def _criar_dataframe_display_melhorado(self, df_final: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame melhorado para exibição"""
        df_display = pd.DataFrame({
            "Produto": df_final["Descrição"].values,
            "Preço Venda": resultados["Preço Venda"].values,
            "Qtd": resultados["Qtd"].values.astype(int),
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

        # Arredondamento melhorado
        colunas_monetarias = [
            "Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
            "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
            "Lucro Líquido", "Equilíbrio"
        ]

        for col in colunas_monetarias:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: CalculadoraTributaria.arredondar_valor(x, 2)
                )

        df_display["Margem %"] = df_display["Margem %"].apply(
            lambda x: CalculadoraTributaria.arredondar_valor(x, 1)
        )

        return df_display

    def _exibir_info_otimizacao(self, df_final: pd.DataFrame):
        """Exibe informações de otimização de frete"""
        if hasattr(st.session_state, 'otimizacao_frete') and st.session_state.otimizacao_frete:
            otimizacao = st.session_state.otimizacao_frete

            if otimizacao['veiculo_otimo'] != 'nenhum':
                col_opt1, col_opt2, col_opt3, col_opt4 = st.columns(4)

                with col_opt1:
                    volume_total = df_final["Quantidade"].sum()
                    st.metric("📦 Volume Total", f"{volume_total} caixas")

                with col_opt2:
                    veiculo_label = otimizacao['veiculo_otimo'].replace('_', ' ').upper()
                    st.metric("🚛 Veículo Otimizado", veiculo_label)

                with col_opt3:
                    st.metric("💰 Frete Total", f"R$ {otimizacao['frete_total']:.2f}")

                with col_opt4:
                    if otimizacao['economia'] > 0:
                        st.metric("💰 Economia", f"R$ {otimizacao['economia']:.2f}", delta="Positiva")
                    else:
                        st.metric("📊 Status", "Otimizado")

    def _exibir_tabela_resultados_melhorada(self, df_display: pd.DataFrame):
        """Tabela de resultados com melhor formatação"""
        st.markdown("#### 📊 Resultados Detalhados")

        # Função de coloração melhorada
        def colorir_valores(val):
            try:
                if isinstance(val, (int, float)):
                    if val < 0:
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                    elif val > 0:
                        return 'background-color: #e8f5e8; color: #2e7d32'
                    else:
                        return 'color: #666666'
                return ''
            except:
                return ''

        # Formatação aprimorada
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
        }).applymap(
            colorir_valores, 
            subset=["Lucro Antes IR", "Lucro Líquido", "Margem %"]
        ).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f0f2f6'), ('color', '#262730'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '8px'), ('text-align', 'right')]},
            {'selector': 'td:first-child', 'props': [('text-align', 'left'), ('font-weight', 'bold')]}
        ])

        st.dataframe(styled_display, use_container_width=True, height=400)

    def _exibir_resumo_executivo_melhorado(self, df_display: pd.DataFrame):
        """Resumo executivo melhorado"""
        st.markdown("#### 📈 Resumo Executivo")

        if len(df_display) > 0:
            # Métricas principais
            col1, col2, col3, col4, col5 = st.columns(5)

            total_receita = df_display["Subtotal"].sum()
            total_lucro_liquido = df_display["Lucro Líquido"].sum()
            margem_ponderada = (total_lucro_liquido / total_receita) * 100 if total_receita > 0 else 0.0
            produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
            total_nf = df_display["Total NF"].sum()

            with col1:
                st.metric("💰 Receita Total", f"R$ {total_receita:,.2f}")

            with col2:
                delta_lucro = f"{margem_ponderada:.1f}%" if total_receita > 0 else "0%"
                delta_color = "normal" if total_lucro_liquido >= 0 else "inverse"
                st.metric("💵 Lucro Líquido", f"R$ {total_lucro_liquido:,.2f}", delta=delta_lucro)

            with col3:
                cor_margem = "🟢" if margem_ponderada > 10 else "🟡" if margem_ponderada > 5 else "🔴"
                st.metric("📊 Margem Ponderada", f"{cor_margem} {margem_ponderada:.1f}%")

            with col4:
                cor_produtos = "🔴" if produtos_prejuizo > 0 else "🟢"
                st.metric("⚠️ Produtos c/ Prejuízo", f"{cor_produtos} {produtos_prejuizo}")

            with col5:
                st.metric("📄 Total NF", f"R$ {total_nf:,.2f}")

            # Alertas inteligentes
            self._exibir_alertas_inteligentes(df_display, margem_ponderada, produtos_prejuizo)

    def _exibir_alertas_inteligentes(self, df_display: pd.DataFrame, margem_ponderada: float, produtos_prejuizo: int):
        """Sistema de alertas inteligentes"""
        alertas = []

        # Análise de margem
        if margem_ponderada < 5:
            alertas.append("🔴 **ATENÇÃO:** Margem muito baixa (< 5%). Revisar preços ou custos.")
        elif margem_ponderada < 10:
            alertas.append("🟡 **CUIDADO:** Margem baixa (< 10%). Monitorar competitividade.")
        elif margem_ponderada > 25:
            alertas.append("🟢 **EXCELENTE:** Margem alta (> 25%). Ótima rentabilidade!")

        # Análise de produtos
        if produtos_prejuizo > 0:
            produtos_negativos = df_display[df_display["Lucro Líquido"] < 0]
            maior_prejuizo = produtos_negativos.nlargest(1, "Lucro Líquido")
            if not maior_prejuizo.empty:
                produto_problema = maior_prejuizo.iloc[0]["Produto"]
                prejuizo_valor = maior_prejuizo.iloc[0]["Lucro Líquido"]
                alertas.append(f"🚨 **PRODUTO CRÍTICO:** {produto_problema} com prejuízo de R$ {abs(prejuizo_valor):.2f}")

        # Análise de concentração
        receita_por_produto = df_display["Subtotal"]
        produto_principal = df_display.loc[receita_por_produto.idxmax(), "Produto"]
        concentracao = (receita_por_produto.max() / receita_por_produto.sum()) * 100
        if concentracao > 50:
            alertas.append(f"📊 **CONCENTRAÇÃO:** {concentracao:.1f}% da receita vem de '{produto_principal}'")

        # Exibir alertas
        for alerta in alertas:
            if "🔴" in alerta or "🚨" in alerta:
                st.error(alerta)
            elif "🟡" in alerta:
                st.warning(alerta)
            else:
                st.success(alerta)

    def _exibir_analises_detalhadas(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Análises detalhadas melhoradas"""
        with st.expander("🔍 Análises Detalhadas", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📊 Composição", "🎯 Top Produtos", "📋 Breakdown"])

            with tab1:
                self._exibir_analise_composicao(df_display)

            with tab2:
                self._exibir_top_produtos(df_display)

            with tab3:
                self._exibir_breakdown_calculo(df_final, resultados)

    def _exibir_analise_composicao(self, df_display: pd.DataFrame):
        """Análise de composição dos resultados"""
        st.markdown("**📊 Composição dos Resultados**")

        # Análise de receita por produto
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Contribuição por Receita**")
            receita_sorted = df_display.nlargest(5, "Subtotal")[["Produto", "Subtotal", "Margem %"]]
            for idx, row in receita_sorted.iterrows():
                participacao = (row["Subtotal"] / df_display["Subtotal"].sum()) * 100
                st.write(f"• {row['Produto']}: R$ {row['Subtotal']:,.2f} ({participacao:.1f}%) - Margem: {row['Margem %']:.1f}%")

        with col2:
            st.markdown("**🎯 Contribuição por Lucro**")
            lucro_sorted = df_display.nlargest(5, "Lucro Líquido")[["Produto", "Lucro Líquido", "Margem %"]]
            for idx, row in lucro_sorted.iterrows():
                if df_display["Lucro Líquido"].sum() > 0:
                    participacao = (row["Lucro Líquido"] / df_display["Lucro Líquido"].sum()) * 100
                else:
                    participacao = 0
                st.write(f"• {row['Produto']}: R$ {row['Lucro Líquido']:,.2f} ({participacao:.1f}%) - Margem: {row['Margem %']:.1f}%")

    def _exibir_top_produtos(self, df_display: pd.DataFrame):
        """Análise dos top produtos"""
        st.markdown("**🏆 Rankings de Produtos**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🥇 Maiores Receitas**")
            top_receita = df_display.nlargest(3, "Subtotal")[["Produto", "Subtotal"]]
            for i, (idx, row) in enumerate(top_receita.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: R$ {row['Subtotal']:,.2f}")

        with col2:
            st.markdown("**💰 Maiores Lucros**")
            top_lucro = df_display.nlargest(3, "Lucro Líquido")[["Produto", "Lucro Líquido"]]
            for i, (idx, row) in enumerate(top_lucro.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: R$ {row['Lucro Líquido']:,.2f}")

        with col3:
            st.markdown("**📈 Maiores Margens**")
            top_margem = df_display.nlargest(3, "Margem %")[["Produto", "Margem %"]]
            for i, (idx, row) in enumerate(top_margem.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                st.write(f"{emoji} {row['Produto']}: {row['Margem %']:.1f}%")

        # Produtos que precisam de atenção
        produtos_atencao = df_display[df_display["Margem %"] < 5]
        if not produtos_atencao.empty:
            st.markdown("**⚠️ Produtos que Precisam de Atenção (Margem < 5%)**")
            for idx, row in produtos_atencao.iterrows():
                st.write(f"🔴 {row['Produto']}: Margem {row['Margem %']:.1f}% - Lucro R$ {row['Lucro Líquido']:,.2f}")

    def _exibir_breakdown_calculo(self, df_final: pd.DataFrame, resultados: pd.DataFrame):
        """Breakdown detalhado do cálculo"""
        st.markdown("**🔍 Breakdown do Cálculo (Primeiro Produto)**")

        if len(resultados) > 0:
            primeiro = resultados.iloc[0]
            produto_nome = df_final.iloc[0]["Descrição"]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**📦 Base do Produto**")
                st.write(f"• Produto: {produto_nome}")
                st.write(f"• Preço Unitário: R$ {primeiro['Preço Venda']:.2f}")
                st.write(f"• Quantidade: {primeiro['Qtd']:.0f}")
                st.write(f"• **Subtotal: R$ {primeiro['Subtotal']:.2f}**")
                st.write(f"• IPI: R$ {primeiro['IPI']:.2f}")

            with col2:
                st.markdown("**🏛️ Impostos e Contribuições**")
                st.write(f"• Base ICMS-ST: R$ {primeiro['Base ICMS-ST']:.2f}")
                st.write(f"• ICMS Próprio: R$ {primeiro['ICMS Próprio']:.2f}")
                st.write(f"• ICMS-ST: R$ {primeiro['ICMS-ST']:.2f}")
                st.write(f"• FCP: R$ {primeiro['FCP']:.2f}")
                st.write(f"• **Total NF: R$ {primeiro['Total NF']:.2f}**")

            with col3:
                st.markdown("**💰 Resultado Financeiro**")
                st.write(f"• Custo Total: R$ {primeiro['Custo Total']:.2f}")
                st.write(f"• Despesas: R$ {primeiro['Total Despesas']:.2f}")
                st.write(f"• Frete: R$ {primeiro['Frete Total']:.2f}")
                st.write(f"• Lucro Antes IR: R$ {primeiro['Lucro Antes IR']:.2f}")
                st.write(f"• IRPJ + CSLL: R$ {primeiro['IRPJ'] + primeiro['CSLL']:.2f}")
                st.write(f"• **Lucro Líquido: R$ {primeiro['Lucro Líquido']:.2f}**")
                st.write(f"• **Margem: {primeiro['Margem Líquida %']:.1f}%**")

            # Fórmulas utilizadas
            st.markdown("**📐 Fórmulas Principais**")
            st.code("""
            Subtotal = Preço × Quantidade
            ICMS-ST = max(0, (Subtotal × (1 + MVA) × ICMS_Destino) - (Subtotal × ICMS_Origem))
            Lucro Antes IR = Subtotal - Custos - Despesas - Frete
            Lucro Líquido = Lucro Antes IR - IRPJ - CSLL
            Margem = (Lucro Líquido / Subtotal) × 100
            """)

    def _exibir_secao_exportacao_melhorada(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Seção de exportação melhorada"""
        st.markdown("#### 📄 Exportar e Compartilhar")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Excel Completo", use_container_width=True, type="primary"):
                excel_buffer = self._gerar_excel_completo(df_final, resultados, df_display)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"simulacao_sobel_SP_{self.uf_selecionado}_{timestamp}.xlsx"
                
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=excel_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with col2:
            if st.button("📋 Relatório PDF", use_container_width=True):
                st.info("🚧 Funcionalidade em desenvolvimento")

        with col3:
            if st.button("📱 Resumo para WhatsApp", use_container_width=True):
                resumo_whatsapp = self._gerar_resumo_whatsapp(df_display)
                st.text_area("📱 Copie e cole no WhatsApp:", resumo_whatsapp, height=200)

    def _gerar_excel_completo(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame) -> io.BytesIO:
        """Gera Excel completo com múltiplas abas"""
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            # Aba 1: Resultados principais
            df_display.to_excel(writer, index=False, sheet_name="Resultados")
            
            # Aba 2: Dados de entrada
            colunas_entrada = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", 
                              "Custo Fixo", "MVA", "Comissão", "Bonificação"]
            df_entrada = df_final[colunas_entrada]
            df_entrada.to_excel(writer, index=False, sheet_name="Dados_Entrada")
            
            # Aba 3: Cálculos detalhados
            df_completo = pd.concat([df_final[colunas_entrada], resultados], axis=1)
            df_completo.to_excel(writer, index=False, sheet_name="Calculos_Completos")
            
            # Aba 4: Resumo executivo
            resumo_data = {
                "Métrica": [
                    "Receita Total", "Lucro Líquido Total", "Margem Ponderada", 
                    "Produtos com Prejuízo", "Total da Nota Fiscal", "Quantidade Total"
                ],
                "Valor": [
                    f"R$ {df_display['Subtotal'].sum():,.2f}",
                    f"R$ {df_display['Lucro Líquido'].sum():,.2f}",
                    f"{(df_display['Lucro Líquido'].sum()/df_display['Subtotal'].sum()*100):.1f}%",
                    len(df_display[df_display["Lucro Líquido"] < 0]),
                    f"R$ {df_display['Total NF'].sum():,.2f}",
                    f"{df_display['Qtd'].sum():,.0f} caixas"
                ]
            }
            resumo_df = pd.DataFrame(resumo_data)
            resumo_df.to_excel(writer, index=False, sheet_name="Resumo_Executivo")
            
            # Aba 5: Parâmetros utilizados
            parametros_data = {
                "Parâmetro": [
                    "UF Origem", "UF Destino", "Tipo de Frete", "Frete por Caixa",
                    "% Contrato", "% Comissão Global", "% Bonificação Global"
                ],
                "Valor": [
                    "SP", self.uf_selecionado, self.tipo_frete, 
                    f"R$ {self.frete_padrao:.2f}",
                    f"{self.contrato_percentual:.2%}",
                    f"{self.comissao_padrao:.2%}" if self.comissao_padrao > 0 else "N/A",
                    f"{self.bonificacao_global:.2%}" if self.bonificacao_global > 0 else "N/A"
                ]
            }
            parametros_df = pd.DataFrame(parametros_data)
            parametros_df.to_excel(writer, index=False, sheet_name="Parametros")

        return excel_buffer

    def _gerar_resumo_whatsapp(self, df_display: pd.DataFrame) -> str:
        """Gera resumo formatado para WhatsApp"""
        total_receita = df_display["Subtotal"].sum()
        total_lucro = df_display["Lucro Líquido"].sum()
        margem = (total_lucro / total_receita * 100) if total_receita > 0 else 0
        produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
        
        resumo = f"""
🏢 *SIMULAÇÃO SOBEL - RESUMO EXECUTIVO*
📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🗺️ *Rota:* SP → {self.uf_selecionado}
📦 *Produtos:* {len(df_display)} itens

💰 *RESULTADOS FINANCEIROS:*
• Receita Total: R$ {total_receita:,.2f}
• Lucro Líquido: R$ {total_lucro:,.2f}
• Margem Ponderada: {margem:.1f}%
• Produtos c/ Prejuízo: {produtos_prejuizo}

🏆 *TOP 3 PRODUTOS POR RECEITA:*
"""
        
        top3_receita = df_display.nlargest(3, "Subtotal")
        for i, (_, row) in enumerate(top3_receita.iterrows(), 1):
            resumo += f"{i}. {row['Produto']}: R$ {row['Subtotal']:,.2f} (Margem: {row['Margem %']:.1f}%)\n"
        
        resumo += f"""
⚠️ *ALERTAS:*
"""
        if margem < 5:
            resumo += "🔴 Margem muito baixa - Revisar preços\n"
        elif margem < 10:
            resumo += "🟡 Margem baixa - Monitorar\n"
        else:
            resumo += "🟢 Margem adequada\n"
            
        if produtos_prejuizo > 0:
            resumo += f"🚨 {produtos_prejuizo} produtos com prejuízo\n"
        
        resumo += "\n🤖 _Gerado pelo Simulador Sobel v3.0_"
        
        return resumo

    def _exibir_relatorios(self):
        """Seção de relatórios e análises históricas"""
        st.markdown("### 📈 Relatórios e Análises")
        
        if not st.session_state.get("resultados_atualizados", False):
            st.info("ℹ️ Execute uma simulação primeiro para gerar relatórios.")
            return
        
        # Placeholder para funcionalidades futuras
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📊 Relatórios Disponíveis
            - 📈 Análise de margem por produto
            - 🎯 Comparativo de cenários
            - 📋 Histórico de simulações
            - 🏆 Ranking de produtos
            """)
            
        with col2:
            st.markdown("""
            #### 🚧 Em Desenvolvimento
            - 📅 Análise temporal
            - 🔄 Comparativo com concorrência
            - 📊 Dashboard executivo
            - 📱 Relatórios mobile
            """)
        
        st.info("💡 **Sugestão:** Use a funcionalidade de exportação para análises externas detalhadas.")

# Função principal melhorada
def main():
    """Função principal com melhor tratamento de erros"""
    try:
        # Verificações iniciais
        if 'inicializado' not in st.session_state:
            st.session_state.inicializado = True
            st.balloons()  # Feedback visual de carregamento
        
        # Executar simulador
        simulador = SimuladorSobel()
        simulador.executar()
        
        # Notas técnicas no final
        st.markdown("---")
        st.markdown("""
        ### 📚 Notas Técnicas - Simulador Sobel v3.0

        #### 🎯 **Estados com FCP (Fundo de Combate à Pobreza):**
        - **2,0%:** AC, AL, BA, MA, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, SC, SE
        - **2,5%:** CE
        - **0,0%:** AP, AM, DF, ES, GO, MT, RO, RR, SP, TO

        #### 🔧 **Funcionalidades Principais:**
        - ✅ Cálculo automático de ICMS-ST por UF
        - ✅ Otimização inteligente de frete por volume
        - ✅ Geolocalização e cálculo de rotas
        - ✅ Edição individual de comissões e bonificações
        - ✅ Exportação completa para Excel
        - ✅ Análises detalhadas e alertas inteligentes

        #### 📊 **Melhorias v3.0:**
        - Interface redesenhada com melhor UX/UI
        - Sistema de alertas inteligentes
        - Otimização automática de frete
        - Análises detalhadas por produto
        - Exportação aprimorada
        - Tratamento de erros melhorado

        ---
        *Desenvolvido para Sobel Suprema - Sistema integrado de simulação de preços*
        """)
        
    except Exception as e:
        st.error(f"""
        🚨 **Erro Crítico na Aplicação**
        
        **Detalhes do erro:** {str(e)}
        
        **Ações recomendadas:**
        1. 🔄 Recarregue a página (F5)
        2. 🧹 Limpe o cache do navegador
        3. 📞 Entre em contato com o suporte técnico
        
        **Informações técnicas:**
        - Versão: Simulador Sobel v3.0
        - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        # Log de erro para debug
        import traceback
        st.expander("🔧 Detalhes Técnicos (Para Suporte)", expanded=False).code(
            traceback.format_exc()
        )

# Executar aplicação
if __name__ == "__main__":
    main()