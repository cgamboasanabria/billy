# Crea un acceso directo a Billy en el escritorio del usuario.
# Uso: powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $scriptDir "LanzarBilly.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Billy.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $launcher
$sc.WorkingDirectory = $scriptDir
$sc.Description = "Billy - Aventura de Estudio"
$sc.Save()

Write-Output "Acceso directo creado en: $shortcutPath"
