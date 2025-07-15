"""
Layout e Interface Principal - VERSÃO FINAL CORRIGIDA
====================================================
CORREÇÃO: Remove duplicação de widgets e corrige botão de calcular frete
"""

import streamlit as st
import pandas as pd
import os
from typing import Optional, Tuple, Dict, Any

from .components import (
    ClienteInfoComponent, ParametrosComponent, StatusComponent,
    ResumoEdicoesComponent, TabelaResultadosComponent, ResumoExecutivoComponent,
    ExportacaoComponent, MapasComponent
)
from utils.format_utils import montar_endereco_geocode
from utils.data_utils import (
    converter_percentuais_para_edicao, converter_percentuais_de_edicao,
    garantir_tipos_numericos
)


class SimuladorLayout:
    """Gerencia o layout e interface do simulador"""
    
    def __init__(self, state_manager, geolocation_service=None):
        self.state = state_manager
        self.geo_service = geolocation_service
    
    def configurar_pagina(self):
        """Configura a página do Streamlit"""
        st.title("📊 Simulador de Formação de Preço de Venda - 3.0")
        
        # Verificar se a imagem existe
        if os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
            st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=300)
    
    def exibir_secao_cliente(self, clientes_df: pd.DataFrame) -> Tuple[Optional[dict], str]:
        """Exibe a seção de seleção de cliente"""
        st.markdown("### 👤 Cliente ou Rede")
        
        opcao_cliente = st.radio(
            "Deseja simular para um cliente específico?", 
            ["Sim", "Não (Cliente novo)"], 
            horizontal=True,
            key="radio_opcao_cliente_principal"
        )
        
        dados_cliente_selecionado = None
        
        if opcao_cliente == "Sim" and not clientes_df.empty:
            # Criar lista de opções mais informativas
            opcoes_clientes = []
            for idx, row in clientes_df.iterrows():
                opcao = f"{row['A1_NOME']} - {row['cidade_ibge']}/{row['A1_EST']} - {row['A1_COD']}/{row['A1_LOJA']}"
                if row['REDE'] and str(row['REDE']) != str(row['A1_NOME'])[:20]:
                    opcao += f" - [{row['REDE']}]"
                opcoes_clientes.append(opcao)
            
            # Selectbox com informações completas
            cliente_escolhido_display = st.selectbox(
                "Selecione o cliente:", 
                opcoes_clientes,
                help="Formato: Nome - Cidade/UF - Código/Loja - [Rede]",
                key="selectbox_cliente_principal"
            )
            
            # Extrair o índice da opção selecionada
            if cliente_escolhido_display:
                indice_selecionado = opcoes_clientes.index(cliente_escolhido_display)
                dados_cliente_selecionado = clientes_df.iloc[indice_selecionado].to_dict()
                
                # Exibir informações do cliente selecionado
                ClienteInfoComponent.exibir_dados_completos(dados_cliente_selecionado)
                
                # Seção de cálculo de frete e rota (somente se tiver geolocalização)
                if self.geo_service:
                    self._exibir_secao_rota_integrada(dados_cliente_selecionado)
        
        elif opcao_cliente == "Sim":
            st.warning("⚠️ Nenhum cliente encontrado na base de dados.")
        
        return dados_cliente_selecionado, opcao_cliente
    
    def _exibir_secao_rota_integrada(self, dados_cliente: dict):
        """Exibe a seção de cálculo de rota integrada com seleção de cliente"""
        with st.expander("📦 Cálculo de Frete e Rota", expanded=False):
            st.markdown("### 🧭 Parâmetros de Rota")
            
            # Origens disponíveis
            origens = self.geo_service.get_origens_disponiveis()
            
            col1, col2 = st.columns(2)
            
            with col1:
                origem_opcao = st.selectbox(
                    "📌 Unidade de Origem", 
                    list(origens.keys()), 
                    index=0,
                    key="selectbox_origem_rota"
                )
                origem = origens[origem_opcao]
                st.text_input(
                    "📌 Endereço de Origem", 
                    origem, 
                    disabled=True,
                    key="text_input_endereco_origem"
                )
            
            with col2:
                # Cliente já selecionado - campo desabilitado
                cliente_info = f"{dados_cliente['A1_NOME']} - {dados_cliente['A1_COD']}/{dados_cliente['A1_LOJA']}"
                st.text_input(
                    "🎯 Cliente Selecionado", 
                    cliente_info, 
                    disabled=True,
                    help="Cliente definido na seção acima",
                    key="text_input_cliente_selecionado"
                )
                
                # Montar endereço destino
                endereco_destino = montar_endereco_geocode(dados_cliente)
                st.text_area(
                    "🎯 Endereço de Destino (para geocodificação)", 
                    endereco_destino, 
                    disabled=True,
                    height=80,
                    help="Endereço otimizado para melhor precisão no Google Maps",
                    key="text_area_endereco_destino"
                )
            
            st.markdown("---")
            
            # Seção de frete calculado automaticamente
            resultado_acao_frete = self._exibir_controles_frete(origem, dados_cliente)
            
            # PROCESSAR A AÇÃO DO BOTÃO AQUI
            if resultado_acao_frete and resultado_acao_frete[0] == 'calcular_frete':
                _, origem_calc, tipo_veiculo, dados_cliente_calc = resultado_acao_frete
                # Importar aqui para evitar dependência circular
                from core.simulador import SimuladorSobel
                # Precisamos de uma instância do simulador - vamos armazenar no state
                simulador_instance = self.state.get('simulador', 'simulador_instance')
                if simulador_instance and hasattr(simulador_instance, 'calcular_frete_automatico'):
                    simulador_instance.calcular_frete_automatico(origem_calc, dados_cliente_calc, tipo_veiculo)
            
            # Exibir resultados da rota se disponível
            if (self.state.get_frete('distancia_calculada') and 
                self.state.get_frete('tempo_calculado')):
                self._exibir_resultados_rota(origem)
    
    def _exibir_controles_frete(self, origem: str, dados_cliente: dict):
        """Exibe controles de frete"""
        col_frete1, col_frete2, col_frete3 = st.columns(3)
        
        with col_frete1:
            # Seletor de tipo de veículo
            tipo_veiculo = st.selectbox(
                "🚛 Tipo de Veículo", 
                ["truck", "carreta"], 
                format_func=lambda x: "Truck" if x == "truck" else "Carreta",
                key="selectbox_tipo_veiculo_frete"
            )
            
            # Botão de cálculo
            if st.button(
                "🚗 Calcular Distância e Frete", 
                use_container_width=True,
                key="button_calcular_frete"
            ):
                return ('calcular_frete', origem, tipo_veiculo, dados_cliente)
        
        with col_frete2:
            # Exibir frete calculado ou permitir override manual
            frete_calculado = self.state.get_frete('frete_calculado_automatico', 0.0)
            if frete_calculado > 0:
                tipo_usado = self.state.get_frete('tipo_veiculo_usado', 'truck')
                st.success(f"🚛 Frete Calculado ({tipo_usado.upper()}): R$ {frete_calculado:.2f}")
                usar_frete_calculado = st.checkbox(
                    "Usar frete calculado", 
                    value=True, 
                    key="checkbox_usar_frete_auto"
                )
                self.state.set_frete('usar_frete_auto', usar_frete_calculado)
            else:
                st.info("🚛 Frete não calculado ainda")
        
        with col_frete3:
            # Override manual do frete
            if not self.state.get_frete('usar_frete_auto', False):
                frete_manual = st.number_input(
                    "Frete Manual (R$)", 
                    min_value=0.0, 
                    value=1.50, 
                    step=0.01,
                    key="number_input_frete_manual"
                )
                return ('frete_manual', frete_manual)
            else:
                # Usar frete calculado
                st.text_input(
                    "Frete a Usar (R$)", 
                    f"{frete_calculado:.2f}", 
                    disabled=True,
                    help="Frete calculado automaticamente",
                    key="text_input_frete_calculado"
                )
                return ('frete_calculado', frete_calculado)
        
        return None
    
    def _exibir_resultados_rota(self, origem: str):
        """Exibe resultados da rota calculada"""
        st.markdown("### 📊 Resultado da Rota")
        col_res1, col_res2 = st.columns(2)
        
        distancia = self.state.get_frete('distancia_calculada')
        tempo = self.state.get_frete('tempo_calculado')
        
        col_res1.metric("📏 Distância", distancia)
        col_res2.metric("⏱️ Tempo Estimado", tempo)
        
        # Exibir mapas se coordenadas disponíveis
        origem_coords = self.state.get_frete('coordenadas_origem')
        destino_coords = self.state.get_frete('coordenadas_destino')
        
        if origem_coords and destino_coords and self.geo_service:
            MapasComponent.exibir_mapas_rota(
                self.geo_service.api_key, origem_coords, destino_coords, origem
            )
    
    def exibir_secao_parametros(self, opcoes_uf: list, uf_cliente: Optional[str] = None, 
                               contrato_real: Optional[float] = None) -> Dict[str, Any]:
        """Exibe a seção de parâmetros - SEM DUPLICAR O TIPO DE FRETE"""
        col_param1, col_param2, col_param3 = st.columns([1, 1, 1])
        
        parametros = {}
        
        with col_param1:
            st.markdown("#### ⚙️ Parâmetros de Origem")
            st.info("🏭 **Origem fixada:** SP (São Paulo)")
            
            # Verificar se há frete específico do cliente
            if self.state.get_frete('usar_frete_auto', False):
                frete_calculado = self.state.get_frete('frete_calculado_automatico', 0.0)
                frete_a_usar = frete_calculado
                frete_origem = "cliente selecionado"
                st.text_input(
                    f"Frete/Caixa (R$) - {frete_origem}", 
                    f"{frete_a_usar:.2f}", 
                    disabled=True,
                    help="Frete definido pela seleção do cliente",
                    key="text_input_frete_cliente_selecionado"
                )
                parametros['frete_padrao'] = frete_a_usar
                parametros['tipo_frete'] = 'CIF'  # Padrão quando há frete calculado
            else:
                frete_padrao = st.number_input(
                    "Frete/Caixa (R$)", 
                    min_value=0.0, 
                    value=self.state.get_frete('frete_padrao', 1.50), 
                    step=0.01,
                    key="number_input_frete_origem_params"
                )
                parametros['frete_padrao'] = frete_padrao
                
                # TIPO DE FRETE - APENAS AQUI, NÃO DUPLICAR
                parametros['tipo_frete'] = st.radio(
                    "Tipo de Frete", 
                    ("CIF", "FOB"),
                    key="radio_tipo_frete_unico"  # KEY ÚNICA
                )
        
        with col_param2:
            # Parâmetros de destino
            st.markdown("#### 📍 Parâmetros de Destino")
            
            if uf_cliente and uf_cliente in opcoes_uf:
                index_uf = opcoes_uf.index(uf_cliente)
                uf_selecionado = st.selectbox(
                    "UF de Destino (Cliente)", 
                    options=opcoes_uf, 
                    index=index_uf,
                    help="UF definida pelo cliente selecionado",
                    key="selectbox_uf_destino_cliente"
                )
            else:
                uf_selecionado = st.selectbox(
                    "UF de Destino", 
                    options=opcoes_uf,
                    key="selectbox_uf_destino_manual"
                )
            
            parametros['uf_selecionado'] = uf_selecionado
            
            # Contrato
            if contrato_real is not None:
                st.info("🧾 Usando contrato real do cliente selecionado.")
                parametros['contrato_percentual'] = contrato_real / 100
            else:
                contrato_input = st.number_input(
                    "% Contrato", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=1.00, 
                    step=0.01,
                    key="number_input_contrato_percentual"
                )
                parametros['contrato_percentual'] = contrato_input / 100
            
            # Mostrar alíquotas se UF selecionada
            if uf_selecionado:
                from config.tributaria import ConfiguracaoTributaria
                config_trib = ConfiguracaoTributaria()
                aliquotas_origem = config_trib.obter_aliquotas('SP')
                aliquotas_destino = config_trib.obter_aliquotas(uf_selecionado)
                
                info_tributos = (
                    f"ICMS SP→{uf_selecionado}: {aliquotas_origem['interestadual']:.1%} | "
                    f"Interno {uf_selecionado}: {aliquotas_destino['interna']:.1%}"
                )
                if aliquotas_destino['fcp'] > 0:
                    info_tributos += f" | FCP: {aliquotas_destino['fcp']:.1%}"
                st.info(info_tributos)
        
        with col_param3:
            # Parâmetros globais
            st.markdown("#### 💰 Parâmetros Globais")
            
            custo_fixo_global = st.number_input(
                "Custo Fixo Global (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha",
                key="number_input_custo_fixo_global"
            )
            
            comissao_input = st.number_input(
                "% Comissão Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.1,
                help="Se zero, usa valor da planilha",
                key="number_input_comissao_global"
            )
            
            bonificacao_input = st.number_input(
                "% Bonificação Global", 
                min_value=0.0, 
                max_value=100.0, 
                value=0.0, 
                step=0.01,
                help="Se zero, usa valor da planilha",
                key="number_input_bonificacao_global"
            )
            
            contrato_input = st.number_input(
                "% Contrato", 
                min_value=0.0, 
                max_value=100.0, 
                value=1.00, 
                step=0.01,
                key="number_input_contrato_global"
            )
            
            parametros.update({
                'custo_fixo_global': custo_fixo_global,
                'comissao_padrao': comissao_input / 100,
                'bonificacao_global': bonificacao_input / 100
            })
        
        return parametros
    
    def exibir_upload_arquivo(self) -> Optional[str]:
        """Exibe a seção de upload de arquivo"""
        uploaded_file = st.file_uploader(
            "📂 Atualizar planilha base (.xlsx)", 
            type="xlsx",
            key="file_uploader_planilha_base"
        )
        
        if uploaded_file:
            return uploaded_file
        
        return None
    
    def exibir_controles_principais(self) -> Optional[str]:
        """Exibe os controles principais"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button(
                "🎯 Calcular Ponto de Equilíbrio", 
                use_container_width=True,
                key="button_calcular_equilibrio"
            ):
                return 'equilibrio'
        
        with col2:
            if st.button(
                "🔄 Resetar", 
                use_container_width=True,
                key="button_resetar_dados"
            ):
                return 'reset'
        
        return None
    
    def exibir_status_simulacao(self):
        """Exibe o status atual da simulação"""
        uf_origem = self.state.get_simulacao('uf_origem', 'SP')
        uf_destino = self.state.get_simulacao('uf_destino', '')
        modo_equilibrio = self.state.get_simulacao('modo_equilibrio', False)
        comissao_global = self.state.get_tributario('comissao_padrao', 0.0)
        bonificacao_global = self.state.get_tributario('bonificacao_global', 0.0)
        comissoes_editadas = self.state.get_edicoes('comissoes_editadas', {})
        bonificacoes_editadas = self.state.get_edicoes('bonificacoes_editadas', {})
        
        StatusComponent.exibir_status_simulacao(
            uf_origem, uf_destino, modo_equilibrio,
            comissao_global, bonificacao_global,
            comissoes_editadas, bonificacoes_editadas
        )
    
    def exibir_resumo_edicoes(self) -> Optional[str]:
        """Exibe resumo das edições individuais"""
        comissoes_editadas = self.state.get_edicoes('comissoes_editadas', {})
        bonificacoes_editadas = self.state.get_edicoes('bonificacoes_editadas', {})
        valores_originais = self.state.get_edicoes('valores_originais', {})
        comissao_global = self.state.get_tributario('comissao_padrao', 0.0)
        bonificacao_global = self.state.get_tributario('bonificacao_global', 0.0)
        
        return ResumoEdicoesComponent.exibir_resumo(
            comissoes_editadas, bonificacoes_editadas,
            valores_originais, comissao_global, bonificacao_global
        )
    
    def exibir_editor_dados(self, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Exibe o editor de dados"""
        st.markdown("### 📊 Simulação Consolidada - Dados + Resultados")
        
        # Preparar dados para edição
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                         "MVA", "Comissão", "Bonificação", "Contrato"]
        
        df_para_edicao_clean = df_para_edicao[colunas_edicao].copy()
        
        # Converter colunas numéricas
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        df_para_edicao_clean = garantir_tipos_numericos(df_para_edicao_clean, colunas_numericas)
        
        # Arredondar valores
        for col in colunas_numericas:
            if col in df_para_edicao_clean.columns:
                df_para_edicao_clean[col] = df_para_edicao_clean[col].round(2)
        
        # Converter colunas percentuais para formato 0-100
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        df_para_edicao_clean = converter_percentuais_para_edicao(df_para_edicao_clean, colunas_percentuais)
        
        # Editor de dados
        df_editado = st.data_editor(
            df_para_edicao_clean,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor_principal",
            column_config={
                "Descrição": st.column_config.TextColumn("Produto", disabled=True),
                "Preço de Venda": st.column_config.NumberColumn("Preço Venda", format="%.2f", min_value=0.0, step=0.01),
                "Quantidade": st.column_config.NumberColumn("Qtd", format="%.0f", min_value=1, step=1),
                "Custo NET": st.column_config.NumberColumn("Custo NET", format="%.2f", min_value=0.0, step=0.01),
                "Custo Fixo": st.column_config.NumberColumn("Custo Fixo", format="%.2f", min_value=0.0, step=0.01),
                "MVA": st.column_config.NumberColumn("MVA (%)", format="%.2f", min_value=0.0, max_value=500.0, step=0.1),
                "Comissão": st.column_config.NumberColumn("Comissão (%) ⭐", format="%.2f", min_value=0.0, max_value=50.0, step=0.1,
                                                          help="⭐ = Editável individualmente. Sobrepõe valor global."),
                "Bonificação": st.column_config.NumberColumn("Bonificação (%) ⭐", format="%.2f", min_value=0.0, max_value=50.0, step=0.1,
                                                             help="⭐ = Editável individualmente. Sobrepõe valor global."),
                "Contrato": st.column_config.NumberColumn("% Contrato ⭐", format="%.2f", min_value=0.0, max_value=50.0, step=0.1, 
                                                          help="⭐ = Editável individualmente. Sobrepõe valor global.")
            }
        )
        
        return df_editado
    
    def processar_dados_editados(self, df_editado: pd.DataFrame, df_para_edicao: pd.DataFrame) -> pd.DataFrame:
        """Processa os dados editados"""
        # Converter valores percentuais de volta para decimal
        colunas_percentuais = ["MVA", "Comissão", "Bonificação", "Contrato"]
        df_processado = converter_percentuais_de_edicao(df_editado, colunas_percentuais)
        
        # Arredondar valores monetários
        colunas_numericas = ["Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo"]
        for col in colunas_numericas:
            if col in df_processado.columns:
                df_processado[col] = df_processado[col].round(2)
        
        # Detectar mudanças nas comissões e bonificações
        produtos_com_mudancas = []
        comissoes_editadas = self.state.get_edicoes('comissoes_editadas', {})
        bonificacoes_editadas = self.state.get_edicoes('bonificacoes_editadas', {})
        
        for index in df_processado.index:
            if index < len(df_para_edicao):
                produto = df_processado.at[index, "Descrição"]
                
                # Verificar mudanças na comissão
                try:
                    comissao_original = float(df_para_edicao.iloc[index]["Comissão"])
                    comissao_editada = float(df_processado.at[index, "Comissão"])
                    
                    if abs(comissao_original - comissao_editada) > 0.001:
                        comissoes_editadas[produto] = comissao_editada
                        produtos_com_mudancas.append(f"Comissão {produto}: {comissao_editada:.2%}")
                except (ValueError, TypeError, KeyError):
                    pass
                
                # Verificar mudanças na bonificação
                try:
                    bonificacao_original = float(df_para_edicao.iloc[index]["Bonificação"])
                    bonificacao_editada = float(df_processado.at[index, "Bonificação"])
                    
                    if abs(bonificacao_original - bonificacao_editada) > 0.001:
                        bonificacoes_editadas[produto] = bonificacao_editada
                        produtos_com_mudancas.append(f"Bonificação {produto}: {bonificacao_editada:.2%}")
                except (ValueError, TypeError, KeyError):
                    pass
        
        # Atualizar state
        self.state.set_edicoes('comissoes_editadas', comissoes_editadas)
        self.state.set_edicoes('bonificacoes_editadas', bonificacoes_editadas)
        
        # Mostrar mudanças detectadas
        if produtos_com_mudancas:
            st.info(f"🎯 Mudanças detectadas: {', '.join(produtos_com_mudancas[:3])}{'...' if len(produtos_com_mudancas) > 3 else ''}")
        
        # Criar DataFrame final combinando dados editados com não editados
        df_final = df_para_edicao.copy()
        
        # Atualizar com dados editados
        colunas_edicao = ["Descrição", "Preço de Venda", "Quantidade", "Custo NET", "Custo Fixo", 
                         "MVA", "Comissão", "Bonificação", "Contrato"]
        
        for col in colunas_edicao:
            if col in df_processado.columns:
                df_final[col] = df_processado[col]
        
        return df_final
    
    def exibir_botao_calcular(self) -> bool:
        """Exibe botão para calcular resultados"""
        return st.button(
            "🚀 Calcular Resultados", 
            type="primary",
            key="button_calcular_resultados_principal"
        )
    
    def exibir_tabela_resultados(self, df_display: pd.DataFrame):
        """Exibe tabela de resultados"""
        TabelaResultadosComponent.exibir_tabela_formatada(df_display)
    
    def exibir_resumo_executivo(self, df_display: pd.DataFrame):
        """Exibe resumo executivo"""
        ResumoExecutivoComponent.exibir_resumo(df_display)
    
    def exibir_detalhamento_calculo(self, df_final: pd.DataFrame, resultados: pd.DataFrame):
        """Exibe detalhamento do cálculo do primeiro produto"""
        if len(resultados) > 0:
            st.markdown("### 🔍 Detalhamento do Cálculo (Primeiro Produto)")
            
            primeiro = resultados.iloc[0]
            produto_nome = df_final.iloc[0]["Descrição"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **📦 {produto_nome}**
                
                **Base de Cálculo:**
                - Preço de Venda: R$ {primeiro['Preço Venda']:.2f}
                - Quantidade: {primeiro['Qtd']:.0f}
                - Subtotal: R$ {primeiro['Subtotal']:.2f}
                
                **ICMS-ST e FCP:**
                - MVA: {df_final.iloc[0]['MVA']:.2%}
                - Base ICMS-ST: R$ {primeiro['Base ICMS-ST']:.2f}
                - ICMS Próprio: R$ {primeiro['ICMS Próprio']:.2f}
                - ICMS-ST: R$ {primeiro['ICMS-ST']:.2f}
                - FCP: R$ {primeiro['FCP']:.2f}
                """)
            
            with col2:
                st.markdown(f"""
                **💰 Resultado Financeiro:**
                
                **Custos e Despesas:**
                - Custo Total: R$ {primeiro['Custo Total']:.2f}
                - Despesas Totais: R$ {primeiro['Total Despesas']:.2f}
                - Frete: R$ {primeiro['Frete Total']:.2f}
                
                **Lucro:**
                - Lucro Antes IR: R$ {primeiro['Lucro Antes IR']:.2f}
                - IRPJ + CSLL: R$ {primeiro['IRPJ'] + primeiro['CSLL']:.2f}
                - **Lucro Líquido: R$ {primeiro['Lucro Líquido']:.2f}**
                - **Margem: {primeiro['Margem Líquida %']:.1f}%**
                """)
    
    def exibir_secao_exportacao(self, df_final: pd.DataFrame, resultados: pd.DataFrame, df_display: pd.DataFrame):
        """Exibe seção de exportação"""
        uf_origem = self.state.get_simulacao('uf_origem', 'SP')
        uf_destino = self.state.get_simulacao('uf_destino', '')
        
        ExportacaoComponent.exibir_secao_exportacao(
            df_final, resultados, df_display, uf_origem, uf_destino
        )
    
    def exibir_notas_tecnicas(self):
        """Exibe as notas técnicas"""
        st.markdown("""
        ---
        ### 📚 Simulador Sobel Suprema v3.0 - Refatorado
        
        #### 🎯 **Melhorias da Versão Refatorada:**
        - 🔧 **Arquitetura Modular:** Código organizado por domínios (geo, cálculo, layout)
        - 🧠 **Estado Encapsulado:** Gerenciamento de estado por namespaces
        - 📁 **Separação de Responsabilidades:** Camadas utils e services bem definidas
        - 🚀 **Manutenibilidade:** Código mais fácil de manter e estender
        - 🧪 **Testabilidade:** Estrutura que facilita testes unitários
        
        #### 📋 **Estados com FCP:**
        AC, AL, BA, CE, MA, MG, MS, PA, PB, PR, PE, PI, RJ, RN, RS, SC, SE
        
        """)