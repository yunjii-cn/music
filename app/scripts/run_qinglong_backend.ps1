# Navigate to UI directory and start backend
# 进入 UI 目录并启动后端
# 使用脚本所在目录的父目录（dist 根目录）
param(
  [int]$Port = 3001,
  [int]$ApiPort = 8001
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$DataDir = Split-Path -Parent $RootDir | Join-Path -ChildPath "data"
Set-Location "$RootDir\ace-step-ui\server"

# Node.js 优先级规则（项目硬约定，详见 project_memory.md）：
#   1. 项目便携 v24 → 2. 系统 v24 → 3. PATH 中已有（含 TRAE 内置）
# 不让 TRAE 内置 v22 抢占第一优先级，避免 better-sqlite3 ABI 不兼容。
$portableNode24Dir = "$DataDir\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64"
$systemNodeDir = "D:\Programs\nodejs"
if (Test-Path "$portableNode24Dir\node.exe") {
    Write-Output "Using portable Node.js 24: $portableNode24Dir"
    $npmCmd = "$portableNode24Dir\npm.cmd"
    $env:PATH = "$portableNode24Dir;$env:PATH"
} elseif (Test-Path "$systemNodeDir\node.exe") {
    Write-Output "Using system Node.js: $systemNodeDir"
    $npmCmd = "$systemNodeDir\npm.cmd"
    $env:PATH = "$systemNodeDir;$env:PATH"
} else {
    $nodePath = Get-Command node -ErrorAction SilentlyContinue
    if ($nodePath) {
        $nodeDir = Split-Path -Parent $nodePath.Path
        Write-Output "Using Node.js from PATH: $nodeDir"
        $npmCmd = "$nodeDir\npm.cmd"
    } else {
        $npmCmd = "npm"
    }
}

# 设置 Python 环境变量，使用 scripts/.venv 中的 Python 用于编译 better-sqlite3
# 统一使用 scripts/.venv（与 main.py 保持一致）
$venvPython = "$ScriptDir\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Output "Using Python for compilation: $venvPython"
    $env:PYTHON = $venvPython
    $env:npm_config_python = $venvPython
}

Write-Output "Using npm: $npmCmd"

# 设置端口环境变量
$env:PORT = "$Port"
$env:ACESTEP_API_URL = "http://localhost:$ApiPort"
Write-Output "Backend port: $Port"
Write-Output "API URL: $env:ACESTEP_API_URL"

Write-Output "Starting ACE-Step UI Backend..."

# 检查依赖是否安装
if (-not (Test-Path "node_modules")) {
    Write-Output "[信息] node_modules 不存在，正在自动安装依赖..."
    & $npmCmd install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[错误] 依赖安装失败！"
        exit 1
    }
    Write-Output "✓ 依赖安装完成"
}

Write-Output "Starting backend server..."
& $npmCmd run dev

Write-Output "Backend server stopped"
