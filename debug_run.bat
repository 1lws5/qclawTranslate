@echo off
chcp 65001 >nul
cd /d "C:\Users\Administrator\Desktop\qclawTranslate"
"C:\Users\Administrator\AppData\Local\Python\bin\python.exe" "main.py" 2>"crash.log"
type crash.log
pause
