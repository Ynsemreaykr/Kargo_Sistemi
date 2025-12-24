@echo off
echo ============================================================
echo Kargo Isletme Sistemi - Baslat
echo ============================================================
echo.

echo [1/2] Backend API baslatiliyor (Port 5002)...
start cmd /k "cd /d %~dp0api && python app.py"
timeout /t 2 /nobreak >nul

echo [2/2] Frontend HTTP Server baslatiliyor (Port 8000)...
start cmd /k "cd /d %~dp0frontend && python -m http.server 8000"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo Sistem baslatildi!
echo ============================================================
echo Backend API:  http://localhost:5002
echo Frontend UI:  http://localhost:8000
echo ============================================================
echo.
echo Tarayicinizda http://localhost:8000 adresini acin
echo.
echo Kapatmak icin her iki terminal penceresini kapatin
echo ============================================================

timeout /t 3 /nobreak >nul
start http://localhost:8000/login.html

pause
