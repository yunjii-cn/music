@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   云集智能音乐创意台 - ACE-Step UI 启动脚本
echo ============================================================
echo.
echo [信息] 验证环境配置...

REM 验证 Node.js 环境
set NPM_CMD=
set NODE_FOUND=0

REM 1. 检查系统 PATH 中的 node
where node >nul 2>&1
if %errorlevel% equ 0 (
    set NPM_CMD=npm
    set NODE_FOUND=1
    echo [信息] 使用系统 Node.js
)

REM 2. 检查 D:\Programs\nodejs
if %NODE_FOUND% equ 0 (
    if exist "D:\Programs\nodejs\npm.cmd" (
        set NPM_CMD="D:\Programs\nodejs\npm.cmd"
        set PATH=D:\Programs\nodejs;%PATH%
        set NODE_FOUND=1
        echo [信息] 使用 D:\Programs\nodejs
    )
)

REM 3. 检查便携版 Node.js 24 (data/tools/)
if %NODE_FOUND% equ 0 (
    if exist "..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64\npm.cmd" (
        set NPM_CMD="..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64\npm.cmd"
        set PATH=..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64;%PATH%
        set NODE_FOUND=1
        echo [信息] 使用便携版 Node.js 24
    )
)

REM 4. 检查便携版 Node.js 22 (data/nodejs/)
if %NODE_FOUND% equ 0 (
    if exist "..\..\data\nodejs\node-v22.14.0-win-x64\npm.cmd" (
        set NPM_CMD="..\..\data\nodejs\node-v22.14.0-win-x64\npm.cmd"
        set PATH=..\..\data\nodejs\node-v22.14.0-win-x64;%PATH%
        set NODE_FOUND=1
        echo [信息] 使用便携版 Node.js 22
    )
)

if %NODE_FOUND% equ 0 (
    echo [错误] 未找到 Node.js！
    echo.
    echo 请安装 Node.js 或将便携版放在 ..\scripts\ 目录下
    echo.
    pause
    exit /b 1
)

echo [信息] 使用 npm: %NPM_CMD%
echo.

REM 检查 node_modules
if not exist "node_modules" (
    echo [信息] 安装前端依赖...
    call %NPM_CMD% install
    if !errorlevel! neq 0 (
        echo [错误] 前端依赖安装失败！
        pause
        exit /b 1
    )
    echo [信息] 前端依赖安装完成
) else (
    echo [信息] 前端依赖已安装
)

REM 检查 server 依赖
if not exist "server\node_modules" (
    echo [信息] 安装服务端依赖...
    cd server
    call %NPM_CMD% install
    if !errorlevel! neq 0 (
        echo [错误] 服务端依赖安装失败！
        pause
        exit /b 1
    )
    cd ..
    echo [信息] 服务端依赖安装完成
) else (
    echo [信息] 服务端依赖已安装
)

echo.
echo [信息] 启动服务...

REM 在独立窗口中启动后端
start "ACE-Step UI Backend" cmd /k "cd /d %CD%\server && %NPM_CMD% run dev"

REM 在独立窗口中启动前端
start "ACE-Step UI Frontend" cmd /k "cd /d %CD% && %NPM_CMD% run dev"

echo.
echo ============================================================
echo   服务已启动！
echo.
echo   前端: http://localhost:3000
echo   后端: http://localhost:3001
echo ============================================================
echo.
echo 请勿关闭本窗口，关闭此窗口不会影响已启动的服务。
echo 要停止服务，请关闭对应的命令行窗口。
echo.
pause