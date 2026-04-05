# Require PowerShell 5.1 or higher
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

Write-Output ""
Write-Output "============================================================"
Write-Output "  云集智能音乐创意台 - 环境安装脚本"
Write-Output "============================================================"
Write-Output ""

# Function to check last command and exit on failure
function Check {
    param([string]$Message)
    if ($LASTEXITCODE -ne 0) {
        Write-Output $Message
        Write-Output "Install failed|安装失败。"
        exit 1
    }
}

# Step 1: Install uv
Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 1: 安装 UV"
Write-Output "============================================================"
Write-Output ""

if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Output "Downloading UV..."
    irm https://astral.sh/uv/install.ps1 | iex
    Check "❌ 下载 UV 失败"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")
}
uv --version
Write-Output "✅ UV 已安装."

# Step 2: Check disk space
Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 2: 检查磁盘空间"
Write-Output "============================================================"
Write-Output ""

# Check UV cache directory
$uv_cache_dir = "$env:LOCALAPPDATA\uv\cache"
if (-not (Test-Path $uv_cache_dir)) {
    New-Item -ItemType Directory -Path $uv_cache_dir -Force | Out-Null
    Write-Output "✅ UV缓存目录已创建"
} else {
    Write-Output "✅ UV缓存目录已存在"
}

# Step 3: Create/Activate virtual environment
Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 3: 创建/激活虚拟环境"
Write-Output "============================================================"
Write-Output ""

$venv_dir = ".venv"
$venv_activate = "$venv_dir\Scripts\Activate.ps1"

if (Test-Path $venv_activate) {
    Write-Output "✅ 使用现有虚拟环境 (.venv)"
    . $venv_activate
} else {
    Write-Output "📦 创建新虚拟环境 (.venv)"
    ~/.local/bin/uv venv -p 3.12 --seed
    . $venv_activate
}

# Step 4: Install dependencies
Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 4: 安装依赖"
Write-Output "============================================================"
Write-Output ""

Write-Output "📦 安装基础依赖..."
Write-Output "   正在安装 wheel_stub, psutil 等..."
~/.local/bin/uv pip install --upgrade wheel_stub psutil hatchling editables
Check "❌ 安装基础依赖失败"

Write-Output ""
Write-Output "📦 安装 PyTorch 生态系统..."
Write-Output "   正在安装 torch, torchvision, torchaudio (CUDA 12.8)..."
~/.local/bin/uv pip install torch==2.9.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
Check "❌ PyTorch 安装失败"
Write-Output "✅ PyTorch 生态系统安装完成"

Write-Output ""
Write-Output "📦 安装项目依赖..."
Write-Output "   正在安装 transformers, diffusers, gradio 等核心依赖..."
~/.local/bin/uv pip install transformers diffusers gradio matplotlib scipy soundfile loguru einops accelerate fastapi diskcache uvicorn numba vector-quantize-pytorch toml peft lycoris-lora lightning tensorboard modelscope typer-slim
if ($LASTEXITCODE -eq 0) {
    Write-Output "✅ 项目依赖安装完成"
}

Write-Output ""
Write-Output "============================================================"
Write-Output "  环境安装完成！"
Write-Output "============================================================"
Write-Output ""
Write-Output "✅ 虚拟环境位置: $venv_dir/"
Write-Output "✅ Python版本: $(python --version)"
Write-Output ""
Write-Output "下一步："
Write-Output "1. 运行软件启动服务"
Write-Output "2. 在部署维护中下载所需模型"
