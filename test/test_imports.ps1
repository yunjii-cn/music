Set-Location 'E:\软件开发\云集智能音乐创意台\dev\app'
$pythonExe = (Resolve-Path '.\scripts\.venv\Scripts\python.exe').Path

$testScript = @"
import sys
import os
os.chdir(r'E:\软件开发\云集智能音乐创意台\dev\app')
sys.path.insert(0, '.')
try:
    print("Step 1: Basic imports...")
    import subprocess
    import threading
    import socket
    print("Step 2: PyQt6 imports...")
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
    print("Step 3: psutil import...")
    import psutil
    print("Step 4: All basic imports OK")
    
    print("Step 5: Creating QApplication...")
    app = QApplication(sys.argv)
    print("Step 6: QApplication created OK")
    
    print("Step 7: Testing main import...")
    import main as main_mod
    print("Step 8: main module imported OK")
    
    print("SUCCESS: All imports work")
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
"@

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = "-u -c `"$testScript`""
$psi.WorkingDirectory = 'E:\软件开发\云集智能音乐创意台\dev\app'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $false
$psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"

$proc = [System.Diagnostics.Process]::Start($psi)
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()
$exited = $proc.WaitForExit(30000)
if (-not $exited) {
    Write-Host "PROCESS DID NOT EXIT - killing"
    $proc.Kill()
}
$stdout = $stdoutTask.Result
$stderr = $stderrTask.Result
Write-Host "EXIT CODE: $($proc.ExitCode)"
Write-Host "STDOUT:"
Write-Host $stdout.Substring(0, [Math]::Min(3000, $stdout.Length))
Write-Host "STDERR:"
Write-Host $stderr.Substring(0, [Math]::Min(3000, $stderr.Length))
