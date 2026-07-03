@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   ACE-Step UI 完整启动脚本
echo ============================================================
echo.

REM 从 port_config.json 读取端口配置
set PORT_CFG=..\port_config.json
if exist "%PORT_CFG%" (
    echo [配置] 读取端口配置...
    for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "(Get-Content '%PORT_CFG%' | ConvertFrom-Json).qinglong_frontend"`) do set FRONTEND_PORT=%%a
    for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "(Get-Content '%PORT_CFG%' | ConvertFrom-Json).qinglong_backend"`) do set BACKEND_PORT=%%a
    for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "(Get-Content '%PORT_CFG%' | ConvertFrom-Json).qinglong_api"`) do set API_PORT=%%a
) else (
    echo [配置] 未找到 port_config.json，使用默认端口
    set FRONTEND_PORT=3070
    set BACKEND_PORT=3060
    set API_PORT=8050
)

echo   前端端口: %FRONTEND_PORT%
echo   后端端口: %BACKEND_PORT%
echo   API 端口: %API_PORT%
echo.

set API_OK=0
set BACKEND_OK=0
set FRONTEND_OK=0
set NPM_CMD=
set NODE_FOUND=0

REM 查找 Node.js
where node >nul 2>&1
if %errorlevel% equ 0 set NPM_CMD=npm & set NODE_FOUND=1 & echo [信息] 使用系统 Node.js

if exist "D:\Programs\nodejs\npm.cmd" (
    set "NPM_CMD=D:\Programs\nodejs\npm.cmd"
    set PATH=D:\Programs\nodejs;%PATH%
    set NODE_FOUND=1
    echo [信息] 使用 D:\Programs\nodejs
)

if exist "..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64\npm.cmd" (
    set "NPM_CMD=..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64\npm.cmd"
    set PATH=..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64;%PATH%
    set NODE_FOUND=1
    echo [信息] 使用便携版 Node.js 24
)

if exist "..\..\data\nodejs\node-v22.14.0-win-x64\npm.cmd" (
    set "NPM_CMD=..\..\data\nodejs\node-v22.14.0-win-x64\npm.cmd"
    set PATH=..\..\data\nodejs\node-v22.14.0-win-x64;%PATH%
    set NODE_FOUND=1
    echo [信息] 使用便携版 Node.js 22
)

if %NODE_FOUND% equ 0 (
    echo [错误] 未找到 Node.js！
    pause
    exit /b 1
)

REM 检查依赖
if not exist "node_modules" (
    echo [信息] 安装前端依赖...
    call %NPM_CMD% install
    if !errorlevel! neq 0 ( echo [错误] 前端依赖安装失败！ & pause & exit /b 1 )
)
if not exist "server\node_modules" (
    echo [信息] 安装服务端依赖...
    pushd server && call %NPM_CMD% install && popd
)

echo.

REM ============================================================
REM 1. ACE-Step API
REM ============================================================
set VENV_PYTHON=..\..\data\.venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    set START_API=1
    echo [1/3] 启动 ACE-Step API (端口 !API_PORT!)...
    set PYTHON_PATH=%CD%\..\..\data\.venv\Scripts\python.exe
    set PYTHONPATH=%CD%\..
    start "ACE-Step API Server" /D "%CD%\.." cmd /k "title ACE-Step API && !PYTHON_PATH! acestep\api_server.py --port !API_PORT!"
) else if exist "..\python_embeded\python.exe" (
    set START_API=1
    echo [1/3] 启动 ACE-Step API (python_embeded)...
    set PYTHONPATH=%CD%\..
    start "ACE-Step API Server" /D "%CD%\.." cmd /k "title ACE-Step API && python_embeded\python acestep\api_server.py --port !API_PORT!"
) else (
    set START_API=0
    echo [1/3] ACE-Step API 虚拟环境未找到，跳过
)

if %START_API% equ 1 (
    echo        等待端口 !API_PORT! 就绪...
    for /l %%i in (1,1,60) do (
        >nul 2>&1 powershell -NoProfile -Command "if((Get-NetTCPConnection -LocalPort !API_PORT! -ErrorAction SilentlyContinue).State -eq 'Listen'){exit 0}else{exit 1}"
        if !errorlevel! equ 0 ( echo        ^^! ACE-Step API (端口 !API_PORT!) 已就绪 & set API_OK=1 & goto api_ok )
        timeout /t 1 /nobreak >nul
    )
    echo        [失败] ACE-Step API (端口 !API_PORT!) 启动超时，请查看 API 窗口确认
) else (
    echo        [跳过] ACE-Step API
)
:api_ok
echo.

REM ============================================================
REM 2. 后端 Express 服务器
REM ============================================================
echo [2/3] 启动后端服务 (端口 !BACKEND_PORT!)...
set PORT=!BACKEND_PORT!
set ACESTEP_API_URL=http://localhost:!API_PORT!
start "ACE-Step UI Backend" /D "%CD%\server" cmd /k "title Backend :%BACKEND_PORT% && %NPM_CMD% run dev"
echo        等待端口 !BACKEND_PORT! 就绪...
for /l %%i in (1,1,30) do (
    >nul 2>&1 powershell -NoProfile -Command "if((Get-NetTCPConnection -LocalPort !BACKEND_PORT! -ErrorAction SilentlyContinue).State -eq 'Listen'){exit 0}else{exit 1}"
    if !errorlevel! equ 0 ( echo        ^^! 后端服务 (端口 !BACKEND_PORT!) 已就绪 & set BACKEND_OK=1 & goto backend_ok )
    timeout /t 1 /nobreak >nul
)
echo        [失败] 后端服务 (端口 !BACKEND_PORT!) 启动超时
:backend_ok
echo.

REM ============================================================
REM 3. 前端 Vite 服务器
REM ============================================================
echo [3/3] 启动前端服务 (端口 !FRONTEND_PORT!)...
set VITE_PORT=!FRONTEND_PORT!
set BACKEND_URL=http://127.0.0.1:!BACKEND_PORT!
start "ACE-Step UI Frontend" /D "%CD%" cmd /k "title Frontend :%FRONTEND_PORT% && %NPM_CMD% run dev"
echo        等待端口 !FRONTEND_PORT! 就绪...
for /l %%i in (1,1,30) do (
    >nul 2>&1 powershell -NoProfile -Command "if((Get-NetTCPConnection -LocalPort !FRONTEND_PORT! -ErrorAction SilentlyContinue).State -eq 'Listen'){exit 0}else{exit 1}"
    if !errorlevel! equ 0 ( echo        ^^! 前端服务 (端口 !FRONTEND_PORT!) 已就绪 & set FRONTEND_OK=1 & goto frontend_ok )
    timeout /t 1 /nobreak >nul
)
echo        [失败] 前端服务 (端口 !FRONTEND_PORT!) 启动超时
:frontend_ok

echo.
echo ============================================================
echo   服务启动状态
echo ============================================================
echo.
if %API_OK% equ 1 (
    echo   [^ok] ACE-Step API:   http://localhost:%API_PORT%
) else if %START_API% equ 1 (
    echo   [FAIL] ACE-Step API:   http://localhost:%API_PORT% (启动失败)
) else (
    echo   [SKIP] ACE-Step API:   已跳过
)
if %BACKEND_OK% equ 1 (
    echo   [^ok] 后端服务:       http://localhost:%BACKEND_PORT%
) else (
    echo   [FAIL] 后端服务:       http://localhost:%BACKEND_PORT% (启动失败)
)
if %FRONTEND_OK% equ 1 (
    echo   [^ok] 前端服务:       http://localhost:%FRONTEND_PORT%
) else (
    echo   [FAIL] 前端服务:       http://localhost:%FRONTEND_PORT% (启动失败)
)

echo.
if %FRONTEND_OK% equ 1 ( start http://localhost:%FRONTEND_PORT% & echo   前端页面已自动打开 )
echo.
if %API_OK% equ 0 if %START_API% equ 1 echo   [警告] ACE-Step API 未就绪，会影响音乐生成功能
if %BACKEND_OK% equ 0 echo   [警告] 后端服务未就绪，影响 API 调用和音频播放
if %FRONTEND_OK% equ 0 echo   [警告] 前端服务未就绪，无法访问页面
echo.
pause
