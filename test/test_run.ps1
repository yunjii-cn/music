Set-Location 'E:\软件开发\云集智能音乐创意台\dev\app'
$pythonExe = '.\scripts\.venv\Scripts\python.exe'
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = (Resolve-Path $pythonExe).Path
$psi.Arguments = 'main.py'
$psi.WorkingDirectory = 'E:\软件开发\云集智能音乐创意台\dev\app'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit(30000)
Write-Host "EXIT CODE: $($proc.ExitCode)"
Write-Host "STDOUT:"
Write-Host $stdout
Write-Host "STDERR:"
Write-Host $stderr
