# Require PowerShell 5.1 or higher
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# 切换到脚本所在目录，确保所有操作都在 scripts/ 目录下进行
Set-Location $PSScriptRoot

Write-Output ""
Write-Output "============================================================"
Write-Output "  云集智能音乐创意台 - 环境安装脚本"
Write-Output "============================================================"
Write-Output ""
Write-Output "📂 工作目录: $PWD"
Write-Output ""

# 配置国内镜像源
Write-Output "🔧 配置国内镜像源..."
$Env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
$Env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu128"
$Env:UV_CACHE_DIR = "${env:LOCALAPPDATA}/uv/cache"
Write-Output "   PyPI 镜像: https://pypi.tuna.tsinghua.edu.cn/simple/"
Write-Output "   PyTorch 镜像: https://download.pytorch.org/whl/cu128"
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

# 检查现有虚拟环境的 PyTorch 版本
$needs_reinstall = $false
if (Test-Path $venv_activate) {
    Write-Output "🔍 检查现有虚拟环境..."
    . $venv_activate
    
    # 检查 PyTorch 版本
    $torch_ok = $false
    try {
        $torch_version = python -c "import torch; print(torch.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0 -and $torch_version -like "*2.9.0*") {
            Write-Output "✅ PyTorch 版本正确: $torch_version"
            $torch_ok = $true
        } else {
            Write-Warning "⚠️ PyTorch 版本不匹配: $torch_version"
        }
    } catch {
        Write-Warning "⚠️ 无法检测 PyTorch 版本"
    }
    
    # 检查 torchaudio
    $torchaudio_ok = $false
    try {
        $torchaudio_version = python -c "import torchaudio; print(torchaudio.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0 -and $torchaudio_version -like "*2.9.0*") {
            Write-Output "✅ torchaudio 版本正确: $torchaudio_version"
            $torchaudio_ok = $true
        } else {
            Write-Warning "⚠️ torchaudio 版本不匹配: $torchaudio_version"
        }
    } catch {
        Write-Warning "⚠️ 无法检测 torchaudio 版本"
    }
    
    if (-not $torch_ok -or -not $torchaudio_ok) {
        Write-Output ""
        Write-Warning "⚠️ 检测到 PyTorch 生态系统版本不匹配"
        Write-Output "   正在重新安装虚拟环境..."
        $needs_reinstall = $true
        
        # 退出虚拟环境
        deactivate
        
        # 删除旧的虚拟环境
        Write-Output "   正在删除旧的虚拟环境..."
        Remove-Item -Path $venv_dir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Output "   ✅ 旧虚拟环境已删除"
    }
}

# 创建或使用虚拟环境
if (-not (Test-Path $venv_activate)) {
    Write-Output "📦 创建新虚拟环境 (.venv)"
    ~/.local/bin/uv venv -p 3.12 --seed
    . $venv_activate
} else {
    Write-Output "✅ 使用现有虚拟环境 (.venv)"
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
Write-Output "   正在安装 torch 2.9.0, torchvision 0.24.0, torchaudio 2.9.0 (CUDA 12.8)..."
~/.local/bin/uv pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0
Check "❌ PyTorch 安装失败"
Write-Output "✅ PyTorch 生态系统安装完成"

Write-Output ""
Write-Output "📦 安装项目依赖..."
Write-Output "   正在安装 transformers, diffusers, gradio 等核心依赖..."
~/.local/bin/uv pip install transformers diffusers gradio matplotlib scipy soundfile loguru einops accelerate fastapi diskcache uvicorn numba vector-quantize-pytorch toml peft lycoris-lora lightning tensorboard modelscope typer-slim sentencepiece huggingface_hub safetensors
if ($LASTEXITCODE -eq 0) {
    Write-Output "✅ 项目依赖安装完成"
}

Write-Output ""
Write-Output "📦 安装 flash_attn (性能优化)..."
$flash_attn_wheel = "flash_attn-2.8.3+cu128torch2.9.0cxx11abiTRUE-cp312-cp312-win_amd64.whl"
$flash_attn_path = Join-Path $PSScriptRoot $flash_attn_wheel
if (Test-Path $flash_attn_path) {
    Write-Output "   正在安装 flash_attn..."
    ~/.local/bin/uv pip install $flash_attn_path
    if ($LASTEXITCODE -eq 0) {
        Write-Output "✅ flash_attn 安装完成"
    } else {
        Write-Warning "⚠️ flash_attn 安装失败，继续..."
    }
} else {
    Write-Warning "⚠️ flash_attn wheel 文件不存在: $flash_attn_wheel"
    Write-Output "   跳过 flash_attn 安装（不影响核心功能）"
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
Write-Output "1. 点击启动按钮运行服务"
Write-Output "2. 在模型管理中下载所需模型"
