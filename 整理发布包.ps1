# 正确的发布包整理脚本
$ErrorActionPreference = "Stop"

$versionDir = "e:\AI应用\云集智能音乐创意台\version\云集智能音乐创意台-v2026.04.11.0031"
$rootDir = "e:\AI应用\云集智能音乐创意台"

Write-Output "========================================"
Write-Output "   整理发布包"
Write-Output "========================================"
Write-Output ""

# 1. 删除旧的发布文件夹
Write-Output "[1/7] 删除旧的发布文件夹..."
if (Test-Path $versionDir) {
    try {
        Remove-Item -Path $versionDir -Recurse -Force -ErrorAction Stop
        Start-Sleep -Seconds 2
    } catch {
        Write-Output "⚠  警告: 删除旧文件夹失败，尝试继续..."
    }
}
Write-Output "✓ 完成"
Write-Output ""

# 2. 创建新的发布文件夹
Write-Output "[2/7] 创建新的发布文件夹..."
New-Item -ItemType Directory -Path $versionDir -Force | Out-Null
Write-Output "✓ 完成"
Write-Output ""

# 3. 复制 EXE
Write-Output "[3/7] 复制 EXE..."
Copy-Item -Path "$rootDir\dist\云集智能音乐创意台-v2026.04.11.0031.exe" -Destination "$versionDir\" -Force
Write-Output "✓ 完成"
Write-Output ""

# 4. 复制 tools 目录（只保留 node-v24 和 uv）
Write-Output "[4/7] 复制 tools 目录（仅 node-v24 和 uv）..."
$toolsDest = Join-Path $versionDir "tools"
New-Item -ItemType Directory -Path $toolsDest -Force | Out-Null
Copy-Item -Path "$rootDir\tools\node-v24.14.1-win-x64" -Destination $toolsDest -Recurse -Force
Copy-Item -Path "$rootDir\tools\uv" -Destination $toolsDest -Recurse -Force
Write-Output "✓ 完成"
Write-Output ""

# 5. 复制 acestep 目录
Write-Output "[5/7] 复制 acestep 目录..."
Copy-Item -Path "$rootDir\acestep" -Destination $versionDir -Recurse -Force
Write-Output "✓ 完成"
Write-Output ""

# 6. 复制 ace-step-ui 目录（排除 node_modules）
Write-Output "[6/7] 复制 ace-step-ui 目录（排除 node_modules）..."
$aceStepUiSource = "$rootDir\ace-step-ui"
$aceStepUiDest = Join-Path $versionDir "ace-step-ui"
New-Item -ItemType Directory -Path $aceStepUiDest -Force | Out-Null
Get-ChildItem -Path $aceStepUiSource -Exclude "node_modules" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $aceStepUiDest -Recurse -Force
}
Write-Output "✓ 完成"
Write-Output ""

# 7. 复制 scripts 目录
Write-Output "[7/7] 复制 scripts 目录..."
Copy-Item -Path "$rootDir\scripts" -Destination $versionDir -Recurse -Force
Write-Output "✓ 完成"
Write-Output ""

Write-Output "========================================"
Write-Output "   ✅ 整理完成！"
Write-Output "========================================"
Write-Output ""
Write-Output "最终发布包内容："
Write-Output ""
Get-ChildItem -Path $versionDir | ForEach-Object {
    if ($_.PSIsContainer) {
        Write-Output "  [文件夹] $($_.Name)"
    } else {
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Output "  [文件]   $($_.Name)  ($sizeMB MB)"
    }
}
Write-Output ""
Write-Output "tools 目录内容："
Get-ChildItem -Path $toolsDest | ForEach-Object {
    Write-Output "  [文件夹] $($_.Name)"
}
Write-Output ""
Write-Output "总结："
Write-Output "- ❌ 不包含 .venv（4.2G，用户自己通过 uv sync 创建）"
Write-Output "- ✅ 只包含 Node.js 24（删除了 v22）"
Write-Output "- ✅ 不包含 tools/python（UV 自带）"
Write-Output "- ✅ scripts 目录包含脚本和 lora_data_prepare"
Write-Output "- ✅ ace-step-ui 排除了 node_modules"
Write-Output ""
