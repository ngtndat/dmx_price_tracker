@echo off
title YT Drama Studio v2.0 Pro - Desktop Launcher
color 0A
echo ========================================================
echo   CHUYEN DOI PHIM TRUYEN NGAN TRUNG QUOC DANG YOUTUBE
echo   Khoi dong Python App Server & Mo trinh duyet...
echo ========================================================
echo.

cd /d "%~dp0"
start "" http://localhost:8000
python app.py
pause
