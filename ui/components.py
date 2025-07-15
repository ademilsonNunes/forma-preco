"""
Componentes de UI - VERSÃO CORRIGIDA
===================================
Componentes reutilizáveis para a interface do usuário.
CORREÇÃO: Adicionadas keys únicas para todos os widgets Streamlit
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from utils.format_utils import (
    formatar_endereco_cliente, formatar_moeda, formatar_percentual,
    criar_status_info, colorir_valores_tabela, criar_resumo_executivo_texto
)
from utils.data_utils import formatar_cnpj_cpf, formatar_data_brasileira, safe_str


class ClienteInfoComponent:
    """Componente para exibir informações do cliente"""
    
    @staticmethod
    def exibir_dados_completos(cliente_data: dict) -> None:
        """Exibe dados completos do cliente selecionado"""
        st.markdown("#### 📋 Dados Completos do Cliente")
        
        # Primeira linha - Informações principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            razao_social = safe_str(cliente_data.get('A1_NOME', ''))
            codigo = safe_str(cliente_data.get('A1_COD', ''))
            loja = safe_str(cliente_data.get('A1_LOJA', ''))
            
            st.info(f"**🏢 Razão Social:**\n{razao_social}")
            st.info(f"**🏷️ Código/Loja:**\n{codigo}/{loja}")
        
        with col2:
            rede_info = safe_str(cliente_data.get('REDE', ''))
            nome_resumo = safe_str(cliente_data.get('A1_NOME', ''))[:20]
            
            if len(rede_info) > 0 and rede_info != nome_resumo:
                st.success(f"**🏪 Rede:**\n{rede_info}")
            else:
                st.info("**🏪 Rede:**\nCliente independente")
            
            try:
                contrato_valor = cliente_data.get("A1_ZZCONTR", 0)
                if contrato_valor is None or pd.isna(contrato_valor):
                    contrato_valor = 0.0
                else:
                    contrato_valor = float(contrato_valor)
            except (ValueError, TypeError):
                contrato_valor = 0.0
            
            st.success(f"**📄 Contrato:**\n{contrato_valor:.2f}%")
        
        with col3:
            uf = safe_str(cliente_data.get('A1_EST', ''))
            risco = safe_str(cliente_data.get('A1_RISCO', 'N/A'))
            
            st.info(f"**📍 UF:**\n{uf}")
            st.info(f"**⚠️ Risco:**\n{risco}")
        
        # Segunda linha - Endereço e dados financeiros
        col4, col5 = st.columns(2)
        
        with col4:
            endereco_completo = formatar_endereco_cliente(cliente_data)
            st.info(f"**📍 Endereço:**\n{endereco_completo}")
        
        with col5:
            # Limite de Crédito
            try:
                lc_value = cliente_data.get('A1_LC', 0)
                if lc_value is None or pd.isna(lc_value):
                    lc_value = 0
                else:
                    lc_value = float(lc_value)
                
                lc_text = formatar_moeda(lc_value) if lc_value > 0 else "Não definido"
            except (ValueError, TypeError):
                lc_text = "Não definido"
            
            st.info(f"**💳 Limite de Crédito:**\n{lc_text}")
            
            # Última compra
            ultima_compra = formatar_data_brasileira(cliente_data.get('A1_ULTCOM', ''))
            st.info(f"**🛒 Última Compra:**\n{ultima_compra}")
            
            # CNPJ/CPF se disponível
            cnpj = safe_str(cliente_data.get('A1_CGC', ''))
            if len(cnpj) > 0 and cnpj not in ['0', '']:
                cnpj_formatado = formatar_cnpj_cpf(cnpj)
                tipo_doc = "🏛️ CNPJ" if len(cnpj_formatado.replace('.', '').replace('/', '').replace('-', '')) == 14 else "👤 CPF"
                st.info(f"**{tipo_doc}:**\n{cnpj_formatado}")


class ParametrosComponent:
    """Componente para configuração de parâmetros"""
    
    @staticmethod
    def exibir_parametros_origem(uf_origem: str, frete_padrao: float, tipo_frete: str) -> Tuple[float, str]:
        """Exibe parâmetros de origem"""
        st.markdown("#### ⚙️ Parâmetros de Origem")
        st.info(f"🏭 **Origem fixada:** {uf_origem} (São Paulo)")
        
        frete = st.number_input(
            "Frete/Caixa (R$)", 
            min_value=0.0, 
            value=frete_padrao, 
            step=0.01,
            key="number_input_frete_origem"  # KEY ÚNICA
        )
        
        tipo = st.radio(
            "Tipo de Frete", 
            ("CIF", "FOB"),
            key="radio_tipo_frete_origem"  # KEY ÚNICA
        )
        
        return frete, tipo
    
    @staticmethod
    def exibir_parametros_destino(opcoes_uf: list, uf_cliente: Optional[str] = None) -> str:
        """Exibe parâmetros de destino"""
        st.markdown("#### 📍 Parâmetros de Destino")
        
        if uf_cliente and uf_cliente in opcoes_uf:
            index_uf = opcoes_uf.index(uf_cliente)
            uf_selecionado = st.selectbox(
                "UF de Destino (Cliente)", 
                options=opcoes_uf, 
                index=index_uf,
                help="UF definida pelo cliente selecionado",
                key="selectbox_uf_destino_cliente"  # KEY ÚNICA
            )
        else:
            uf_selecionado = st.selectbox(
                "UF de Destino", 
                options=opcoes_uf,
                key="selectbox_uf_destino_manual"  # KEY ÚNICA
            )
        
        return uf_selecionado
    
    @staticmethod
    def exibir_parametros_globais() -> Tuple[float, float, float, float]:
        """Exibe parâmetros globais"""
        st.markdown("#### 💰 Parâmetros Globais")
        
        custo_fixo_global = st.number_input(
            "Custo Fixo Global (R$)", 
            min_value=0.0, 
            value=0.0, 
            step=0.01,
            help="Se zero, usa valor da planilha",
            key="number_input_custo_fixo_global"  # KEY ÚNICA
        )
        
        comissao_input = st.number_input(
            "% Comissão Global", 
            min_value=0.0, 
            max_value=100.0, 
            value=0.0, 
            step=0.1,
            help="Se zero, usa valor da planilha",
            key="number_input_comissao_global"  # KEY ÚNICA
        )
        
        bonificacao_input = st.number_input(
            "% Bonificação Global", 
            min_value=0.0, 
            max_value=100.0, 
            value=0.0, 
            step=0.01,
            help="Se zero, usa valor da planilha",
            key="number_input_bonificacao_global"  # KEY ÚNICA
        )
        
        contrato_input = st.number_input(
            "% Contrato", 
            min_value=0.0, 
            max_value=100.0, 
            value=1.00, 
            step=0.01,
            key="number_input_contrato_global"  # KEY ÚNICA
        )
        
        return custo_fixo_global, comissao_input / 100, bonificacao_input / 100, contrato_input / 100


class StatusComponent:
    """Componente para exibir status da simulação"""
    
    @staticmethod
    def exibir_status_simulacao(uf_origem: str, uf_destino: str, modo_equilibrio: bool,
                              comissao_global: float, bonificacao_global: float,
                              comissoes_editadas: dict, bonificacoes_editadas: dict) -> None:
        """Exibe status atual da simulação"""
        status_info = criar_status_info(
            uf_origem, uf_destino, modo_equilibrio,
            comissao_global, bonificacao_global,
            comissoes_editadas, bonificacoes_editadas
        )
        st.info(status_info)


class ResumoEdicoesComponent:
    """Componente para resumo de edições individuais"""
    
    @staticmethod
    def exibir_resumo(comissoes_editadas: dict, bonificacoes_editadas: dict,
                     valores_originais: dict, comissao_global: float, bonificacao_global: float) -> None:
        """Exibe resumo das edições individuais"""
        if comissoes_editadas or bonificacoes_editadas:
            with st.expander("🎯 Resumo das Edições Individuais", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    if comissoes_editadas:
                        st.markdown("**Comissões Personalizadas:**")
                        for produto, valor in comissoes_editadas.items():
                            original = valores_originais.get(produto, {}).get('comissao', 0)
                            global_val = comissao_global if comissao_global > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                    
                    if st.button(
                        "🔄 Limpar Comissões Editadas",
                        key="button_limpar_comissoes"  # KEY ÚNICA
                    ):
                        return 'clear_comissoes'
                
                with col2:
                    if bonificacoes_editadas:
                        st.markdown("**Bonificações Personalizadas:**")
                        for produto, valor in bonificacoes_editadas.items():
                            original = valores_originais.get(produto, {}).get('bonificacao', 0)
                            global_val = bonificacao_global if bonificacao_global > 0 else original
                            st.write(f"• {produto}: {valor:.1%} (era {global_val:.1%})")
                    
                    if st.button(
                        "🔄 Limpar Bonificações Editadas",
                        key="button_limpar_bonificacoes"  # KEY ÚNICA
                    ):
                        return 'clear_bonificacoes'
        
        return None


class TabelaResultadosComponent:
    """Componente para exibir tabela de resultados"""
    
    @staticmethod
    def exibir_tabela_formatada(df_display: pd.DataFrame) -> None:
        """Exibe a tabela de resultados com formatação"""
        styled_display = df_display.style.format({
            "Preço Venda": "R$ {:.2f}",
            "Subtotal": "R$ {:.2f}",
            "IPI": "R$ {:.2f}",
            "ICMS-ST": "R$ {:.2f}",
            "FCP": "R$ {:.2f}",
            "Total NF": "R$ {:.2f}",
            "Custo Total": "R$ {:.2f}",
            "Despesas": "R$ {:.2f}",
            "Lucro Antes IR": "R$ {:.2f}",
            "IRPJ+CSLL": "R$ {:.2f}",
            "Lucro Líquido": "R$ {:.2f}",
            "Margem %": "{:.1f}%",
            "Equilíbrio": "R$ {:.2f}"
        }).applymap(colorir_valores_tabela, subset=["Lucro Antes IR", "Lucro Líquido", "Margem %"])
        
        st.dataframe(styled_display, use_container_width=True)


class ResumoExecutivoComponent:
    """Componente para exibir resumo executivo"""
    
    @staticmethod
    def exibir_resumo(df_display: pd.DataFrame) -> None:
        """Exibe o resumo executivo"""
        if len(df_display) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receita = df_display["Subtotal"].sum()
                st.metric("💰 Receita Total", formatar_moeda(total_receita))
            
            with col2:
                total_lucro_liquido = df_display["Lucro Líquido"].sum()
                delta_text = f"{(total_lucro_liquido/total_receita)*100:.1f}%" if total_receita > 0 else "0%"
                st.metric("💵 Lucro Líquido", formatar_moeda(total_lucro_liquido), delta=delta_text)
            
            with col3:
                margem_media = df_display["Margem %"].mean()
                st.metric("📊 Margem Média", formatar_percentual(margem_media))
            
            with col4:
                produtos_prejuizo = len(df_display[df_display["Lucro Líquido"] < 0])
                st.metric("⚠️ Produtos c/ Prejuízo", produtos_prejuizo)


class ExportacaoComponent:
    """Componente para exportação de dados"""
    
    @staticmethod
    def exibir_secao_exportacao(df_final: pd.DataFrame, resultados: pd.DataFrame, 
                               df_display: pd.DataFrame, uf_origem: str, uf_destino: str) -> None:
        """Exibe a seção de exportação"""
        st.markdown("### 📄 Exportar Resultados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "📊 Baixar Resumo Executivo", 
                use_container_width=True,
                key="button_baixar_resumo"  # KEY ÚNICA
            ):
                # Criar DataFrame consolidado
                from utils.data_utils import preparar_dados_para_exportacao
                df_export = preparar_dados_para_exportacao(df_final, resultados)
                
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    # Aba principal
                    df_export.to_excel(writer, index=False, sheet_name="Simulacao_Completa")
                    
                    # Aba resumo
                    resumo = pd.DataFrame({
                        "Métrica": ["Receita Total", "Lucro Líquido Total", "Margem Média", "Produtos com Prejuízo"],
                        "Valor": [
                            formatar_moeda(df_display['Subtotal'].sum()),
                            formatar_moeda(df_display['Lucro Líquido'].sum()),
                            formatar_percentual(df_display['Margem %'].mean()),
                            len(df_display[df_display["Lucro Líquido"] < 0])
                        ]
                    })
                    resumo.to_excel(writer, index=False, sheet_name="Resumo_Executivo")
                
                st.download_button(
                    label="📄 Download Excel Completo",
                    data=excel_buffer.getvalue(),
                    file_name=f"simulacao_sobel_{uf_origem}_{uf_destino}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_button_excel"  # KEY ÚNICA
                )
        
        with col2:
            if st.button(
                "📋 Copiar Resumo", 
                use_container_width=True,
                key="button_copiar_resumo"  # KEY ÚNICA
            ):
                resumo_texto = criar_resumo_executivo_texto(df_display, uf_origem, uf_destino)
                st.code(resumo_texto)


class MapasComponent:
    """Componente para exibir mapas"""
    
    @staticmethod
    def exibir_mapas_rota(api_key: str, origem_coords: Tuple[float, float], 
                         destino_coords: Tuple[float, float], origem_nome: str) -> None:
        """Exibe mapas para a rota calculada"""
        st.markdown("---")
        col_mapa, col_street = st.columns(2)
        
        with col_mapa:
            st.markdown("#### 🗺️ Mapa com Rota")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={api_key}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{map_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)
        
        with col_street:
            st.markdown("#### 🚦 Street View - Destino")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={api_key}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'''
                <iframe width="100%" height="300" frameborder="0" style="border:0"
                src="{street_embed_url}" allowfullscreen></iframe>
            ''', unsafe_allow_html=True)
        
        # Informações sobre coordenadas
        st.markdown("#### 📍 Coordenadas Utilizadas")
        col_coord1, col_coord2 = st.columns(2)
        with col_coord1:
            st.info(f"**Origem:**\n{origem_coords[0]:.6f}, {origem_coords[1]:.6f}")
        with col_coord2:
            st.info(f"**Destino:**\n{destino_coords[0]:.6f}, {destino_coords[1]:.6f}")
        
        st.markdown("---")