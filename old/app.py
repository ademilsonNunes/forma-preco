# Configuração da página - DEVE SER A PRIMEIRA COISA!
import streamlit as st

# Configurar página ANTES de qualquer outro comando Streamlit
st.set_page_config(
    page_title="Simulador de Preço de Venda Sobel", 
    layout="wide"
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
    Retorna: {
        'truck': {'valor': float, 'faixa_usada': str, 'metodo': str},
        'carreta': {'valor': float, 'faixa_usada': str, 'metodo': str},
        'capacidades': {'truck': int, 'carreta': int}
    }
    """
    resultado = {
        'truck': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'carreta': {'valor': 0.0, 'faixa_usada': 'não encontrada', 'metodo': 'não encontrado'},
        'capacidades': {'truck': 870, 'carreta': 1740}  # Capacidades médias da tabela
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
    Retorna: {
        'veiculo_otimo': str,
        'frete_total': float,
        'frete_por_caixa': float,
        'economia': float,
        'alerta': str,
        'detalhes': dict
    }
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
    
    # Calcular economia (comparar com carreta se não for a melhor opção)
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
    Busca o valor do frete de forma inteligente:
    1. Primeiro: busca exata por IBGE + faixa
    2. Segundo: busca por IBGE e calcula pela faixa mais próxima
    3. Retorna: (valor_frete, faixa_usada, metodo_usado)
    """
    
    # Primeira tentativa: busca exata por cidade_ibge e faixa
    linha_exata = df_clientes[
        (df_clientes['cidade_ibge'] == cidade_ibge) &
        (df_clientes['FAIXA_KM'] == faixa_km)
    ]
    
    if not linha_exata.empty:
        # Encontrou correspondência exata
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
        # Extrair distância da faixa solicitada para comparação
        distancia_solicitada = extrair_distancia_da_faixa(faixa_km)
        
        if distancia_solicitada is not None:
            # Encontrar a faixa mais próxima disponível para este IBGE
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
            
            # Se encontrou uma faixa próxima, calcular o valor
            if melhor_linha is not None:
                if tipo_veiculo == 'truck':
                    valor = melhor_linha['TBL_TRCK'] if not pd.isna(melhor_linha['TBL_TRCK']) else 0.0
                elif tipo_veiculo == 'carreta':
                    valor = melhor_linha['TBL_CRRT'] if 'TBL_CRRT' in melhor_linha and not pd.isna(melhor_linha['TBL_CRRT']) else 0.0
                else:
                    valor = 0.0
                
                if valor > 0:
                    return float(valor), melhor_faixa, f"aproximada (IBGE {cidade_ibge})"
        
        # Se não conseguiu calcular por proximidade, pegar qualquer valor do IBGE
        if tipo_veiculo == 'truck':
            valores_validos = linhas_ibge['TBL_TRCK'].dropna()
            if not valores_validos.empty:
                primeira_linha = linhas_ibge[linhas_ibge['TBL_TRCK'].notna()].iloc[0]
                return float(valores_validos.iloc[0]), primeira_linha['FAIXA_KM'], f"IBGE {cidade_ibge} (primeira disponível)"
        elif tipo_veiculo == 'carreta':
            if 'TBL_CRRT' in linhas_ibge.columns:
                valores_validos = linhas_ibge['TBL_CRRT'].dropna()
                if not valores_validos.empty:
                    primeira_linha = linhas_ibge[linhas_ibge['TBL_CRRT'].notna()].iloc[0]
                    return float(valores_validos.iloc[0]), primeira_linha['FAIXA_KM'], f"IBGE {cidade_ibge} (primeira disponível)"
    
    # Terceira tentativa: buscar por região (primeiros dígitos do IBGE)
    if len(cidade_ibge) >= 4:
        prefixo_ibge = cidade_ibge[:4]
        linhas_similar = df_clientes[df_clientes['cidade_ibge'].str.startswith(prefixo_ibge)]
        
        if not linhas_similar.empty:
            if tipo_veiculo == 'truck':
                valores_validos = linhas_similar['TBL_TRCK'].dropna()
                if not valores_validos.empty:
                    return float(valores_validos.median()), "regional", f"regional ({prefixo_ibge}*)"
            elif tipo_veiculo == 'carreta':
                if 'TBL_CRRT' in linhas_similar.columns:
                    valores_validos = linhas_similar['TBL_CRRT'].dropna()
                    if not valores_validos.empty:
                        return float(valores_validos.median()), "regional", f"regional ({prefixo_ibge}*)"
    
    # Se nada funcionou, retorna 0
    return 0.0, "não encontrada", "não encontrado"


def extrair_distancia_da_faixa(faixa: str) -> float:
    """Extrai a distância média de uma faixa (ex: '100-200' -> 150)"""
    try:
        faixa_str = str(faixa).strip()
        
        if '+' in faixa_str:
            # Faixa aberta: "1000+" -> retorna o valor inicial + 50
            valor = int(faixa_str.replace('+', '').strip())
            return float(valor + 50)
        elif '-' in faixa_str:
            # Faixa fechada: "100-200" -> retorna a média (150)
            partes = faixa_str.split('-')
            if len(partes) == 2:
                ini, fim = int(partes[0].strip()), int(partes[1].strip())
                return float((ini + fim) / 2)
        else:
            # Faixa única: "50" -> retorna o valor
            return float(faixa_str)
    except (ValueError, IndexError):
        return None

# Carrega chave da API
load_dotenv()

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
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data["status"] == "OK" and data["results"]:
                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
            return None, None
        except Exception as e:
            st.error(f"Erro na geocodificação: {str(e)}")
            return None, None
    
    def calcular_distancia(self, origem_coords: Tuple[float, float], 
                          destino_coords: Tuple[float, float]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Consulta a Distance Matrix API e retorna distância e tempo"""
        try:
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
            with pyodbc.connect(_self.connection_string) as conexao:
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
            st.error(f"Erro ao carregar dados dos clientes: {e}")
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
            
            # Adicionar FCP como despesa
            total_despesas_operacionais = despesas_operacionais + fcp_valor

            # Lucro antes dos impostos sobre lucro
            lucro_antes_ir = CalculadoraTributaria.arredondar_valor(
                subtotal - custo_total - total_despesas_operacionais - frete_total
            )

            # Calcular IR e CSLL
            irpj, csll = self._calcular_ir_csll(lucro_antes_ir)
            
            # Lucro líquido
            lucro_liquido = CalculadoraTributaria.arredondar_valor(lucro_antes_ir - irpj - csll)

            # Margens
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
            st.error(f"Erro no cálculo: {str(e)}")
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
            'usar_frete_auto': False
        }
        
        for key, value in estados_default.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def resetar_estado(self):
        """Reseta o estado da aplicação"""
        st.session_state.df_atual = None
        st.session_state.modo_equilibrio = False
        st.session_state.comissao_global_aplicada = False
        st.session_state.comissoes_editadas = {}
        st.session_state.bonificacoes_editadas = {}
        st.session_state.valores_originais = {}
        st.session_state.df_edicao_temp = None
        st.session_state.resultados_atualizados = False
        st.session_state.frete_calculado_automatico = 0.0
        st.session_state.distancia_calculada = None
        st.session_state.tempo_calculado = None
        st.session_state.usar_frete_auto = False

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
            "AGUA SANITARIA 5L", "AGUA SANITARIA 2L", "AGUA SANITARIA 1L",
            "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
            "AMACIANTE 5L", "AMACIANTE 2L",
            "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
            "LAVA LOUCAS 500ML", "LAVA LOUCAS 5L",
            "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
            "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
            "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
        ]
        
        # Novos atributos para controle de cliente e frete
        self.dados_cliente_selecionado = None
        self.frete_padrao_cliente = None
        # Faixas de KM extraídas da query de clientes
        self.faixas_km_ordenadas = self._extrair_faixas_ordenadas()
    
    def _extrair_faixas_ordenadas(self) -> list:
        """Extrai e ordena as faixas de KM disponíveis da base de clientes"""
        try:
            df_clientes = self.db_manager.carregar_clientes_ou_rede()
            faixas = []
            faixas_unicas = df_clientes['FAIXA_KM'].dropna().unique()
            
            for faixa in faixas_unicas:
                try:
                    faixa_str = str(faixa).strip()
                    if '+' in faixa_str:
                        # Faixa aberta: "1000+"
                        ini = int(faixa_str.replace('+', '').strip())
                        faixas.append((ini, float('inf'), faixa_str))
                    elif '-' in faixa_str:
                        # Faixa fechada: "100-200"
                        partes = faixa_str.split('-')
                        if len(partes) == 2:
                            ini, fim = int(partes[0].strip()), int(partes[1].strip())
                            faixas.append((ini, fim, faixa_str))
                    else:
                        # Faixa única: "50"
                        valor = int(faixa_str)
                        faixas.append((valor, valor, faixa_str))
                except (ValueError, IndexError) as e:
                    st.warning(f"Erro ao processar faixa '{faixa}': {e}")
                    continue
            
            # Ordenar por valor inicial
            faixas.sort(key=lambda x: x[0])
            
            # Debug: mostrar faixas carregadas
            if faixas:
                st.info(f"🎯 Faixas de KM carregadas: {[f[2] for f in faixas[:5]]}{'...' if len(faixas) > 5 else ''}")
            
            return faixas
        except Exception as e:
            st.error(f"Erro ao extrair faixas de frete: {e}")
            return []
    
    def executar(self):
        """Método principal para executar o simulador"""
        self._configurar_pagina()
        self._carregar_dados_iniciais()
        self._exibir_interface()
    
    def _configurar_pagina(self):
        """Configura a página do Streamlit"""
        # Página já configurada no início do script
        st.title("📊 Simulador de Formação de Preço de Venda - 3.0")
        
        # Verificar se a imagem existe
        if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
            st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=300)
    
    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais necessários"""
        arquivo_padrao = "Custo de reposição.xlsx"
        
        if os.path.exists(arquivo_padrao):
            try:
                self.df_padrao = pd.read_excel(arquivo_padrao)
                self.df_padrao.columns = self.df_padrao.columns.str.strip()
            except Exception as e:
                st.error(f"Erro ao carregar arquivo padrão: {str(e)}")
                self.df_padrao = pd.DataFrame()
        else:
            st.warning("Arquivo padrão 'Custo de reposição.xlsx' não encontrado.")
            self.df_padrao = pd.DataFrame()
    
    def _exibir_interface(self):
        """Exibe a interface principal"""
        # Seção de cliente
        self._exibir_secao_cliente()
        
        # Seção de parâmetros
        self._exibir_secao_parametros()
        
        # Upload de arquivo
        self._exibir_upload_arquivo()
        
        # Validação e processamento
        if self._validar_dados():
            self._processar_simulacao()
    
    def _exibir_secao_cliente(self):
        """Exibe a seção de seleção de cliente"""
        st.markdown("### 👤 Cliente ou Rede")
        
        clientes_df = self.db_manager.carregar_clientes_ou_rede()
        
        opcao_cliente = st.radio(
            "Deseja simular para um cliente específico?", 
            ["Sim", "Não (Cliente novo)"], 
            horizontal=True
        )
        
        self.contrato_real = None
        self.dados_cliente_selecionado = None
        
        if opcao_cliente == "Sim" and not clientes_df.empty:
            # Criar lista de opções mais informativas
            opcoes_clientes = []
            for idx, row in clientes_df.iterrows():
                # Formatação: "NOME - CIDADE/UF - CÓDIGO/LOJA - REDE"
                opcao = f"{row['A1_NOME']} - {row['cidade_ibge']}/{row['A1_EST']} - {row['A1_COD']}/{row['A1_LOJA']}"
                if row['REDE'] and str(row['REDE']) != str(row['A1_NOME'])[:20]:
                    opcao += f" - [{row['REDE']}]"
                opcoes_clientes.append(opcao)
            
            # Selectbox com informações completas
            cliente_escolhido_display = st.selectbox(
                "Selecione o cliente:", 
                opcoes_clientes,
                help="Formato: Nome - Cidade/UF - Código/Loja - [Rede]"
            )
            
            # Extrair o índice da opção selecionada
            indice_selecionado = opcoes_clientes.index(cliente_escolhido_display)
            self.dados_cliente_selecionado = clientes_df.iloc[indice_selecionado]
            
            # Exibir informações do cliente selecionado
            self._exibir_dados_completos_cliente()
            
            # Seção de cálculo de frete e rota (somente se tiver dados de geolocalização)
            if self.geolocalizacao and self.dados_cliente_selecionado is not None:
                self._exibir_secao_rota_integrada()
        
        elif opcao_cliente == "Sim":
            st.warning("⚠️ Nenhum cliente encontrado na base de dados.")
    
    def _exibir_dados_completos_cliente(self):
        """Exibe dados completos do cliente selecionado"""
        st.markdown("#### 📋 Dados Completos do Cliente")
        
        # Converter Series para dict para evitar problemas de ambiguidade
        cliente_dict = self.dados_cliente_selecionado.to_dict()
        
        # Função auxiliar para converter valores em string de forma segura
        def safe_str(value):
            if value is None or pd.isna(value):
                return ""
            return str(value).strip()
        
        # Função para formatar data brasileira
        def formatar_data_brasileira(data_str):
            try:
                data_safe = safe_str(data_str)
                if not data_safe or data_safe.lower() == 'não informado':
                    return "Não informado"
                
                # Se já está no formato brasileiro (DD/MM/YYYY)
                if '/' in data_safe:
                    return data_safe
                
                # Se está no formato YYYYMMDD
                if len(data_safe) == 8 and data_safe.isdigit():
                    ano = data_safe[:4]
                    mes = data_safe[4:6]
                    dia = data_safe[6:8]
                    return f"{dia}/{mes}/{ano}"
                
                return data_safe
            except:
                return "Data inválida"
        
        # Primeira linha - Informações principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            razao_social = safe_str(cliente_dict.get('A1_NOME', ''))
            codigo = safe_str(cliente_dict.get('A1_COD', ''))
            loja = safe_str(cliente_dict.get('A1_LOJA', ''))
            
            st.info(f"**🏢 Razão Social:**\n{razao_social}")
            st.info(f"**🏷️ Código/Loja:**\n{codigo}/{loja}")
            
        with col2:
            rede_info = safe_str(cliente_dict.get('REDE', ''))
            nome_resumo = safe_str(cliente_dict.get('A1_NOME', ''))[:20]
            
            # Comparação simples sem ambiguidade
            if len(rede_info) > 0 and rede_info != nome_resumo:
                st.success(f"**🏪 Rede:**\n{rede_info}")
            else:
                st.info("**🏪 Rede:**\nCliente independente")
            
            try:
                contrato_valor = cliente_dict.get("A1_ZZCONTR", 0)
                if contrato_valor is None or pd.isna(contrato_valor):
                    contrato_valor = 0.0
                else:
                    contrato_valor = float(contrato_valor)
                self.contrato_real = contrato_valor
            except (ValueError, TypeError):
                self.contrato_real = 0.0
            
            st.success(f"**📄 Contrato:**\n{self.contrato_real:.2f}%")
                
        with col3:
            uf = safe_str(cliente_dict.get('A1_EST', ''))
            risco = safe_str(cliente_dict.get('A1_RISCO', 'N/A'))
            
            st.info(f"**📍 UF:**\n{uf}")
            st.info(f"**⚠️ Risco:**\n{risco}")
        
        # Segunda linha - Endereço e dados financeiros
        col4, col5 = st.columns(2)
        
        with col4:
            # Endereço limpo e organizado
            endereco_partes = []
            
            # Rua/Avenida
            endereco_rua = safe_str(cliente_dict.get('A1_END', ''))
            if len(endereco_rua) > 0 and endereco_rua.lower() != 'não informado':
                endereco_partes.append(endereco_rua)
            
            # Bairro
            bairro = safe_str(cliente_dict.get('A1_BAIRRO', ''))
            if len(bairro) > 0 and bairro.lower() not in ['', 'não informado']:
                endereco_partes.append(bairro)
            
            # Cidade/UF
            cidade = safe_str(cliente_dict.get('A1_MUN', ''))
            uf_endereco = safe_str(cliente_dict.get('A1_EST', ''))
            if len(cidade) > 0 and len(uf_endereco) > 0:
                endereco_partes.append(f"{cidade}/{uf_endereco}")
            elif len(uf_endereco) > 0:
                endereco_partes.append(uf_endereco)
            
            # CEP
            cep = safe_str(cliente_dict.get('A1_CEP', ''))
            if len(cep) > 0 and cep not in ['N/A', '0']:
                # Formatar CEP
                if len(cep) == 8 and cep.isdigit():
                    cep_formatado = f"{cep[:5]}-{cep[5:]}"
                    endereco_partes.append(f"CEP: {cep_formatado}")
                else:
                    endereco_partes.append(f"CEP: {cep}")
            
            # Montar endereço final
            if len(endereco_partes) > 0:
                endereco_completo = '\n'.join(endereco_partes)
            else:
                endereco_completo = "Endereço não informado"
            
            st.info(f"**📍 Endereço:**\n{endereco_completo}")
            
        with col5:
            # Limite de Crédito
            try:
                lc_value = cliente_dict.get('A1_LC', 0)
                if lc_value is None or pd.isna(lc_value):
                    lc_value = 0
                else:
                    lc_value = float(lc_value)
                
                if lc_value > 0:
                    lc_text = f"R$ {lc_value:,.2f}"
                else:
                    lc_text = "Não definido"
            except (ValueError, TypeError):
                lc_text = "Não definido"
            
            st.info(f"**💳 Limite de Crédito:**\n{lc_text}")
            
            # Última compra
            ultima_compra = formatar_data_brasileira(cliente_dict.get('A1_ULTCOM', ''))
            st.info(f"**🛒 Última Compra:**\n{ultima_compra}")
            
            # CNPJ/CPF se disponível
            cnpj = safe_str(cliente_dict.get('A1_CGC', ''))
            if len(cnpj) > 0 and cnpj not in ['0', '']:
                # Formatar CNPJ/CPF
                cnpj_limpo = ''.join(filter(str.isdigit, cnpj))  # Remove caracteres não numéricos
                if len(cnpj_limpo) == 14:
                    cnpj_formatado = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
                    st.info(f"**🏛️ CNPJ:**\n{cnpj_formatado}")
                elif len(cnpj_limpo) == 11:
                    # É CPF
                    cpf_formatado = f"{cnpj_limpo[:3]}.{cnpj_limpo[3:6]}.{cnpj_limpo[6:9]}-{cnpj_limpo[9:11]}"
                    st.info(f"**👤 CPF:**\n{cpf_formatado}")
        
    def _montar_endereco_completo_para_geocode(self, cliente_dict: dict) -> str:
        """Monta endereço completo otimizado para geocodificação do Google Maps"""
        partes_endereco = []
        
        # Função auxiliar
        def safe_str(value):
            if value is None or pd.isna(value):
                return ""
            return str(value).strip()
        
        # Rua/Avenida com número se disponível
        endereco_rua = safe_str(cliente_dict.get('A1_END', ''))
        if len(endereco_rua) > 0 and endereco_rua.lower() != 'não informado':
            partes_endereco.append(endereco_rua)
        
        # Bairro
        bairro = safe_str(cliente_dict.get('A1_BAIRRO', ''))
        if len(bairro) > 0 and bairro.lower() not in ['', 'não informado']:
            partes_endereco.append(bairro)
        
        # Cidade
        cidade = safe_str(cliente_dict.get('A1_MUN', ''))
        if len(cidade) > 0:
            partes_endereco.append(cidade)
        
        # Estado
        uf = safe_str(cliente_dict.get('A1_EST', ''))
        if len(uf) > 0:
            partes_endereco.append(uf)
        
        # CEP (muito importante para precisão)
        cep = safe_str(cliente_dict.get('A1_CEP', ''))
        if len(cep) > 0 and cep not in ['N/A', '0']:
            # Formatar CEP com hífen se necessário
            if len(cep) == 8 and cep.isdigit():
                cep_formatado = f"{cep[:5]}-{cep[5:]}"
                partes_endereco.append(f"CEP {cep_formatado}")
            else:
                partes_endereco.append(f"CEP {cep}")
        
        # País para maior precisão
        partes_endereco.append("Brasil")
        
        # Montar endereço final separado por vírgulas (formato ideal para Google Maps)
        endereco_completo = ", ".join(partes_endereco)
        
        return endereco_completo
    
    def _exibir_secao_rota_integrada(self):
        """Exibe a seção de cálculo de rota integrada com seleção de cliente"""
        with st.expander("📦 Cálculo de Frete e Rota", expanded=False):
            st.markdown("### 🧭 Parâmetros de Rota")
            
            # Unidade de origem
            origens = {
                "Matriz (SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
                "Filial (Atibaia)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                origem_opcao = st.selectbox("📌 Unidade de Origem", list(origens.keys()), index=0)
                origem = origens[origem_opcao]
                st.text_input("📌 Endereço de Origem", origem, disabled=True)
            
            with col2:
                # Cliente já selecionado - campo desabilitado
                cliente_info = f"{self.dados_cliente_selecionado['A1_NOME']} - {self.dados_cliente_selecionado['A1_COD']}/{self.dados_cliente_selecionado['A1_LOJA']}"
                st.text_input("🎯 Cliente Selecionado", cliente_info, disabled=True, 
                             help="Cliente definido na seção acima")
                
                # Montar endereço destino usando a nova função
                endereco_destino = self._montar_endereco_completo_para_geocode(
                    self.dados_cliente_selecionado.to_dict()
                )
                st.text_area(
                    "🎯 Endereço de Destino (para geocodificação)", 
                    endereco_destino, 
                    disabled=True,
                    height=80,
                    help="Endereço otimizado para melhor precisão no Google Maps"
                )
            
            st.markdown("---")
            
            # Seção de frete calculado automaticamente
            col_frete1, col_frete2, col_frete3 = st.columns(3)
            
            with col_frete1:
                # Seletor de tipo de veículo
                tipo_veiculo = st.selectbox(
                    "🚛 Tipo de Veículo", 
                    ["truck", "carreta"], 
                    format_func=lambda x: "Truck" if x == "truck" else "Carreta",
                    key="tipo_veiculo_select"
                )
                
                # Botão de cálculo
                if st.button("🚗 Calcular Distância e Frete", use_container_width=True):
                    self._calcular_frete_automatico(origem, tipo_veiculo)
            
            with col_frete2:
                # Exibir frete calculado ou permitir override manual
                frete_calculado = st.session_state.get('frete_calculado_automatico', 0.0)
                if frete_calculado > 0:
                    tipo_usado = st.session_state.get('tipo_veiculo_usado', 'truck')
                    st.success(f"🚛 Frete Calculado ({tipo_usado.upper()}): R$ {frete_calculado:.2f}")
                    usar_frete_calculado = st.checkbox("Usar frete calculado", value=True, key="usar_frete_auto")
                else:
                    usar_frete_calculado = False
                    st.info("🚛 Frete não calculado ainda")
            
            with col_frete3:
                # Override manual do frete
                if not st.session_state.get('usar_frete_auto', False):
                    self.frete_padrao_cliente = st.number_input(
                        "Frete Manual (R$)", 
                        min_value=0.0, 
                        value=1.50, 
                        step=0.01,
                        key="frete_manual_cliente"
                    )
                else:
                    # Usar frete calculado
                    self.frete_padrao_cliente = frete_calculado
                    st.text_input(
                        "Frete a Usar (R$)", 
                        f"{frete_calculado:.2f}", 
                        disabled=True,
                        help="Frete calculado automaticamente"
                    )
            
            # Exibir resultados da rota se disponível
            if st.session_state.get('distancia_calculada') and st.session_state.get('tempo_calculado'):
                st.markdown("### 📊 Resultado da Rota")
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("📏 Distância", st.session_state.get('distancia_calculada'))
                col_res2.metric("⏱️ Tempo Estimado", st.session_state.get('tempo_calculado'))
                
                self._exibir_mapas_cliente(origem)

    def _calcular_frete_automatico(self, origem: str, tipo_veiculo: str = "truck"):
        """Calcula frete automaticamente baseado na distância real e tabela TRANSP_TARGET"""
        origem_coords = self.geolocalizacao.geocode(origem)
        
        # NOVA ABORDAGEM: Usar endereço formatado para geocodificação precisa
        cliente_dict = self.dados_cliente_selecionado.to_dict()
        endereco_destino_completo = self._montar_endereco_completo_para_geocode(cliente_dict)
        
        st.info(f"🔍 Geocodificando endereço: {endereco_destino_completo}")
        
        # Geocodificar endereço de destino
        destino_coords = self.geolocalizacao.geocode(endereco_destino_completo)

        if not origem_coords:
            st.error("❌ Não foi possível localizar o endereço de origem.")
            return
            
        if not destino_coords:
            st.error(f"❌ Não foi possível localizar o endereço de destino: {endereco_destino_completo}")
            # Fallback: tentar usar coordenadas do banco se disponíveis
            try:
                lat_banco = float(self.dados_cliente_selecionado["latitude"])
                lng_banco = float(self.dados_cliente_selecionado["longitude"])
                if lat_banco != 0 and lng_banco != 0:
                    destino_coords = (lat_banco, lng_banco)
                    st.warning("⚠️ Usando coordenadas do banco como fallback.")
                else:
                    return
            except (ValueError, TypeError, KeyError):
                st.error("❌ Coordenadas do banco também não disponíveis.")
                return

        distancia, duracao, erro = self.geolocalizacao.calcular_distancia(origem_coords, destino_coords)

        if erro:
            st.warning(erro)
            return

        try:
            # Corrigir conversão da distância - lidar com vírgula como separador de milhares
            distancia_texto = distancia.replace('km', '').strip()
            
            # Se tem vírgula, verificar se é separador de milhares ou decimal
            if ',' in distancia_texto:
                # Se tem ponto E vírgula (ex: "1,159.5"), vírgula é separador de milhares
                if '.' in distancia_texto:
                    # Formato: "1,159.5 km" - vírgula = milhares, ponto = decimal
                    distancia_km = float(distancia_texto.replace(',', ''))
                else:
                    # Só tem vírgula - verificar posição
                    partes = distancia_texto.split(',')
                    if len(partes[1]) == 3:  # "1,159" - vírgula é separador de milhares
                        distancia_km = float(distancia_texto.replace(',', ''))
                    else:  # "1,5" - vírgula é decimal
                        distancia_km = float(distancia_texto.replace(',', '.'))
            else:
                # Só números e possivelmente ponto decimal
                distancia_km = float(distancia_texto.replace('.', ''))

            # Debug: mostrar conversão e coordenadas
            st.success(f"✅ Geocodificação bem-sucedida!")
            col_debug1, col_debug2 = st.columns(2)
            with col_debug1:
                st.info(f"🔍 Origem: {origem_coords[0]:.6f}, {origem_coords[1]:.6f}")
            with col_debug2:
                st.info(f"🎯 Destino: {destino_coords[0]:.6f}, {destino_coords[1]:.6f}")
            
            st.info(f"📏 Conversão: '{distancia}' → {distancia_km} km")

            # Armazenar distância e tempo no estado
            st.session_state.distancia_calculada = distancia
            st.session_state.tempo_calculado = duracao
            st.session_state.coordenadas_origem = origem_coords
            st.session_state.coordenadas_destino = destino_coords

            # 1. Obter a faixa de KM com base na distância
            faixa_km = obter_faixa_km_exata(distancia_km, self.faixas_km_ordenadas)

            # 2. Obter código IBGE do cliente
            cidade_ibge = str(self.dados_cliente_selecionado["cidade_ibge"])

            # 3. Carregar a base de clientes com faixas
            df_clientes_frete = self.db_manager.carregar_clientes_ou_rede()

            # 4. NOVO: Buscar ambos os valores (truck e carreta) para otimização
            resultado_frete = buscar_frete_inteligente(df_clientes_frete, cidade_ibge, faixa_km)

            # 5. Calcular volume total estimado (será usado para otimização)
            # Para agora, usar valor padrão que será ajustado quando o usuário definir quantidades
            volume_estimado = 500  # Volume padrão para cálculo inicial
            
            # 6. Calcular frete otimizado
            otimizacao = calcular_frete_otimizado(resultado_frete, volume_estimado)

            # 7. Armazenar no session_state
            st.session_state.frete_calculado_automatico = otimizacao['frete_por_caixa']
            st.session_state.tipo_veiculo_usado = otimizacao['veiculo_otimo']
            st.session_state.resultado_frete_completo = resultado_frete
            st.session_state.otimizacao_frete = otimizacao

            # 8. Exibir resultados detalhados
            if otimizacao['frete_por_caixa'] > 0:
                # Mensagem principal
                st.success(
                    f"✅ Rota calculada com sucesso!\n\n"
                    f"📏 Distância: {distancia} ({duracao}) → **{distancia_km:.0f} km**\n\n"
                    f"📍 IBGE: {cidade_ibge}\n\n"
                    f"🎯 Faixa: **{faixa_km}**\n\n"
                    f"💰 Frete/Caixa: R$ {otimizacao['frete_por_caixa']:.2f}\n\n"
                    f"🚛 Veículo Otimizado: {otimizacao['veiculo_otimo'].upper()}"
                )
                
                # Alerta de otimização
                if otimizacao['alerta']:
                    if 'OTIMIZAÇÃO' in otimizacao['alerta']:
                        st.success(otimizacao['alerta'])
                    elif 'MÚLTIPLOS' in otimizacao['alerta']:
                        st.warning(otimizacao['alerta'])
                    else:
                        st.info(otimizacao['alerta'])
                
                # Tabela de comparação
                st.markdown("#### 📊 Comparação de Fretes Encontrados")
                
                truck_info = resultado_frete['truck']
                carreta_info = resultado_frete['carreta']
                
                comparacao_data = []
                if truck_info['valor'] > 0:
                    comparacao_data.append({
                        'Veículo': '🚚 Truck',
                        'Frete Total': f"R$ {truck_info['valor']:,.2f}",
                        'Capacidade': '870 caixas',
                        'Frete/Caixa': f"R$ {truck_info['valor']/870:.2f}",
                        'Método': truck_info['metodo']
                    })
                
                if carreta_info['valor'] > 0:
                    comparacao_data.append({
                        'Veículo': '🚛 Carreta',
                        'Frete Total': f"R$ {carreta_info['valor']:,.2f}",
                        'Capacidade': '1.740 caixas',
                        'Frete/Caixa': f"R$ {carreta_info['valor']/1740:.2f}",
                        'Método': carreta_info['metodo']
                    })
                
                if comparacao_data:
                    df_comparacao = pd.DataFrame(comparacao_data)
                    st.dataframe(df_comparacao, use_container_width=True, hide_index=True)
                
                st.info("💡 **Otimização Automática:** O frete será reavaliado automaticamente quando você definir as quantidades dos produtos!")
                
            else:
                st.warning(
                    f"⚠️ Rota calculada, mas frete não encontrado!\n\n"
                    f"📏 Distância: {distancia} ({duracao}) → **{distancia_km:.0f} km**\n\n"
                    f"📍 IBGE: {cidade_ibge}\n\n"
                    f"🎯 Faixa de KM: **{faixa_km}**\n\n"
                    f"💡 Sugestão: Use frete manual ou verifique tabela de fretes"
                )

        except Exception as e:
            st.error(f"❌ Erro ao calcular frete: {e}")
            # Debug info em caso de erro
            if 'distancia_texto' in locals():
                st.info(f"Debug - Distância original: '{distancia}', Texto processado: '{distancia_texto}'")
            st.info(f"Debug - IBGE: {cidade_ibge if 'cidade_ibge' in locals() else 'N/A'}, Faixa: {faixa_km if 'faixa_km' in locals() else 'N/A'}")

    def _exibir_mapas_cliente(self, origem: str):
        """Exibe mapas para o cliente selecionado usando coordenadas calculadas"""
        # Usar coordenadas armazenadas no session_state (mais precisas)
        origem_coords = st.session_state.get('coordenadas_origem')
        destino_coords = st.session_state.get('coordenadas_destino')
        
        if not origem_coords or not destino_coords:
            st.warning("⚠️ Coordenadas não disponíveis para exibir mapas.")
            return
        
        st.markdown("---")
        col_mapa, col_street = st.columns(2)
        
        with col_mapa:
            st.markdown("#### 🗺️ Mapa com Rota")
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
            st.markdown("#### 🚦 Street View - Destino")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)
        
        # Informações extras sobre as coordenadas
        st.markdown("#### 📍 Coordenadas Utilizadas")
        col_coord1, col_coord2 = st.columns(2)
        with col_coord1:
            st.info(f"**Origem:**\n{origem_coords[0]:.6f}, {origem_coords[1]:.6f}")
        with col_coord2:
            st.info(f"**Destino:**\n{destino_coords[0]:.6f}, {destino_coords[1]:.6f}")
        
        st.markdown("---")
    
    def _exibir_secao_parametros(self):
        """Exibe a seção de parâmetros"""
        col_param1, col_param2, col_param3 = st.columns([1, 1, 1])
        
        with col_param1:
            st.markdown("#### ⚙️ Parâmetros de Origem")
            # Origem fixada como SP
            uf_origem = 'SP'
            st.info(f"🏭 **Origem fixada:** {uf_origem} (São Paulo)")
            
            # Verificar se há frete específico do cliente
            if hasattr(self, 'frete_padrao_cliente') and self.frete_padrao_cliente is not None:
                frete_a_usar = self.frete_padrao_cliente
                frete_origem = "cliente selecionado"
                st.text_input(
                    f"Frete/Caixa (R$) - {frete_origem}", 
                    f"{frete_a_usar:.2f}", 
                    disabled=True,
                    help="Frete definido pela seleção do cliente"
                )
                self.frete_padrao = frete_a_usar
            else:
                # Frete padrão quando não há cliente selecionado
                self.frete_padrao = st.number_input(
                    "Frete/Caixa (R$) - Padrão", 
                    min_value=0.0, 
                    value=1.50, 
                    step=0.01,
                    help="Frete padrão para cliente novo"
                )
            
            self.tipo_frete = st.radio("Tipo de Frete", ("CIF", "FOB"))
        
        with col_param2:
            st.markdown("#### 📍 Parâmetros de Destino")
            opcoes_uf = self.df_padrao["UF"].dropna().unique().tolist() if not self.df_padrao.empty else []
            
            # Se cliente selecionado, usar UF do cliente
            if self.dados_cliente_selecionado is not None:
                uf_cliente = self.dados_cliente_selecionado['A1_EST']
                if uf_cliente in opcoes_uf:
                    index_uf = opcoes_uf.index(uf_cliente)
                    self.uf_selecionado = st.selectbox(
                        "UF de Destino (Cliente)", 
                        options=opcoes_uf, 
                        index=index_uf,
                        key="uf_select",
                        help="UF definida pelo cliente selecionado"
                    )
                else:
                    st.warning(f"UF do cliente ({uf_cliente}) não encontrada na planilha!")
                    self.uf_selecionado = st.selectbox("UF de Destino", options=opcoes_uf, key="uf_select")
            else:
                self.uf_selecionado = st.selectbox("UF de Destino", options=opcoes_uf, key="uf_select")
            
            # Contrato
            if self.contrato_real is not None:
                st.info("🧾 Usando contrato real do cliente selecionado.")
                self.contrato_percentual = self.contrato_real / 100
            else:
                contrato_input = st.number_input("% Contrato", min_value=0.0, max_value=100.0, value=1.00, step=0.01)
                self.contrato_percentual = contrato_input / 100
            
            # Mostrar alíquotas
            if self.uf_selecionado:
                aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
                aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)
                
                info_tributos = (
                    f"ICMS SP→{self.uf_selecionado}: {aliquotas_origem['interestadual']:.1%} | "
                    f"Interno {self.uf_selecionado}: {aliquotas_destino['interna']:.1%}"
                )
                if aliquotas_destino['fcp'] > 0:
                    info_tributos += f" | FCP: {aliquotas_destino['fcp']:.1%}"
                st.info(info_tributos)
        
        with col_param3:
            st.markdown("#### 💰 Parâmetros Globais")
            self.custo_fixo_global = st.number_input(
                "Custo Fixo Global (R$)", min_value=0.0, value=0.0, step=0.01,
                help="Se zero, usa valor da planilha"
            )
            comissao_input = st.number_input(
                "% Comissão Global", min_value=0.0, max_value=100.0, value=0.0, step=0.1,
                help="Se zero, usa valor da planilha"
            )
            self.comissao_padrao = comissao_input / 100
            
            bonificacao_input = st.number_input(
                "% Bonificação Global", min_value=0.0, max_value=100.0, value=0.0, step=0.01,
                help="Se zero, usa valor da planilha"
            )
            self.bonificacao_global = bonificacao_input / 100
    
    def _exibir_upload_arquivo(self):
        """Exibe a seção de upload de arquivo"""
        uploaded_file = st.file_uploader("📂 Atualizar planilha base (.xlsx)", type="xlsx")
        
        if uploaded_file:
            try:
                arquivo_padrao = "Custo de reposição.xlsx"
                
                # Criar backup se arquivo existe
                if os.path.exists(arquivo_padrao):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
                    os.rename(arquivo_padrao, backup_name)
                    st.success(f"Backup criado: {backup_name}")
                
                # Salvar novo arquivo
                with open(arquivo_padrao, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success("Arquivo atualizado com sucesso!")
                
                # Recarregar dados
                self.df_padrao = pd.read_excel(arquivo_padrao)
                self.df_padrao.columns = self.df_padrao.columns.str.strip()
                
                # Resetar estado
                self.gerenciador_estado.resetar_estado()
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {str(e)}")
    
    def _validar_dados(self) -> bool:
        """Valida se os dados necessários estão disponíveis"""
        if self.df_padrao.empty or not self.uf_selecionado:
            st.warning("Carregue uma planilha e selecione uma UF de destino.")
            return False
        return True
    
    def _processar_simulacao(self):
        """Processa a simulação principal"""
        # Preparar dados base
        df_base = self._preparar_dados_base()
        
        if df_base.empty:
            st.error(f"Nenhum produto encontrado para a UF {self.uf_selecionado}")
            return
        
        # Exibir controles
        self._exibir_controles(df_base)
        
        # Processar edição e resultados
        self._processar_edicao_e_resultados(df_base)
    
    def _preparar_dados_base(self) -> pd.DataFrame:
        """Prepara os dados base para simulação"""
        # Filtrar por UF
        df_base = self.df_padrao[self.df_padrao["UF"] == self.uf_selecionado].copy()
        
        # Resetar dados se mudou UF
        if (st.session_state.df_atual is not None and 
            "UF" in st.session_state.df_atual.columns):
            ufs_atuais = st.session_state.df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != self.uf_selecionado:
                self.gerenciador_estado.resetar_estado()
        
        # Filtrar produtos esperados
        df_base = df_base[df_base["Descrição"].isin(self.produtos_esperados)].copy()
        
        # Ajustar colunas necessárias
        df_base = self._ajustar_colunas_necessarias(df_base)
        
        # Aplicar parâmetros globais
        df_base = self._aplicar_parametros_globais(df_base)
        
        return df_base
    
    def _ajustar_colunas_necessarias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajusta colunas necessárias no DataFrame"""
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
        """Aplica parâmetros globais ao DataFrame"""
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(self.uf_selecionado)
        
        df["Frete Caixa"] = self.frete_padrao
        df["Contrato"] = self.contrato_percentual
        df["UF Origem"] = 'SP'
        df["UF Destino"] = self.uf_selecionado
        df["ICMS Interestadual"] = aliquotas_origem['interestadual']
        df["ICMS Interno Destino"] = aliquotas_destino['interna']
        df["FCP"] = aliquotas_destino['fcp']
        
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
        """Exibe os controles principais"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🎯 Calcular Ponto de Equilíbrio", use_container_width=True):
                df_equilibrio, alertas = self._calcular_ponto_equilibrio(df_base)
                
                if alertas:
                    for alerta in alertas:
                        st.warning(alerta)
                
                st.session_state.df_atual = df_equilibrio.copy()
                st.session_state.modo_equilibrio = True
                st.success("✅ Ponto de equilíbrio calculado!")
        
        with col2:
            if st.button("🔄 Resetar", use_container_width=True):
                self.gerenciador_estado.resetar_estado()
                st.info("Dados resetados.")
    
    def _calcular_ponto_equilibrio(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """Calcula o ponto de equilíbrio para todos os produtos"""
        df_resultado = df.copy()
        alertas = []
        
        for index, row in df_resultado.iterrows():
            try:
                # Custos base
                custo_net = float(row.get("Custo NET", 0))
                custo_fixo = float(row.get("Custo Fixo", 0))
                custo_total_unit = custo_net + custo_fixo
                frete_unit = float(row.get("Frete Caixa", 0)) if self.tipo_frete == "CIF" else 0
                
                # Despesas percentuais diretas sobre receita
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
                
                # Verificar se é possível calcular
                if despesas_diretas >= 1.0:
                    alertas.append(f"{row.get('Descrição', 'Produto')}: Despesas = {despesas_diretas:.1%} (≥100%)")
                    preco_equilibrio = 0.0
                else:
                    custos_totais = custo_total_unit + frete_unit
                    preco_equilibrio = custos_totais / (1 - despesas_diretas)
                    preco_equilibrio = CalculadoraTributaria.arredondar_valor(preco_equilibrio, 2)
                
                # Garantir que não seja negativo
                preco_equilibrio = max(0.0, preco_equilibrio)
                df_resultado.at[index, "Preço de Venda"] = preco_equilibrio
                
            except Exception as e:
                alertas.append(f"Erro no produto {row.get('Descrição', 'N/A')}: {str(e)}")
                df_resultado.at[index, "Preço de Venda"] = 0.0
        
        return df_resultado, alertas
    
    def _processar_edicao_e_resultados(self, df_base: pd.DataFrame):
        """Processa a edição de dados e cálculo de resultados"""
        # Determinar DataFrame para edição
        if st.session_state.df_atual is not None:
            df_para_edicao = st.session_state.df_atual.copy()
        else:
            df_para_edicao = df_base.copy()
        
        # Aplicar lógica híbrida de comissão e bonificação
        df_para_edicao = self._aplicar_logica_comissao_bonificacao(df_para_edicao)
        
        # Exibir status
        self._exibir_status()
        
        # Exibir resumo de edições
        self._exibir_resumo_edicoes()
        
        # Exibir editor de dados
        df_editado = self._exibir_editor_dados(df_para_edicao)
        
        # Processar dados editados
        df_final = self._processar_dados_editados(df_editado, df_para_edicao)
        
        # Calcular e exibir resultados
        self._calcular_e_exibir_resultados(df_final)
    
    def _aplicar_logica_comissao_bonificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica lógica híbrida de comissão e bonificação"""
        df_temp = df.copy()
        
        # Garantir que colunas existam e sejam numéricas
        for col in ["Comissão", "Bonificação"]:
            if col not in df_temp.columns:
                df_temp[col] = 0.0
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0.0)
        
        # Armazenar valores originais se ainda não foram armazenados
        if not st.session_state.valores_originais:
            for index in df_temp.index:
                produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
                st.session_state.valores_originais[produto] = {
                    'comissao': float(df_temp.at[index, "Comissão"]),
                    'bonificacao': float(df_temp.at[index, "Bonificação"])
                }
        
        # Aplicar valores globais se ativos e não editados individualmente
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
        
        # Aplicar valores editados individualmente (PRIORIDADE MÁXIMA)
        for produto, valor in st.session_state.comissoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Comissão"] = float(valor)
        
        for produto, valor in st.session_state.bonificacoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Bonificação"] = float(valor)
        
        # Garantir tipos corretos
        df_temp["Comissão"] = df_temp["Comissão"].astype(float)
        df_temp["Bonificação"] = df_temp["Bonificação"].astype(float)
        
        return df_temp
    
    def _exibir_status(self):
        """Exibe o status atual da simulação"""
        status_info = f"🗺️ **SP → {self.uf_selecionado}** | "
        
        if st.session_state.modo_equilibrio:
            status_info += "🔒 **Modo Equilíbrio Ativo**"
        else:
            status_info += "📋 **Modo Normal**"
        
        # Parâmetros globais ativos
        parametros_ativos = []
        if st.session_state.comissao_global_aplicada and self.comissao_padrao > 0:
            parametros_ativos.append(f"Comissão Global: {self.comissao_padrao:.1%}")
        if self.bonificacao_global > 0:
            parametros_ativos.append(f"Bonificação Global: {self.bonificacao_global:.1%}")
        
        if parametros_ativos:
            status_info += f" | {' | '.join(parametros_ativos)}"
        
        # Edições individuais
        edicoes_individuais = []
        if st.session_state.comissoes_editadas:
            edicoes_individuais.append(f"Comissões editadas: {len(st.session_state.comissoes_editadas)}")
        if st.session_state.bonificacoes_editadas:
            edicoes_individuais.append(f"Bonificações editadas: {len(st.session_state.bonificacoes_editadas)}")
        
        if edicoes_individuais:
            status_info += f" | 🎯 {' | '.join(edicoes_individuais)}"
        
        st.info(status_info)
    
    def _exibir_resumo_edicoes(self):
        """Exibe resumo das edições individuais"""
        if st.session_state.comissoes_editadas or st.session_state.bonificacoes_editadas:
            with st.expander("🎯 Resumo das Edições Individuais", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.session_state.comissoes_editadas:
                        st.markdown("**Comissões Personalizadas:**")
                        for produto, valor in st.session_state.comissoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('comissao', 0)
                            global_val = self.comissao_padrao if self.comissao_padrao > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                    
                    if st.button("🔄 Limpar Comissões Editadas"):
                        st.session_state.comissoes_editadas = {}
                        st.rerun()
                
                with col2:
                    if st.session_state.bonificacoes_editadas:
                        st.markdown("**Bonificações Personalizadas:**")
                        for produto, valor in st.session_state.bonificacoes_editadas.items():
                            original = st.session_state.valores_originais.get(produto, {}).get('bonificacao', 0)
                            global_val = self.bonificacao_global if self.bonificacao_global > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                    
                    if st.button("🔄 Limpar Bonificações Editadas"):
                        st.session_state.bonificacoes_editadas = {}
                        st.rerun()
    
    def _exibir_editor_dados(self, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Exibe o editor de dados"""
        st.markdown("### 📊 Simulação Consolidada - Dados + Resultados")
        
        # Preparar dados para edição
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                         "MVA", "Comissão", "Bonificação", "Contrato"]
        
        df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()
        
        # Converter colunas numéricas
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_para_edicao_clean.columns:
                df_para_edicao_clean[col] = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)
        
        # Converter colunas percentuais para formato 0-100
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_para_edicao_clean.columns:
                valores = pd.to_numeric(df_para_edicao_clean[col], errors='coerce').fillna(0.0)
                df_para_edicao_clean[col] = (valores * 100).round(2)
        
        # Editor de dados
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
                "Contrato": st.column_config.NumberColumn("% Contrato ⭐", format="%.2f", min_value=0.0, max_value=50.0, step=0.1, 
                                                          help="⭐ = Editável individualmente. Sobrepõe valor global.")
            }
        )
        
        return df_editado
    
    def _processar_dados_editados(self, df_editado: pd.DataFrame, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Processa os dados editados"""
        df_processado = df_editado.copy()
        
        # Converter valores percentuais de volta para decimal
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        for col in colunas_percentuais:
            if col in df_processado.columns:
                df_processado[col] = pd.to_numeric(df_processado[col], errors='coerce').fillna(0.0) / 100
        
        # Arredondar valores monetários
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_processado.columns:
                df_processado[col] = df_processado[col].round(2)
        
        # Detectar mudanças nas comissões e bonificações
        produtos_com_mudancas = []
        
        for index in df_processado.index:
            if index < len(df_para_edicao):
                produto = df_processado.at[index, "Descrição"]
                
                # Verificar mudanças na comissão
                try:
                    comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
                    comissao_editada = float(df_processado.at[index, "Comissão"])
                    
                    if abs(comissao_original - comissao_editada) > 0.001:
                        st.session_state.comissoes_editadas[produto] = comissao_editada
                        produtos_com_mudancas.append(f"Comissão {produto}: {comissao_editada:.2%}")
                except (ValueError, TypeError, KeyError):
                    pass
                
                # Verificar mudanças na bonificação
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
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                         "MVA", "Comissão", "Bonificação", "Contrato"]
        
        for col in colunas_edicao:
            if col in df_processado.columns:
                df_final[col] = df_processado[col]
        
        # Armazenar edição temporária
        st.session_state.df_edicao_temp = df_final.copy()
        
        return df_final
    
    def _calcular_e_exibir_resultados(self, df_final: pd.DataFrame):
        """Calcula e exibe os resultados"""
        # Botão para aplicar cálculo
        if st.button("🚀 Calcular Resultados", type="primary"):
            # OTIMIZAÇÃO DE FRETE: Reavalia baseado no volume total
            if (hasattr(st.session_state, 'resultado_frete_completo') and 
                st.session_state.resultado_frete_completo):
                
                # Calcular volume total
                volume_total = df_final["Quantidade"].sum()
                
                # Reavalia a otimização com o volume real
                nova_otimizacao = calcular_frete_otimizado(
                    st.session_state.resultado_frete_completo, 
                    volume_total
                )
                
                # Verificar se houve mudança na recomendação
                otimizacao_anterior = st.session_state.get('otimizacao_frete', {})
                veiculo_anterior = otimizacao_anterior.get('veiculo_otimo', 'desconhecido')
                veiculo_novo = nova_otimizacao['veiculo_otimo']
                
                # Atualizar frete se necessário
                if veiculo_novo != veiculo_anterior and nova_otimizacao['frete_por_caixa'] > 0:
                    # Atualizar frete em todos os produtos
                    df_final["Frete Caixa"] = nova_otimizacao['frete_por_caixa']
                    
                    # Alertar sobre otimização
                    if nova_otimizacao['economia'] > 0:
                        st.success(
                            f"🎯 **FRETE OTIMIZADO!**\n\n"
                            f"Volume total: {volume_total} caixas\n\n"
                            f"{nova_otimizacao['alerta']}\n\n"
                            f"Novo frete/caixa: R$ {nova_otimizacao['frete_por_caixa']:.2f}"
                        )
                    else:
                        st.info(nova_otimizacao['alerta'])
                
                # Atualizar session state
                st.session_state.otimizacao_frete = nova_otimizacao
            
            st.session_state.df_atual = st.session_state.df_edicao_temp.copy()
            st.session_state.resultados_atualizados = True
            st.rerun()
        
        # Mostrar resultados apenas após clique no botão
        if st.session_state.get("resultados_atualizados", False):
            calculadora = CalculadoraResultados(self.tipo_frete)
            
            # Calcular resultados
            resultados = df_final.apply(calculadora.calcular_resultados_completos, axis=1)
            
            # Criar DataFrame para exibição
            df_display = self._criar_dataframe_display(df_final, resultados)
            
            # Exibir informações de otimização se disponível
            if hasattr(st.session_state, 'otimizacao_frete') and st.session_state.otimizacao_frete:
                otimizacao = st.session_state.otimizacao_frete
                
                if otimizacao['veiculo_otimo'] != 'nenhum':
                    col_opt1, col_opt2, col_opt3 = st.columns(3)
                    
                    with col_opt1:
                        volume_total = df_final["Quantidade"].sum()
                        st.metric("📦 Volume Total", f"{volume_total} caixas")
                    
                    with col_opt2:
                        st.metric("🚛 Veículo Otimizado", otimizacao['veiculo_otimo'].upper())
                    
                    with col_opt3:
                        if otimizacao['economia'] > 0:
                            st.metric("💰 Economia", f"R$ {otimizacao['economia']:.2f}", delta=f"R$ {otimizacao['economia']:.2f}")
                        else:
                            st.metric("💰 Frete Total", f"R$ {otimizacao['frete_total']:.2f}")
            
            # Exibir tabela com formatação
            self._exibir_tabela_resultados(df_display)
            
            # Exibir resumo executivo
            self._exibir_resumo_executivo(df_display)
            
            # Exibir detalhamento do cálculo
            self._exibir_detalhamento_calculo(df_final, resultados)
            
            # Seção de exportação
            self._exibir_secao_exportacao(df_final, resultados, df_display)
    
    def _criar_dataframe_display(self, df_final: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame para exibição dos resultados"""
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
        
        # Arredondar valores para evitar -0.00
        colunas_monetarias = ["Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
                             "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
                             "Lucro Líquido", "Equilíbrio"]
        
        for col in colunas_monetarias:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: CalculadoraTributaria.arredondar_valor(x, 2))
        
        # Arredondar margem
        if "Margem %" in df_display.columns:
            df_display["Margem %"] = df_display["Margem %"].apply(lambda x: CalculadoraTributaria.arredondar_valor(x, 1))
        
        return df_display
    
    def _exibir_tabela_resultados(self, df_display: pd.DataFrame):
        """Exibe a tabela de resultados com formatação"""
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
    
    def _exibir_resumo_executivo(self, df_display: pd.DataFrame):
        """Exibe o resumo executivo"""
        if len(df_display) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receita = df_display["Subtotal"].sum()
                st.metric("💰 Receita Total", f"R$ {total_receita:,.2f}")
            
            with col2:
                total_lucro_liquido = df_display["Lucro Líquido"].sum()
                delta_text = f"{(total_lucro_liquido/total_receita)*100:.1f}%" if total_receita > 0 else "0%"
                st.metric("💵 Lucro Líquido", f"R$ {total_lucro_liquido:,.2f}", delta=delta_text)
            
            with col3:
                margem_media = df_display["Margem %"].mean()
                st.metric("📊 Margem Média", f"{margem_media:.1f}%")
            
            with col4:
                produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
                st.metric("⚠️ Produtos c/ Prejuízo", produtos_prejuizo)
    
    def _exibir_detalhamento_calculo(self, df_final: pd.DataFrame, resultados: pd.DataFrame):
        """Exibe detalhamento do cálculo do primeiro produto"""
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
    
    def _exibir_secao_exportacao(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Exibe a seção de exportação"""
        st.markdown("### 📄 Exportar Resultados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Baixar Resumo Executivo", use_container_width=True):
                # Criar DataFrame consolidado
                colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                                 "MVA", "Comissão", "Bonificação", "Contrato"]
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
                    file_name=f"simulacao_sobel_SP_{self.uf_selecionado}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if st.button("📋 Copiar Resumo", use_container_width=True):
                resumo_texto = f"""
SIMULAÇÃO SOBEL - SP → {self.uf_selecionado}
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
    
    def _exibir_notas_tecnicas(self):
        """Exibe as notas técnicas"""
        st.markdown("""
        ---
        ### 📚 Simulador Sobel Suprema v3.0 
        
        #### 🎯 **Estados com FCP:**

    
        """)

# Função principal para executar o simulador
def main():
    """Função principal"""
    try:
        simulador = SimuladorSobel()
        simulador.executar()
        simulador._exibir_notas_tecnicas()
    except Exception as e:
        st.error(f"Erro crítico na aplicação: {str(e)}")
        st.error("Por favor, recarregue a página e tente novamente.")

# Executar aplicação
if __name__ == "__main__":
    main()