@echo off
chcp 65001 >nul
title Kindle 生词 - 一键启动

echo ================================================
echo   Kindle 生词学习 - 一键启动
echo ================================================
echo.

rem ===== 固化 AnkiConnect 局域网绑定（防止被重置回 127.0.0.1）=====
set "ANKICONNECT_BIND_ADDRESS=0.0.0.0"
set "ANKICONNECT_BIND_PORT=8765"

echo [0/3] 正在校验 AnkiConnect 配置（防止被重置回 127.0.0.1）...
"C:\Users\Cysteine\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0fix_ankiconnect.py"
echo.

echo [1/3] 正在启动 Anki ...
start "" "F:\anki\Anki.exe"
echo       Anki 已启动（稍等几秒让其加载 AnkiConnect）

echo.
echo [2/3] 正在启动自动补全监听器 ...
echo.
echo  ── 监听器说明 ──────────────────────────────
echo   · 自动为 Anki 新词补全 词根词缀/词源
echo   · 本窗口保持打开 = 监听中
echo   · 关闭本窗口 = 停止监听（不影响 Anki）
echo  ─────────────────────────────────────────────
echo.

"C:\Users\Cysteine\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0auto_enrich.py"

pause
