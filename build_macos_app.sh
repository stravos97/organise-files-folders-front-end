#!/bin/bash
# build_macos_app.sh
# Script to build a macOS application bundle (.app) and DMG for the organize-gui project

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

# Clear screen
clear

print_green "=========================================================="
print_green "   Building macOS Application for File Organization System"
print_green "=========================================================="
echo

# Check if we're in the correct directory
if [ ! -f "app.py" ]; then
    if [ -d "organize_gui" ] && [ -f "organize_gui/app.py" ]; then
        cd organize_gui
        print_yellow "Changed directory to organize_gui/"
    else
        print_red "Error: app.py not found. Please run this script from the project root or organize_gui directory."
        exit 1
    fi
fi

# Check for virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    print_yellow "No active virtual environment detected."
    
    # Check if venv exists in parent directory or current directory
    if [ -d "../venv" ]; then
        print_yellow "Found virtual environment in parent directory. Activating..."
        source ../venv/bin/activate
    elif [ -d "venv" ]; then
        print_yellow "Found virtual environment in current directory. Activating..."
        source venv/bin/activate
    else
        print_yellow "Creating new virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        
        print_yellow "Installing dependencies..."
        pip install -e .
    fi
    
    if [ -z "$VIRTUAL_ENV" ]; then
        print_red "Failed to activate virtual environment. Please activate it manually and try again."
        exit 1
    else
        print_green "Virtual environment activated. ✓"
    fi
fi

# Check for PyInstaller
print_yellow "Checking for PyInstaller..."
if ! command_exists pyinstaller; then
    print_yellow "PyInstaller not found. Installing..."
    pip install pyinstaller
    
    if ! command_exists pyinstaller; then
        print_red "Failed to install PyInstaller. Please install it manually and try again."
        exit 1
    else
        print_green "PyInstaller installed successfully. ✓"
    fi
else
    print_green "PyInstaller is already installed. ✓"
fi

# Create a directory for build files
BUILD_DIR="build_macos"
print_yellow "Creating build directory: $BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create a simple icon for the application if it doesn't exist
ICON_PATH="$BUILD_DIR/app_icon.icns"
if [ ! -f "$ICON_PATH" ]; then
    print_yellow "Creating application icon..."
    
    # Check if we have the tools to create an icon
    if command_exists convert && command_exists iconutil; then
        # Create a temporary directory for the iconset
        ICONSET_DIR="$BUILD_DIR/app.iconset"
        mkdir -p "$ICONSET_DIR"
        
        # Create a simple colored square as a base image
        convert -size 1024x1024 xc:#4287f5 "$BUILD_DIR/base.png"
        
        # Add text to the image
        convert "$BUILD_DIR/base.png" -gravity center -pointsize 200 -font Helvetica -weight Bold -fill white -annotate 0 "O" "$BUILD_DIR/icon_1024.png"
        
        # Create different sizes for the iconset
        convert "$BUILD_DIR/icon_1024.png" -resize 16x16 "$ICONSET_DIR/icon_16x16.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 32x32 "$ICONSET_DIR/icon_16x16@2x.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 32x32 "$ICONSET_DIR/icon_32x32.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 64x64 "$ICONSET_DIR/icon_32x32@2x.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 128x128 "$ICONSET_DIR/icon_128x128.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 256x256 "$ICONSET_DIR/icon_128x128@2x.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 256x256 "$ICONSET_DIR/icon_256x256.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 512x512 "$ICONSET_DIR/icon_256x256@2x.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 512x512 "$ICONSET_DIR/icon_512x512.png"
        convert "$BUILD_DIR/icon_1024.png" -resize 1024x1024 "$ICONSET_DIR/icon_512x512@2x.png"
        
        # Convert the iconset to .icns file
        iconutil -c icns "$ICONSET_DIR" -o "$ICON_PATH"
        
        # Clean up temporary files
        rm -f "$BUILD_DIR/base.png" "$BUILD_DIR/icon_1024.png"
        rm -rf "$ICONSET_DIR"
        
        print_green "Application icon created. ✓"
    else
        print_yellow "ImageMagick or iconutil not found. Using PyInstaller's default icon."
        ICON_PATH=""
    fi
