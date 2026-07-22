
# ============= Command Line Parameters | 命令行参数 =====================
param(
  [int]$Port = 8001,                          # Server port
  [string]$ServerHost = "127.0.0.1",                 # Server host
  [string]$LogFile = ""                       # Redirect all output to this file (launcher uses this to survive uv stub exit)
)

# ============= DO NOT MODIFY CONTENTS BELOW | 请勿修改下方内容 =====================
# 修复路径问题：ace-step-ui 在 scripts 的父目录（即 dev/app/）下
# Set environment variables - 工作目录设为脚本父目录（项目根目录）
Set-Location (Split-Path $PSScriptRoot -Parent)
$project_root = Split-Path $PSScriptRoot -Parent
$data_dir = Join-Path $project_root "..\data"
$env:PYTHONPATH = "$project_root$([System.IO.Path]::PathSeparator)$($env:PYTHONPATH)"

#$Env:ACESTEP_NO_INIT = "true"  # Disabled: model now loads at startup for faster LoRA loading
$Env:HF_HOME = Join-Path $data_dir "huggingface"
$Env:XFORMERS_FORCE_DISABLE_TRITON = "1"
$Env:HF_ENDPOINT = "https://hf-mirror.com"
$Env:PILLOW_IGNORE_XMP_DATA_IS_TOO_LONG = "1"
$Env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
$Env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu128"
$Env:UV_CACHE_DIR = Join-Path $data_dir ".uv_cache"
$Env:UV_NO_BUILD_ISOLATION = "1"
$Env:UV_NO_CACHE = "0"
$Env:UV_LINK_MODE = "symlink"
$Env:UV_INDEX_STRATEGY = "unsafe-best-match"
#$Env:ACESTEP_NO_INIT = "true"  # Disabled: lazy-load was broken, now model loads at startup
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
$venv_dir = Join-Path (Split-Path $PSScriptRoot -Parent) "..\data\.venv"
$python_exe = Join-Path $venv_dir "Scripts\python.exe"

if (-not (Test-Path $python_exe)) {
    Write-Error "Virtual environment not found at $venv_dir. Please run deployment maintenance first."
    exit 1
}

Write-Output "Starting API server..."
Write-Output "Python path: $env:PYTHONPATH"
Write-Output "Working directory: $(Get-Location)"
Write-Output "Using Python: $python_exe"

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

if ($LogFile -ne "") {
    # Robust logging:
    #   - stdout streams to the launcher's pipe (the launcher already logs it),
    #   - stderr is captured to a separate file for crash diagnosis.
    # We intentionally AVOID `| Tee-Object` here. Under memory pressure (e.g. while
    # loading the 4B LLM) Tee-Object's file write can fail on pipeline teardown
    # with a spurious "out-file : Insufficient system resources" error, which masks the
    # real Python traceback that lives in api_server_stderr.log.
    $logDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $errLog = Join-Path $logDir "api_server_stderr.log"
    & $python_exe acestep/api_server.py $ext_args 2>>"$errLog"
} else {
    & $python_exe acestep/api_server.py $ext_args
}

Write-Output "Start finished"
