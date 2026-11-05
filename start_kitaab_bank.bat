@echo off
setlocal
title Kitaab Bank - Smart School Book Exchange
chcp 65001 >nul 2>&1

cd /d "%~dp0"

echo ===============================================================================
echo                KITAAB BANK - SMART SCHOOL BOOK EXCHANGE
echo                      کتاب بینک - اسکول کتاب تبادلہ
echo ===============================================================================
echo.

:: Detect Python executable
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [ERROR] Python not found!
        echo Please ensure Python 3.10+ or the virtual environment (.venv) is installed.
        echo.
        pause
        exit /b 1
    )
)

echo Starting Kitaab Bank Local Server...
echo Opening browser at http://127.0.0.1:5000 ...
start "" "http://127.0.0.1:5000"

echo.
%PYTHON_EXE% run_server.py

pause
