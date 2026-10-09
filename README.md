# Fosters Printer v3.3

Rama autoactualizable del sistema de impresión 50x25 mm.

## Instalación
Clonar solo esta rama:

git clone --branch printer --single-branch https://github.com/aguamilanobo/fosters-tools.git FostersPrinter

Después abrir siempre **ABRIR.cmd**. Ese archivo:
1. hace git pull,
2. instala la última versión local desde FostersPrinter-latest.zip,
3. abre el puente de impresión.

Los tokens, el diseño y el historial permanecen fuera de GitHub en:
%LOCALAPPDATA%\EtiquetasUniversal\

## Telegram
/status, /cola, /borrarcola #ID, /borrarcola all, /forzarcola, /forzarcola #ID, /pausar, /reanudar, /historial, /reimprimir #PrintID, /stats, /version, /whoami, /help y /print.

La V3.3 también conecta con el Mini App "Panel Printer" alojado en fosters-tools.
