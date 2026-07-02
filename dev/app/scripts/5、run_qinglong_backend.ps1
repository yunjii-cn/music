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

$portableNode24Dir = "$DataDir\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64"
$portableNode22Dir = "$DataDir\nodejs\node-v22.14.0-win-x64"
$nodePath = Get-Command node -ErrorAction SilentlyContinue
if ($nodePath) {
    $nodeDir = Split-Path -Parent $nodePath.Path
    $npmCmd = "$nodeDir\npm.cmd"
} elseif (Test-Path "$portableNode24Dir\node.exe") {
    # 使用便携版 Node.js 24
    Write-Output "Using portable Node.js: $portableNode24Dir"
    $npmCmd = "$portableNode24Dir\npm.cmd"
    # 将便携版 Node.js 添加到 PATH，确保子进程也能找到
    $env:PATH = "$portableNode24Dir;$env:PATH"
} elseif (Test-Path "$portableNode22Dir\node.exe") {
    # 使用便携版 Node.js 22
    Write-Output "Using portable Node.js: $portableNode22Dir"
    $npmCmd = "$portableNode22Dir\npm.cmd"
    # 将便携版 Node.js 添加到 PATH，确保子进程也能找到
    $env:PATH = "$portableNode22Dir;$env:PATH"
} else {
    # 如果找不到 node，尝试使用系统路径中的 npm
    $npmCmd = "npm"
}

# 设置 Python 环境变量，使用 uv 虚拟环境中的 Python 用于编译 better-sqlite3
$venvPython = "$DataDir\.venv\Scripts\python.exe"
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
