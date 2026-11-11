@echo off
chcp 65001 >nul
title Leeloo AI Robot Server
color 0b

echo ========================================================
echo    🏄‍♀️ LEELOO AI ENGLISH TUTOR - WINDOWS SERVER 🏄‍♀️
echo ========================================================
echo.

set "PYCMD="

:: Check standard python
python --version >nul 2>&1
if %errorlevel% equ 0 set "PYCMD=python"

:: Check py launcher
if not defined PYCMD (
    py --version >nul 2>&1
    if %errorlevel% equ 0 set "PYCMD=py"
)

:: Check common install locations
if not defined PYCMD (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PYCMD=%%D\python.exe"
    )
)
if not defined PYCMD (
    for /d %%D in ("C:\Program Files\Python3*") do (
        if exist "%%D\python.exe" set "PYCMD=%%D\python.exe"
    )
)

if not defined PYCMD (
    echo [ERROR] Windows cannot find Python yet.
    echo Please RESTART your computer once so Windows updates its system paths!
    pause
    exit /b 1
)

echo [1/3] Found Python: %PYCMD%
echo.

if not exist .env (
    echo [Setup] Creating .env file with your Gemini API key...
    set "K1=AQ.Ab8RN6KrJ_98l0Kb9oo9Dw8es2qOKq"
    set "K2=_v2RtLhwVG5Byq4KyZvA"
    call echo GEMINI_API_KEY=%%K1%%%%K2%% > .env
)

echo [2/3] Installing/updating requirements...
"%PYCMD%" -m pip install -r requirements.txt

echo.
echo [3/3] Starting Leeloo Server on port 8000...
echo.
echo Local IP: 192.168.0.101
echo WebSocket endpoint: ws://192.168.0.101:8000/xiaozhi/v1/
echo.
echo Leave this window open while chatting with your robot!
echo ========================================================
echo.

"%PYCMD%" app.py
pause
