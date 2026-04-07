# Navigate to UI directory and run setup
# 进入 UI 目录并运行安装脚本
# 使用脚本所在目录的绝对路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 修复路径问题：ace-step-ui 在 scripts 的父目录（即 dist/）下
$ParentDir = Split-Path -Parent $ScriptDir
Set-Location "$ParentDir\ace-step-ui"

# 查找 npm 命令的完整路径
# 首先检查便携版 Node.js（优先使用 Node.js 24）
$portableNode24Dir = "$ScriptDir\node-v24.14.1-win-x64\node-v24.14.1-win-x64"
$portableNode22Dir = "$ScriptDir\node-v22.22.2-win-x64\node-v22.22.2-win-x64"
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

Write-Output "Starting ACE-Step UI..."

# 检查依赖是否安装
if (-not (Test-Path "node_modules")) {
    Write-Error "Error: Dependencies not installed!"
    Write-Error "Please run setup.bat first."
    exit 1
}

if (-not (Test-Path "server\node_modules")) {
    Write-Error "Error: Server dependencies not installed!"
    Write-Error "Please run setup.bat first."
    exit 1
}

# 检查端口是否被占用
function Test-Port {
    param($port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", $port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

# 启动后端服务
Write-Output "Starting backend server..."
try {
    $backendProcess = Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "cd '$(Get-Location)\\server'; & '$npmCmd' run dev" -NoNewWindow -PassThru
    Write-Output "Backend server started with PID: $($backendProcess.Id)"
} catch {
    Write-Error "Failed to start backend server: $_"
    exit 1
}

# 等待后端启动
Write-Output "Waiting for backend to start..."
$backendReady = $false
$maxWait = 60
$waited = 0
while (-not $backendReady -and $waited -lt $maxWait) {
    if (Test-Port 3001) {
        $backendReady = $true
        Write-Output "✓ Backend server is ready!"
    } else {
        Start-Sleep -Seconds 2
        $waited += 2
    }
}

if (-not $backendReady) {
    Write-Error "Backend server failed to start within $maxWait seconds"
    if ($backendProcess) {
        try { $backendProcess.Kill() } catch {}
    }
    exit 1
}

# 启动前端服务
Write-Output "Starting frontend..."
try {
    $frontendProcess = Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "cd '$(Get-Location)'; & '$npmCmd' run dev" -NoNewWindow -PassThru
    Write-Output "Frontend started with PID: $($frontendProcess.Id)"
} catch {
    Write-Error "Failed to start frontend: $_"
    # 停止后端服务
    if ($backendProcess) {
        try { $backendProcess.Kill() } catch {}
    }
    exit 1
}

# 等待前端启动
Write-Output "Waiting for frontend to start..."
$frontendReady = $false
$maxWait = 30
$waited = 0
while (-not $frontendReady -and $waited -lt $maxWait) {
    if (Test-Port 3000) {
        $frontendReady = $true
        Write-Output "✓ Frontend is ready!"
    } else {
        Start-Sleep -Seconds 2
        $waited += 2
    }
}

Write-Output ""
Write-Output "=================================="
Write-Output "   ACE-Step UI Running!"
Write-Output "=================================="
Write-Output ""
Write-Output "   Frontend: http://localhost:3000"
Write-Output "   Backend:  http://localhost:3001"
Write-Output ""

# 浏览器由启动器统一打开，这里不自动打开

Write-Output ""
Write-Output "=================================="
Write-Output "Start finished"
Write-Output "=================================="

# 保持脚本运行，以便可以终止服务
Write-Output "Press Ctrl+C to stop all services"
try {
    # 等待用户输入
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # 停止服务
    Write-Output "Stopping services..."
    if ($frontendProcess) {
        try { $frontendProcess.Kill() } catch {}
    }
    if ($backendProcess) {
        try { $backendProcess.Kill() } catch {}
    }
    Write-Output "Services stopped"
}
