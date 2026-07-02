#!/usr/bin/env powershell
# 统一启动脚本 - 同时启动API服务器和前端开发服务器

Write-Host "========================================" -ForegroundColor Green
Write-Host "ACE-Step 统一启动脚本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 获取项目根目录（scripts 的父目录）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "项目根目录: $ProjectRoot" -ForegroundColor Cyan

# 启动API服务器
Write-Host "\n[1/2] 启动 API 服务器..." -ForegroundColor Yellow
$ApiServerJob = Start-Job -ScriptBlock {
    param($Root, $ScriptDir)
    Set-Location $Root
    & "$ScriptDir\3、run_server.ps1"
} -ArgumentList $ProjectRoot, $ScriptDir

# 等待API服务器启动
Start-Sleep -Seconds 3

# 启动前端开发服务器
Write-Host "\n[2/2] 启动 前端开发服务器..." -ForegroundColor Yellow
$FrontendJob = Start-Job -ScriptBlock {
    param($Root)
    Set-Location "$Root\ace-step-ui"
    npm start
} -ArgumentList $ProjectRoot

Write-Host "\n========================================" -ForegroundColor Green
Write-Host "所有服务已启动!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "\n服务地址:" -ForegroundColor Cyan
Write-Host "API服务器: http://localhost:8001" -ForegroundColor White
Write-Host "前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "Gradio界面: http://localhost:7860" -ForegroundColor White
Write-Host "\n按任意键停止所有服务..." -ForegroundColor Yellow

# 等待用户输入
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

# 停止所有作业
Write-Host "\n停止所有服务..." -ForegroundColor Yellow
Stop-Job $ApiServerJob
Stop-Job $FrontendJob
Remove-Job $ApiServerJob
Remove-Job $FrontendJob

Write-Host "\n所有服务已停止!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
