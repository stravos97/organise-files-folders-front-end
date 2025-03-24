#!/bin/bash

# run.sh - Launcher script for the File Organization System frontend

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    # Check if venv exists
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        
        echo "Installing dependencies..."
        pip install -e .
    fi
fi

# Run the application
python app.py

# Windows version (run.bat)
# @echo off
# 
# rem Get the directory where this script is located
# set SCRIPT_DIR=%~dp0
# 
# rem Change to the script directory
# cd /d %SCRIPT_DIR%
# 
# rem Check if venv exists
# if exist venv\Scripts\activate.bat (
#     echo Activating virtual environment...
#     call venv\Scripts\activate.bat
# ) else (
#     echo Creating virtual environment...
#     python -m venv venv
#     call venv\Scripts\activate.bat
#     
#     echo Installing dependencies...
#     pip install -e .
# )
# 
# rem Run the application
# python app.py
# 
# pause