# Navigate to UI directory and run setup
# 进入 UI 目录并运行安装脚本
# 使用脚本所在目录的绝对路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 修复路径问题：ace-step-ui 在 scripts 的父目录（即 dev/app/）下
$ParentDir = Split-Path -Parent $ScriptDir
$DataDir = Join-Path (Split-Path $ParentDir -Parent) "data"
Set-Location "$ParentDir\ace-step-ui"

# Node.js 优先级规则（项目硬约定，详见 project_memory.md）：
#   1. 项目便携 v24（data/tools/node-v24.14.1...）—— 版本与 better-sqlite3
#      等原生模块的 NODE_MODULE_VERSION 严格匹配，优先级最高
#   2. 系统安装 v24（D:\Programs\nodejs）—— 用户主动安装，作为兜底
#   3. PATH 中已有的 node（含 TRAE 内置）—— 最后兜底，避免 TRAE 注入
#      的 v22 抢占优先级导致原生模块 ABI 不兼容
# 历史教训：曾因 PATH 中 TRAE 内置 v22 排在第一优先级，导致 better-sqlite3
# （用 v24 编译，NODE_MODULE_VERSION 137）在 v22（127）下无法加载。
$nodeExe = $null
$npmCmd = $null
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
        $env:PATH = "$nodeDir;$env:PATH"
    } else {
        Write-Error "Error: Node.js not found! Please install Node.js or place portable Node.js in data/tools/ directory."
        Read-Host "按回车键退出" | Out-Null
        exit 1
    }
}

Write-Output "Using npm: $npmCmd"

Write-Output "Starting ACE-Step UI..."

# 检查依赖是否安装
if (-not (Test-Path "node_modules")) {
    Write-Output "Dependencies not installed, installing now..."
    
    # 配置 npm 使用项目虚拟环境中的 Python（用于 node-gyp 编译）
    $venvPython = "$ScriptDir\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Output "[信息] 配置 npm 使用虚拟环境 Python: $venvPython"
        & $npmCmd config set python "$venvPython"
        $env:PYTHON = $venvPython
        $env:npm_config_python = $venvPython
    } else {
        Write-Output "[警告] 未找到虚拟环境 Python，将使用系统 Python"
    }
    
    # 配置国内镜像加速
    Write-Output "[信息] 配置 npm 国内镜像..."
    & $npmCmd config set registry https://registry.npmmirror.com
    
    # 安装依赖
    Write-Output "[信息] 开始安装前端依赖..."
    & $npmCmd install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error: Frontend dependencies installation failed!"
        exit 1
    }
    Write-Output "✓ Frontend dependencies installed"
}

if (-not (Test-Path "server\node_modules")) {
    Write-Output "Server dependencies not installed, installing now..."
    
    # 配置 npm 使用项目虚拟环境中的 Python（用于 node-gyp 编译）
    $venvPython = "$ScriptDir\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Output "[信息] 配置 npm 使用虚拟环境 Python: $venvPython"
        & $npmCmd config set python "$venvPython"
        $env:PYTHON = $venvPython
        $env:npm_config_python = $venvPython
    }
    
    # 配置国内镜像加速
    Write-Output "[信息] 配置 npm 国内镜像..."
    & $npmCmd config set registry https://registry.npmmirror.com
    
    # 安装 server 依赖
    Write-Output "[信息] 开始安装 server 依赖..."
    Set-Location "server"
    & $npmCmd install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error: Server dependencies installation failed!"
        exit 1
    }
    Set-Location ".."
    Write-Output "✓ Server dependencies installed"
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
