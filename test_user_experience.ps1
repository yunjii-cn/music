# 云集智能音乐创意台 - 用户体验测试脚本
# 用于模拟用户首次使用场景

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  云集智能音乐创意台 - 用户体验测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$projectRoot = "E:\AI应用\云集智能音乐创意台"
$testRoot = "E:\AI应用\测试环境"
$testDir = Join-Path $testRoot "云集智能音乐创意台-测试"
$exePattern = "云集智能音乐创意台-v*.exe"

Write-Host "[1/5] 准备测试环境..." -ForegroundColor Yellow

# 创建测试目录
if (Test-Path $testDir) {
    Write-Host "  清理旧的测试目录..." -ForegroundColor Gray
    Remove-Item -Path $testDir -Recurse -Force
}
New-Item -Path $testDir -ItemType Directory -Force | Out-Null
Write-Host "  ✓ 测试目录已创建: $testDir" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] 复制项目文件..." -ForegroundColor Yellow

# 复制必要文件
$filesToCopy = @(
    "requirements.txt",
    "install-env.ps1",
    "start.ps1",
    "download_python_312.py"
)

foreach ($file in $filesToCopy) {
    $src = Join-Path $projectRoot $file
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $testDir
        Write-Host "  ✓ 已复制: $file" -ForegroundColor Green
    }
}

# 复制最新的EXE
$latestExe = Get-ChildItem -Path (Join-Path $projectRoot "dist") -Filter $exePattern | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestExe) {
    Copy-Item -Path $latestExe.FullName -Destination $testDir
    Write-Host "  ✓ 已复制: $($latestExe.Name)" -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到EXE文件！" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/5] 验证测试环境结构..." -ForegroundColor Yellow

Write-Host ""
Write-Host "测试目录结构：" -ForegroundColor Cyan
Get-ChildItem -Path $testDir | ForEach-Object {
    $type = if ($_.PSIsContainer) { "[DIR]  " } else { "[FILE] " }
    Write-Host "  $type$($_.Name)" -ForegroundColor White
}

Write-Host ""
Write-Host "[4/5] 检查开发环境痕迹..." -ForegroundColor Yellow

$devArtifacts = @(
    ".venv",
    "tools",
    "__pycache__",
    "*.pyc",
    ".git"
)

$foundDevArtifacts = @()
foreach ($artifact in $devArtifacts) {
    $path = Join-Path $testDir $artifact
    if (Test-Path $path) {
        $foundDevArtifacts += $artifact
        Write-Host "  ⚠ 发现开发环境痕迹: $artifact" -ForegroundColor Yellow
    }
}

if ($foundDevArtifacts.Count -eq 0) {
    Write-Host "  ✓ 未发现开发环境痕迹" -ForegroundColor Green
}

Write-Host ""
Write-Host "[5/5] 准备就绪！" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试环境准备完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "测试目录: $testDir" -ForegroundColor White
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "  1. 打开测试目录" -ForegroundColor White
Write-Host "  2. 双击运行EXE" -ForegroundColor White
Write-Host "  3. 观察用户体验" -ForegroundColor White
Write-Host ""
Write-Host "按任意键打开测试目录..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 打开测试目录
Invoke-Item $testDir
