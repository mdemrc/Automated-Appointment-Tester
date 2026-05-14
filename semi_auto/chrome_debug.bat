@echo off
echo ========================================
echo   Chrome Debug Mode Baslatici
echo ========================================
echo.
echo Mevcut Chrome pencereleri kapatiliyor...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 >nul
echo.
echo Chrome debug modda aciliyor...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
echo.
echo Chrome started.
echo Now navigate to the target login URL configured in your local .env (TARGET_LOGIN_URL).
echo.
pause
