@echo off
chcp 65001 >nul
title Leeloo AI Robot Server
color 0b

echo ========================================================
echo    🏄‍♀️ LEELOO AI ENGLISH TUTOR - WINDOWS SERVER 🏄‍♀️
echo ========================================================
echo.

set "PYCMD=python"
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYCMD=py"
    ) else (
        echo [ERROR] Python is not installed or not in PATH!
        echo Please download and install Python from https://www.python.org/
        echo (Make sure to check "Add Python to PATH" during installation!)
        pause
        exit /b 1
    )
)

echo [1/3] Found Python (%PYCMD%)!
echo.

echo [2/3] Installing/updating requirements...
%PYCMD% -m pip install -r requirements.txt

echo.
echo [3/3] Starting Leeloo Server on port 8000...
echo.
echo Local IP: 192.168.0.101
echo WebSocket endpoint: ws://192.168.0.101:8000/xiaozhi/v1/
echo.
echo Leave this window open while chatting with your robot!
echo ========================================================
echo.

%PYCMD% app.py
pause
