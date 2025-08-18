@echo off
echo ==========================================
echo   CONSTRUCCION DEL CONCILIADOR DE CARGAS
echo ==========================================
echo.

:: Limpiar builds anteriores
echo Limpiando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
echo.

:: Verificar que existen todos los archivos necesarios
echo Verificando archivos necesarios...
if not exist "run.py" (
    echo ERROR: No se encuentra run.py
    pause
    exit /b 1
)
if not exist "app_conciliador.py" (
    echo ERROR: No se encuentra app_conciliador.py
    pause
    exit /b 1
)
if not exist "hooks\hook-streamlit.py" (
    echo ERROR: No se encuentra hooks\hook-streamlit.py
    pause
    exit /b 1
)
if not exist "ConciliadorDeCargas.spec" (
    echo ERROR: No se encuentra ConciliadorDeCargas.spec
    pause
    exit /b 1
)
echo Todos los archivos necesarios encontrados.
echo.

:: Construir el ejecutable
echo Construyendo el ejecutable...
pyinstaller ConciliadorDeCargas.spec

:: Verificar que la construcción fue exitosa
if exist "dist\ConciliadorDeCargas.exe" (
    echo.
    echo ==========================================
    echo   CONSTRUCCION COMPLETADA EXITOSAMENTE
    echo ==========================================
    echo.
    echo El ejecutable se encuentra en: dist\ConciliadorDeCargas.exe
    echo.
) else (
    echo.
    echo ==========================================
    echo        ERROR EN LA CONSTRUCCION
    echo ==========================================
    echo.
    echo Revisa los mensajes de error arriba.
)

pause