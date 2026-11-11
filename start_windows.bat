@echo off
chcp 65001 >nul
title Leeloo AI Robot Server
color 0b

echo ========================================================
echo    🏄‍♀️ LEELOO AI ENGLISH TUTOR - WINDOWS SERVER 🏄‍♀️
echo ========================================================
echo.

echo [1/3] Checking Python via py launcher...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [Python OK!]
echo [2/3] Installing/updating requirements...
py -m pip install -r requirements.txt

echo.
echo [3/3] Starting Leeloo Server on port 8000...
echo.
echo Local IP: 192.168.0.101
echo WebSocket endpoint: ws://192.168.0.101:8000/xiaozhi/v1/
echo.
echo Leave this window open while chatting with your robot!
echo ========================================================
echo.

py app.py
pause
