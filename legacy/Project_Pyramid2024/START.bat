@echo off
title EVO PYRAMID LAUNCHER
color 0A

echo [BAT] Searching for Python...

:: 1. Try global python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [BAT] Found Global Python. Launching...
    python LAUNCH_PYRAMID.py
    goto :end
)

:: 2. Try standard Windows path (User)
set PY_PATH="%LocalAppData%\Programs\Python\Python313\python.exe"
if exist %PY_PATH% (
    echo [BAT] Found Python 3.13 at default path. Launching...
    %PY_PATH% LAUNCH_PYRAMID.py
    goto :end
)

:: 3. Try standard Windows path (System)
set PY_PATH_SYS="C:\Python313\python.exe"
if exist %PY_PATH_SYS% (
    echo [BAT] Found Python 3.13 at system path. Launching...
    %PY_PATH_SYS% LAUNCH_PYRAMID.py
    goto :end
)

echo [BAT] CRITICAL ERROR: Python not found!
echo Please install Python 3.10+ and add it to PATH.
pause

:end
pause
