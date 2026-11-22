@echo off
cd /d "%~dp0"
title Hethereau Owner's Selection Tool (HOST)
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)
py etero_owner_selection.py
if errorlevel 1 pause
