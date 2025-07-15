"""
Gerenciador de Estado
====================
Centraliza e organiza o estado da aplicação por namespaces.
"""

import streamlit as st
from typing import Any, Dict, Optional


class StateManager:
    """Gerenciador de estado centralizado com namespaces"""
    
    # Namespaces organizados por domínio
    NAMESPACE_SIMULACAO = "simulacao"
    NAMESPACE_CLIENTE = "cliente"
    NAMESPACE_FRETE = "frete"
    NAMESPACE_EDICOES = "edicoes"
    NAMESPACE_TRIBUTARIO = "tributario"
    NAMESPACE_UI = "ui"
    
    def __init__(self):
        self._inicializar_namespaces()
    
    def _inicializar_namespaces(self):
        """Inicializa todos os namespaces com valores padrão"""
        self._init_namespace_simulacao()
        self._init_namespace_cliente()
        self._init_namespace_frete()
        self._init_namespace_edicoes()
        self._init_namespace_tributario()
        self._init_namespace_ui()
    
    def _init_namespace_simulacao(self):
        """Inicializa estado da simulação"""
        namespace = self.NAMESPACE_SIMULACAO
        defaults = {
            'df_atual': None,
            'df_edicao_temp': None,
            'modo_equilibrio': False,
            'resultados_atualizados': False,
            'tipo_frete': 'CIF',
            'uf_origem': 'SP',
            'uf_destino': None
        }
        self._set_defaults(namespace, defaults)
    
    def _init_namespace_cliente(self):
        """Inicializa estado do cliente"""
        namespace = self.NAMESPACE_CLIENTE
        defaults = {
            'dados_selecionado': None,
            'contrato_real': None,
            'cliente_escolhido': None,
            'opcao_cliente': 'Não (Cliente novo)'
        }
        self._set_defaults(namespace, defaults)
    
    def _init_namespace_frete(self):
        """Inicializa estado do frete"""
        namespace = self.NAMESPACE_FRETE
        defaults = {
            'frete_padrao': 1.50,
            'frete_calculado_automatico': 0.0,
            'usar_frete_auto': False,
            'distancia_calculada': None,
            'tempo_calculado': None,
            'coordenadas_origem': None,
            'coordenadas_destino': None,
            'resultado_frete_completo': None,
            'otimizacao_frete': None,
            'tipo_veiculo_usado': 'truck'
        }
        self._set_defaults(namespace, defaults)
    
    def _init_namespace_edicoes(self):
        """Inicializa estado das edições"""
        namespace = self.NAMESPACE_EDICOES
        defaults = {
            'comissoes_editadas': {},
            'bonificacoes_editadas': {},
            'valores_originais': {},
            'comissao_global_aplicada': False
        }
        self._set_defaults(namespace, defaults)
    
    def _init_namespace_tributario(self):
        """Inicializa estado tributário"""
        namespace = self.NAMESPACE_TRIBUTARIO
        defaults = {
            'custo_fixo_global': 0.0,
            'comissao_padrao': 0.0,
            'bonificacao_global': 0.0,
            'contrato_percentual': 0.01
        }
        self._set_defaults(namespace, defaults)
    
    def _init_namespace_ui(self):
        """Inicializa estado da interface"""
        namespace = self.NAMESPACE_UI
        defaults = {
            'produtos_esperados': [
                "AGUA SANITARIA 5L", "AGUA SANITARIA 2L", "AGUA SANITARIA 1L",
                "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
                "AMACIANTE 5L", "AMACIANTE 2L",
                "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
                "LAVA LOUCAS 500ML", "LAVA LOUCAS 5L",
                "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
                "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
                "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
            ],
            'expandir_secoes': {
                'cliente': False,
                'rota': False,
                'resumo_edicoes': False
            }
        }
        self._set_defaults(namespace, defaults)
    
    def _set_defaults(self, namespace: str, defaults: Dict[str, Any]):
        """Define valores padrão para um namespace"""
        if namespace not in st.session_state:
            st.session_state[namespace] = {}
        
        for key, default_value in defaults.items():
            full_key = f"{namespace}.{key}"
            if full_key not in st.session_state:
                st.session_state[full_key] = default_value
    
    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Obtém valor do estado por namespace e chave"""
        full_key = f"{namespace}.{key}"
        return st.session_state.get(full_key, default)
    
    def set(self, namespace: str, key: str, value: Any) -> None:
        """Define valor no estado por namespace e chave"""
        full_key = f"{namespace}.{key}"
        st.session_state[full_key] = value
    
    def update(self, namespace: str, updates: Dict[str, Any]) -> None:
        """Atualiza múltiplos valores em um namespace"""
        for key, value in updates.items():
            self.set(namespace, key, value)
    
    def clear_namespace(self, namespace: str) -> None:
        """Limpa todos os valores de um namespace"""
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith(f"{namespace}.")]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Reinicializar o namespace
        if namespace == self.NAMESPACE_SIMULACAO:
            self._init_namespace_simulacao()
        elif namespace == self.NAMESPACE_CLIENTE:
            self._init_namespace_cliente()
        elif namespace == self.NAMESPACE_FRETE:
            self._init_namespace_frete()
        elif namespace == self.NAMESPACE_EDICOES:
            self._init_namespace_edicoes()
        elif namespace == self.NAMESPACE_TRIBUTARIO:
            self._init_namespace_tributario()
        elif namespace == self.NAMESPACE_UI:
            self._init_namespace_ui()
    
    def reset_all(self) -> None:
        """Reseta todo o estado da aplicação"""
        namespaces = [
            self.NAMESPACE_SIMULACAO,
            self.NAMESPACE_CLIENTE,
            self.NAMESPACE_FRETE,
            self.NAMESPACE_EDICOES,
            self.NAMESPACE_TRIBUTARIO,
            self.NAMESPACE_UI
        ]
        
        for namespace in namespaces:
            self.clear_namespace(namespace)
    
    def reset_calculation_state(self) -> None:
        """Reseta apenas o estado relacionado a cálculos"""
        self.clear_namespace(self.NAMESPACE_SIMULACAO)
        self.clear_namespace(self.NAMESPACE_EDICOES)
    
    def get_debug_info(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações de debug organizadas por namespace"""
        debug_info = {}
        
        for key, value in st.session_state.items():
            if '.' in key:
                namespace, attr = key.split('.', 1)
                if namespace not in debug_info:
                    debug_info[namespace] = {}
                debug_info[namespace][attr] = value
        
        return debug_info
    
    # Métodos de conveniência para acesso aos namespaces mais usados
    
    def get_simulacao(self, key: str, default: Any = None) -> Any:
        """Acesso rápido ao namespace de simulação"""
        return self.get(self.NAMESPACE_SIMULACAO, key, default)
    
    def set_simulacao(self, key: str, value: Any) -> None:
        """Define valor no namespace de simulação"""
        self.set(self.NAMESPACE_SIMULACAO, key, value)
    
    def get_cliente(self, key: str, default: Any = None) -> Any:
        """Acesso rápido ao namespace de cliente"""
        return self.get(self.NAMESPACE_CLIENTE, key, default)
    
    def set_cliente(self, key: str, value: Any) -> None:
        """Define valor no namespace de cliente"""
        self.set(self.NAMESPACE_CLIENTE, key, value)
    
    def get_frete(self, key: str, default: Any = None) -> Any:
        """Acesso rápido ao namespace de frete"""
        return self.get(self.NAMESPACE_FRETE, key, default)
    
    def set_frete(self, key: str, value: Any) -> None:
        """Define valor no namespace de frete"""
        self.set(self.NAMESPACE_FRETE, key, value)
    
    def get_edicoes(self, key: str, default: Any = None) -> Any:
        """Acesso rápido ao namespace de edições"""
        return self.get(self.NAMESPACE_EDICOES, key, default)
    
    def set_edicoes(self, key: str, value: Any) -> None:
        """Define valor no namespace de edições"""
        self.set(self.NAMESPACE_EDICOES, key, value)
    
    def get_tributario(self, key: str, default: Any = None) -> Any:
        """Acesso rápido ao namespace tributário"""
        return self.get(self.NAMESPACE_TRIBUTARIO, key, default)
    
    def set_tributario(self, key: str, value: Any) -> None:
        """Define valor no namespace tributário"""
        self.set(self.NAMESPACE_TRIBUTARIO, key, value)
    
    def get_ui(self, key: str, default: Any = None) -> Any:
        """Acesso rápido ao namespace de UI"""
        return self.get(self.NAMESPACE_UI, key, default)
    
    def set_ui(self, key: str, value: Any) -> None:
        """Define valor no namespace de UI"""
        self.set(self.NAMESPACE_UI, key, value)