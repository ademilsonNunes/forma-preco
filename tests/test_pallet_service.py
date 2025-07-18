import pandas as pd
from services.logistics_service import LogisticsService

def test_calculo_pallets_e_sugestoes():
    log_df = pd.DataFrame({
        'CODIGO': ['A', 'B'],
        'CXS_PLT': [50, 40],
        'PESO_KG': [10, 8],
        'VOLUME_M3': [0.1, 0.08]
    })
    prod_df = pd.DataFrame({
        'CODIGO': ['A', 'B'],
        'Quantidade': [75, 80]
    })
    service = LogisticsService(log_df)
    info = service.calcular_logistica(prod_df)
    detalhes = info['detalhes']
    a = detalhes[detalhes['CODIGO'] == 'A'].iloc[0]
    assert a['pallets_fechados'] == 1
    assert a['resto_caixas'] == 25
    assert info['truck_qtd'] >= 1
    assert any(s['produto'] == 'A' and s['quantidade'] == 25 for s in info['sugestoes'])
