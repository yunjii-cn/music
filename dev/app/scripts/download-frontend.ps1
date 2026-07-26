#Requires -Version 5.1
<#
 .SYNOPSIS
  一键部署维护的"最后一步"：从码云(Gitee)拉取预构建前端包并解压到部署根目录。
  前端包包含：ace-step-ui 的 node_modules（前端 + server 各一套）+ 便携 Node.js，
  因此解压后前端无需 npm install、无需联网即可显示（彻底根治"启动后前端空白"）。
#>
param(
  [string]$BaseDir = "",
  [int]$BudgetSec = 900
)

$ErrorActionPreference = "Stop"

# 部署根目录（含 app/ 与 data/ 的那一层）。调用方(main.py)应传入 get_install_root()。
if (-not $BaseDir) {
    $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    # scripts -> app -> 部署根
    $BaseDir = Split-Path -Parent (Split-Path -Parent $ScriptRoot)
}
if (-not (Test-Path $BaseDir)) {
    Write-Error "部署根目录不存在: $BaseDir"
    exit 1
}
Write-Output "[前端] 部署根目录: $BaseDir"

# ===== 下载源：码云(Gitee) 分卷（国内源，已上传验证）=====
# 单附件上限 100MB，故切成 2 片上传到 frontend release。
$giteeParts = @(
    "https://gitee.com/yunjii/music/releases/download/frontend/frontend_bundle.part1",
    "https://gitee.com/yunjii/music/releases/download/frontend/frontend_bundle.part2"
)
# 各分卷精确预期大小（与上传时一致），用于逐片完整性校验
$partExpected = @(94371840, 5791058)
$ExpectedTotal = 100162898

$appUiNm = Join-Path $BaseDir "app/ace-step-ui/node_modules"
$nodeExe = Join-Path $BaseDir "data/tools/node-v24.14.1-win-x64/node-v24.14.1-win-x64/node.exe"

# 已就绪则跳过（幂等，重跑部署不重复下载）
if ((Test-Path $appUiNm) -and (Test-Path $nodeExe)) {
    Write-Output "[前端] 前端依赖与便携 Node 均已存在，跳过下载。"
    exit 0
}

$start = Get-Date

function Download-GiteeMultipart {
    param([string]$DestPath, [string[]]$PartUrls, [int64]$ExpectedSize)
    $partFiles = @()
    $ok = $true
    for ($i = 0; $i -lt $PartUrls.Count; $i++) {
        if (((Get-Date) - $start).TotalSeconds -ge $BudgetSec) {
            Write-Warning "  [前端] 已超总预算，放弃下载"
            $ok = $false; break
        }
        $u = $PartUrls[$i]
        $tmp = Join-Path $env:TEMP "frontend_bundle.part$($i + 1)"
        Write-Output "  [前端] 分卷 ($($i + 1)/$($PartUrls.Count)): $u"
        & curl.exe -sSL --connect-timeout 20 -m 300 --retry 3 --retry-delay 2 -o "$tmp" "$u" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tmp)) {
            Write-Warning "  [前端] 分卷 $($i + 1) 下载失败 (curl=$LASTEXITCODE)"
            if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
            $ok = $false; break
        }
        $sz = (Get-Item $tmp).Length
        if ($i -lt $partExpected.Count -and [math]::Abs($sz - $partExpected[$i]) -gt 1024) {
            Write-Warning "  [前端] 分卷 $($i + 1) 大小异常: $sz (预期 $($partExpected[$i]))，可能损坏"
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
            $ok = $false; break
        }
        Write-Output "  [前端] 分卷 $($i + 1) 已下载 $([math]::Round($sz/1MB, 1)) MB"
        $partFiles += $tmp
    }
    if ($ok) {
        try {
            $out = [System.IO.File]::Create($DestPath)
            foreach ($p in $partFiles) {
                $in = [System.IO.File]::OpenRead($p)
                $in.CopyTo($out)
                $in.Close()
            }
            $out.Close()
            $finalLen = (Get-Item $DestPath).Length
            if ($ExpectedSize -gt 0 -and $finalLen -ne $ExpectedSize) {
                Write-Warning "  [前端] 拼接后大小 $finalLen 与预期 $ExpectedSize 不符，可能损坏"
                return $false
            }
            Write-Output "  [前端] 分卷拼接完成 ($finalLen 字节)"
            return $true
        } catch {
            Write-Warning "  [前端] 拼接失败: $_"
            return $false
        }
    }
    return $false
}

Write-Output "[前端] 开始从码云拉取前端包（约 95MB，分 2 卷）..."
$zipPath = Join-Path $env:TEMP "frontend_bundle.zip"
$downloaded = Download-GiteeMultipart $zipPath $giteeParts $ExpectedTotal

if (-not $downloaded -or -not (Test-Path $zipPath)) {
    Write-Error "[前端] 前端包下载失败，请检查网络后重跑一键部署。应用仍可打开，但 Web 前端可能不显示。"
    exit 1
}

# 解压到部署根目录（app/ 与 data/ 之上）
Write-Output "[前端] 解压前端包到: $BaseDir"
try {
    Expand-Archive -Path $zipPath -DestinationPath $BaseDir -Force
} catch {
    Write-Error "[前端] 解压失败: $_"
    exit 1
}

# 校验关键产物
if (-not (Test-Path $appUiNm)) {
    Write-Error "[前端] 解压后未找到 app/ace-step-ui/node_modules"
    exit 1
}
if (-not (Test-Path $nodeExe)) {
    Write-Error "[前端] 解压后未找到便携 Node.js"
    exit 1
}

# 保险：确保 server/public（人声分离/音频静态资源）与 server/data（SQLite 库目录）存在，
# 避免 Node 后端相关路由因目录缺失而 404。server/data 即便为空，server 启动时也会自动建库。
$serverPublic = Join-Path $BaseDir "app/ace-step-ui/server/public"
$serverData = Join-Path $BaseDir "app/ace-step-ui/server/data"
if (-not (Test-Path $serverPublic)) {
    New-Item -ItemType Directory -Force -Path $serverPublic | Out-Null
    Write-Output "[前端] 已补齐 server/public 目录"
}
if (-not (Test-Path $serverData)) {
    New-Item -ItemType Directory -Force -Path $serverData | Out-Null
    Write-Output "[前端] 已补齐 server/data 目录"
}

# 清理临时文件
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
for ($i = 1; $i -le $giteeParts.Count; $i++) {
    Remove-Item (Join-Path $env:TEMP "frontend_bundle.part$i") -Force -ErrorAction SilentlyContinue
}

Write-Output "[前端] 前端依赖与便携 Node 已就绪，前端可离线显示。"
exit 0
