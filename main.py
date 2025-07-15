"""
Simulador de Preço de Venda Sobel - Versão Refatorada
====================================================

Ponto de entrada principal da aplicação refatorada.

Autor: Sistema Refatorado
Versão: 3.0 - Modular
Data: 2025

Melhorias desta versão:
- 🔧 Arquitetura modular por domínios
- 🧠 Estado encapsulado por namespaces  
- 📁 Separação clara de responsabilidades
- 🚀 Maior manutenibilidade e testabilidade
"""

# Configuração da página - DEVE SER A PRIMEIRA COISA!
import streamlit as st

# Configurar página ANTES de qualquer outro comando Streamlit
st.set_page_config(
    page_title="Simulador de Preço de Venda Sobel - Refatorado", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import sys
from pathlib import Path

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("⚠️ python-dotenv não encontrado, variáveis de ambiente podem não carregar")

# Adicionar diretório raiz ao PYTHONPATH para imports
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))


def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    dependencias_verificacao = [
        # (nome_pip, nome_import, obrigatorio)
        ('pandas', 'pandas', True),
        ('streamlit', 'streamlit', True), 
        ('pyodbc', 'pyodbc', True),
        ('requests', 'requests', True),
        ('python-dotenv', 'dotenv', True),
        ('xlsxwriter', 'xlsxwriter', False),
        ('openpyxl', 'openpyxl', False)
    ]
    
    problemas_obrigatorios = []
    problemas_opcionais = []
    
    for nome_pip, nome_import, obrigatorio in dependencias_verificacao:
        try:
            __import__(nome_import)
        except ImportError:
            if obrigatorio:
                problemas_obrigatorios.append(f"❌ **{nome_pip}** (obrigatório)")
            else:
                problemas_opcionais.append(f"⚠️ **{nome_pip}** (opcional - funcionalidade limitada)")
    
    if problemas_obrigatorios or problemas_opcionais:
        todos_problemas = problemas_obrigatorios + problemas_opcionais
        
        st.error(f"""
        **Dependências em falta:**
        
        {chr(10).join(todos_problemas)}
        
        **Para instalar todas:**
        ```bash
        pip install pandas streamlit pyodbc requests python-dotenv xlsxwriter openpyxl
        ```
        
        **Para instalar apenas obrigatórias:**
        ```bash
        pip install pandas streamlit pyodbc requests python-dotenv
        ```
        """)
        return len(problemas_obrigatorios) == 0  # Retorna True se só há opcionais
    
    return True


def verificar_configuracao():
    """Verifica configurações essenciais"""
    problemas = []
    
    # Verificar arquivo de custos
    if not os.path.exists("Custo de reposição.xlsx"):
        problemas.append("⚠️ Arquivo 'Custo de reposição.xlsx' não encontrado (upload será necessário)")
    
    # Verificar API key do Google Maps
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        problemas.append("⚠️ GOOGLE_MAPS_API_KEY não configurada (funcionalidades de geolocalização desabilitadas)")
    
    # Verificar logo
    if not os.path.exists("Logo-Suprema-Slogan-Alta-ai-1.webp"):
        problemas.append("ℹ️ Logo da empresa não encontrada (layout simplificado)")
    
    if problemas:
        with st.expander("⚙️ Avisos de Configuração", expanded=False):
            for problema in problemas:
                if problema.startswith("❌"):
                    st.error(problema)
                elif problema.startswith("⚠️"):
                    st.warning(problema)
                else:
                    st.info(problema)
    
    return True


def importar_aplicacao():
    """Importa a aplicação principal com tratamento de erros"""
    try:
        from core.simulador import SimuladorSobel
        return SimuladorSobel
    except ImportError as e:
        st.error(f"""
        ❌ **Erro de Importação:** {e}
        
        **Possíveis soluções:**
        1. Verifique se todos os arquivos estão na estrutura correta
        2. Certifique-se que os arquivos `__init__.py` existem em cada pasta
        3. Execute a partir do diretório raiz do projeto
        4. Teste os imports individualmente
        
        **Para diagnóstico detalhado:**
        ```bash
        streamlit run main_debug.py
        ```
        
        **Estrutura esperada:**
        ```
        simulador_sobel/
        ├── main.py                    (este arquivo)
        ├── config/
        │   ├── __init__.py
        │   └── tributaria.py
        ├── services/
        │   ├── __init__.py
        │   ├── database_service.py
        │   ├── geolocation_service.py
        │   └── calculation_service.py
        ├── utils/
        │   ├── __init__.py
        │   ├── frete_utils.py
        │   ├── data_utils.py
        │   └── format_utils.py
        ├── core/
        │   ├── __init__.py
        │   ├── state_manager.py
        │   └── simulador.py
        └── ui/
            ├── __init__.py
            ├── components.py
            └── layout.py
        ```
        """)
        return None


