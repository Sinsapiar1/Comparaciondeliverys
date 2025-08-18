# -*- mode: python ; coding: utf-8 -*-
import os
import streamlit
from PyInstaller.utils.hooks import copy_metadata

# Obtener la ruta de instalación de Streamlit
streamlit_path = os.path.dirname(streamlit.__file__)

block_cipher = None

# Recopilar metadatos de paquetes críticos de manera segura
metadata_datas = []
critical_packages = [
    'streamlit', 'altair', 'plotly', 'pandas', 'numpy', 'click', 
    'typing_extensions', 'pyarrow', 'tornado', 'blinker'
]

for package in critical_packages:
    try:
        metadata_datas += copy_metadata(package)
    except Exception:
        # Si no se puede copiar metadatos de este paquete, continuar
        pass

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Incluir todos los archivos estáticos de Streamlit
        (os.path.join(streamlit_path, 'static'), 'streamlit/static'),
        (os.path.join(streamlit_path, 'runtime'), 'streamlit/runtime'),
        (os.path.join(streamlit_path, 'web'), 'streamlit/web'),
        (os.path.join(streamlit_path, 'components'), 'streamlit/components'),
        # Incluir el archivo principal de la aplicación
        ('app_conciliador.py', '.'),
    ] + metadata_datas,  # Añadir los metadatos recopilados
    hiddenimports=[
        # Streamlit core
        'streamlit',
        'streamlit.web.cli',
        'streamlit.web.server',
        'streamlit.web.bootstrap',
        'streamlit.runtime',
        'streamlit.runtime.app_session',
        'streamlit.runtime.runtime',
        'streamlit.runtime.state',
        'streamlit.components.v1',
        'streamlit.components.v1.components',
        'streamlit.version',
        
        # Data processing
        'pandas',
        'numpy',
        'xlsxwriter',
        'openpyxl',
        
        # Visualization
        'altair',
        'plotly',
        'plotly.graph_objects',
        'plotly.express',
        'plotly.io',
        
        # Web framework
        'tornado',
        'tornado.web',
        'tornado.websocket',
        'tornado.ioloop',
        'tornado.httpserver',
        
        # Utilities
        'click',
        'typing_extensions',
        'pyarrow',
        'PIL',
        'PIL.Image',
        'requests',
        'blinker',
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        'pytz',
        'dateutil',
        'dateutil.parser',
        'packaging',
        'packaging.version',
        'cachetools',
        'jsonschema',
        'rich',
        'toml',
        'protobuf',
        'tenacity',
        
        # Metadatos críticos
        'importlib.metadata',
        'importlib_metadata',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ConciliadorDeCargas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Cambiar a False para ocultar la consola en producción
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Puedes añadir un icono aquí: icon='path/to/icon.ico'
)