@echo off
echo Iniciando Ofrezco App...
python run.py > startup_log.txt 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Hubo un error. Revisa startup_log.txt
) else (
    echo Aplicacion detenida.
)
pause
