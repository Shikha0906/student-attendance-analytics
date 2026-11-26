@echo off
title Student Attendance Analytics - Teacher Demo
cd /d "%~dp0"
echo ========================================================
echo   Running Student Attendance Analytics Demonstration
echo ========================================================
echo.
python demo.py
echo.
echo ========================================================
echo   Press any key to close this demo window...
echo ========================================================
pause > nul
