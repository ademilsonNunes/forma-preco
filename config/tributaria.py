"""
Configurações Tributárias
========================
Centraliza todas as configurações relacionadas a tributação por UF.
"""

from typing import Dict


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
    
    @classmethod
    def get_estados_com_fcp(cls) -> list:
        """Retorna lista de estados que possuem FCP"""
        return [uf for uf, data in cls.ICMS_ALIQUOTAS.items() if data['fcp'] > 0]
    
    @classmethod
    def get_aliquota_icms_origem(cls, uf_origem: str = 'SP') -> float:
        """Retorna alíquota ICMS interestadual da origem"""
        return cls.obter_aliquotas(uf_origem)['interestadual']