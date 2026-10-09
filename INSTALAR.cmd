@echo off
setlocal
title Instalar Fosters Printer
set "DEST=%USERPROFILE%\FostersPrinter"
set "REPO=https://github.com/aguamilanobo/fosters-tools.git"
echo.
echo ========================================
echo   INSTALAR FOSTERS PRINTER V3.3
echo ========================================
echo.
where git >nul 2>nul
if errorlevel 1 (
  echo ERROR: Git for Windows no esta instalado.
  echo Instala Git y vuelve a ejecutar este archivo.
  echo https://git-scm.com/download/win
  pause
  exit /b 1
)
if exist "%DEST%\.git" (
  echo Ya existe FostersPrinter. Actualizando rama printer...
  cd /d "%DEST%"
  git fetch origin printer
  git checkout printer
  git pull --ff-only origin printer
) else (
  if exist "%DEST%" (
    echo ERROR: la carpeta %DEST% ya existe pero no es una instalacion Git.
    echo Renombrala o borrala y vuelve a ejecutar.
    pause
    exit /b 1
  )
  echo Descargando Fosters Printer...
  git clone --branch printer --single-branch "%REPO%" "%DEST%"
  if errorlevel 1 (
    echo ERROR: no se pudo descargar el repositorio.
    pause
    exit /b 1
  )
)
echo.
echo [OK] Instalacion lista.
start "" "%DEST%\ABRIR.cmd"
