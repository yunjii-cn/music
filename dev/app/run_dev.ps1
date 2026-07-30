# 开发环境启动器：用 pythonw（无控制台子系统）启动 main.py，
# 彻底消除"python main.py 自身那个可见控制台窗口"（dev 下 dll 弹窗的唯一来源）。
# 用法：双击本文件，或在 dev/app 目录执行  powershell -ExecutionPolicy Bypass -File run_dev.ps1
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 优先用项目 venv 的 pythonw，否则回退系统 pythonw
$venvPy = Join-Path $ScriptDir ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $venvPy)) { $venvPy = "pythonw.exe" }

$logOut = Join-Path $ScriptDir "dev_console.log"
$logErr = Join-Path $ScriptDir "dev_console.err"

# -WindowStyle Hidden：启动器自身也不可见；
# RedirectStandard*：把 app 的 stdout/stderr 落盘，崩溃也能查（不弹窗）。
Start-Process -FilePath $venvPy `
    -ArgumentList @("`"$ScriptDir\main.py`"") `
    -WindowStyle Hidden `
    -WorkingDirectory $ScriptDir `
    -RedirectStandardOutput $logOut `
    -RedirectStandardError $logErr
