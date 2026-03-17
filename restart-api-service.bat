@echo off
chcp 65001 >nul
echo ========================================
echo ACE-Step API 服务重启工具
echo ========================================
echo.

echo 【1】停止现有的 API 服务...
taskkill /F /PID 2064 2>nul
timeout /t 3 /nobreak >nul

echo.
echo 【2】清理 GPU 内存...
powershell.exe -Command "nvidia-smi --gpu-reset -i 0" 2>nul

echo.
echo 【3】检查 GPU 内存状态...
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv

echo.
echo ========================================
echo GPU 内存状态已更新
echo ========================================
echo.
echo 请重新启动 API 服务：
echo   方式1: 运行启动器，点击【启动 API 服务】
echo   方式2: 手动运行 .\3、run_server.ps1
echo.
echo 【提示】如果内存仍然不足，请：
echo   1. 关闭其他占用GPU的程序
echo   2. 确保启用 offload_to_cpu 选项
echo.
pause
