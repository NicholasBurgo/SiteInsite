@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

pushd "%ROOT_DIR%"

if exist ".venv\Scripts\python.exe" (
    set "DEV_PYTHON=.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "DEV_PYTHON=py"
    ) else (
        where python >nul 2>nul
        if %errorlevel%==0 (
            set "DEV_PYTHON=python"
        ) else (
            echo Python 3.10+ is required but was not found on PATH.
            popd
            exit /b 1
        )
    )
)

%DEV_PYTHON% scripts\dev.py

set "EXIT_CODE=%errorlevel%"
popd
exit /b %EXIT_CODE%