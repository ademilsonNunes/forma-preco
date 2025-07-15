"""
Serviço de Cálculos - Versão Corrigida
======================================
Centraliza todos os cálculos tributários e financeiros.
"""

import pandas as pd
from typing import Tuple, Any

# Importar streamlit apenas quando necessário
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def st_error(message):
    """Função condicional para erro"""
    if HAS_STREAMLIT:
        st.error(message)
    else:
        print(f"ERROR: {message}")


def arredondar_valor(valor: Any, decimais: int = 2) -> float:
    """Arredonda valores para evitar problemas de precisão"""
    try:
        return round(float(valor), decimais)
    except (ValueError, TypeError):
        return 0.0


class CalculadoraTributaria:
    """Classe para realizar cálculos tributários"""
    
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
        base_sem_mva = arredondar_valor(valor_produto + ipi_valor)

        # Aplica MVA
        base_com_mva = arredondar_valor(base_sem_mva * (1 + mva))

        # ICMS origem (interestadual) sobre base sem MVA
        icms_origem = arredondar_valor(base_sem_mva * icms_interestadual)

        # ICMS destino (interno) sobre base com MVA
        icms_destino = arredondar_valor(base_com_mva * icms_interno_destino)

        # ICMS-ST: diferença entre ICMS destino e ICMS origem
        icms_st = arredondar_valor(max(icms_destino - icms_origem, 0.0))

        # FCP somente se a alíquota for maior que zero
        fcp = arredondar_valor(base_sem_mva * fcp_aliquota) if fcp_aliquota > 0 else 0.0

        return icms_st, base_com_mva, icms_origem, icms_destino, fcp


class CalculadoraResultados:
    """Classe para calcular resultados financeiros"""
    
    def __init__(self, tipo_frete: str = "CIF"):
        self.tipo_frete = tipo_frete
    
    def calcular_resultados_completos(self, row: pd.Series) -> pd.Series:
        """Calcula todos os resultados financeiros para uma linha de produto"""
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
            frete_total = arredondar_valor(
                float(row.get("Frete Caixa", 0)) * qtd
            ) if self.tipo_frete == "CIF" else 0.0
            
            frete_unit = arredondar_valor(
                float(row.get("Frete Caixa", 0))
            ) if self.tipo_frete == "CIF" else 0.0

            # IPI
            ipi_percent = float(row.get("IPI", 0))
            ipi_total = arredondar_valor(subtotal * ipi_percent)

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
            lucro_antes_ir = arredondar_valor(
                subtotal - custo_total - total_despesas_operacionais - frete_total
            )

            # Calcular IR e CSLL
            irpj, csll = self._calcular_ir_csll(lucro_antes_ir)
            
            # Lucro líquido
            lucro_liquido = arredondar_valor(lucro_antes_ir - irpj - csll)

            # Margens
            margem_antes_ir = arredondar_valor(
                (lucro_antes_ir / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0
            
            margem_liquida = arredondar_valor(
                (lucro_liquido / subtotal) * 100, 1
            ) if subtotal > 0 else 0.0

            # Total NF
            total_nf = arredondar_valor(subtotal + ipi_total + icms_st + fcp_valor)

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
            st_error(f"Erro no cálculo: {str(e)}")
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
            total += arredondar_valor(subtotal * percentual)
        
        return total
    
    def _calcular_ir_csll(self, lucro_antes_ir: float) -> Tuple[float, float]:
        """Calcula IRPJ e CSLL"""
        if lucro_antes_ir <= 0:
            return 0.0, 0.0
        
        # IRPJ: 15% + 10% sobre o que exceder R$ 20.000/mês
        irpj = arredondar_valor(lucro_antes_ir * 0.15)
        if lucro_antes_ir > 20000:
            adicional_irpj = arredondar_valor((lucro_antes_ir - 20000) * 0.10)
            irpj += adicional_irpj
        
        # CSLL: 9%
        csll = arredondar_valor(lucro_antes_ir * 0.09)
        
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
            return arredondar_valor(ponto_equilibrio)
            
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


class CalculadoraPontoEquilibrio:
    """Classe especializada para cálculo de ponto de equilíbrio"""
    
    @staticmethod
    def calcular_para_dataframe(df: pd.DataFrame, tipo_frete: str = "CIF") -> Tuple[pd.DataFrame, list]:
        """Calcula o ponto de equilíbrio para todos os produtos"""
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
                    preco_equilibrio = arredondar_valor(preco_equilibrio, 2)
                
                # Garantir que não seja negativo
                preco_equilibrio = max(0.0, preco_equilibrio)
                df_resultado.at[index, "Preço de Venda"] = preco_equilibrio
                
            except Exception as e:
                alertas.append(f"Erro no produto {row.get('Descrição', 'N/A')}: {str(e)}")
                df_resultado.at[index, "Preço de Venda"] = 0.0
        
        return df_resultado, alertas