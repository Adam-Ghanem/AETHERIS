@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Run Start_AETHERIS.bat once to install Python dependencies.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pytest -v tests
set RESULT=%errorlevel%
echo.
if %RESULT% NEQ 0 echo [ERROR] Test suite failed with exit code %RESULT%.
if %RESULT% EQU 0 echo [SUCCESS] All automated tests passed.
pause
exit /b %RESULT%
