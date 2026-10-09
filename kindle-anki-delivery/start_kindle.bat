@echo off
chcp 65001 >nul
title Kindle Vocab - Launcher

echo ================================================
echo   Kindle Shengci Launcher
echo ================================================
echo.

rem ===== Pin AnkiConnect LAN binding (prevent reset to 127.0.0.1) =====
set "ANKICONNECT_BIND_ADDRESS=0.0.0.0"
set "ANKICONNECT_BIND_PORT=8765"

echo [0/3] Checking AnkiConnect config ...
"C:\Users\Cysteine\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0fix_ankiconnect.py"
echo.

echo [1/3] Starting Anki ...
start "" "F:\anki\Anki.exe"
echo       Anki started (wait a few seconds for AnkiConnect to load)

echo.
echo [2/3] Starting auto-enrich listener ...
echo.
echo  -- Listener info --
echo   * Auto-fill word root / etymology for new Anki notes
echo   * Keep this window open = listening
echo   * Close this window = stop listening (Anki unaffected)
echo  --------------------
echo.

"C:\Users\Cysteine\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0auto_enrich.py"

pause
