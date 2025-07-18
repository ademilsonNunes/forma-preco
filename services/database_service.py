"""
Serviço de Banco de Dados - Versão Corrigida
============================================
Gerencia conexões e consultas ao banco de dados.
"""

import pandas as pd
import pyodbc
from typing import Optional

# Importar streamlit apenas quando necessário para evitar problemas de import
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def st_cache_data(ttl=600):
    """Decorator condicional para cache"""
    def decorator(func):
        if HAS_STREAMLIT:
            return st.cache_data(ttl=ttl)(func)
        return func
    return decorator


def st_error(message):
    """Função condicional para erro"""
    if HAS_STREAMLIT:
        st.error(message)
    else:
        print(f"ERROR: {message}")


class DatabaseService:
    """Serviço para gerenciar conexões e consultas ao banco de dados"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    @st_cache_data(ttl=600)
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
            st_error(f"Erro ao carregar dados dos clientes: {e}")
            return pd.DataFrame()
    
    def buscar_cliente_por_codigo(self, codigo: str, loja: str) -> Optional[dict]:
        """Busca cliente específico por código e loja"""
        try:
            df_clientes = self.carregar_clientes_ou_rede()
            cliente = df_clientes[
                (df_clientes['A1_COD'] == codigo) & 
                (df_clientes['A1_LOJA'] == loja)
            ]
            if not cliente.empty:
                return cliente.iloc[0].to_dict()
            return None
        except Exception as e:
            st_error(f"Erro ao buscar cliente: {e}")
            return None
    
    def buscar_clientes_por_rede(self, rede: str) -> pd.DataFrame:
        """Busca clientes pertencentes a uma rede específica"""
        try:
            df_clientes = self.carregar_clientes_ou_rede()
            return df_clientes[df_clientes['REDE'].str.contains(rede, case=False, na=False)]
        except Exception as e:
            st_error(f"Erro ao buscar clientes por rede: {e}")
            return pd.DataFrame()
    
    def buscar_clientes_por_uf(self, uf: str) -> pd.DataFrame:
        """Busca clientes de uma UF específica"""
        try:
            df_clientes = self.carregar_clientes_ou_rede()
            return df_clientes[df_clientes['A1_EST'] == uf]
        except Exception as e:
            st_error(f"Erro ao buscar clientes por UF: {e}")
            return pd.DataFrame()
    
    def get_faixas_frete_disponiveis(self) -> list:
        """Retorna lista das faixas de frete disponíveis no banco"""
        try:
            df_clientes = self.carregar_clientes_ou_rede()
            faixas = df_clientes['FAIXA_KM'].dropna().unique().tolist()
            return sorted(faixas)
        except Exception as e:
            st_error(f"Erro ao buscar faixas de frete: {e}")
            return []
    
    def verificar_conexao(self) -> bool:
        """Verifica se a conexão com o banco está funcionando"""
        try:
            with pyodbc.connect(self.connection_string) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            st_error(f"Erro na conexão com banco: {e}")
            return False

    @st_cache_data(ttl=600)
    def carregar_produtos_truck_carreta(_self) -> pd.DataFrame:
        """Carrega tabela de logística de produtos"""
        try:
            with pyodbc.connect(_self.connection_string) as conexao:
                query = "SELECT * FROM BISOBEL.dbo.PRODUTOS_TRUCK_CARRETA"
                df = pd.read_sql(query, conexao)
                df.columns = df.columns.str.strip()

                # Normalizar campos importantes
                for col in ["CXS_PLT", "PESO", "PESO_KG", "VOLUME", "VOLUME_M3"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                return df
        except Exception as e:
            st_error(f"Erro ao carregar dados logísticos: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_default_connection_string() -> str:
        """Retorna string de conexão padrão"""
        return (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=;"
            "DATABASE=;"
            "UID=;"
            "PWD="
        )