fi

# Create a PyInstaller spec file
SPEC_FILE="$BUILD_DIR/organize_gui.spec"
print_yellow "Creating PyInstaller spec file..."

# Get the absolute paths
APP_PATH="$(pwd)/app.py"
CONFIG_PATH="$(pwd)/config"
UI_PATH="$(pwd)/ui"
CORE_PATH="$(pwd)/core"
UTILS_PATH="$(pwd)/utils"

cat > "$SPEC_FILE" << EOL
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['${APP_PATH}'],
    pathex=[],
    binaries=[],
    datas=[
        ('${CONFIG_PATH}', 'config'),
        ('${UI_PATH}', 'ui'),
        ('${CORE_PATH}', 'core'),
        ('${UTILS_PATH}', 'utils'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.font',
        'yaml',
        'organize',
        'mutagen',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='organize-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='organize-gui',
)

app = BUNDLE(
    coll,
    name='organize-gui.app',
    icon='${ICON_PATH}',
    bundle_identifier='com.organize-gui',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'CFBundleDisplayName': 'File Organization System',
        'CFBundleName': 'organize-gui',
    },
)
EOL

print_green "PyInstaller spec file created. ✓"

# Build the application
print_yellow "Building the application with PyInstaller..."
pyinstaller --clean "$SPEC_FILE"

if [ $? -ne 0 ]; then
    print_red "Failed to build the application. Check the error messages above."
    exit 1
fi

print_green "Application built successfully. ✓"

# Create a DMG file
print_yellow "Creating DMG file..."

# Check if create-dmg is installed
if ! command_exists create-dmg; then
    print_yellow "create-dmg not found. Installing with Homebrew..."
    
    if command_exists brew; then
        brew install create-dmg
        
        if ! command_exists create-dmg; then
            print_yellow "Failed to install create-dmg. Will use a simpler approach."
            SIMPLE_DMG=true
        fi
    else
        print_yellow "Homebrew not found. Will use a simpler approach."
        SIMPLE_DMG=true
    fi
fi

# Path to the built .app bundle
APP_PATH="dist/organize-gui.app"

if [ "$SIMPLE_DMG" = true ] || ! command_exists create-dmg; then
    # Simple approach using hdiutil directly
    DMG_PATH="dist/organize-gui-1.0.0.dmg"
    
    print_yellow "Creating DMG using hdiutil..."
    hdiutil create -volname "File Organization System" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
    
    if [ $? -ne 0 ]; then
        print_red "Failed to create DMG file. Check the error messages above."
        exit 1
    fi
else
    # More sophisticated approach using create-dmg
    DMG_PATH="dist/organize-gui-1.0.0.dmg"
    
    print_yellow "Creating DMG using create-dmg..."
    create-dmg \
        --volname "File Organization System" \
        --volicon "$ICON_PATH" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "organize-gui.app" 200 190 \
        --hide-extension "organize-gui.app" \
        --app-drop-link 600 185 \
        "$DMG_PATH" \
        "$APP_PATH"
    
    if [ $? -ne 0 ]; then
        print_red "Failed to create DMG file. Falling back to simple approach..."
        hdiutil create -volname "File Organization System" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
        
        if [ $? -ne 0 ]; then
            print_red "Failed to create DMG file. Check the error messages above."
            exit 1
        fi
    fi
fi

print_green "DMG file created successfully: $DMG_PATH ✓"

echo
print_green "=========================================================="
print_green "   Build Complete!"
print_green "=========================================================="
echo
print_green "Application bundle: dist/organize-gui.app"
print_green "DMG installer: $DMG_PATH"
echo
print_green "To install, open the DMG file and drag the application to your Applications folder."
echo
print_green "Happy organizing! 🎉"
