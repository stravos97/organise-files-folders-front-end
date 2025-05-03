# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['/Users/haashimalvi/git_repo/organise_dirs_front_end/organize_gui/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('/Users/haashimalvi/git_repo/organise_dirs_front_end/organize_gui/config', 'config'),
        ('/Users/haashimalvi/git_repo/organise_dirs_front_end/organize_gui/ui', 'ui'),
        ('/Users/haashimalvi/git_repo/organise_dirs_front_end/organize_gui/core', 'core'),
        ('/Users/haashimalvi/git_repo/organise_dirs_front_end/organize_gui/utils', 'utils'),
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
    icon='',
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
