@echo off
cd /d "C:\Users\seral\Desktop\arkadya-cobre"

:: Generar fecha y hora en formato YYYYMMDD_HHMMSS
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set FECHA=%%c%%a%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set HORA=%%a%%b
set HORA=%HORA: =0%

:: Verificar que la base de datos existe
if not exist "db.sqlite3" (
    echo ERROR: No se encuentra db.sqlite3 en la carpeta actual
    pause
    exit /b 1
)

:: Crear backup
copy /Y "db.sqlite3" "Backup\db_backup_%FECHA%_%HORA%.sqlite3"

if errorlevel 1 (
    echo ERROR: No se pudo copiar el archivo. Asegurate de cerrar el servidor Django primero.
) else (
    echo ✅ Backup completado: db_backup_%FECHA%_%HORA%.sqlite3
)
pause