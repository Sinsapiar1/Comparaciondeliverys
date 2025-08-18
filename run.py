# -*- coding: utf-8 -*-
# run.py - Lanzador mejorado para el ejecutable

import sys
import os

# CRÍTICO: Configurar el entorno antes de importar Streamlit
def setup_environment():
    # Configuración para el ejecutable
    if hasattr(sys, '_MEIPASS'):
        # Estamos ejecutando desde un bundle de PyInstaller
        bundle_dir = sys._MEIPASS
        
        # Añadir el directorio temporal al path para encontrar metadatos
        sys.path.insert(0, bundle_dir)
        
        # Configurar variables de entorno para Streamlit
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        
    else:
        # Estamos ejecutando en modo normal
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    
    return bundle_dir

def main():
    try:
        # Configurar el entorno primero
        bundle_dir = setup_environment()
        
        # Ahora importar Streamlit
        import streamlit.web.cli as stcli
        
        # Determinar la ruta de la aplicación
        if hasattr(sys, '_MEIPASS'):
            app_path = os.path.join(bundle_dir, 'app_conciliador.py')
        else:
            app_path = os.path.join(bundle_dir, 'app_conciliador.py')
        
        # Verificar que el archivo existe
        if not os.path.exists(app_path):
            print(f"ERROR: No se puede encontrar {app_path}")
            input("Presiona Enter para salir...")
            return
        
        # Configurar argumentos para Streamlit
        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--global.developmentMode=false",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.runOnSave=false",
            "--logger.level=error",
            "--server.port=8501"
        ]
        
        # Ejecutar Streamlit
        print("Iniciando Conciliador de Cargas...")
        stcli.main()
        
    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Faltan dependencias críticas.")
        input("Presiona Enter para salir...")
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        print("Detalles del error:")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()