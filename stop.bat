@echo off
title Options Suggester Pro - Stopper
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_servers.ps1"
