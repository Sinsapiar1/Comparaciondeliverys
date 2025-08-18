@echo off
echo ========================================
echo   RECONSTRUCCION DEL CONCILIADOR
echo ========================================
echo.

:: Limpiar COMPLETAMENTE builds anteriores
echo Limpiando builds anteriores...
if exist "build" (
    echo Eliminando carpeta build...
    rmdir /s /q "build"
)
if exist "dist" (
    echo Eliminando carpeta dist...
    rmdir /s /q "dist"
)
if exist "__pycache__" (
    echo Eliminando carpeta __pycache__...
    rmdir /s /q "__pycache__"
)
if exist "*.pyc" (
    echo Eliminando archivos .pyc...
    del /q *.pyc
)

:: Limpiar cache de PyInstaller
if exist "%APPDATA%\pyinstaller" (
    echo Limpiando cache de PyInstaller...
    rmdir /s /q "%APPDATA%\pyinstaller"
)

echo.
echo Limpieza completada.
echo.

:: Verificar archivos necesarios
echo Verificando archivos necesarios...
set MISSING_FILES=0

if not exist "run.py" (
    echo ERROR: Falta run.py
    set MISSING_FILES=1
)
if not exist "app_conciliador.py" (
    echo ERROR: Falta app_conciliador.py
    set MISSING_FILES=1
)
if not exist "hooks\hook-streamlit.py" (
    echo ERROR: Falta hooks\hook-streamlit.py
    set MISSING_FILES=1
)
if not exist "ConciliadorDeCargas.spec" (
    echo ERROR: Falta ConciliadorDeCargas.spec
    set MISSING_FILES=1
)

if %MISSING_FILES%==1 (
    echo.
    echo FALTAN ARCHIVOS CRÍTICOS. REVISA LA ESTRUCTURA.
    pause
    exit /b 1
)

echo Todos los archivos encontrados.
echo.

:: Verificar dependencias
echo Verificando dependencias de Python...
python -c "import streamlit; print('Streamlit OK')" 2>nul
if errorlevel 1 (
    echo ERROR: Streamlit no está instalado
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Dependencias OK.
echo.

:: Construir el ejecutable
echo ========================================
echo   CONSTRUYENDO EJECUTABLE...
echo ========================================
echo.

pyinstaller --clean ConciliadorDeCargas.spec

:: Verificar resultado
if exist "dist\ConciliadorDeCargas.exe" (
    echo.
    echo ========================================
    echo   CONSTRUCCION EXITOSA!
    echo ========================================
    echo.
    echo El ejecutable está en: dist\ConciliadorDeCargas.exe
    echo Tamaño: 
    dir "dist\ConciliadorDeCargas.exe" | find "ConciliadorDeCargas.exe"
    echo.
    echo ¿Quieres probarlo ahora? (s/n)
    set /p TEST_NOW=
    if /i "%TEST_NOW%"=="s" (
        echo.
        echo Ejecutando prueba...
        cd dist
        start ConciliadorDeCargas.exe
        cd ..
    )
) else (
    echo.
    echo ========================================
    echo   ERROR EN LA CONSTRUCCION
    echo ========================================
    echo.
    echo El ejecutable no se creó. Revisa los errores arriba.
)

echo.
pause