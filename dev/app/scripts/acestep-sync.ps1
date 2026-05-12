<#
.SYNOPSIS
    ACE-Step 官方代码同步脚本
.DESCRIPTION
    从官方 GitHub 仓库拉取最新代码并合并到本地 acestep/ 目录。
    
    同步策略:
    1. 下载官方最新 acestep/ 目录到临时位置
    2. 用官方文件替换本地 acestep/
    3. 恢复我们的自定义修改:
       - acestep/model_downloader.py (添加 XL 模型支持)
       - acestep/models/ (自定义模型代码)
       - acestep/mlx/ (自定义 MLX 加速模块)
    4. 清理临时文件
    
    备份保存在: dev/app/acestep-sync-backup/YYYYMMDD-HHmmss/
.NOTES
    使用方式: cd scripts && .\acestep-sync.ps1
    需要安装 git
#>

Set-Location $PSScriptRoot

$OfficialRepo = "https://github.com/ace-step/ACE-Step-1.5.git"
$ProjectRoot = Join-Path $PSScriptRoot ".."
$AceStepDir = Join-Path $ProjectRoot "acestep"
$SyncBackupDir = Join-Path $ProjectRoot "acestep-sync-backup"
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $SyncBackupDir $Timestamp

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ACE-Step 官方代码同步工具" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "官方仓库: $OfficialRepo" -ForegroundColor Gray
Write-Host ""

# 检查 git 是否可用
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ git 未安装，请先安装 Git" -ForegroundColor Red
    exit 1
}

# 创建备份目录
if (-not (Test-Path $SyncBackupDir)) {
    New-Item -Path $SyncBackupDir -ItemType Directory -Force | Out-Null
}

try {
    # 1. 备份当前 acestep/
    Write-Host "[1/5] 备份当前 acestep/ 目录..." -ForegroundColor Yellow
    if (Test-Path $AceStepDir) {
        Copy-Item -Path $AceStepDir -Destination $BackupDir -Recurse -Force
        Write-Host "      备份: $BackupDir" -ForegroundColor Green
    } else {
        Write-Host "      acestep/ 不存在，跳过备份" -ForegroundColor DarkGray
    }
    
    # 2. 记录我们需要保留的自定义文件
    Write-Host ""
    Write-Host "[2/5] 识别自定义修改文件..." -ForegroundColor Yellow
    $CustomFiles = @()
    
    # model_downloader.py 是我们的核心自定义文件
    if (Test-Path (Join-Path $BackupDir "model_downloader.py")) {
        $CustomFiles += "model_downloader.py"
        Write-Host "      ✓ model_downloader.py" -ForegroundColor Green
    }
    
    # models/ 目录包含自定义模型代码
    if (Test-Path (Join-Path $BackupDir "models")) {
        $CustomFiles += "models"
        Write-Host "      ✓ models/ (自定义模型代码)" -ForegroundColor Green
    }
    
    # mlx/ 目录是自定义 MLX 加速模块
    if (Test-Path (Join-Path $BackupDir "mlx")) {
        $CustomFiles += "mlx"
        Write-Host "      ✓ mlx/ (MLX 加速模块)" -ForegroundColor Green
    }
    
    Write-Host "      共 $($CustomFiles.Count) 个自定义文件/目录" -ForegroundColor Gray
    
    # 3. 下载官方最新代码
    Write-Host ""
    Write-Host "[3/5] 从官方仓库下载最新代码..." -ForegroundColor Yellow
    $TempDir = Join-Path $env:TEMP "acestep-sync-$(Get-Random)"
    
    git clone --depth 1 --quiet $OfficialRepo $TempDir
    if ($LASTEXITCODE -ne 0) {
        throw "git clone 失败"
    }
    
    $OfficialAceStep = Join-Path $TempDir "acestep"
    if (-not (Test-Path $OfficialAceStep)) {
        throw "官方仓库中没有 acestep/ 目录"
    }
    
    Write-Host "      ✓ 官方代码下载完成" -ForegroundColor Green
    
    # 4. 合并官方代码
    Write-Host ""
    Write-Host "[4/5] 合并官方代码..." -ForegroundColor Yellow
    
    if (Test-Path $AceStepDir) {
        Remove-Item -Path $AceStepDir -Recurse -Force
    }
    
    Copy-Item -Path $OfficialAceStep -Destination $AceStepDir -Recurse -Force
    
    Write-Host "      ✓ 官方代码已部署" -ForegroundColor Green
    
    # 5. 恢复自定义修改
    Write-Host ""
    Write-Host "[5/5] 恢复自定义修改..." -ForegroundColor Yellow
    
    # 恢复 model_downloader.py
    if ("model_downloader.py" -in $CustomFiles) {
        $SrcFile = Join-Path $BackupDir "model_downloader.py"
        $DestFile = Join-Path $AceStepDir "model_downloader.py"
        Copy-Item -Path $SrcFile -Destination $DestFile -Force
        Write-Host "      ✓ model_downloader.py 已恢复" -ForegroundColor Green
    }
    
    # 恢复 models/ 目录
    if ("models" -in $CustomFiles) {
        $SrcModels = Join-Path $BackupDir "models"
        $DestModels = Join-Path $AceStepDir "models"
        if (-not (Test-Path $DestModels)) {
            New-Item -Path $DestModels -ItemType Directory -Force | Out-Null
        }
        Copy-Item -Path "$SrcModels\*" -Destination $DestModels -Recurse -Force
        Write-Host "      ✓ models/ 已恢复" -ForegroundColor Green
    }
    
    # 恢复 mlx/ 目录
    if ("mlx" -in $CustomFiles) {
        $SrcMlx = Join-Path $BackupDir "mlx"
        $DestMlx = Join-Path $AceStepDir "mlx"
        if (-not (Test-Path $DestMlx)) {
            New-Item -Path $DestMlx -ItemType Directory -Force | Out-Null
        }
        Copy-Item -Path "$SrcMlx\*" -Destination $DestMlx -Recurse -Force
        Write-Host "      ✓ mlx/ 已恢复" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  ✅ 同步完成！" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "备份位置: $BackupDir" -ForegroundColor Gray
    Write-Host ""
    Write-Host "如需回滚:" -ForegroundColor Yellow
    Write-Host "  Remove-Item '$AceStepDir' -Recurse -Force" -ForegroundColor DarkGray
    Write-Host "  Copy-Item '$BackupDir' '$AceStepDir' -Recurse" -ForegroundColor DarkGray
    
} catch {
    Write-Host ""
    Write-Host "❌ 同步失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "正在从备份恢复..." -ForegroundColor Yellow
    
    if (Test-Path $AceStepDir) {
        Remove-Item -Path $AceStepDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $BackupDir) {
        Copy-Item -Path $BackupDir -Destination $AceStepDir -Recurse -Force
        Write-Host "✓ 已从备份恢复" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 没有可用备份，请手动恢复" -ForegroundColor Red
    }
    exit 1
    
} finally {
    # 清理临时目录
    if (Test-Path $TempDir) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
