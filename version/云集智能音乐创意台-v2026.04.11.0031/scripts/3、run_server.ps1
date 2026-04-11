
# ============= Command Line Parameters | 命令行参数 =====================
param(
  [int]$Port = 8001,                          # Server port
  [string]$ServerHost = "127.0.0.1"                 # Server host
)

# ============= DO NOT MODIFY CONTENTS BELOW | 请勿修改下方内容 =====================
# Set environment variables - 工作目录设为脚本父目录（项目根目录）
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONPATH = "$(Split-Path $PSScriptRoot -Parent)$([System.IO.Path]::PathSeparator)$($env:PYTHONPATH)"

$Env:HF_HOME = "huggingface"
$Env:XFORMERS_FORCE_DISABLE_TRITON = "1"
$Env:HF_ENDPOINT = "https://hf-mirror.com"
$Env:PILLOW_IGNORE_XMP_DATA_IS_TOO_LONG = "1"
$Env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
$Env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu128"
$Env:UV_CACHE_DIR = "${env:LOCALAPPDATA}/uv/cache"
$Env:UV_NO_BUILD_ISOLATION = "1"
$Env:UV_NO_CACHE = "0"
$Env:UV_LINK_MODE = "symlink"
$Env:UV_INDEX_STRATEGY = "unsafe-best-match"
$Env:ACESTEP_NO_INIT = "true"
#$Env:CUDA_VISIBLE_DEVICES = "1"  # 设置GPU id，0表示使用第一个GPU，-1表示不使用GPU

#$Env:HTTP_PROXY = "http://127.0.0.1:7890"
#$Env:HTTPS_PROXY = "http://127.0.0.1:7890"

$ext_args = [System.Collections.ArrayList]::new()

# ============= Build Arguments | 构建参数 =====================
# Server configuration
[void]$ext_args.Add("--port")
[void]$ext_args.Add($Port)
[void]$ext_args.Add("--host")
[void]$ext_args.Add($ServerHost)

# Directly use virtual environment python to avoid uv pyproject.toml checks
$venv_dir = "scripts\.venv"
$python_exe = Join-Path $venv_dir "Scripts\python.exe"

if (-not (Test-Path $python_exe)) {
    Write-Error "Virtual environment not found at $venv_dir. Please run deployment maintenance first."
    exit 1
}

Write-Output "Starting API server..."
Write-Output "Python path: $env:PYTHONPATH"
Write-Output "Working directory: $(Get-Location)"
Write-Output "Using Python: $python_exe"
Write-Output "Venv dir: $venv_dir"

# First test if we can import the necessary modules
Write-Output "Testing imports..."
try {
    Write-Output "Testing loguru..."
    & $python_exe -c "import loguru; print('✓ Loguru: OK')"
} catch {
    Write-Output "Loguru test failed, but continuing..."
}

# Run API server directly with virtual environment python
Write-Output "Starting API server..."
& $python_exe acestep/api_server.py $ext_args

Write-Output "Start finished"
