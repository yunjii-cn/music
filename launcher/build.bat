@echo off
:: ACE-Step Launcher 构建脚本
:: 打包为 EXE 可执行文件

echo =========================================
echo ACE-Step Launcher 构建脚本
echo =========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到 PATH
    pause
    exit /b 1
)

:: 运行构建脚本
echo 开始构建...
python build.py

if errorlevel 1 (
    echo.
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo 构建完成！
pause
