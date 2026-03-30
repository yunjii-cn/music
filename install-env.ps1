Set-Location $PSScriptRoot

$Env:HF_HOME = "huggingface"
$Env:HF_ENDPOINT = "https://hf-mirror.com"
$Env:PIP_DISABLE_PIP_VERSION_CHECK = 1
$Env:PIP_NO_CACHE_DIR = 1
$Env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
$Env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu128"
$Env:UV_CACHE_DIR = "${env:LOCALAPPDATA}/uv/cache"
$Env:UV_NO_BUILD_ISOLATION = "1"
$Env:UV_NO_CACHE = "0"
$Env:UV_LINK_MODE = "symlink"
$Env:GIT_LFS_SKIP_SMUDGE = 1

function InstallFail {
    Write-Output "Install failed|安装失败。"
    Read-Host | Out-Null 
    Exit
}

function Check {
    param (
        $ErrorInfo
    )
    if (!($?)) {
        Write-Output $ErrorInfo
        InstallFail
    }
}

Write-Output "============================================================"
Write-Output "  云集智能音乐创意台 - 环境安装脚本"
Write-Output "============================================================"
Write-Output ""

$tools_dir = Join-Path $PSScriptRoot "tools"
$python_downloader = Join-Path $PSScriptRoot "download_python_312.py"
$python_dir = Join-Path $tools_dir "python"
$python_exe = $null

Write-Output "============================================================"
Write-Output "  步骤 1: 下载 Python 3.12 便携版"
Write-Output "============================================================"
Write-Output ""

if (Test-Path $python_downloader) {
    Write-Output "📦 使用 Python 3.12 便携版..."
    
    $python_download_result = & python $python_downloader --download-dir $python_dir 2>&1
    
    Write-Output $python_download_result
    
    $python_path_line = $python_download_result | Where-Object { $_ -match "^PYTHON_PATH=(.*)" }
    
    if ($python_path_line) {
        $python_exe = $matches[1]
        Write-Output ""
        Write-Output "✅ Python 3.12 便携版已就绪: $python_exe"
    }
    else {
        Write-Warning "⚠️ 未能解析 Python 路径，尝试使用系统 Python"
    }
}
else {
    Write-Warning "⚠️ 未找到 download_python_312.py，使用系统 Python"
}

Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 2: 安装 UV"
Write-Output "============================================================"
Write-Output ""

try {
    ~/.local/bin/uv --version
    Write-Output "✅ UV模块已安装."
}
catch {
    Write-Output "📦 正在安装UV模块中..."
    if ($Env:OS -ilike "*windows*") {
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        Check "❌ 安装UV模块失败。"
    }
    else {
        curl -LsSf https://astral.sh/uv/install.sh | sh
        Check "❌ 安装UV模块失败。"
    }
}

Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 3: 检查磁盘空间"
Write-Output "============================================================"
if ($env:OS -ilike "*windows*") {
    chcp 65001 | Out-Null
    if (Test-Path -Path "${env:LOCALAPPDATA}/uv/cache") {
        Write-Host "✅ UV缓存目录已存在"
    }
    else {
        try {
            $CDrive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction Stop
            if ($CDrive) {
                $FreeSpaceGB = [math]::Round($CDrive.FreeSpace / 1GB, 2)
                Write-Host "C: 盘剩余空间: ${FreeSpaceGB}GB"
                
                if ($FreeSpaceGB -lt 10) {
                    Write-Host "⚠️ 检测到磁盘空间不足，使用本地缓存目录"
                    $Env:UV_CACHE_DIR = ".cache"
                } 
            }
            else {
                Write-Warning "⚠️ 未找到C: 盘，使用本地缓存目录"
                $Env:UV_CACHE_DIR = ".cache"
            }
        }
        catch {
            Write-Warning "⚠️ 检查磁盘空间失败，使用本地缓存目录"
            $Env:UV_CACHE_DIR = ".cache"
        }
    }
}

Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 4: 创建/激活虚拟环境"
Write-Output "============================================================"

$venv_dir = Join-Path $PSScriptRoot ".venv"
$venv_activate = Join-Path $venv_dir "Scripts\Activate.ps1"

if (Test-Path $venv_activate) {
    Write-Output "✅ 使用现有虚拟环境 (.venv)"
    . $venv_activate
}
else {
    Write-Output "📦 创建新虚拟环境 (.venv)"
    
    if ($python_exe -and (Test-Path $python_exe)) {
        Write-Output "   使用 Python 3.12 便携版: $python_exe"
        ~/.local/bin/uv venv --python $python_exe --seed
    }
    else {
        Write-Output "   使用系统 Python 3.12"
        ~/.local/bin/uv venv -p 3.12 --seed
    }
    
    . $venv_activate
}

Write-Output ""
Write-Output "============================================================"
Write-Output "  步骤 5: 安装依赖"
Write-Output "============================================================"
Write-Output "📦 安装基础依赖..."
~/.local/bin/uv pip install --upgrade wheel_stub torch==2.9.0 psutil hatchling editables
Check "❌ 安装基础依赖失败"

Write-Output "📦 安装项目依赖..."
if (Test-Path "requirements.txt") {
    ~/.local/bin/uv pip install -r requirements.txt --index-strategy unsafe-best-match
    Check "❌ 安装项目依赖失败"
} else {
    Write-Warning "⚠️ 未找到 requirements.txt，跳过"
}

Write-Output ""
Write-Output "============================================================"
Write-Output "  环境安装完成！"
Write-Output "============================================================"
Write-Output ""
Write-Output "✅ 虚拟环境位置: .venv/"
Write-Output "✅ Python版本: $(python --version)"
if ($python_exe) {
    Write-Output "✅ Python来源: 便携版"
} else {
    Write-Output "✅ Python来源: 系统"
}
Write-Output ""
Write-Output "下一步："
Write-Output "  1. 运行软件启动服务"
Write-Output "  2. 在部署维护中下载所需模型"
Write-Output ""
Read-Host "按回车键退出" | Out-Null 
