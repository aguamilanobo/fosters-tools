@echo off
setlocal EnableExtensions
title Fosters Printer - Auto Update
cd /d "%~dp0"

echo.
echo ========================================
echo   FOSTERS PRINTER - AUTO UPDATE
echo ========================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [AVISO] Git no esta instalado. Se intentara abrir la version local.
  goto START_LOCAL
)

if exist ".git" (
  echo Buscando actualizaciones...
  git pull --ff-only origin printer
  if errorlevel 1 (
    echo [AVISO] No se pudo actualizar desde GitHub.
    echo Se intentara abrir la ultima version local funcional.
    goto START_LOCAL
  )
)

echo Preparando paquete verificado...
if not exist "package\chunk01.b64" goto PACKAGE_ERROR
if not exist "package\chunk02.b64" goto PACKAGE_ERROR
if not exist "package\chunk03.b64" goto PACKAGE_ERROR
if not exist "package\chunk04.b64" goto PACKAGE_ERROR
if not exist "package\chunk05.b64" goto PACKAGE_ERROR
if not exist "package\chunk06.b64" goto PACKAGE_ERROR
if not exist "package\chunk07.b64" goto PACKAGE_ERROR
if not exist "package\chunk08.b64" goto PACKAGE_ERROR

copy /b "package\chunk01.b64"+"package\chunk02.b64"+"package\chunk03.b64"+"package\chunk04.b64"+"package\chunk05.b64"+"package\chunk06.b64"+"package\chunk07.b64"+"package\chunk08.b64" "package\release.b64" >nul
if errorlevel 1 goto PACKAGE_ERROR

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $b64=[IO.File]::ReadAllText('%CD%\package\release.b64').Trim(); [IO.File]::WriteAllBytes('%CD%\package\release.zip',[Convert]::FromBase64String($b64)); $h=(Get-FileHash '%CD%\package\release.zip' -Algorithm SHA256).Hash.ToLower(); if($h -ne '2f7f3414036f728f22631a69171ba57771ea3b6210609a2b77c96bbf0833f279'){ throw ('Hash invalido: '+$h) }; Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('%CD%\package\release.zip'); $z.Dispose()"
if errorlevel 1 goto PACKAGE_ERROR

if exist "runtime_new" rmdir /s /q "runtime_new"
mkdir "runtime_new"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Expand-Archive -LiteralPath '%CD%\package\release.zip' -DestinationPath '%CD%\runtime_new' -Force"
if errorlevel 1 goto PACKAGE_ERROR

set "SOURCE="
if exist "runtime_new\INICIAR.cmd" set "SOURCE=runtime_new"
if exist "runtime_new\FostersPrinterV33\INICIAR.cmd" set "SOURCE=runtime_new\FostersPrinterV33"
if not defined SOURCE (
  for /d %%D in ("runtime_new\*") do (
    if exist "%%~fD\INICIAR.cmd" set "SOURCE=%%~fD"
  )
)
if not defined SOURCE goto PACKAGE_ERROR

if exist "runtime_backup" rmdir /s /q "runtime_backup"
if exist "runtime" move "runtime" "runtime_backup" >nul

mkdir "runtime"
xcopy "%SOURCE%\*" "runtime\" /E /I /Y >nul
if errorlevel 1 (
  if exist "runtime" rmdir /s /q "runtime"
  if exist "runtime_backup" move "runtime_backup" "runtime" >nul
  goto PACKAGE_ERROR
)

if exist "runtime_backup" rmdir /s /q "runtime_backup"
if exist "runtime_new" rmdir /s /q "runtime_new"
if exist "package\release.b64" del /q "package\release.b64"
if exist "package\release.zip" del /q "package\release.zip"

:START_LOCAL
if not exist "runtime\INICIAR.cmd" (
  echo.
  echo [ERROR] No hay una version local funcional instalada.
  echo Ejecuta nuevamente ABRIR.cmd con internet para repararla.
  pause
  exit /b 1
)

if exist VERSION (
  set /p FP_VERSION=<VERSION
) else (
  set "FP_VERSION=3.3.0"
)

echo [OK] Iniciando Fosters Printer v%FP_VERSION%
call "runtime\INICIAR.cmd"
exit /b 0

:PACKAGE_ERROR
echo.
echo [ERROR] No se pudo verificar o instalar la actualizacion.
echo La version anterior NO fue borrada.
if exist "runtime_new" rmdir /s /q "runtime_new"
if exist "package\release.b64" del /q "package\release.b64"
if exist "package\release.zip" del /q "package\release.zip"
goto START_LOCAL
