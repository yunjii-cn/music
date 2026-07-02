@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   ACE-Step UI Complete Startup
echo ============================================================
echo.

REM ?? Node.js ??
set NPM_CMD=
set NODE_FOUND=0

REM 1. ???? PATH ?? node
where node >nul 2>&1
if %errorlevel% equ 0 (
    set NPM_CMD=npm
    set NODE_FOUND=1
    echo [??] ???? Node.js
)

REM 2. ?? D:\Programs\nodejs
if %NODE_FOUND% equ 0 (
    if exist "D:\Programs\nodejs\npm.cmd" (
        set NPM_CMD="D:\Programs\nodejs\npm.cmd"
        set PATH=D:\Programs\nodejs;%PATH%
        set NODE_FOUND=1
        echo [??] ?? D:\Programs\nodejs
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
    echo [??] ??? Node.js?
    echo.
    echo ??? Node.js ??????? ..\scripts\ ???
    echo.
    pause
    exit /b 1
)

REM 检查 node_modules
if not exist "node_modules" (
    echo [信息] 前端依赖未安装，正在自动安装...
    call %NPM_CMD% install
    if !errorlevel! neq 0 (
        echo [错误] 前端依赖安装失败！
        pause
        exit /b 1
    )
    echo [信息] 前端依赖安装完成
)

if not exist "server\node_modules" (
    echo [信息] 服务端依赖未安装，正在自动安装...
    cd server
    call %NPM_CMD% install
    if !errorlevel! neq 0 (
        echo [错误] 服务端依赖安装失败！
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [信息] 服务端依赖安装完成
)

REM ACE-Step API ??
if "%ACESTEP_PATH%"=="" (
    set ACESTEP_PATH=..\ACE-Step-1.5
)

REM ?? ACE-Step ????
set START_API=0
if exist "%ACESTEP_PATH%" (
    set START_API=1
    if exist "%ACESTEP_PATH%\python_embeded\python.exe" (
        echo [??] ??? ACE-Step ???
        set API_COMMAND=python_embeded\python acestep\api_server.py
    ) else (
        echo [??] ??? ACE-Step ????
        set API_COMMAND=uv run acestep-api --port 8001
    )
) else (
    echo [??] ACE-Step ???? %ACESTEP_PATH%???? API ??
)

echo.
echo ============================================================
echo   ??????...
echo ============================================================
echo.

if %START_API% equ 1 (
    echo [1/3] ?? ACE-Step API ???...
    start "ACE-Step API Server" cmd /k "cd /d "%ACESTEP_PATH%" && %API_COMMAND%"
    echo ?? API ???...
    timeout /t 5 /nobreak >nul
) else (
    echo [1/2] ?? ACE-Step API?????
)

echo [2/3] ??????...
start "ACE-Step UI Backend" cmd /k "cd /d "%~dp0server" && !NPM_CMD! run dev"
timeout /t 3 /nobreak >nul

echo [3/3] ??????...
start "ACE-Step UI Frontend" cmd /k "cd /d "%~dp0" && !NPM_CMD! run dev"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo   ????????
echo ============================================================
echo.
if %START_API% equ 1 (
    echo   ACE-Step API: http://localhost:8001
)
echo   ??:         http://localhost:3001
echo   ??:         http://localhost:3000
echo.
echo ?????????????????
echo ============================================================

echo.
echo ??????????????????
pause >nul