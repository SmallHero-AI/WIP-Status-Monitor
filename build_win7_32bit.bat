@echo off
echo ======================================================
echo   WIP Status Monitor v1.3 - Win7 32-bit Build Script
echo ======================================================
echo.
echo [1/4] Checking Python version...
python --version
echo.

echo [2/4] Creating 32-bit Virtual Environment...
python -m venv venv_win7_32
call venv_win7_32\Scripts\activate

echo [3/4] Installing dependencies (Win7 Compatible)...
python -m pip install --upgrade pip
pip install pandas==1.4.4 xlrd==2.0.1 fastapi==0.85.0 uvicorn==0.18.3 jinja2==3.1.2 pyinstaller==5.13.2

echo [4/4] Building Executable...
pyinstaller --name "WIP_Status_Monitor_v1.3_Win7_x86" --add-data "wip-monitor-web/dist;dist" wip-monitor-api.py --onefile

echo.
echo ======================================================
echo   Done! Check 'dist/WIP_Status_Monitor_v1.3_Win7_x86.exe'
echo ======================================================
pause
