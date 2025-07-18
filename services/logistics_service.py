import math
import pandas as pd


class LogisticsService:
    """Realiza cálculos logísticos de pallets e veículos"""

    PALLET_TRUCK = 29
    PALLET_CARRETA = 58
    PESO_TRUCK = 12000  # kg
    PESO_CARRETA = 28000  # kg

    def __init__(self, df_logistica: pd.DataFrame):
        self.df_logistica = df_logistica if df_logistica is not None else pd.DataFrame()
        self.codigo_col = next((c for c in ['CODIGO', 'Codigo', 'PRODUTO', 'SKU'] if c in self.df_logistica.columns), None)
        self.pallet_col = next((c for c in ['CXS_PLT', 'CX_PALLET', 'CAIXAS_PALLET'] if c in self.df_logistica.columns), None)
        self.peso_col = next((c for c in ['PESO', 'PESO_KG'] if c in self.df_logistica.columns), None)
        self.volume_col = next((c for c in ['VOLUME', 'VOLUME_M3', 'CUBAGEM'] if c in self.df_logistica.columns), None)

    def calcular_logistica(self, df_produtos: pd.DataFrame) -> dict:
        """Calcula pallets fechados e veículos necessários"""
        if self.df_logistica.empty or not self.codigo_col or not self.pallet_col:
            return {
                'peso_total': 0.0,
                'truck_qtd': 0,
                'carreta_qtd': 0,
                'sugestoes': [],
                'detalhes': pd.DataFrame()
            }

        codigo_prod = next((c for c in ['CODIGO', 'Codigo', 'SKU', 'Produto', 'Descrição', 'DESCRICAO'] if c in df_produtos.columns), None)
        if not codigo_prod or 'Quantidade' not in df_produtos.columns:
            return {
                'peso_total': 0.0,
                'truck_qtd': 0,
                'carreta_qtd': 0,
                'sugestoes': [],
                'detalhes': pd.DataFrame()
            }

        df_merge = df_produtos[[codigo_prod, 'Quantidade']].merge(
            self.df_logistica,
            left_on=codigo_prod,
            right_on=self.codigo_col,
            how='left'
        )

        df_merge[self.pallet_col] = pd.to_numeric(df_merge[self.pallet_col], errors='coerce').fillna(1)
        if self.peso_col:
            df_merge[self.peso_col] = pd.to_numeric(df_merge[self.peso_col], errors='coerce').fillna(0)
        if self.volume_col:
            df_merge[self.volume_col] = pd.to_numeric(df_merge[self.volume_col], errors='coerce').fillna(0)

        df_merge['pallets_fechados'] = (df_merge['Quantidade'] // df_merge[self.pallet_col]).astype(int)
        df_merge['resto_caixas'] = (df_merge['Quantidade'] % df_merge[self.pallet_col]).astype(int)
        df_merge['peso_total'] = df_merge['Quantidade'] * (df_merge[self.peso_col] if self.peso_col else 0)
        df_merge['volume_total'] = df_merge['Quantidade'] * (df_merge[self.volume_col] if self.volume_col else 0)

        total_pallets = (df_merge['pallets_fechados'] + (df_merge['resto_caixas'] > 0).astype(int)).sum()
        total_peso = df_merge['peso_total'].sum()

        trucks_pallet = math.ceil(total_pallets / self.PALLET_TRUCK) if total_pallets > 0 else 0
        trucks_peso = math.ceil(total_peso / self.PESO_TRUCK) if total_peso > 0 else 0
        trucks = max(trucks_pallet, trucks_peso)

        carretas_pallet = math.ceil(total_pallets / self.PALLET_CARRETA) if total_pallets > 0 else 0
        carretas_peso = math.ceil(total_peso / self.PESO_CARRETA) if total_peso > 0 else 0
        carretas = max(carretas_pallet, carretas_peso)

        sugestoes = []
        for _, row in df_merge.iterrows():
            if row['resto_caixas'] > 0:
                faltam = int(row[self.pallet_col] - row['resto_caixas'])
                sugestoes.append({'produto': row[codigo_prod], 'quantidade': faltam})

        return {
            'peso_total': float(total_peso),
            'truck_qtd': int(trucks),
            'carreta_qtd': int(carretas),
            'sugestoes': sugestoes,
            'detalhes': df_merge
        }
