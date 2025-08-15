from PyInstaller.utils.hooks import collect_submodules
from PyQt6.QtCore import QLibraryInfo
import os
import pathlib

# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

# Resolve Qt paths so QtWebEngine assets are bundled.
base = QLibraryInfo.path(QLibraryInfo.LibraryPath.PrefixPath)
data_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.DataPath)
plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)

def _tree(src: str, dest: str):
    files = []
    root = pathlib.Path(src)
    if not root.exists():
        return files
    for path in root.rglob('*'):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            files.append((str(path), os.path.join(dest, rel)))
    return files

datas = [('rules/popular.json', 'rules')]
# QtWebEngine resources, translations, and plugins
datas += _tree(os.path.join(data_path, 'resources'), 'PyQt6/Qt6/resources')
datas += _tree(translations_path, 'PyQt6/Qt6/translations')
datas += _tree(plugins_path, 'PyQt6/Qt6/plugins')

# QtWebEngineProcess executable is required for embedded browser. Use
# .exe on Windows, fallback to the Linux binary name so the spec can be
# executed in non-Windows environments for testing.
qt_process = os.path.join(base, 'bin', 'QtWebEngineProcess.exe')
if not os.path.exists(qt_process):
    qt_process = os.path.join(base, 'bin', 'QtWebEngineProcess')
binaries = []
if os.path.exists(qt_process):
    binaries.append((qt_process, 'PyQt6/Qt6/bin'))

# Pull in PyQt6 submodules and optional OCR helper
hiddenimports = collect_submodules('PyQt6') + ['pytesseract']

a = Analysis(
    ['ss_ui.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ss_scraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
