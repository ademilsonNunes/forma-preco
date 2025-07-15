# =============================================================================

# ui/__init__.py
# ==============
"""
Interface do Usuário
===================
Pacote contendo todos os componentes de interface e layout.
"""

from .components import (
    ClienteInfoComponent,
    ParametrosComponent,
    StatusComponent,
    ResumoEdicoesComponent,
    TabelaResultadosComponent,
    ResumoExecutivoComponent,
    ExportacaoComponent,
    MapasComponent
)

from .layout import SimuladorLayout

__all__ = [
    'ClienteInfoComponent',
    'ParametrosComponent', 
    'StatusComponent',
    'ResumoEdicoesComponent',
    'TabelaResultadosComponent',
    'ResumoExecutivoComponent',
    'ExportacaoComponent',
    'MapasComponent',
    'SimuladorLayout'
]
