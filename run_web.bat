@echo off
title Student Attendance Analytics - Web Server
cd /d "%~dp0"
echo ========================================================
echo   Starting Student Attendance Analytics Web Dashboard
echo ========================================================
echo.
echo Launching server on http://localhost:5000...
python web_app.py
pause
