@echo off
setlocal
cd /d "%~dp0"
title Hethereau Owner's Selection Tool (HOST)

rem Request elevation before installing dependencies or launching HOST.
fltmc >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)
py etero_owner_selection.py
if errorlevel 1 pause
