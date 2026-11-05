@echo off
setlocal
title Kitaab Bank - Instant Hot Backup
cd /d "%~dp0"

echo ===============================================================================
echo                KITAAB BANK - INSTANT DATABASE BACKUP
echo ===============================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Creating consistent online snapshot with SHA-256 and integrity verification...
echo.

%PYTHON_EXE% scripts\backup_cli.py

echo.
pause
