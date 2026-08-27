@echo off
rem Billy - instalador de una sola vez en la maquina de Billy.
rem Instala git y uv (si faltan), prepara el entorno, guarda la API key y crea un acceso directo.

cd /d "%~dp0"

rem 1. Instalar git si no esta disponible
where git >nul 2>nul
if errorlevel 1 (
  echo Instalando git...
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
)

rem 2. Instalar uv si no esta disponible
where uv >nul 2>nul
if errorlevel 1 (
  echo Instalando uv...
  powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

rem 3. Preparar entorno (Python + dependencias)
echo Preparando el entorno...
call uv sync

rem 4. Guardar la API key del tutor (pregunta enmascarada; Enter en blanco para saltar)
echo.
.venv\Scripts\python.exe Script\guardar_key.py

rem 5. Crear acceso directo en el escritorio
powershell -ExecutionPolicy Bypass -File "%~dp0crear_acceso_directo.ps1"

echo.
echo Listo. Billy puede abrir la app desde el acceso directo "Billy" del escritorio.
echo Para actualizar el contenido mas adelante, usa ActualizarBilly.bat.
pause
