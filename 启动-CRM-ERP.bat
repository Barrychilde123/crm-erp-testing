@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=python"
where python >nul 2>&1
if errorlevel 1 set "PYTHON=py"
where %PYTHON% >nul 2>&1
if errorlevel 1 (
  echo Python not found. Please install Python first.
  pause
  exit /b 1
)

echo Starting CRM/ERP server...
echo URL:   http://127.0.0.1:5000
echo Login: admin / admin123
echo To reset demo data: %PYTHON% -m app.seed
echo.

start "CRM ERP Server" cmd /k "%PYTHON% run.py"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:5000"
endlocal
