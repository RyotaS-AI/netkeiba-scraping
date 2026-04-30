@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =========================================
echo 競馬スクレイピングツールを起動します...
echo =========================================
echo.
py main.py
echo.
pause
