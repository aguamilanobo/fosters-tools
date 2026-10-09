@echo off
setlocal
title Fosters Printer - Auto Update
cd /d "%~dp0"
echo.
echo ========================================
echo   FOSTERS PRINTER - AUTO UPDATE
echo ========================================
echo.
where git >nul 2>nul
if errorlevel 1 (
  echo [AVISO] Git no esta instalado. Se usara la version local.
  goto EXTRACT
)
if exist ".git" (
  echo Buscando actualizaciones...
  git pull --ff-only origin printer
  if errorlevel 1 echo [AVISO] GitHub no respondio o hay un conflicto. Seguimos con la version local.
)
:EXTRACT
if not exist "FostersPrinter-latest.zip" (
  echo ERROR: falta FostersPrinter-latest.zip
  pause
  exit /b 1
)
if exist "runtime_new" rmdir /s /q "runtime_new"
mkdir "runtime_new"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%CD%\FostersPrinter-latest.zip' -DestinationPath '%CD%\runtime_new' -Force"
if errorlevel 1 (
  echo ERROR: no se pudo preparar la version.
  pause
  exit /b 1
)
if exist "runtime" rmdir /s /q "runtime"
move "runtime_new" "runtime" >nul
if exist VERSION (set /p FP_VERSION=<VERSION) else set "FP_VERSION=desconocida"
echo [OK] Iniciando Fosters Printer v%FP_VERSION%
call "runtime\INICIAR.cmd"
