Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Output "============================================================"
Write-Output "  云集智能音乐创意台 - 启动脚本"
Write-Output "============================================================"
Write-Output ""

$dataVenv = Join-Path (Split-Path $PSScriptRoot -Parent) "..\data\.venv"
if (Test-Path "$dataVenv\Scripts\activate") {
    Write-Output "✅ 激活虚拟环境..."
    . "$dataVenv\Scripts\activate"
} else {
    Write-Warning "⚠️ 未找到虚拟环境，请先运行 install-env.ps1"
    Read-Host "按回车键退出" | Out-Null
    Exit
}

Write-Output "🚀 启动云集智能音乐创意台..."
Write-Output ""

python main.py

Write-Output ""
Write-Output "软件已退出"
Read-Host "按回车键退出" | Out-Null 
