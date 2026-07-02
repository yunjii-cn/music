Set-Location 'E:\软件开发\云集智能音乐创意台\dev\app'
$pythonExe = (Resolve-Path '.\scripts\.venv\Scripts\python.exe').Path
Write-Host "Python: $pythonExe"
Write-Host "CWD: $PWD"

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = '-c "import sys; print(sys.version); import PyQt6; print(PyQt6.__file__)"'
$psi.WorkingDirectory = 'E:\软件开发\云集智能音乐创意台\dev\app'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit(15000)
Write-Host "EXIT CODE: $($proc.ExitCode)"
Write-Host "STDOUT: $stdout"
Write-Host "STDERR: $stderr"
