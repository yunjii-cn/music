@echo off

:: ACE-Step 一键启动器
:: 一键启动 Gradio Web UI

echo =========================================
echo ACE-Step 一键启动器
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
echo 正在启动 ACE-Step...
echo =========================================
echo.

:: 启动 Gradio Web UI
echo 正在启动 Gradio Web UI...
start "ACE-Step Gradio" powershell.exe -NoExit -Command "& '%~dp02、run_gradio.ps1'"

echo.
echo =========================================
echo ACE-Step 已启动！
echo =========================================
echo.
echo 按任意键退出此窗口...
pause >nul
