$bytes = [IO.File]::ReadAllBytes('E:\软件开发\云集智能音乐创意台\dev\运行.bat')
$hex = ($bytes[0..50] | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
Write-Host "First 50 bytes: $hex"
Write-Host "Total length: $($bytes.Length)"
$lfCount = 0
$crlfCount = 0
for ($i = 0; $i -lt $bytes.Length - 1; $i++) {
    if ($bytes[$i] -eq 0x0A) {
        if ($i -gt 0 -and $bytes[$i-1] -eq 0x0D) {
            $crlfCount++
        } else {
            $lfCount++
        }
    }
}
Write-Host "LF count: $lfCount"
Write-Host "CRLF count: $crlfCount"
