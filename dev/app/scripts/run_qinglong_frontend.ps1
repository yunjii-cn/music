# Navigate to UI directory and start frontend
# 进入 UI 目录并启动前端
# 使用脚本所在目录的父目录（dist 根目录）
param(
  [int]$Port = 3000,
  [int]$BackendPort = 3001
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$DataDir = Split-Path -Parent $RootDir | Join-Path -ChildPath "data"
Set-Location "$RootDir\ace-step-ui"

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

Write-Output "Using npm: $npmCmd"

# 设置端口环境变量
$env:VITE_PORT = "$Port"
$env:BACKEND_URL = "http://127.0.0.1:$BackendPort"
Write-Output "Frontend port: $Port"
Write-Output "Backend URL: $env:BACKEND_URL"

Write-Output "Starting ACE-Step UI Frontend..."

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

Write-Output "Starting frontend server..."
& $npmCmd run dev

Write-Output "Frontend server stopped"
