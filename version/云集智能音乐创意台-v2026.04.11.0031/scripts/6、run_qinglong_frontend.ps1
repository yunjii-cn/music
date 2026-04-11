# Navigate to UI directory and start frontend
# 进入 UI 目录并启动前端
# 使用脚本所在目录的父目录（dist 根目录）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location "$RootDir\ace-step-ui"

# 查找 npm 命令的完整路径
# 首先检查便携版 Node.js（优先使用 Node.js 24）
$portableNode24Dir = "$RootDir\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64"
$portableNode22Dir = "$RootDir\tools\node-v22.22.2-win-x64\node-v22.22.2-win-x64"
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

Write-Output "Starting ACE-Step UI Frontend..."

# 检查依赖是否安装
if (-not (Test-Path "node_modules")) {
    Write-Error "Error: Dependencies not installed!"
    Write-Error "Please run setup.bat first."
    exit 1
}

Write-Output "Starting frontend server..."
& $npmCmd run dev

Write-Output "Frontend server stopped"
