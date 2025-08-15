@echo off
REM One-click Windows build script
SETLOCAL

REM Clean previous builds and run PyInstaller using the bundled spec.
pyinstaller --noconfirm --clean ss_scraper.spec

echo Build complete.  Executable can be found under dist\ss_scraper.exe
ENDLOCAL
