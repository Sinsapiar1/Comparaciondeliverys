# hook-streamlit.py - VERSIÓN SEGURA
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

# Recopilar todos los archivos de datos de Streamlit
datas = collect_data_files('streamlit')

# Lista de paquetes para intentar copiar metadatos
packages_to_try = [
    'streamlit', 'altair', 'plotly', 'pandas', 'numpy', 'click', 
    'typing_extensions', 'validators', 'pillow', 'requests', 
    'blinker', 'markdown', 'pyarrow', 'tornado', 'watchdog', 'protobuf'
]

# Copiar metadatos de manera segura
for package in packages_to_try:
    try:
        datas += copy_metadata(package)
    except Exception:
        # Si no se puede copiar metadatos de este paquete, continuar con el siguiente
        pass

# Recopilar todos los submódulos de Streamlit
hiddenimports = collect_submodules('streamlit')

# Añadir imports adicionales específicos que PyInstaller podría perderse
hiddenimports += [
    'streamlit.web.cli',
    'streamlit.web.server',
    'streamlit.web.bootstrap',
    'streamlit.runtime',
    'streamlit.runtime.app_session',
    'streamlit.runtime.runtime',
    'streamlit.components.v1',
    'streamlit.components.v1.components',
    'streamlit.version',
    'altair',
    'plotly',
    'plotly.graph_objects',
    'plotly.express',
    'plotly.io',
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    'tornado',
    'tornado.web',
    'tornado.websocket',
    'tornado.ioloop',
    'tornado.httpserver',
    'click',
    'typing_extensions',
    'pyarrow',
    'PIL',
    'PIL.Image',
    'requests',
    'blinker',
    'importlib.metadata',
    'importlib_metadata'
]