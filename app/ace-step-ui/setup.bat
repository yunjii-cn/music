@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   ACE-Step UI - ??????
echo ============================================================
echo.

REM 查找 Node.js（优先级：便携 v24 → 系统 v24 → PATH，详见 project_memory.md）
set NPM_CMD=
set NODE_FOUND=0

REM 1. 便携版 Node.js 24 (data/tools/)
if exist "..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64\npm.cmd" (
    set NPM_CMD="..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64\npm.cmd"
    set PATH=..\..\data\tools\node-v24.14.1-win-x64\node-v24.14.1-win-x64;%PATH%
    set NODE_FOUND=1
    echo [信息] 使用便携版 Node.js 24
)

REM 2. 系统 Node.js 24
if %NODE_FOUND% equ 0 (
    if exist "D:\Programs\nodejs\npm.cmd" (
        set NPM_CMD="D:\Programs\nodejs\npm.cmd"
        set PATH=D:\Programs\nodejs;%PATH%
        set NODE_FOUND=1
        echo [信息] 使用 D:\Programs\nodejs
    )
)

REM 3. PATH 中的 node（含 TRAE 内置，最后兜底）
if %NODE_FOUND% equ 0 (
    where node >nul 2>&1
    if %errorlevel% equ 0 (
        set NPM_CMD=npm
        set NODE_FOUND=1
        echo [信息] 使用 PATH 中的 Node.js
    )
)

if %NODE_FOUND% equ 0 (
    echo [错误] 未找到 Node.js
    echo.
    echo 请安装 Node.js 或放置便携版到 ..\..\data\tools\ 目录
    echo.
    pause
    exit /b 1
)

echo [??] ?? npm: %NPM_CMD%
echo.

echo [??] ??????...
call %NPM_CMD% install
if !errorlevel! neq 0 (
    echo [??] ?????????
    pause
    exit /b 1
)
echo [??] ????????

echo.
echo [??] ???????...
cd server
call %NPM_CMD% install
if !errorlevel! neq 0 (
    echo [??] ??????????
    cd ..
    pause
    exit /b 1
)
cd ..
echo [??] ?????????

echo.
echo ============================================================
echo   ???????
echo ============================================================
echo.
echo ?????? start.bat ?????
echo.
pause