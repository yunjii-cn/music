# Require PowerShell 5.1 or higher
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# 切换到脚本所在目录，确保所有操作都在 scripts/ 目录下进行
Set-Location $PSScriptRoot
$data_dir = Join-Path $PSScriptRoot "..\..\data"

Write-Output ""
Write-Output "============================================================"
Write-Output "  云集智能音乐创意台 - 环境安装脚本"
Write-Output "============================================================"
Write-Output ""
Write-Output "📂 工作目录: $PWD"
Write-Output ""

Write-Output "🔧 配置国内镜像源..."
$Env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
$Env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu128"
$Env:UV_CACHE_DIR = Join-Path $data_dir ".uv_cache"
$Env:HF_HOME = Join-Path $data_dir "huggingface"
# 以下变量原由 install-uv-qinglong.ps1 设置，合并保留（中国镜像 / CUDA / LFS 友好）
$Env:HF_ENDPOINT = "https://hf-mirror.com"
$Env:PIP_DISABLE_IP_VERSION_CHECK = "1"
$Env:GIT_LFS_SKIP_SMUDGE = "1"
if ($env:CUDA_PATH) { $Env:CUDA_HOME = $env:CUDA_PATH }
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

# 虚拟环境统一建在 scripts\.venv（与 main.py 的 find_venv_python / 各处检查一致）。
# 历史坑：曾建在 ..\..\data\.venv，而 main.py 全程找 scripts\.venv，两者永不相交，
# 导致每次都判"环境未安装"并重复跑十几分钟的安装。切勿再改回 data\.venv。
$venv_dir = Join-Path $PSScriptRoot ".venv"
$venv_activate = Join-Path $venv_dir "Scripts\Activate.ps1"

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
    Write-Output "📦 创建新虚拟环境 (scripts\.venv)"
    ~/.local/bin/uv venv -p 3.12 --seed $venv_dir
    . $venv_activate
} else {
    Write-Output "✅ 使用现有虚拟环境 (scripts\.venv)"
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
Write-Output "   正在安装 torch 2.9.0, torchaudio 2.9.0 (CUDA 12.8)..."
~/.local/bin/uv pip install torch==2.9.0 torchaudio==2.9.0
Check "❌ PyTorch 安装失败"
Write-Output "✅ PyTorch 生态系统安装完成"

Write-Output ""
Write-Output "📦 安装项目依赖..."
Write-Output "   正在安装 transformers, diffusers, gradio 等���心依赖..."
Write-Output "   ⚠ 锁定 transformers<4.58.0 避免版本不兼容降级"
~/.local/bin/uv pip install "transformers>=4.51.0,<4.58.0" diffusers gradio matplotlib scipy soundfile loguru einops accelerate fastapi diskcache uvicorn numba peft lycoris-lora lightning tensorboard modelscope huggingface_hub safetensors vector-quantize-pytorch
if ($LASTEXITCODE -eq 0) {
    Write-Output "✅ 项目依赖安装完成"
}

Write-Output ""
Write-Output "📦 安装 flash_attn (性能优化，仅 NVIDIA 显卡加速)..."
$flash_attn_wheel = "flash_attn-2.8.3+cu128torch2.9.0cxx11abiTRUE-cp312-cp312-win_amd64.whl"
$flash_attn_path = Join-Path $PSScriptRoot $flash_attn_wheel

# 候选下载源：GitHub 官方 + 国内可达镜像（ghproxy.net / mirror.ghproxy.com）
# 安装时自动竞速：先探测各源首字节延迟，选最快可达源；失败自动顺延下一个。
# 注：码云镜像待上传后，把对应 raw 地址追加进下方 $candidates 即可，竞速会自动纳入。
$FA_BASE = $flash_attn_wheel
$candidates = @(
    "https://ghproxy.net/https://github.com/yunjii-cn/music/releases/download/wheels/$FA_BASE",
    "https://mirror.ghproxy.com/https://github.com/yunjii-cn/music/releases/download/wheels/$FA_BASE",
    "https://github.com/yunjii-cn/music/releases/download/wheels/$FA_BASE"
)

# ---- GPU 门控：仅 NVIDIA 且算力 >= SM75 (7.5) 才下载/安装 flash_attn ----
$supportsFA = $false
$faReason = ""
try {
    $smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($smi) {
        $gpuInfo = & nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader,nounits 2>$null
        if ($LASTEXITCODE -eq 0 -and $gpuInfo) {
            $line = ($gpuInfo -split "`n")[0]
            $parts = $line -split ","
            $gpuName = $parts[0].Trim()
            $capStr = $parts[-1].Trim()
            if ($capStr -match '^(\d+)\.(\d+)$') {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                $cap = $major + $minor / 10.0
                if ($cap -ge 7.5) {
                    $supportsFA = $true
                    Write-Output "  ✅ 检测到兼容显卡: $gpuName (算力 $($cap.ToString('0.0')))"
                } else {
                    $faReason = "当前显卡 $gpuName 算力 $($cap.ToString('0.0')) 低于 SM75(7.5)，不支持 Flash Attention"
                }
            } else {
                $faReason = "无法解析显卡算力: $capStr"
            }
        } else {
            $faReason = "nvidia-smi 未返回显卡信息"
        }
    } else {
        $faReason = "未检测到 NVIDIA 显卡驱动 (nvidia-smi 不存在)"
    }
} catch {
    $supportsFA = $true   # 探测异常时保守允许尝试
    $faReason = "显卡探测异常: $_（仍尝试安装）"
}

function Get-FastestMirror {
    param([string[]]$Urls)
    $ranked = @()
    foreach ($u in $Urls) {
        try {
            $out = & curl.exe -s -m 8 -o NUL -r 0-0 -w "%{time_starttransfer}" $u 2>$null
            if ($LASTEXITCODE -eq 0 -and $out -match '^[0-9]') {
                $t = [double]::Parse($out, [System.Globalization.CultureInfo]::InvariantCulture)
                $ranked += [PSCustomObject]@{Url=$u; T=$t}
            }
        } catch {}
    }
    # 若探测全部失败（如 curl 不支持 -r），退回原始顺序
    if ($ranked.Count -eq 0) {
        foreach ($u in $Urls) { $ranked += [PSCustomObject]@{Url=$u; T=0} }
    }
    return ($ranked | Sort-Object T | ForEach-Object { $_.Url })
}

if (-not $supportsFA) {
    Write-Warning "⚠️ $faReason"
    Write-Output "   跳过 flash_attn 安装，将使用标准推理（SDPA / eager attention，速度略慢但不影响功能）"
    Write-Output "   如需 Flash Attention 加速，请使用 NVIDIA RTX 20/30/40 系及以上显卡，并确保驱动支持 CUDA 12.8"
}
if ($supportsFA -and -not (Test-Path $flash_attn_path)) {
    Write-Output "  本地 wheel 不存在，开始竞速选择最快下载源..."
    $ordered = Get-FastestMirror $candidates
    $downloaded = $false
    foreach ($u in $ordered) {
        try {
            Write-Output "  🏁 尝试源: $u"
            $temp_wheel = Join-Path $env:TEMP $flash_attn_wheel
            & curl.exe -L -m 600 -o "$temp_wheel" "$u" 2>$null
            if ((Test-Path $temp_wheel) -and ((Get-Item $temp_wheel).Length -gt 1MB)) {
                Move-Item $temp_wheel $flash_attn_path -Force
                $downloaded = $true
                Write-Output "  ✅ 下载完成 (源: $u)"
                break
            }
        } catch {
            Write-Warning "  ⚠️ 该源下载失败，尝试下一个"
        }
    }
    if (-not $downloaded -and (Get-Command "bitsadmin" -ErrorAction SilentlyContinue)) {
        Write-Output "  curl 全部失败，bitsadmin 兜底..."
        foreach ($u in $ordered) {
            bitsadmin /transfer "flash_attn_dl" /download /priority high $u $flash_attn_path 2>$null
            if ((Test-Path $flash_attn_path) -and ((Get-Item $flash_attn_path).Length -gt 1MB)) {
                $downloaded = $true
                Write-Output "  ✅ 下载完成 (bitsadmin)"
                break
            }
        }
    }
    if (-not $downloaded) {
        Write-Warning "⚠️ 无法下载 flash_attn wheel，跳过安装（不影响核心功能）"
    }
}
if ($supportsFA -and (Test-Path $flash_attn_path)) {
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
