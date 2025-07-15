"""
Utilitários de Dados
===================
Funções para manipulação e formatação de dados.
"""

import pandas as pd
from typing import Any


def arredondar_valor(valor: Any, decimais: int = 2) -> float:
    """Arredonda valores para evitar problemas de precisão"""
    try:
        return round(float(valor), decimais)
    except (ValueError, TypeError):
        return 0.0


def safe_str(value):
    """Converte valores em string de forma segura"""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def formatar_data_brasileira(data_str):
    """Formatar data no formato brasileiro"""
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


def formatar_cnpj_cpf(documento: str) -> str:
    """Formatar CNPJ ou CPF"""
    if not documento or documento in ['0', '']:
        return ""
    
    # Remove caracteres não numéricos
    doc_limpo = ''.join(filter(str.isdigit, documento))
    
    if len(doc_limpo) == 14:
        # É CNPJ
        return f"{doc_limpo[:2]}.{doc_limpo[2:5]}.{doc_limpo[5:8]}/{doc_limpo[8:12]}-{doc_limpo[12:14]}"
    elif len(doc_limpo) == 11:
        # É CPF
        return f"{doc_limpo[:3]}.{doc_limpo[3:6]}.{doc_limpo[6:9]}-{doc_limpo[9:11]}"
    else:
        return documento


def formatar_cep(cep: str) -> str:
    """Formatar CEP"""
    if not cep or cep in ['N/A', '0']:
        return ""
    
    cep_limpo = ''.join(filter(str.isdigit, cep))
    if len(cep_limpo) == 8:
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    return cep


def converter_percentuais_para_edicao(df: pd.DataFrame, colunas_percentuais: list) -> pd.DataFrame:
    """Converte colunas percentuais de decimal para 0-100 para edição"""
    df_edit = df.copy()
    for col in colunas_percentuais:
        if col in df_edit.columns:
            valores = pd.to_numeric(df_edit[col], errors='coerce').fillna(0.0)
            df_edit[col] = (valores * 100).round(2)
    return df_edit


def converter_percentuais_de_edicao(df: pd.DataFrame, colunas_percentuais: list) -> pd.DataFrame:
    """Converte colunas percentuais de 0-100 para decimal após edição"""
    df_final = df.copy()
    for col in colunas_percentuais:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0.0) / 100
    return df_final


def garantir_tipos_numericos(df: pd.DataFrame, colunas_numericas: list) -> pd.DataFrame:
    """Garante que colunas sejam numéricas"""
    df_num = df.copy()
    for col in colunas_numericas:
        if col in df_num.columns:
            df_num[col] = pd.to_numeric(df_num[col], errors='coerce').fillna(0.0)
    return df_num


def preparar_dados_para_exportacao(df_input: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
    """Prepara dados consolidados para exportação"""
    colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                     "MVA", "Comissão", "Bonificação", "Contrato"]
    
    df_export = pd.concat([df_input[colunas_edicao], resultados], axis=1)
    return df_export


def extrair_faixas_km_ordenadas(df_clientes: pd.DataFrame) -> list:
    """Extrai e ordena as faixas de KM disponíveis da base de clientes"""
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
        except (ValueError, IndexError):
            continue
    
    # Ordenar por valor inicial
    faixas.sort(key=lambda x: x[0])
    return faixas