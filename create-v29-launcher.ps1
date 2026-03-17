#!/usr/bin/env powershell
# 创建版本 29.0 的 ACE-Step 启动器

# 获取当前时间作为版本号
$version = Get-Date -Format "yyyyMMdd-HHmm"
$outputFile = "E:\AI应用\qinglong-music-trainer-2.8.3\ACE-Step-Launcher-v$version.exe"

Write-Host "正在创建版本 29.0 启动器: $outputFile" -ForegroundColor Green

# 执行 ps2exe 命令
Invoke-ps2exe -InputFile "E:\AI应用\qinglong-music-trainer-2.8.3\ace-step-launcher-v29.ps1" `
              -OutputFile $outputFile `
              -NoConsole `
              -Title "ACE-Step 启动器"

# 检查文件是否创建成功
if (Test-Path $outputFile) {
    Write-Host "启动器创建成功！" -ForegroundColor Green
    Write-Host "文件位置: $outputFile" -ForegroundColor Yellow
} else {
    Write-Host "启动器创建失败！" -ForegroundColor Red
}
