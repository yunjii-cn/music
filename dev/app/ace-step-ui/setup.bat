@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   ACE-Step UI - ??????
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