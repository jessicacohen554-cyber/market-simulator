@echo off
setlocal enabledelayedexpansion
rem Desktop launcher entry point (ADR 0016): resolve a usable Python, then
rem start the local launch-page server (`python -m lce_portfolio.launcher`).
rem Twin of run_lce.sh — keep the two in lockstep on any behavior change.
rem NOT CI-tested on Windows (see launcher/README.md) — review carefully.
rem
rem Usage:
rem   run_lce.bat                rem open the launch page in the default browser
rem   run_lce.bat --no-open      rem start the server without opening a browser
rem   run_lce.bat --port 8765    rem bind a fixed port instead of an ephemeral one

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "TOOL_ROOT=%%~fI"
set "VENV_PYTHON=%TOOL_ROOT%\..\.venv\Scripts\python.exe"

rem pyproject.toml requires-python = ">=3.11"
set "MIN_PYTHON_MINOR=11"

set "PYTHON="

call :check_python "%VENV_PYTHON%"
if "!PYTHON_OK!"=="1" (
    set "PYTHON=%VENV_PYTHON%"
) else (
    for %%P in (python3.exe python.exe) do (
        if not defined PYTHON (
            for /f "delims=" %%W in ('where %%P 2^>nul') do (
                if not defined PYTHON (
                    call :check_python "%%W"
                    if "!PYTHON_OK!"=="1" set "PYTHON=%%W"
                )
            )
        )
    )
)

if not defined PYTHON (
    echo error: no usable Python found for the LCE portfolio launcher. 1>&2
    echo   Tried: %VENV_PYTHON%, then python3/python on PATH. 1>&2
    echo   Need Python ^>= 3.%MIN_PYTHON_MINOR% with highspy, numpy, and pandas importable. 1>&2
    echo   Fix: create the venv and install dependencies, e.g.: 1>&2
    echo     python -m venv .venv 1>&2
    echo     .venv\Scripts\pip install -r scope2-lce-portfolio\requirements.txt 1>&2
    exit /b 1
)

cd /d "%TOOL_ROOT%"
rem Run straight from a clone without requiring `pip install -e .` (mirrors
rem run_portfolio.py's sys.path.insert trick, done here via PYTHONPATH since
rem this is a `-m` invocation, not a script that can insert its own path).
set "PYTHONPATH=%TOOL_ROOT%\src;%PYTHONPATH%"
"%PYTHON%" -m lce_portfolio.launcher %*
exit /b %ERRORLEVEL%

:check_python
rem Sets PYTHON_OK=1 if %~1 exists, is >= the required version, and can
rem import highspy/numpy/pandas; PYTHON_OK=0 otherwise. Never errors out.
set "PYTHON_OK=0"
if not exist "%~1" exit /b 0
"%~1" -c "import sys,importlib.util; sys.exit(0 if sys.version_info>=(3,%MIN_PYTHON_MINOR%) and all(importlib.util.find_spec(m) for m in ('highspy','numpy','pandas')) else 1)" >nul 2>&1
if !ERRORLEVEL! EQU 0 set "PYTHON_OK=1"
exit /b 0
