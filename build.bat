@echo off
chcp 65001 >nul
echo ============================================
echo   Steam 自动加好友工具 - 打包为 EXE
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller >nul 2>&1

REM 打包
echo [2/3] 正在打包为 EXE...
pyinstaller --onefile --windowed --name SteamFriendBot --clean steam_friend_bot_gui.py

echo.
if exist "dist\SteamFriendBot.exe" (
    echo [3/3] ✅ 打包成功!
    echo.
    echo EXE 文件位置: dist\SteamFriendBot.exe
    echo.
    echo 你可以将 dist\SteamFriendBot.exe 复制到任意位置运行。
) else (
    echo [错误] 打包失败，请检查错误信息。
)

echo.
pause
