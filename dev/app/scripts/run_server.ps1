
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

# 展平参数：Start-Process -ArgumentList 只接受 string[]，不能直接塞 ArrayList（否则 PowerShell 5.1
# 报 Cannot convert 'System.Collections.ArrayList' to 'System.String'，进程根本不启动）
$apiArgs = @("acestep/api_server.py")
foreach ($a in $ext_args) { $apiArgs += [string]$a }

# Directly use virtual environment python to avoid uv pyproject.toml checks
# 统一使用 scripts/.venv（与 install-env.ps1 / main.py 保持一致）
$venv_dir = Join-Path $PSScriptRoot ".venv"
$python_exe = Join-Path $venv_dir "Scripts\python.exe"
# pythonw.exe 是无控制台窗口版本：用它启动服务，彻底避免弹出可见的 python.exe 控制台窗口。
# 根因：本脚本由主程序 `powershell -WindowStyle Hidden` 拉起（powershell 自身已隐藏），
# 但里面的 python.exe 是控制台子系统程序，Windows 仍会为它单独分配一个可见控制台——
# 这正是"起服务/打开软件更新时弹出一连串 Python 窗口"的真正来源。
$pythonw_exe = Join-Path $venv_dir "Scripts\pythonw.exe"
if (-not (Test-Path $pythonw_exe)) { $pythonw_exe = $python_exe }

if (-not (Test-Path $python_exe)) {
    Write-Error "Virtual environment not found at $venv_dir. Please run deployment maintenance first."
    exit 1
}

Write-Output "Starting API server..."
Write-Output "Python path: $env:PYTHONPATH"
Write-Output "Working directory: $(Get-Location)"
Write-Output "Using Python: $pythonw_exe"

# First test if we can import the necessary modules（pythonw 无控制台，静默测试）
Write-Output "Testing imports..."
try {
    Write-Output "Testing loguru..."
    & $pythonw_exe -c "import loguru; print('✓ Loguru: OK')" 2>$null
} catch {
    Write-Output "Loguru test failed, but continuing..."
}

# Run API server with pythonw（无控制台窗口）。输出写入日志文件后由 Get-Content -Wait
# 实时回显到 stdout（主程序通过管道捕获），既隐藏控制台、又不丢服务日志。
Write-Output "Starting API server..."

if ($LogFile -ne "") {
    # Robust logging:
    #   - stdout 实时回显给主程序管道（主程序已记录），
    #   - stderr 单独落 api_server_stderr.log 供崩溃诊断。
    # 沿用原设计：避免 `| Tee-Object`（加载 4B LLM 时内存压力下管道拆卸可能抛
    # "Insufficient system resources"，掩盖真实 traceback）。
    $logDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $errLog = Join-Path $logDir "api_server_stderr.log"
    Start-Process -FilePath $pythonw_exe -ArgumentList $apiArgs `
        -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $errLog -PassThru | Out-Null
    Start-Sleep -Milliseconds 300
    Get-Content -Path $LogFile -Wait
} else {
    $logDir = Join-Path $env:TEMP "yunji_logs"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $logFile = Join-Path $logDir "api_server.log"
    Start-Process -FilePath $pythonw_exe -ArgumentList $apiArgs `
        -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru | Out-Null
    Start-Sleep -Milliseconds 300
    Get-Content -Path $logFile -Wait
}

Write-Output "Start finished"
