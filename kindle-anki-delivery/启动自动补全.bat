@echo off
chcp 65001 >nul
title Kindle 生词自动补全监听器
echo ================================================
echo   Kindle 生词自动补全监听器
echo   后台自动为 Anki 新词补全词根词缀/词源
echo ================================================
echo.
echo 提示：
echo   1. 请确保电脑上的 Anki 已启动
echo   2. 本窗口保持打开即表示监听中，关闭窗口即停止
echo   3. 在 Kindle 选词后，几秒内会自动补全
echo.
"C:\Users\Cysteine\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0auto_enrich.py"
pause
