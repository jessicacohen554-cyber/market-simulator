@echo off
REM ===================================================================
REM  Market Simulator - desktop run launcher (Windows)
REM  Double-click this file. On first run it creates a local Python
REM  environment and installs dependencies (a few minutes); after that
REM  it just opens the launcher UI in your browser.
REM ===================================================================
setlocal
cd /d "%~dp0"

REM --- locate a Python interpreter ---
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo.
  echo Python 3.11 or newer was not found on this PC.
  echo Install it from https://www.python.org/downloads/
  echo ^(tick "Add python.exe to PATH" during install^), then run this file again.
  echo.
  pause
  exit /b 1
)

REM --- create the virtual environment on first run ---
if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment ^(first run only^)...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo Could not create the virtual environment.
    pause
    exit /b 1
  )
)
set "VENV_PY=.venv\Scripts\python.exe"

REM --- install dependencies on first run ---
if not exist ".venv\.deps_installed" (
  echo Installing dependencies ^(first run only - this can take a few minutes^)...
  "%VENV_PY%" -m pip install --upgrade pip
  "%VENV_PY%" -m pip install -e .
  if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and retry.
    pause
    exit /b 1
  )
  echo done > ".venv\.deps_installed"
)

REM --- launch the local UI ---
echo.
echo Starting the launcher. Your browser will open at http://127.0.0.1:8765/
echo Leave this window open while you work; close it to stop the server.
echo.
"%VENV_PY%" tools\launcher.py
pause
