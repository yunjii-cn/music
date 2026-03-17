#!/usr/bin/env powershell
# ACE-Step Launcher
# 重新封装的启动器

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "=========================================" -ForegroundColor Green
Write-Host "ACE-Step 启动器" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. 启动音乐演练场 (Gradio UI)"
Write-Host "2. 启动青龙 LoRA 训练器 (NPM UI)"
Write-Host "3. 退出"
Write-Host ""

$choice = Read-Host "请选择要启动的服务 (1-3)"

switch ($choice) {
    "1" {
        Write-Host "正在检查环境..." -ForegroundColor Cyan
        
        # 检查 uv 是否安装
        $uv_path = "$HOME\.local\bin\uv.exe"
        if (-not (Test-Path $uv_path)) {
            Write-Host "环境未安装，正在执行安装..." -ForegroundColor Yellow
            & "$scriptDir\1、install-uv-qinglong.ps1"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "安装失败，请检查错误信息" -ForegroundColor Red
                pause
                exit 1
            }
            Write-Host "环境安装成功！" -ForegroundColor Green
        }
        
        # 检查 bitsandbytes
        $bitsandbytes_installed = $false
        try {
            $output = & $uv_path pip list | Select-String "bitsandbytes"
            if ($output) {
                $bitsandbytes_installed = $true
            }
        } catch {
        }
        
        if (-not $bitsandbytes_installed) {
            Write-Host "正在安装 bitsandbytes..." -ForegroundColor Yellow
            & $uv_path pip install bitsandbytes
            Write-Host "bitsandbytes 安装成功！" -ForegroundColor Green
        }
        
        Write-Host "正在启动音乐演练场..." -ForegroundColor Cyan
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; . '.\2、run_gradio.ps1'"
        Start-Sleep -Seconds 5
        Start-Process "http://127.0.0.1:7860"
        Write-Host "音乐演练场已启动，浏览器已打开！" -ForegroundColor Green
        break
    }
    "2" {
        Write-Host "正在启动青龙 LoRA 训练器..." -ForegroundColor Cyan
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; . '.\4、run_npmgui.ps1'"
        Start-Sleep -Seconds 5
        Start-Process "http://localhost:3000"
        Write-Host "青龙 LoRA 训练器已启动，浏览器已打开！" -ForegroundColor Green
        break
    }
    "3" {
        Write-Host "退出启动器..." -ForegroundColor Cyan
        exit
        break
    }
    default {
        Write-Host "无效选项，请重新选择" -ForegroundColor Red
        break
    }
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Cyan
pause
