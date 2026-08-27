@echo off
rem Billy Web App - lanzador con doble clic
rem Activa el entorno virtual y abre la app en el navegador.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Preparando el entorno por primera vez...
  uv sync
)

.venv\Scripts\python.exe -m streamlit run src/app.py

pause
