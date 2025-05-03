#!/bin/bash
# setup_organise_gui.sh
# Script to set up the environment for the organize-files-folders-front-end project on macOS
# This script is immutable - it runs without user interaction and installs all required dependencies
# Including Homebrew, Git, Python, Visual Studio Code, and the project itself

# Print colored output
print_green() {
    echo -e "\033[32m$1\033[0m"
}

print_yellow() {
    echo -e "\033[33m$1\033[0m"
}

print_red() {
    echo -e "\033[31m$1\033[0m"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 6 ]); then
        print_red "Python version $version detected. Version 3.6 or newer is required."
        return 1
    else
        print_green "Python version $version detected. ✓"
        return 0
    fi
}

# Set fixed installation directory - immutable approach with no user input
INSTALL_DIR="$HOME/organize-gui"

# Clear screen
clear

print_green "=========================================================="
print_green "   Immutable Setup Script for File Organization System"
print_green "=========================================================="
echo

# Install Homebrew if not present
echo "Checking for Homebrew..."
if command_exists brew; then
    print_green "Homebrew is installed. ✓"
    print_yellow "Updating Homebrew..."
    brew update
else
    print_yellow "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for the current session
    if [[ $(uname -m) == "arm64" ]]; then
        # For Apple Silicon Macs
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        # For Intel Macs
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    if command_exists brew; then
        print_green "Homebrew installed successfully. ✓"
    else
        print_red "Failed to install Homebrew. Please install it manually and try again."
        exit 1
    fi
fi

# Install Git using Homebrew if not present
echo "Checking for Git..."
if command_exists git; then
    print_green "Git is installed. ✓"
else
    print_yellow "Git not found. Installing Git using Homebrew..."
    brew install git
    
    if command_exists git; then
        print_green "Git installed successfully. ✓"
    else
        print_red "Failed to install Git. Please install it manually and try again."
        exit 1
    fi
fi

# Install Python using Homebrew if not present or version is too old
echo "Checking for Python..."
if command_exists python3; then
    if check_python_version; then
        print_green "Python 3.6+ is installed. ✓"
    else
        print_yellow "Python version is too old. Installing Python using Homebrew..."
        brew install python
        
        if check_python_version; then
            print_green "Python installed successfully. ✓"
        else
            print_red "Failed to install Python 3.6+. Please install it manually and try again."
            exit 1
        fi
    fi
else
    print_yellow "Python 3 not found. Installing Python using Homebrew..."
    brew install python
    
    if command_exists python3 && check_python_version; then
        print_green "Python installed successfully. ✓"
    else
        print_red "Failed to install Python. Please install it manually and try again."
        exit 1
    fi
fi

# Install Visual Studio Code using Homebrew if not present
echo "Checking for Visual Studio Code..."
if command_exists code; then
    print_green "Visual Studio Code is installed. ✓"
else
    print_yellow "Visual Studio Code not found. Installing using Homebrew..."
    brew install --cask visual-studio-code
    
    if command_exists code; then
        print_green "Visual Studio Code installed successfully. ✓"
    else
        print_yellow "Failed to install Visual Studio Code via Homebrew."
        print_yellow "You may need to install it manually from https://code.visualstudio.com/"
    fi
fi

echo
print_green "All prerequisites are installed! ✓"
echo

print_yellow "Setting up project directory at: $INSTALL_DIR"

# Check if directory already exists and remove it
if [ -d "$INSTALL_DIR" ]; then
    print_yellow "Directory already exists. Removing for clean installation..."
    rm -rf "$INSTALL_DIR"
fi

# Create directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Clone the repository
print_green "Cloning the repository..."
git clone https://github.com/stravos97/organise-files-folders-front-end.git "$INSTALL_DIR"

if [ $? -ne 0 ]; then
    print_red "Failed to clone the repository. Please check your internet connection and try again."
    exit 1
fi

# Change to the installation directory
cd "$INSTALL_DIR"

# Create and activate virtual environment
print_green "Setting up virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    print_red "Failed to create virtual environment. Please check your Python installation and try again."
    exit 1
fi

# Source the activation script
source venv/bin/activate

if [ $? -ne 0 ]; then
    print_red "Failed to activate virtual environment. Please check your Python installation and try again."
    exit 1
fi

# Navigate to the organize_gui directory
cd organize_gui

# Install dependencies
print_green "Installing dependencies..."
pip3 install -U organize-tool
pip3 install -e .

if [ $? -ne 0 ]; then
    print_red "Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi

# Install test dependencies
print_green "Installing test dependencies..."
pip3 install pytest pytest-mock pytest-cov

if [ $? -ne 0 ]; then
    print_red "Failed to install test dependencies. Please check your internet connection and try again."
    print_yellow "Continuing with installation, but tests may not work properly."
fi

# Verify installation
print_green "Verifying installation..."
if command_exists organize-gui; then
    print_green "organize-gui installed successfully! ✓"
else
    # If the command is not found in PATH, it might be installed in the venv bin directory
    if [ -f "$INSTALL_DIR/venv/bin/organize-gui" ]; then
        print_green "organize-gui installed successfully in the virtual environment! ✓"
    else
        print_yellow "organize-gui binary not found. The installation might have issues."
        print_yellow "Try running the application using the run.sh script instead."
    fi
fi

# Install recommended VSCode extensions if VSCode is installed
if command_exists code; then
    print_green "Installing recommended VSCode extensions for Python development..."
    code --install-extension ms-python.python
    code --install-extension ms-python.vscode-pylance
    code --install-extension njpwerner.autodocstring
    print_green "VSCode extensions installed. ✓"
fi

echo
print_green "=========================================================="
print_green "   Installation Complete!"
print_green "=========================================================="
echo
print_green "You can now run the application using:"
echo
print_yellow "   cd $INSTALL_DIR/organize_gui"
print_yellow "   source ../venv/bin/activate  # Activate the virtual environment"
print_yellow "   ./run.sh                     # Run the application"
echo
print_green "Or use the entry point directly:"
echo
print_yellow "   cd $INSTALL_DIR"
print_yellow "   source venv/bin/activate     # Activate the virtual environment"
print_yellow "   organize-gui                  # Run the application"
echo
print_green "If you installed VSCode, you can open the project with:"
echo
print_yellow "   code $INSTALL_DIR"
echo
print_green "To run tests, use:"
echo
print_yellow "   cd $INSTALL_DIR"
print_yellow "   source venv/bin/activate     # Activate the virtual environment"
print_yellow "   pytest tests/                # Run all tests"
print_yellow "   pytest -v tests/             # Run tests with verbose output"
print_yellow "   pytest --cov=organize_gui tests/  # Run tests with coverage report"
echo
print_green "To exit the virtual environment when you're done, type 'deactivate'"
echo
print_green "Happy organizing! 🎉"
