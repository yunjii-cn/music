#!/usr/bin/env powershell
# ACE-Step Minimal Launcher

# 启动所有服务
function Start-ACEStep {
    # 检查环境
    $uv_path = "$HOME\.local\bin\uv.exe"
    $env_exists = Test-Path $uv_path
    
    if (-not $env_exists) {
        Write-Host "环境未安装，正在执行安装..."
        & "$PSScriptRoot\1、install-uv-qinglong.ps1"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "安装失败，请检查错误信息"
            return
        }
    }
    
    # 检查 bitsandbytes
    $bitsandbytes_installed = $false
    try {
        $output = & $uv_path pip list | Select-String "bitsandbytes"
        if ($output) {
            $bitsandbytes_installed = $true
        }
    } catch {
        # 忽略错误
    }
    
    if (-not $bitsandbytes_installed) {
        Write-Host "正在安装 bitsandbytes..."
        & $uv_path pip install bitsandbytes
    }
    
    # 启动所有服务
    Write-Host "正在启动所有服务..."
    
    # 启动 Gradio Web UI
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\2、run_gradio.ps1'"
    
    # 等待 3 秒
    Start-Sleep -Seconds 3
    
    # 启动 API 服务器
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\3、run_server.ps1'"
    
    # 等待 3 秒
    Start-Sleep -Seconds 3
    
    # 启动 NPM GUI
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\4、run_npmgui.ps1'"
    
    # 等待 5 秒，然后打开浏览器
    Start-Sleep -Seconds 5
    Start-Process "http://127.0.0.1:7860"
    
    Write-Host "所有服务已启动，浏览器已打开！"
}

# 运行启动器
Start-ACEStep
Read-Host "按任意键退出..."
