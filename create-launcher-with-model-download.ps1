# 创建包含模型下载功能的启动器EXE
# 版本号基于当前时间

# 获取当前时间作为版本号
$version = Get-Date -Format "yyyy.MM.dd.HHmm"
$exeName = "ACE-Step-Launcher-v$version.exe"

Write-Host "开始创建启动器 EXE: $exeName" -ForegroundColor Green
Write-Host "版本号: $version" -ForegroundColor Green

# 检查是否安装了 pyinstaller
Write-Host "检查 pyinstaller..." -ForegroundColor Yellow
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "正在安装 pyinstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# 检查是否安装了 PyQt6
Write-Host "检查 PyQt6..." -ForegroundColor Yellow
if (-not (pip list | Select-String -Pattern "PyQt6")) {
    Write-Host "正在安装 PyQt6..." -ForegroundColor Yellow
    pip install PyQt6
}

# 检查是否安装了 psutil
Write-Host "检查 psutil..." -ForegroundColor Yellow
if (-not (pip list | Select-String -Pattern "psutil")) {
    Write-Host "正在安装 psutil..." -ForegroundColor Yellow
    pip install psutil
}

# 检查是否安装了 Pillow (用于图标处理)
Write-Host "检查 Pillow..." -ForegroundColor Yellow
if (-not (pip list | Select-String -Pattern "Pillow")) {
    Write-Host "正在安装 Pillow..." -ForegroundColor Yellow
    pip install Pillow
}

# 检查是否安装了 model_downloader 所需的依赖
Write-Host "检查模型下载依赖..." -ForegroundColor Yellow
if (-not (pip list | Select-String -Pattern "huggingface_hub")) {
    Write-Host "正在安装 huggingface_hub..." -ForegroundColor Yellow
    pip install huggingface_hub
}

if (-not (pip list | Select-String -Pattern "modelscope")) {
    Write-Host "正在安装 modelscope..." -ForegroundColor Yellow
    pip install modelscope
}

# 切换到launcher目录执行构建
Write-Host "切换到launcher目录..." -ForegroundColor Yellow
$launcherDir = "launcher"

# 构建命令 - 使用与build.py相同的参数
$pyinstallerCmd = "pyinstaller --name '$exeName' --onefile --windowed --add-data '../2、run_gradio.ps1;.' --add-data '../3、run_server.ps1;.' --add-data '../4、run_npmgui.ps1;.' --add-data '../ico.png;.' --clean --noconfirm --hidden-import PyQt6.sip --hidden-import psutil --hidden-import loguru --icon 'icon.ico' main.py"

Write-Host "执行封装命令..." -ForegroundColor Yellow
Write-Host $pyinstallerCmd -ForegroundColor Cyan

# 执行封装
try {
    Push-Location $launcherDir
    Invoke-Expression $pyinstallerCmd
    Pop-Location
} catch {
    Write-Host "执行命令时出错: $_" -ForegroundColor Red
    Pop-Location
}

# 检查结果
if (Test-Path "launcher\dist\$exeName") {
    Write-Host "封装成功！" -ForegroundColor Green
    Write-Host "EXE 文件位置: launcher\dist\$exeName" -ForegroundColor Green
    
    # 复制到根目录
    Copy-Item "launcher\dist\$exeName" ".\" -Force
    Write-Host "已复制到根目录: .\$exeName" -ForegroundColor Green
    
    # 清理临时文件
    Write-Host "清理临时文件..." -ForegroundColor Yellow
    Remove-Item "launcher\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "launcher\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "launcher\$exeName.spec" -Force -ErrorAction SilentlyContinue
    Remove-Item "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "acestep\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host "封装完成！" -ForegroundColor Green
} else {
    Write-Host "封装失败！" -ForegroundColor Red
    Write-Host "请检查错误信息。" -ForegroundColor Red
}
