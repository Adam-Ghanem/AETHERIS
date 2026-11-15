@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run Start_AETHERIS.bat to install Python dependencies.
  pause
  exit /b 1
)
.venv\Scripts\python.exe scripts\verify_live_nasa.py
if errorlevel 1 (
  echo LIVE NASA verification failed. Check internet or NASA POWER availability.
) else (
  echo LIVE NASA integration and climate forensics checked successfully.
)
pause
