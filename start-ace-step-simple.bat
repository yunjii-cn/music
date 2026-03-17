@echo off

:: ACE-Step 启动器
:: 一键启动所有服务并自动打开浏览器

echo =========================================
echo ACE-Step 启动器
echo =========================================
echo.

:: 检查 uv 是否安装
if not exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo 环境未安装，正在执行安装...
    echo.
    call "%~dp01、install-uv-qinglong.ps1"
    if errorlevel 1 (
        echo 安装失败，请检查错误信息
        pause
        exit /b 1
    )
    echo.
    echo 环境安装成功！
    echo.
)

:: 检查 bitsandbytes 是否安装
echo 检查 bitsandbytes...
powershell.exe -Command "& '%USERPROFILE%\.local\bin\uv.exe' pip list | Select-String 'bitsandbytes'" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 bitsandbytes...
    powershell.exe -Command "& '%USERPROFILE%\.local\bin\uv.exe' pip install bitsandbytes"
    if errorlevel 0 (
        echo bitsandbytes 安装成功！
    ) else (
        echo bitsandbytes 安装失败，但不影响运行
    )
    echo.
) else (
    echo bitsandbytes 已安装
    echo.
)

echo =========================================
echo 正在启动所有服务...
echo =========================================
echo.

:: 进入脚本目录
cd /d "%~dp0"

:: 启动 Gradio Web UI
echo 正在启动 Gradio Web UI...
start "ACE-Step Gradio" powershell.exe -NoExit -Command "cd '%~dp0'; . '.\2、run_gradio.ps1'"

:: 等待 3 秒
echo 等待 3 秒...
ping 127.0.0.1 -n 4 >nul

:: 启动 API 服务器
echo 正在启动 API 服务器...
start "ACE-Step API" powershell.exe -NoExit -Command "cd '%~dp0'; . '.\3、run_server.ps1'"

:: 等待 3 秒
echo 等待 3 秒...
ping 127.0.0.1 -n 4 >nul

:: 启动 NPM GUI
echo 正在启动 NPM GUI...
start "ACE-Step NPM" powershell.exe -NoExit -Command "cd '%~dp0'; . '.\4、run_npmgui.ps1'"

:: 等待 5 秒，然后打开浏览器
echo 等待 5 秒，打开浏览器...
ping 127.0.0.1 -n 6 >nul
start "" "http://127.0.0.1:7860"

echo.
echo =========================================
echo 所有服务已启动，浏览器已打开！
echo =========================================
echo.
echo 按任意键退出此窗口...
pause >nul
