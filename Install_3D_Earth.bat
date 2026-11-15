@echo off
setlocal
cd /d "%~dp0"
echo =====================================================
echo     AETHERIS - GhostCat 3D Earth Assets (MIT)
echo =====================================================
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\install_ghostcat_assets.py
) else (
  python scripts\install_ghostcat_assets.py
)
echo.
echo The original globe texture and Three.js runtime are installed if the downloads succeeded.
echo AETHERIS continues to work with its offline globe if not.
pause
