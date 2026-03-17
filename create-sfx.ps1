#!/usr/bin/env powershell
# 创建自解压的 ACE-Step 启动器

Write-Host "正在创建 ACE-Step 启动器 EXE 文件..." -ForegroundColor Green

# 获取当前目录
$currentDir = Get-Location

# 创建临时目录
$tempDir = "$env:TEMP\ace-step-build"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# 复制必要的文件到临时目录
Write-Host "复制必要的文件..." -ForegroundColor Cyan
Copy-Item -Path "$currentDir\launch-ace-step.ps1" -Destination $tempDir
Copy-Item -Path "$currentDir\1、install-uv-qinglong.ps1" -Destination $tempDir
Copy-Item -Path "$currentDir\2、run_gradio.ps1" -Destination $tempDir
Copy-Item -Path "$currentDir\3、run_server.ps1" -Destination $tempDir
Copy-Item -Path "$currentDir\4、run_npmgui.ps1" -Destination $tempDir

# 创建启动脚本
$launchScript = @"
@echo off

:: ACE-Step 启动器
:: 自解压启动脚本

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File launch-ace-step.ps1
"@

$launchScript | Out-File -FilePath "$tempDir\start.bat" -Encoding UTF8

# 创建自解压的 EXE 文件
Write-Host "创建自解压 EXE 文件..." -ForegroundColor Cyan

# 使用 IExpress 创建自解压 EXE
$iexpressConfig = @"
[Version]
Class=IEXPRESS
SEDVersion=3.00
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=ACE-Step 启动器
DisplayLicense=
FinishMessage=ACE-Step 启动器已启动！
TargetName=$currentDir\ACE-Step-Launcher.exe
FriendlyName=ACE-Step 启动器
AppLaunched=cmd.exe /c start.bat
PostInstallCmd=
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=SourceFiles
[Strings]
[SourceFiles]
SourceFiles0=$tempDir\
[SourceFiles0]
start.bat
launch-ace-step.ps1
1、install-uv-qinglong.ps1
2、run_gradio.ps1
3、run_server.ps1
4、run_npmgui.ps1
"@

$iexpressConfig | Out-File -FilePath "$tempDir\iexpress.sed" -Encoding UTF8

# 运行 IExpress
Write-Host "运行 IExpress 创建 EXE 文件..." -ForegroundColor Cyan
Start-Process -FilePath "iexpress.exe" -ArgumentList "/N", "/Q", "$tempDir\iexpress.sed" -Wait

# 清理临时文件
Write-Host "清理临时文件..." -ForegroundColor Cyan
Remove-Item -Recurse -Force $tempDir

# 检查 EXE 文件是否创建成功
if (Test-Path "$currentDir\ACE-Step-Launcher.exe") {
    Write-Host "ACE-Step-Launcher.exe 创建成功！" -ForegroundColor Green
    Write-Host "文件位置：$currentDir\ACE-Step-Launcher.exe" -ForegroundColor Yellow
} else {
    Write-Host "ACE-Step-Launcher.exe 创建失败！" -ForegroundColor Red
}
