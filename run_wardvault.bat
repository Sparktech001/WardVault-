@echo off
title WardVault PHC Gateway
echo ========================================================
echo   Starting WardVault PHC - Offline-First Gateway
echo   Universal Service Provision Fund (USPF) Changemaker
echo ========================================================
echo.

cd /d "%~dp0"

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run: python -m venv .venv
    pause
    exit /b 1
)

echo Starting FastAPI server at http://127.0.0.1:8000 ...
start "" "http://127.0.0.1:8000"
.\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000 --reload
pause

