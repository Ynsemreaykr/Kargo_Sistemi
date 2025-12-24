@echo off
echo ============================================================
echo Kargo Isletme Sistemi - Ilk Kurulum
echo ============================================================
echo.
echo Bu scripti sadece 1 kez calistirin (ilk kurulumda)
echo.

echo [1/2] Gerekli kutuphaneler yukleniyor...
pip install -r requirements.txt
echo.

echo [2/2] Veritabani ve kullanicilar olusturuluyor...
cd /d %~dp0api
python quick_setup.py
echo.

echo ============================================================
echo Kurulum tamamlandi!
echo Sistemi baslatmak icin: start.bat
echo ============================================================
echo.
pause

