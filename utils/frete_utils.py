"""
Utilitários de Frete
====================
Funções para cálculo e otimização de frete.
"""

import math
import pandas as pd
import streamlit as st


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