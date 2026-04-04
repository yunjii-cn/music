# Navigate to UI directory and run setup
# 进入 UI 目录并运行安装脚本
# 使用脚本所在目录的绝对路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\ace-step-ui"

# 查找 npm 命令的完整路径
$nodePath = Get-Command node -ErrorAction SilentlyContinue
if ($nodePath) {
    $nodeDir = Split-Path -Parent $nodePath.Path
    $npmCmd = "$nodeDir\npm.cmd"
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

# 启动后端服务
Write-Output "Starting backend server..."
try {
    # 在后台启动后端服务
    $backendProcess = Start-Process $npmCmd -ArgumentList "run dev" -WorkingDirectory "server" -NoNewWindow -PassThru
    Write-Output "Backend server started with PID: $($backendProcess.Id)"
} catch {
    Write-Error "Failed to start backend server: $_"
    exit 1
}

# 等待后端启动
Write-Output "Waiting for backend to start..."
Start-Sleep -Seconds 3

# 启动前端服务
Write-Output "Starting frontend..."
try {
    # 在后台启动前端服务
    $frontendProcess = Start-Process $npmCmd -ArgumentList "run dev" -NoNewWindow -PassThru
    Write-Output "Frontend started with PID: $($frontendProcess.Id)"
} catch {
    Write-Error "Failed to start frontend: $_"
    # 停止后端服务
    if ($backendProcess) {
        $backendProcess.Kill()
    }
    exit 1
}

# 等待前端启动
Start-Sleep -Seconds 2

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
        $frontendProcess.Kill()
    }
    if ($backendProcess) {
        $backendProcess.Kill()
    }
    Write-Output "Services stopped"
}
