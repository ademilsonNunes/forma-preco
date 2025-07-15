"""
Debug e Correção de Imports
===========================
Script para identificar e corrigir problemas de importação.
"""

import sys
import os
from pathlib import Path

def debug_imports():
    """Debug sistemático dos imports"""
    print("🔍 DIAGNÓSTICO DE IMPORTS")
    print("=" * 50)
    
    # 1. Verificar estrutura de arquivos
    print("\n📁 Verificando estrutura de arquivos:")
    
    required_files = [
        "services/__init__.py",
        "services/database_service.py", 
        "services/geolocation_service.py",
        "services/calculation_service.py",
        "utils/__init__.py",
        "utils/frete_utils.py",
        "utils/data_utils.py", 
        "utils/format_utils.py",
        "config/__init__.py",
        "config/tributaria.py",
        "core/__init__.py",
        "core/state_manager.py",
        "core/simulador.py",
        "ui/__init__.py",
        "ui/components.py",
        "ui/layout.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - ARQUIVO FALTANDO")
    
    # 2. Testar imports individuais
    print("\n🧪 Testando imports individuais:")
    
    # Test config
    try:
        from config.tributaria import ConfiguracaoTributaria
        print("✅ config.tributaria.ConfiguracaoTributaria")
    except Exception as e:
        print(f"❌ config.tributaria.ConfiguracaoTributaria: {e}")
    
    # Test utils
    try:
        from utils.data_utils import arredondar_valor
        print("✅ utils.data_utils.arredondar_valor")
    except Exception as e:
        print(f"❌ utils.data_utils.arredondar_valor: {e}")
    
    try:
        from utils.frete_utils import extrair_distancia_da_faixa
        print("✅ utils.frete_utils.extrair_distancia_da_faixa")
    except Exception as e:
        print(f"❌ utils.frete_utils.extrair_distancia_da_faixa: {e}")
    
    try:
        from utils.format_utils import formatar_moeda
        print("✅ utils.format_utils.formatar_moeda")
    except Exception as e:
        print(f"❌ utils.format_utils.formatar_moeda: {e}")
    
    # Test services (aqui está o problema)
    try:
        from services.database_service import DatabaseService
        print("✅ services.database_service.DatabaseService")
    except Exception as e:
        print(f"❌ services.database_service.DatabaseService: {e}")
        
    try:
        from services.calculation_service import CalculadoraTributaria
        print("✅ services.calculation_service.CalculadoraTributaria")
    except Exception as e:
        print(f"❌ services.calculation_service.CalculadoraTributaria: {e}")
    
    try:
        from services.geolocation_service import GeolocationService
        print("✅ services.geolocation_service.GeolocationService")
    except Exception as e:
        print(f"❌ services.geolocation_service.GeolocationService: {e}")
    
    # Test core
    try:
        from core.state_manager import StateManager
        print("✅ core.state_manager.StateManager")
    except Exception as e:
        print(f"❌ core.state_manager.StateManager: {e}")
    
    # Test ui
    try:
        from ui.components import ClienteInfoComponent
        print("✅ ui.components.ClienteInfoComponent")
    except Exception as e:
        print(f"❌ ui.components.ClienteInfoComponent: {e}")

if __name__ == "__main__":
    debug_imports()