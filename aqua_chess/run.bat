@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo ===================================================
    echo 🌊 Aqua Chess - First-Time Automatic Setup
    echo ===================================================
    echo [1/2] Creating isolated virtual environment ^(.venv^)...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Python was not found! Please install Python 3.10+ and check "Add Python to PATH".
        pause
        exit /b 1
    )
    echo [2/2] Installing dependencies ^(PySide6, python-chess^)...
    call .venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies from requirements.txt.
        pause
        exit /b 1
    )
    echo.
    echo Setup complete! Launching Aqua Chess...
)

start "" ".venv\Scripts\pythonw.exe" main.py