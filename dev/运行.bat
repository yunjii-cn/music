@echo off
chcp 936 >nul 2>&1
title YunJi MusicCreativeStation - Dev Test

set "APP_DIR=%~dp0app"
set "PYTHON="

if exist "%~dp0data\.venv\Scripts\python.exe" set "PYTHON=%~dp0data\.venv\Scripts\python.exe"
if defined PYTHON goto :python_found

if exist "D:\Programs\Python312\python.exe" set "PYTHON=D:\Programs\Python312\python.exe"
if defined PYTHON goto :python_found
if exist "C:\Program Files\Python312\python.exe" set "PYTHON=C:\Program Files\Python312\python.exe"
if defined PYTHON goto :python_found
if exist "C:\Python312\python.exe" set "PYTHON=C:\Python312\python.exe"
if defined PYTHON goto :python_found
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PYTHON goto :python_found

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%i in ('where python') do set "PYTHON=%%i"
)

if not defined PYTHON (
    echo [ERROR] Cannot find Python!
    echo Please edit run.bat and set PYTHON manually.
    timeout /t 10
    exit /b 1
)

:python_found
echo ============================================================
echo   YunJi Music CreativeStation - Dev Mode
echo   Python:  %PYTHON%
echo   App:     %APP_DIR%
echo   Close this window to exit
echo ============================================================
echo.

cd /d "%APP_DIR%"

"%PYTHON%" main.py
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% EQU 0 (
    echo.
    echo Normal exit. Window closes in 3 seconds...
    timeout /t 3
    exit /b 0
)

echo.
echo [ERROR] Exit code: %EXIT_CODE%
if %EXIT_CODE%==-1073741819 echo [INFO] 0xC0000005 = Access Violation
if %EXIT_CODE%==-1073740771 echo [INFO] 0xC000041D = Status Stack Buffer Overrun
if %EXIT_CODE%==-1073740940 echo [INFO] 0xC0000374 = Heap Corruption
if %EXIT_CODE%==-1073741510 echo [INFO] 0xC000013A = Ctrl+C Exit
echo.
echo Window will close in 15 seconds...
timeout /t 15