Set-Location 'E:\软件开发\云集智能音乐创意台\dev\app'
$pythonExe = (Resolve-Path '.\scripts\.venv\Scripts\python.exe').Path

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = '-u E:\软件开发\云集智能音乐创意台\dev\test_splash.py'
$psi.WorkingDirectory = 'E:\软件开发\云集智能音乐创意台\dev\app'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $false
$psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"

$proc = [System.Diagnostics.Process]::Start($psi)
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()
$exited = $proc.WaitForExit(15000)
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
