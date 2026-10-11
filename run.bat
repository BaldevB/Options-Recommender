@echo off
title Options Suggester Pro - Launcher
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launcher.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong during launch. Press any key to exit.
    pause >nul
)
