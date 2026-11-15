@echo off
setlocal
cd /d "%~dp0"
echo =====================================================
echo           AETHERIS - EARTH INTELLIGENCE
echo =====================================================
if not exist ".venv\Scripts\python.exe" (
  echo [SETUP] Creating Python virtual environment...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe -c "import fastapi, uvicorn, httpx, numpy, scipy, statsmodels, reportlab" >nul 2>nul
if errorlevel 1 (
  echo [SETUP] Installing scientific dependencies. This requires internet on first run...
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
  )
)
if not exist "static\vendor\ghostcat-earth\.setup-attempted" (
  echo [OPTIONAL] Preparing GhostCat 3D Earth visual assets...
  .venv\Scripts\python.exe scripts\install_ghostcat_assets.py
)
echo.
echo Starting AETHERIS locally at http://127.0.0.1:8765
start "AETHERIS Browser" "http://127.0.0.1:8765"
.venv\Scripts\python.exe -m uvicorn aetheris.server:app --host 127.0.0.1 --port 8765
if errorlevel 1 (
  echo [ERROR] Check the console log above. Is port 8765 already in use?
  pause
)
