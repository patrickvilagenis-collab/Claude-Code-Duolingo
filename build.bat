@echo off
REM ============================================================
REM  Construye el .exe portable de Asistente Pro (Windows)
REM  Resultado:  dist\AsistentePro.exe  (un solo archivo)
REM ============================================================

echo [1/4] Creando entorno virtual...
python -m venv .venv
if errorlevel 1 goto :error

echo [2/4] Activando e instalando dependencias...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 goto :error

echo [3/4] Empaquetando con PyInstaller...
pyinstaller --noconfirm --clean --onefile --windowed --name AsistentePro ^
  --collect-all customtkinter ^
  --collect-all anthropic ^
  --collect-submodules msal ^
  run.py
if errorlevel 1 goto :error

echo [4/4] Listo.
echo.
echo  Ejecutable portable:  dist\AsistentePro.exe
echo  Copia ese archivo a cualquier PC con Windows y ejecutalo.
echo.
goto :eof

:error
echo.
echo  ERROR durante la construccion. Revisa los mensajes anteriores.
exit /b 1
