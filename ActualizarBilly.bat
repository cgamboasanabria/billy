@echo off
rem Billy - actualizador de contenido con doble clic.
rem Baja los cambios del repo (git pull), sincroniza dependencias y relanza la app.

cd /d "%~dp0"

echo Actualizando el material de estudio...
git pull
if errorlevel 1 (
  echo No se pudo actualizar. Revisa la conexion a internet e intentalo de nuevo.
  pause
  exit /b 1
)

echo Sincronizando el entorno...
call uv sync

echo Abriendo la app...
.venv\Scripts\python.exe -m streamlit run src/app.py

pause
