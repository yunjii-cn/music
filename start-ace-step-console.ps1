#!/usr/bin/env powershell
# ACE-Step Console Launcher
# 命令行启动器，在同一窗口中执行所有命令

Write-Host "=========================================" -ForegroundColor Green
Write-Host "ACE-Step 启动器 v1.0" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 显示菜单
function Show-Menu {
    Write-Host "请选择要启动的服务：" -ForegroundColor Cyan
    Write-Host "1. 启动音乐演练场 (http://127.0.0.1:7860/)" -ForegroundColor Yellow
    Write-Host "2. 启动青龙 LoRA 训练器 (http://localhost:3000/)" -ForegroundColor Yellow
    Write-Host "3. 退出" -ForegroundColor Yellow
    Write-Host ""
    $choice = Read-Host "请输入选项 (1-3)"
    return $choice
}

# 检查环境
function Check-Environment {
    Write-Host "正在检查环境..." -ForegroundColor Cyan
    
    # 检查 uv 是否安装
    $uv_path = "$HOME\.local\bin\uv.exe"
    $env_exists = Test-Path $uv_path
    
    if (-not $env_exists) {
        Write-Host "环境未安装，正在执行安装..." -ForegroundColor Yellow
        
        # 运行安装脚本
        & "$scriptDir\1、install-uv-qinglong.ps1"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "安装失败，请检查错误信息" -ForegroundColor Red
            return $false
        }
        
        Write-Host "环境安装成功！" -ForegroundColor Green
    } else {
        Write-Host "环境已安装" -ForegroundColor Green
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
        Write-Host "正在安装 bitsandbytes..." -ForegroundColor Yellow
        & $uv_path pip install bitsandbytes
        Write-Host "bitsandbytes 安装成功！" -ForegroundColor Green
    } else {
        Write-Host "bitsandbytes 已安装" -ForegroundColor Green
    }
    
    return $true
}

# 启动音乐演练场
function Start-MusicArena {
    Write-Host "正在启动音乐演练场..." -ForegroundColor Cyan
    
    # 启动 Gradio Web UI
    Write-Host "启动 Gradio Web UI..." -ForegroundColor Yellow
    
    # 在当前窗口中启动
    & "$scriptDir\2、run_gradio.ps1"
}

# 启动青龙 LoRA 训练器
function Start-LoraTrainer {
    Write-Host "正在启动青龙 LoRA 训练器..." -ForegroundColor Cyan
    
    # 启动 NPM GUI
    Write-Host "启动 NPM GUI..." -ForegroundColor Yellow
    
    # 在当前窗口中启动
    & "$scriptDir\4、run_npmgui.ps1"
}

# 主循环
while ($true) {
    $choice = Show-Menu
    
    switch ($choice) {
        "1" {
            if (Check-Environment) {
                Start-MusicArena
            }
            break
        }
        "2" {
            Start-LoraTrainer
            break
        }
        "3" {
            Write-Host "退出启动器..." -ForegroundColor Cyan
            exit
            break
        }
        default {
            Write-Host "无效选项，请重新输入" -ForegroundColor Red
            break
        }
    }
    
    Write-Host ""
    Write-Host "按任意键继续..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Write-Host ""
}
