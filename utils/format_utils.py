"""
Utilitários de Formatação
=========================
Funções para formatação de dados para exibição.
"""

import pandas as pd
from datetime import datetime


def formatar_moeda(valor: float) -> str:
    """Formata valor como moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_percentual(valor: float) -> str:
    """Formata valor como percentual"""
    return f"{valor:.1f}%"


def criar_status_info(uf_origem: str, uf_destino: str, modo_equilibrio: bool, 
                     comissao_global: float, bonificacao_global: float,
                     comissoes_editadas: dict, bonificacoes_editadas: dict) -> str:
    """Cria string de status da simulação"""
    status_info = f"🗺️ **{uf_origem} → {uf_destino}** | "
    
    if modo_equilibrio:
        status_info += "🔒 **Modo Equilíbrio Ativo**"
    else:
        status_info += "📋 **Modo Normal**"
    
    # Parâmetros globais ativos
    parametros_ativos = []
    if comissao_global > 0:
        parametros_ativos.append(f"Comissão Global: {comissao_global:.1%}")
    if bonificacao_global > 0:
        parametros_ativos.append(f"Bonificação Global: {bonificacao_global:.1%}")
    
    if parametros_ativos:
        status_info += f" | {' | '.join(parametros_ativos)}"
    
    # Edições individuais
    edicoes_individuais = []
    if comissoes_editadas:
        edicoes_individuais.append(f"Comissões editadas: {len(comissoes_editadas)}")
    if bonificacoes_editadas:
        edicoes_individuais.append(f"Bonificações editadas: {len(bonificacoes_editadas)}")
    
    if edicoes_individuais:
        status_info += f" | 🎯 {' | '.join(edicoes_individuais)}"
    
    return status_info


def colorir_valores_tabela(val):
    """Aplica cores condicionais para valores na tabela"""
    try:
        if isinstance(val, (int, float)):
            if val < 0:
                return 'color: red; font-weight: bold'
            elif val > 0:
                return 'color: green'
        return 'color: black'
    except:
        return 'color: black'


def criar_resumo_executivo_texto(df_display: pd.DataFrame, uf_origem: str, uf_destino: str) -> str:
    """Cria texto do resumo executivo para exportação"""
    resumo_texto = f"""
SIMULAÇÃO SOBEL - {uf_origem} → {uf_destino}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

RESUMO EXECUTIVO:
• Receita Total: {formatar_moeda(df_display['Subtotal'].sum())}
• Lucro Líquido: {formatar_moeda(df_display['Lucro Líquido'].sum())}
• Margem Média: {formatar_percentual(df_display['Margem %'].mean())}
• Produtos com Prejuízo: {len(df_display[df_display['Lucro Líquido'] < 0])}

PRODUTOS:
{chr(10).join([f"• {row['Produto']}: {formatar_moeda(row['Preço Venda'])} | Margem: {formatar_percentual(row['Margem %'])}" for _, row in df_display.iterrows()])}
    """
    return resumo_texto


def formatar_endereco_cliente(cliente_dict: dict) -> str:
    """Formata endereço do cliente de forma organizada"""
    from .data_utils import safe_str
    
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
        from .data_utils import formatar_cep
        cep_formatado = formatar_cep(cep)
        if cep_formatado:
            endereco_partes.append(f"CEP: {cep_formatado}")
    
    # Montar endereço final
    if len(endereco_partes) > 0:
        return '\n'.join(endereco_partes)
    else:
        return "Endereço não informado"


def montar_endereco_geocode(cliente_dict: dict) -> str:
    """Monta endereço completo otimizado para geocodificação do Google Maps"""
    from .data_utils import safe_str
    
    partes_endereco = []
    
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
        from .data_utils import formatar_cep
        cep_formatado = formatar_cep(cep)
        if cep_formatado:
            partes_endereco.append(f"CEP {cep_formatado}")
    
    # País para maior precisão
    partes_endereco.append("Brasil")
    
    # Montar endereço final separado por vírgulas (formato ideal para Google Maps)
    return ", ".join(partes_endereco)