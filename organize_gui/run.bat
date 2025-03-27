@echo off
rem run.bat - Launcher script for the File Organization System frontend on Windows

rem Get the directory where this script is located
set SCRIPT_DIR=%~dp0

rem Change to the script directory (use /d to handle potential drive changes)
cd /d %SCRIPT_DIR%

rem Check if we're in a virtual environment already (less reliable on Windows, but a basic check)
rem A more robust check might involve checking if python path points inside venv
if "%VIRTUAL_ENV%"=="" (
    rem Check if venv exists by looking for the activate script
    if exist "venv\Scripts\activate.bat" (
        echo Activating existing virtual environment...
        call "venv\Scripts\activate.bat"
    ) else (
        echo Creating virtual environment...
        python -m venv venv
        if errorlevel 1 (
            echo Failed to create virtual environment. Make sure Python is installed and in PATH.
            pause
            exit /b 1
        )
        
        echo Activating new virtual environment...
        call "venv\Scripts\activate.bat"
        
        echo Installing dependencies...
        pip install -e .
        if errorlevel 1 (
            echo Failed to install dependencies. Check pip and network connection.
            pause
            exit /b 1
        )
    )
) else (
    echo Already in a virtual environment.
)

rem Run the application
echo Starting File Organization System...
python app.py

rem Pause at the end to see output if run by double-clicking
echo.
pause
