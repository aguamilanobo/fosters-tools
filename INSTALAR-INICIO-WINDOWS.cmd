@echo off
setlocal
set "TARGET=%~dp0ABRIR.cmd"
set "LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Fosters Printer.lnk"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('%LINK%');$s.TargetPath='%TARGET%';$s.WorkingDirectory='%~dp0';$s.Save()"
if errorlevel 1 (echo No se pudo configurar el inicio automatico.) else (echo OK: Fosters Printer se abrira con Windows.)
pause
