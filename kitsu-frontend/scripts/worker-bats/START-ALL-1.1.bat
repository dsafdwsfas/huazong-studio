@echo off
chcp 65001 >nul
echo Starting 3 workers for feature 1.1...
echo.
start "" "D:\claude\bot-01\workspace\kitsu-frontend\scripts\worker-bats\start-1.1-w1.bat"
timeout /t 3 /nobreak >nul
start "" "D:\claude\bot-01\workspace\kitsu-frontend\scripts\worker-bats\start-1.1-w7.bat"
timeout /t 3 /nobreak >nul
start "" "D:\claude\bot-01\workspace\kitsu-frontend\scripts\worker-bats\start-1.1-w3.bat"
timeout /t 3 /nobreak >nul
echo.
echo All 3 workers launched!
echo.
pause