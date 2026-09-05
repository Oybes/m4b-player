@echo off
title M4B Player
echo ==============================================
echo Starting Lightweight M4B Audiobook Player...
echo Access in your browser at: http://localhost:8765
echo ==============================================

python main.py
if errorlevel 1 (
    echo.
    echo Trying explicit Python path...
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main.py
)
pause
