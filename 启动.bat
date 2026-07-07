@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "" /B "C:\Users\Administrator\AppData\Local\Python\bin\pythonw.exe" "main.py"