def main():
    """Função principal da aplicação"""
    # Cabeçalho da aplicação
    st.markdown("""
    <div style="text-align: center; padding: 1rem; margin-bottom: 2rem; 
                background: linear-gradient(90deg, #1f4e79 0%, #2e86de 100%); 
                border-radius: 10px; color: white;">
        <h1>🏭 Simulador Sobel Suprema v3.0</h1>
        <p style="margin: 0; opacity: 0.9;">
            <strong>Versão Refatorada</strong> • Arquitetura Modular • 
            Estado Encapsulado • Responsabilidades Separadas
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificações iniciais
    if not verificar_dependencias():
        st.stop()
    
    if not verificar_configuracao():
        st.stop()
    
    # Importar aplicação
    SimuladorSobel = importar_aplicacao()
    if not SimuladorSobel:
        st.stop()
    
    # Executar aplicação principal
    try:
        simulador = SimuladorSobel()
        simulador.executar()
        
        # Exibir notas técnicas no final
        simulador.layout.exibir_notas_tecnicas()
        
    except Exception as e:
        st.error(f"""
        ❌ **Erro crítico na aplicação:** {str(e)}
        
        **Informações para debug:**
        - Tipo do erro: {type(e).__name__}
        - Arquivo: {__file__}
        
        **Ações sugeridas:**
        1. Recarregue a página (Ctrl+F5)
        2. Verifique se todos os arquivos estão presentes
        3. Verifique as configurações de banco de dados
        4. Verifique as variáveis de ambiente (.env)
        5. Execute o diagnóstico: `streamlit run main_debug.py`
        
        Se o erro persistir, contate o suporte técnico.
        """)
        
        # Debug information (apenas em desenvolvimento)
        if st.checkbox("🔧 Mostrar informações de debug", key="debug_checkbox"):
            st.exception(e)


def exibir_info_sistema():
    """Exibe informações do sistema na sidebar"""
    with st.sidebar:
        st.markdown("### 🛠️ Informações do Sistema")
        
        st.markdown(f"""
        **Versão:** 3.0 Refatorada  
        **Python:** {sys.version.split()[0]}  
        **Streamlit:** {st.__version__}
        
        **🏗️ Arquitetura:**
        - ✅ Modular por domínios
        - ✅ Estado encapsulado
        - ✅ Responsabilidades separadas
        - ✅ Serviços especializados
        
        **📁 Estrutura:**
        - `config/` - Configurações
        - `services/` - Serviços de negócio
        - `utils/` - Utilitários
        - `core/` - Lógica principal
        - `ui/` - Interface do usuário
        """)
        
        # Verificar dependências para sidebar
        st.markdown("### 📦 Status das Dependências")
        
        dependencias_sidebar = [
            ('pandas', 'pandas'),
            ('streamlit', 'streamlit'),
            ('pyodbc', 'pyodbc'),
            ('requests', 'requests'),
            ('python-dotenv', 'dotenv'),
            ('xlsxwriter', 'xlsxwriter')
        ]
        
        for nome_pip, nome_import in dependencias_sidebar:
            try:
                __import__(nome_import)
                st.success(f"✅ {nome_pip}")
            except ImportError:
                st.error(f"❌ {nome_pip}")
        
        # Informações de configuração
        st.markdown("### ⚙️ Status dos Serviços")
        
        # Google Maps API
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key:
            st.success("🗺️ Google Maps: Ativo")
        else:
            st.warning("🗺️ Google Maps: Inativo")
        
        # Arquivo de custos
        if os.path.exists("Custo de reposição.xlsx"):
            st.success("📊 Planilha Base: Carregada")
        else:
            st.warning("📊 Planilha Base: Não encontrada")
        
        # Informações de debug
        with st.expander("🔧 Debug Info"):
            st.text(f"PYTHONPATH: {len(sys.path)} entradas")
            st.text(f"Diretório atual: {os.getcwd()}")
            st.text(f"Arquivo principal: {__file__}")


if __name__ == "__main__":
    # Executar aplicação
    main()
    
    # Exibir informações do sistema na sidebar
    exibir_info_sistema()