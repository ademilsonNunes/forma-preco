"""
Simulador Principal - VERSÃO CORRIGIDA
=====================================
CORREÇÃO: Botão de calcular frete funcionando e instância disponível no layout
"""

import pandas as pd
import streamlit as st
import os
from datetime import datetime
from typing import Optional, Tuple

from .state_manager import StateManager
from services.database_service import DatabaseService
from services.geolocation_service import GeolocationService
from services.calculation_service import CalculadoraResultados, CalculadoraPontoEquilibrio
from services.logistics_service import LogisticsService
from config.tributaria import ConfiguracaoTributaria
from ui.layout import SimuladorLayout
from utils.frete_utils import (
    buscar_frete_inteligente, calcular_frete_otimizado, obter_faixa_km_exata
)
from utils.data_utils import extrair_faixas_km_ordenadas, arredondar_valor
from utils.format_utils import montar_endereco_geocode


class SimuladorSobel:
    """Classe principal do simulador refatorada"""
    
    def __init__(self):
        # Inicializar gerenciadores principais
        self.state = StateManager()
        self.config_tributaria = ConfiguracaoTributaria()
        
        # Configurar serviços
        self._configurar_servicos()
        
        # Configurar layout
        self.layout = SimuladorLayout(self.state, self.geo_service)
        
        # IMPORTANTE: Armazenar instância do simulador no state para o layout acessar
        self.state.set('simulador', 'simulador_instance', self)
        
        # Carregar dados iniciais
        self._carregar_dados_iniciais()
    
    def _configurar_servicos(self):
        """Configura todos os serviços necessários"""
        # Serviço de banco de dados
        connection_string = DatabaseService.get_default_connection_string()
        self.db_service = DatabaseService(connection_string)

        # Carregar dados logísticos de capacidade de produtos
        self.df_logistica = self.db_service.carregar_produtos_truck_carreta()
        if self.df_logistica.empty:
            self.df_logistica = pd.DataFrame()
            st.info("ℹ️ Dados logísticos não encontrados ou vazios.")
        self.logistics_service = None if self.df_logistica.empty else LogisticsService(self.df_logistica)
        
        # Serviço de geolocalização
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key:
            self.geo_service = GeolocationService(api_key)
        else:
            self.geo_service = None
            st.warning("⚠️ Google Maps API key não encontrada. Funcionalidades de geolocalização desabilitadas.")
    
    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais necessários"""
        arquivo_padrao = "Custo de reposição.xlsx"
        
        if os.path.exists(arquivo_padrao):
            try:
                self.df_padrao = pd.read_excel(arquivo_padrao)
                self.df_padrao.columns = self.df_padrao.columns.str.strip()
                st.success("✅ Planilha base carregada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao carregar arquivo padrão: {str(e)}")
                self.df_padrao = pd.DataFrame()
        else:
            st.warning("⚠️ Arquivo padrão 'Custo de reposição.xlsx' não encontrado.")
            self.df_padrao = pd.DataFrame()
        
        # Carregar clientes e extrair faixas de frete
        self.clientes_df = self.db_service.carregar_clientes_ou_rede()
        if not self.clientes_df.empty:
            self.faixas_km_ordenadas = extrair_faixas_km_ordenadas(self.clientes_df)
            if self.faixas_km_ordenadas:
                st.success(f"✅ {len(self.faixas_km_ordenadas)} faixas de frete carregadas!")
        else:
            self.faixas_km_ordenadas = []
            st.warning("⚠️ Nenhum dado de cliente carregado.")
    
    def executar(self):
        """Método principal para executar o simulador"""
        # Configurar página
        self.layout.configurar_pagina()
        
        # Verificar se dados estão disponíveis
        if not self._validar_dados_iniciais():
            return
        
        # Exibir interface principal
        self._exibir_interface_principal()
    
    def _validar_dados_iniciais(self) -> bool:
        """Valida se os dados iniciais estão disponíveis"""
        if self.df_padrao.empty:
            st.error("❌ Planilha base não carregada. Faça upload de uma planilha válida.")
            return False
        
        if self.clientes_df.empty:
            st.warning("⚠️ Base de clientes não disponível. Algumas funcionalidades podem estar limitadas.")
        
        return True
    
    def _exibir_interface_principal(self):
        """Exibe a interface principal da aplicação"""
        # Seção de cliente
        dados_cliente, opcao_cliente = self.layout.exibir_secao_cliente(self.clientes_df)
        self.state.set_cliente('dados_selecionado', dados_cliente)
        self.state.set_cliente('opcao_cliente', opcao_cliente)
        
        # Extrair dados do cliente para uso posterior
        contrato_real = None
        uf_cliente = None
        if dados_cliente:
            try:
                contrato_valor = dados_cliente.get("A1_ZZCONTR", 0)
                if contrato_valor and not pd.isna(contrato_valor):
                    contrato_real = float(contrato_valor)
                uf_cliente = dados_cliente.get('A1_EST')
            except (ValueError, TypeError):
                pass
        
        # Seção de parâmetros
        opcoes_uf = self.df_padrao["UF"].dropna().unique().tolist()
        parametros = self.layout.exibir_secao_parametros(opcoes_uf, uf_cliente, contrato_real)
        self._aplicar_parametros(parametros)
        
        # Upload de arquivo
        uploaded_file = self.layout.exibir_upload_arquivo()
        if uploaded_file:
            self._processar_upload_arquivo(uploaded_file)
            return
        
        # Verificar se UF foi selecionada
        if not parametros.get('uf_selecionado'):
            st.warning("⚠️ Selecione uma UF de destino para continuar.")
            return
        
        # Processar simulação principal
        self._processar_simulacao_principal(parametros)
    
    def _aplicar_parametros(self, parametros: dict):
        """Aplica parâmetros ao estado"""
        # Parâmetros de simulação
        self.state.set_simulacao('uf_origem', 'SP')
        self.state.set_simulacao('uf_destino', parametros.get('uf_selecionado'))
        self.state.set_simulacao('tipo_frete', parametros.get('tipo_frete', 'CIF'))
        
        # Parâmetros de frete
        self.state.set_frete('frete_padrao', parametros.get('frete_padrao', 1.50))
        
        # Parâmetros tributários
        self.state.set_tributario('custo_fixo_global', parametros.get('custo_fixo_global', 0.0))
        self.state.set_tributario('comissao_padrao', parametros.get('comissao_padrao', 0.0))
        self.state.set_tributario('bonificacao_global', parametros.get('bonificacao_global', 0.0))
        self.state.set_tributario('contrato_percentual', parametros.get('contrato_percentual', 0.01))
    
    def _processar_upload_arquivo(self, uploaded_file):
        """Processa upload de novo arquivo"""
        try:
            arquivo_padrao = "Custo de reposição.xlsx"
            
            # Criar backup se arquivo existe
            if os.path.exists(arquivo_padrao):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"Custo de reposição_backup_{timestamp}.xlsx"
                os.rename(arquivo_padrao, backup_name)
                st.success(f"✅ Backup criado: {backup_name}")
            
            # Salvar novo arquivo
            with open(arquivo_padrao, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("✅ Arquivo atualizado com sucesso!")
            
            # Recarregar dados
            self.df_padrao = pd.read_excel(arquivo_padrao)
            self.df_padrao.columns = self.df_padrao.columns.str.strip()
            
            # Resetar estado
            self.state.reset_all()
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
    
    def _processar_simulacao_principal(self, parametros: dict):
        """Processa a simulação principal"""
        uf_destino = parametros['uf_selecionado']
        
        # Preparar dados base
        df_base = self._preparar_dados_base(uf_destino, parametros)
        
        if df_base.empty:
            st.error(f"❌ Nenhum produto encontrado para a UF {uf_destino}")
            return
        
        # Exibir controles principais
        acao = self.layout.exibir_controles_principais()
        if acao == 'equilibrio':
            self._calcular_ponto_equilibrio(df_base)
        elif acao == 'reset':
            self.state.reset_calculation_state()
            st.success("✅ Dados resetados!")
            st.rerun()
        
        # Processar edição e resultados
        self._processar_edicao_e_resultados(df_base)
    
    def _preparar_dados_base(self, uf_destino: str, parametros: dict) -> pd.DataFrame:
        """Prepara os dados base para simulação"""
        # Filtrar por UF
        df_base = self.df_padrao[self.df_padrao["UF"] == uf_destino].copy()
        
        # Resetar dados se mudou UF
        df_atual = self.state.get_simulacao('df_atual')
        if df_atual is not None and "UF" in df_atual.columns:
            ufs_atuais = df_atual["UF"].unique()
            if len(ufs_atuais) > 0 and ufs_atuais[0] != uf_destino:
                self.state.reset_calculation_state()
        
        # Filtrar produtos esperados
        produtos_esperados = self.state.get_ui('produtos_esperados', [])
        df_base = df_base[df_base["Descrição"].isin(produtos_esperados)].copy()
        
        # Ajustar colunas necessárias
        df_base = self._ajustar_colunas_necessarias(df_base, uf_destino)
        
        # Aplicar parâmetros globais
        df_base = self._aplicar_parametros_globais(df_base, parametros)
        
        return df_base
    
    def _ajustar_colunas_necessarias(self, df: pd.DataFrame, uf_destino: str) -> pd.DataFrame:
        """Ajusta colunas necessárias no DataFrame"""
        colunas_necessarias = [
            "Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico", "IPI", 
            "ICMS ST", "ICMS", "MVA", "Comissão", "Bonificação", "COFINS", "PIS", 
            "Contigência", "ICMS Interestadual", "ICMS Interno Destino", "FCP"
        ]
        
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(uf_destino)
        
        for col in colunas_necessarias:
            if col not in df.columns:
                if col == "Quantidade":
                    df[col] = 1
                elif col == "ICMS Interestadual":
                    df[col] = aliquotas_origem['interestadual']
                elif col == "ICMS Interno Destino":
                    df[col] = aliquotas_destino['interna']
                elif col == "FCP":
                    df[col] = aliquotas_destino['fcp']
                else:
                    df[col] = 0.0
        
        return df
    
    def _aplicar_parametros_globais(self, df: pd.DataFrame, parametros: dict) -> pd.DataFrame:
        """Aplica parâmetros globais ao DataFrame"""
        uf_destino = parametros['uf_selecionado']
        aliquotas_origem = self.config_tributaria.obter_aliquotas('SP')
        aliquotas_destino = self.config_tributaria.obter_aliquotas(uf_destino)
        
        # Aplicar frete (pode vir do cliente ou manual)
        frete_padrao = parametros.get('frete_padrao', 1.50)
        df["Frete Caixa"] = frete_padrao
        
        # Outros parâmetros
        df["Contrato"] = parametros.get('contrato_percentual', 0.01)
        df["UF Origem"] = 'SP'
        df["UF Destino"] = uf_destino
        df["ICMS Interestadual"] = aliquotas_origem['interestadual']
        df["ICMS Interno Destino"] = aliquotas_destino['interna']
        df["FCP"] = aliquotas_destino['fcp']
        
        # Parâmetros globais condicionais
        custo_fixo_global = parametros.get('custo_fixo_global', 0.0)
        if custo_fixo_global > 0:
            df["Custo Fixo"] = custo_fixo_global
        
        comissao_padrao = parametros.get('comissao_padrao', 0.0)
        if comissao_padrao > 0:
            df["Comissão"] = comissao_padrao
            self.state.set_edicoes('comissao_global_aplicada', True)
        else:
            self.state.set_edicoes('comissao_global_aplicada', False)
        
        bonificacao_global = parametros.get('bonificacao_global', 0.0)
        if bonificacao_global > 0:
            df["Bonificação"] = bonificacao_global
        
        return df
    
    def _calcular_ponto_equilibrio(self, df_base: pd.DataFrame):
        """Calcula ponto de equilíbrio para todos os produtos"""
        tipo_frete = self.state.get_simulacao('tipo_frete', 'CIF')
        df_equilibrio, alertas = CalculadoraPontoEquilibrio.calcular_para_dataframe(df_base, tipo_frete)
        
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        
        self.state.set_simulacao('df_atual', df_equilibrio.copy())
        self.state.set_simulacao('modo_equilibrio', True)
        st.success("✅ Ponto de equilíbrio calculado!")
    
    def _processar_edicao_e_resultados(self, df_base: pd.DataFrame):
        """Processa a edição de dados e cálculo de resultados"""
        # Determinar DataFrame para edição
        df_atual = self.state.get_simulacao('df_atual')
        df_edicao_temp = self.state.get_simulacao('df_edicao_temp')

        if df_atual is not None:
            df_para_edicao = df_atual.copy()
        elif df_edicao_temp is not None:
            df_para_edicao = df_edicao_temp.copy()
        else:
            df_para_edicao = df_base.copy()
        
        # Aplicar lógica híbrida de comissão e bonificação
        df_para_edicao = self._aplicar_logica_comissao_bonificacao(df_para_edicao)
        
        # Exibir status
        self.layout.exibir_status_simulacao()
        
        # Exibir resumo de edições
        acao_resumo = self.layout.exibir_resumo_edicoes()
        if acao_resumo == 'clear_comissoes':
            self.state.set_edicoes('comissoes_editadas', {})
            st.rerun()
        elif acao_resumo == 'clear_bonificacoes':
            self.state.set_edicoes('bonificacoes_editadas', {})
            st.rerun()
        
        # Exibir editor de dados
        df_editado = self.layout.exibir_editor_dados(df_para_edicao)
        
        # Processar dados editados
        df_final = self.layout.processar_dados_editados(df_editado, df_para_edicao)
        
        # Armazenar edição temporária
        self.state.set_simulacao('df_edicao_temp', df_final.copy())
        
        # Calcular e exibir resultados
        self._calcular_e_exibir_resultados(df_final)
    
    def _aplicar_logica_comissao_bonificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica lógica híbrida de comissão e bonificação"""
        df_temp = df.copy()
        
        # Garantir que colunas existam e sejam numéricas
        for col in ["Comissão", "Bonificação"]:
            if col not in df_temp.columns:
                df_temp[col] = 0.0
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0.0)
        
        # Armazenar valores originais se ainda não foram armazenados
        valores_originais = self.state.get_edicoes('valores_originais', {})
        if not valores_originais:
            for index in df_temp.index:
                produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
                valores_originais[produto] = {
                    'comissao': float(df_temp.at[index, "Comissão"]),
                    'bonificacao': float(df_temp.at[index, "Bonificação"])
                }
            self.state.set_edicoes('valores_originais', valores_originais)
        
        # Aplicar valores globais se ativos e não editados individualmente
        comissao_global_aplicada = self.state.get_edicoes('comissao_global_aplicada', False)
        comissao_padrao = self.state.get_tributario('comissao_padrao', 0.0)
        bonificacao_global = self.state.get_tributario('bonificacao_global', 0.0)
        comissoes_editadas = self.state.get_edicoes('comissoes_editadas', {})
        bonificacoes_editadas = self.state.get_edicoes('bonificacoes_editadas', {})
        
        for index in df_temp.index:
            produto = df_temp.at[index, "Descrição"] if "Descrição" in df_temp.columns else str(index)
            
            # Comissão global
            if (comissao_global_aplicada and 
                comissao_padrao > 0 and 
                produto not in comissoes_editadas):
                df_temp.at[index, "Comissão"] = float(comissao_padrao)
            
            # Bonificação global
            if (bonificacao_global > 0 and 
                produto not in bonificacoes_editadas):
                df_temp.at[index, "Bonificação"] = float(bonificacao_global)
        
        # Aplicar valores editados individualmente (PRIORIDADE MÁXIMA)
        for produto, valor in comissoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Comissão"] = float(valor)
        
        for produto, valor in bonificacoes_editadas.items():
            mask = df_temp["Descrição"] == produto if "Descrição" in df_temp.columns else False
            if isinstance(mask, pd.Series) and mask.any():
                df_temp.loc[mask, "Bonificação"] = float(valor)
        
        # Garantir tipos corretos
        df_temp["Comissão"] = df_temp["Comissão"].astype(float)
        df_temp["Bonificação"] = df_temp["Bonificação"].astype(float)
        
        return df_temp
    
    def _calcular_e_exibir_resultados(self, df_final: pd.DataFrame):
        """Calcula e exibe os resultados"""
        # Botão para aplicar cálculo
        if self.layout.exibir_botao_calcular():
            # OTIMIZAÇÃO DE FRETE: Reavalia baseado no volume total
            self._otimizar_frete_por_volume(df_final)
            
            # Armazenar dados no estado
            self.state.set_simulacao('df_atual', df_final.copy())
            self.state.set_simulacao('resultados_atualizados', True)
            st.rerun()
        
        # Mostrar resultados apenas após clique no botão
        if self.state.get_simulacao('resultados_atualizados', False):
            self._exibir_resultados_calculados(df_final)
    
    def _otimizar_frete_por_volume(self, df_final: pd.DataFrame):
        """Otimiza frete baseado no volume total"""
        resultado_frete_completo = self.state.get_frete('resultado_frete_completo')
        if resultado_frete_completo:
            # Calcular volume total
            volume_total = df_final["Quantidade"].sum()
            if hasattr(self, "df_logistica") and not self.df_logistica.empty:
                try:
                    codigo_col_final = next((c for c in ["CODIGO", "Codigo", "Código", "Produto", "Descrição", "Descrição"] if c in df_final.columns), None)
                    codigo_col_log = next((c for c in ["CODIGO", "Codigo", "produto", "PRODUTO", "DESCRICAO", "Descrição"] if c in self.df_logistica.columns), None)
                    peso_col = next((c for c in ["PESO", "PESO_KG", "PESO_CAIXA"] if c in self.df_logistica.columns), None)
                    volume_col = next((c for c in ["VOLUME", "VOLUME_M3", "CUBAGEM"] if c in self.df_logistica.columns), None)

                    if codigo_col_final and codigo_col_log and (peso_col or volume_col):
                        df_merge = df_final[[codigo_col_final, "Quantidade"]].merge(
                            self.df_logistica,
                            left_on=codigo_col_final,
                            right_on=codigo_col_log,
                            how="left"
                        )
                        df_merge["_peso"] = pd.to_numeric(df_merge[peso_col], errors="coerce").fillna(0) * df_merge["Quantidade"] if peso_col else 0
                        df_merge["_vol"] = pd.to_numeric(df_merge[volume_col], errors="coerce").fillna(0) * df_merge["Quantidade"] if volume_col else 0
                        total_peso = df_merge["_peso"].sum()
                        total_m3 = df_merge["_vol"].sum()
                        cap_truck_peso = 12000
                        cap_carreta_peso = 28000
                        cap_truck_m3 = 36
                        cap_carreta_m3 = 76
                        eq_truck_peso = (total_peso / cap_truck_peso) * resultado_frete_completo["capacidades"]["truck"]
                        eq_carreta_peso = (total_peso / cap_carreta_peso) * resultado_frete_completo["capacidades"]["carreta"]
                        eq_truck_vol = (total_m3 / cap_truck_m3) * resultado_frete_completo["capacidades"]["truck"]
                        eq_carreta_vol = (total_m3 / cap_carreta_m3) * resultado_frete_completo["capacidades"]["carreta"]
                        volume_total = max(volume_total, eq_truck_peso, eq_carreta_peso, eq_truck_vol, eq_carreta_vol)
                except Exception as e:
                    st.info(f"Dados logísticos ignorados: {e}")
            
            # Reavalia a otimização com o volume real
            nova_otimizacao = calcular_frete_otimizado(resultado_frete_completo, volume_total)
            
            # Verificar se houve mudança na recomendação
            otimizacao_anterior = self.state.get_frete('otimizacao_frete', {})
            veiculo_anterior = otimizacao_anterior.get('veiculo_otimo', 'desconhecido')
            veiculo_novo = nova_otimizacao['veiculo_otimo']
            
            # Atualizar frete se necessário
            if veiculo_novo != veiculo_anterior and nova_otimizacao['frete_por_caixa'] > 0:
                # Atualizar frete em todos os produtos
                df_final["Frete Caixa"] = nova_otimizacao['frete_por_caixa']
                
                # Alertar sobre otimização
                if nova_otimizacao['economia'] > 0:
                    st.success(
                        f"🎯 **FRETE OTIMIZADO!**\n\n"
                        f"Volume total: {volume_total} caixas\n\n"
                        f"{nova_otimizacao['alerta']}\n\n"
                        f"Novo frete/caixa: R$ {nova_otimizacao['frete_por_caixa']:.2f}"
                    )
                else:
                    st.info(nova_otimizacao['alerta'])
            
            # Atualizar session state
            self.state.set_frete('otimizacao_frete', nova_otimizacao)
    
    def _exibir_resultados_calculados(self, df_final: pd.DataFrame):
        """Exibe resultados calculados"""
        tipo_frete = self.state.get_simulacao('tipo_frete', 'CIF')
        calculadora = CalculadoraResultados(tipo_frete)
        
        # Calcular resultados
        resultados = df_final.apply(calculadora.calcular_resultados_completos, axis=1)
        
        # Criar DataFrame para exibição
        df_display = self._criar_dataframe_display(df_final, resultados)
        
        # Exibir informações de otimização se disponível
        self._exibir_info_otimizacao(df_final)
        
        # Exibir tabela com formatação
        self.layout.exibir_tabela_resultados(df_display)
        
        # Exibir resumo executivo
        self.layout.exibir_resumo_executivo(df_display)

        # Resumo logístico se dados disponíveis
        if self.logistics_service:
            info_log = self.logistics_service.calcular_logistica(df_final)
            self.layout.exibir_resumo_logistico(info_log)

        # Exibir detalhamento do cálculo
        self.layout.exibir_detalhamento_calculo(df_final, resultados)
        
        # Seção de exportação
        self.layout.exibir_secao_exportacao(df_final, resultados, df_display)
    
    def _exibir_info_otimizacao(self, df_final: pd.DataFrame):
        """Exibe informações de otimização de frete"""
        otimizacao = self.state.get_frete('otimizacao_frete')
        if otimizacao and otimizacao['veiculo_otimo'] != 'nenhum':
            col_opt1, col_opt2, col_opt3 = st.columns(3)
            
            with col_opt1:
                volume_total = df_final["Quantidade"].sum()
                st.metric("📦 Volume Total", f"{volume_total} caixas")
            
            with col_opt2:
                st.metric("🚛 Veículo Otimizado", otimizacao['veiculo_otimo'].upper())
            
            with col_opt3:
                if otimizacao['economia'] > 0:
                    st.metric("💰 Economia", f"R$ {otimizacao['economia']:.2f}", delta=f"R$ {otimizacao['economia']:.2f}")
                else:
                    st.metric("💰 Frete Total", f"R$ {otimizacao['frete_total']:.2f}")
    
    def _criar_dataframe_display(self, df_final: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame para exibição dos resultados"""
        df_display = pd.DataFrame({
            "Produto": df_final["Descrição"].values,
            "Preço Venda": resultados["Preço Venda"].values,
            "Qtd": resultados["Qtd"].values,
            "Subtotal": resultados["Subtotal"].values,
            "IPI": resultados["IPI"].values,
            "ICMS-ST": resultados["ICMS-ST"].values,
            "FCP": resultados["FCP"].values,
            "Total NF": resultados["Total NF"].values,
            "Custo Total": resultados["Custo Total"].values,
            "Despesas": resultados["Total Despesas"].values,
            "Lucro Antes IR": resultados["Lucro Antes IR"].values,
            "IRPJ+CSLL": (resultados["IRPJ"] + resultados["CSLL"]).values,
            "Lucro Líquido": resultados["Lucro Líquido"].values,
            "Margem %": resultados["Margem Líquida %"].values,
            "Equilíbrio": resultados["Ponto Equilíbrio"].values
        })
        
        # Arredondar valores para evitar -0.00
        colunas_monetarias = ["Preço Venda", "Subtotal", "IPI", "ICMS-ST", "FCP", "Total NF", 
                             "Custo Total", "Despesas", "Lucro Antes IR", "IRPJ+CSLL", 
                             "Lucro Líquido", "Equilíbrio"]
        
        for col in colunas_monetarias:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: arredondar_valor(x, 2))
        
        # Arredondar margem
        if "Margem %" in df_display.columns:
            df_display["Margem %"] = df_display["Margem %"].apply(lambda x: arredondar_valor(x, 1))
        
        return df_display
    
    def calcular_frete_automatico(self, origem: str, dados_cliente: dict, tipo_veiculo: str = "truck"):
        """Calcula frete automaticamente baseado na distância real e tabela TRANSP_TARGET"""
        if not self.geo_service:
            st.error("❌ Serviço de geolocalização não disponível.")
            return
        
        with st.spinner("🔍 Calculando frete automático..."):
            # Montar endereço de destino
            endereco_destino_completo = montar_endereco_geocode(dados_cliente)
            st.info(f"🔍 Geocodificando endereço: {endereco_destino_completo}")
            
            # Calcular rota completa
            resultado_rota = self.geo_service.calcular_rota_completa(origem, endereco_destino_completo)
            
            if not resultado_rota['sucesso']:
                # Tentar fallback com coordenadas do banco
                try:
                    lat_banco = float(dados_cliente.get("latitude", 0))
                    lng_banco = float(dados_cliente.get("longitude", 0))
                    if lat_banco != 0 and lng_banco != 0:
                        origem_coords = self.geo_service.geocode(origem)
                        if origem_coords:
                            distancia, duracao, erro = self.geo_service.calcular_distancia(
                                origem_coords, (lat_banco, lng_banco)
                            )
                            if not erro:
                                distancia_km = self.geo_service._extrair_km_da_string(distancia)
                                resultado_rota = {
                                    'sucesso': True,
                                    'origem_coords': origem_coords,
                                    'destino_coords': (lat_banco, lng_banco),
                                    'distancia': distancia,
                                    'duracao': duracao,
                                    'distancia_km': distancia_km
                                }
                                st.warning("⚠️ Usando coordenadas do banco como fallback.")
                            else:
                                st.error(resultado_rota['erro'])
                                return
                        else:
                            st.error(resultado_rota['erro'])
                            return
                    else:
                        st.error(resultado_rota['erro'])
                        return
                except (ValueError, TypeError, KeyError):
                    st.error(resultado_rota['erro'])
                    return
            
            # Armazenar resultados no estado
            self.state.update('frete', {
                'distancia_calculada': resultado_rota['distancia'],
                'tempo_calculado': resultado_rota['duracao'],
                'coordenadas_origem': resultado_rota['origem_coords'],
                'coordenadas_destino': resultado_rota['destino_coords']
            })
            
            # Processar frete
            self._processar_calculo_frete(resultado_rota, dados_cliente, tipo_veiculo)
    
    def _processar_calculo_frete(self, resultado_rota: dict, dados_cliente: dict, tipo_veiculo: str):
        """Processa o cálculo de frete"""
        distancia_km = resultado_rota['distancia_km']
        
        # Obter a faixa de KM com base na distância
        faixa_km = obter_faixa_km_exata(distancia_km, self.faixas_km_ordenadas)
        
        # Obter código IBGE do cliente
        cidade_ibge = str(dados_cliente["cidade_ibge"])
        
        # Buscar ambos os valores (truck e carreta) para otimização
        resultado_frete = buscar_frete_inteligente(self.clientes_df, cidade_ibge, faixa_km)
        
        # Calcular volume total estimado
        volume_estimado = 500  # Volume padrão para cálculo inicial
        
        # Calcular frete otimizado
        otimizacao = calcular_frete_otimizado(resultado_frete, volume_estimado)
        
        # Armazenar no estado
        self.state.update('frete', {
            'frete_calculado_automatico': otimizacao['frete_por_caixa'],
            'tipo_veiculo_usado': otimizacao['veiculo_otimo'],
            'resultado_frete_completo': resultado_frete,
            'otimizacao_frete': otimizacao
        })
        
        # Exibir resultados
        self._exibir_resultados_calculo_frete(resultado_rota, otimizacao, resultado_frete, cidade_ibge, faixa_km)
    
    def _exibir_resultados_calculo_frete(self, resultado_rota: dict, otimizacao: dict, 
                                       resultado_frete: dict, cidade_ibge: str, faixa_km: str):
        """Exibe resultados do cálculo de frete"""
        distancia = resultado_rota['distancia']
        duracao = resultado_rota['duracao']
        distancia_km = resultado_rota['distancia_km']
        
        if otimizacao['frete_por_caixa'] > 0:
            # Mensagem principal
            st.success(
                f"✅ Rota calculada com sucesso!\n\n"
                f"📏 Distância: {distancia} ({duracao}) → **{distancia_km:.0f} km**\n\n"
                f"📍 IBGE: {cidade_ibge}\n\n"
                f"🎯 Faixa: **{faixa_km}**\n\n"
                f"💰 Frete/Caixa: R$ {otimizacao['frete_por_caixa']:.2f}\n\n"
                f"🚛 Veículo Otimizado: {otimizacao['veiculo_otimo'].upper()}"
            )
            
            # Alerta de otimização
            if otimizacao['alerta']:
                if 'OTIMIZAÇÃO' in otimizacao['alerta']:
                    st.success(otimizacao['alerta'])
                elif 'MÚLTIPLOS' in otimizacao['alerta']:
                    st.warning(otimizacao['alerta'])
                else:
                    st.info(otimizacao['alerta'])
            
            # Tabela de comparação
            self._exibir_tabela_comparacao_fretes(resultado_frete)
            
            st.info("💡 **Otimização Automática:** O frete será reavaliado automaticamente quando você definir as quantidades dos produtos!")
        
        else:
            st.warning(
                f"⚠️ Rota calculada, mas frete não encontrado!\n\n"
                f"📏 Distância: {distancia} ({duracao}) → **{distancia_km:.0f} km**\n\n"
                f"📍 IBGE: {cidade_ibge}\n\n"
                f"🎯 Faixa de KM: **{faixa_km}**\n\n"
                f"💡 Sugestão: Use frete manual ou verifique tabela de fretes"
            )
    
    def _exibir_tabela_comparacao_fretes(self, resultado_frete: dict):
        """Exibe tabela de comparação de fretes"""
        st.markdown("#### 📊 Comparação de Fretes Encontrados")
        
        truck_info = resultado_frete['truck']
        carreta_info = resultado_frete['carreta']
        
        comparacao_data = []
        if truck_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚚 Truck',
                'Frete Total': f"R$ {truck_info['valor']:,.2f}",
                'Capacidade': '870 caixas',
                'Frete/Caixa': f"R$ {truck_info['valor']/870:.2f}",
                'Método': truck_info['metodo']
            })
        
        if carreta_info['valor'] > 0:
            comparacao_data.append({
                'Veículo': '🚛 Carreta',
                'Frete Total': f"R$ {carreta_info['valor']:,.2f}",
                'Capacidade': '1.740 caixas',
                'Frete/Caixa': f"R$ {carreta_info['valor']/1740:.2f}",
                'Método': carreta_info['metodo']
            })
        
        if comparacao_data:
            df_comparacao = pd.DataFrame(comparacao_data)
            st.dataframe(df_comparacao, use_container_width=True, hide_index=True)