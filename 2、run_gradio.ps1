
<#
文件用途: 官方音乐演练场启动脚本
项目名称: 云集智能音乐创意台 (ACE-Step)
版本: v2.8.3+

核心功能:
- 使用uv启动Gradio界面
- 启动官方音乐生成界面

端口: 7860

技术栈: Gradio + Python

关键变量:
- $uvPath: uv可执行文件路径
- $scriptPath: 脚本路径

依赖文件:
- acestep/ui/gradio/ (Gradio界面代码)

被调用:
- launcher/main.py (启动器)
- 用户手动运行

修改注意事项:
- 尽量不要修改，除非Gradio启动流程改变
- 修改前请查看FILE_INDEX.md了解用途

更多信息请参考:
- .ai-context/FILE_INDEX.md
- .ai-context/KNOWLEDGE_GRAPH.md
#>

# ============= Command Line Parameters | 命令行参数 =====================
param(
  [int]$Port = 7860,                           # Server port
  [string]$ServerName = "127.0.0.1",          # Server address (use 0.0.0.0 for network access)
  [switch]$Share,                              # Create public Gradio link
  [ValidateSet("en", "zh", "ja")]
  [string]$Language = "zh",                    # UI language: en, zh, ja
  [switch]$InitService,                        # Auto-initialize models on startup
  [string]$ConfigPath = "auto",                # DiT model (e.g., acestep-v15-turbo, acestep-v15-turbo-shift3)
  [string]$LmModelPath = "auto",               # LM model (e.g., acestep-5Hz-lm-0.6B, acestep-5Hz-lm-1.7B)
  [string]$OffloadToCpu = "auto",              # CPU offload (auto-enabled if VRAM < 16GB)
  [switch]$EnableApi,                          # Enable REST API endpoints alongside Gradio UI
  [string]$ApiKey = "none",                    # API key for API endpoints authentication
  [string]$AuthUsername = "none",              # Username for Gradio authentication
  [string]$AuthPassword = "none"               # Password for Gradio authentication
)

# ============= DO NOT MODIFY CONTENTS BELOW | 请勿修改下方内容 =====================
# Set environment variables
Set-Location $PSScriptRoot
$env:PYTHONPATH = "$PSScriptRoot$([System.IO.Path]::PathSeparator)$($env:PYTHONPATH)"

$Env:HF_HOME = "huggingface"
$Env:XFORMERS_FORCE_DISABLE_TRITON = "1"
$Env:HF_ENDPOINT = "https://hf-mirror.com"
$Env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu128"
$Env:UV_CACHE_DIR = "${env:LOCALAPPDATA}/uv/cache"
$Env:UV_NO_BUILD_ISOLATION = "1"
$Env:UV_NO_CACHE = "0"
$Env:UV_LINK_MODE = "symlink"
$Env:UV_INDEX_STRATEGY = "unsafe-best-match"
#$Env:CUDA_VISIBLE_DEVICES = "1"  # 设置GPU id，0表示使用第一个GPU，-1表示不使用GPU

#$Env:HTTP_PROXY = "http://127.0.0.1:7890"
#$Env:HTTPS_PROXY = "http://127.0.0.1:7890"

$ext_args = [System.Collections.ArrayList]::new()
$uv_args = [System.Collections.ArrayList]::new()

# ============= Build Arguments | 构建参数 =====================
# Server configuration
[void]$ext_args.Add("--port")
[void]$ext_args.Add($Port)
[void]$ext_args.Add("--server-name")
[void]$ext_args.Add($ServerName)

# Share link
if ($Share) {
  [void]$ext_args.Add("--share")
}

# Language
[void]$ext_args.Add("--language")
[void]$ext_args.Add($Language)

# Initialize service
if ($InitService) {
  [void]$ext_args.Add("--init_service")
  [void]$ext_args.Add("false")
}

# Model paths
if ($ConfigPath -ne "auto") {
  [void]$ext_args.Add("--config_path")
  [void]$ext_args.Add($ConfigPath)
}

if ($LmModelPath -ne "auto") {
  [void]$ext_args.Add("--lm_model_path")
  [void]$ext_args.Add($LmModelPath)
}

# CPU offload
if ($OffloadToCpu -ne "auto") {
  [void]$ext_args.Add("--offload_to_cpu")
  [void]$ext_args.Add($OffloadToCpu)
}

# API configuration
if ($EnableApi) {
  [void]$ext_args.Add("--enable-api")
}

if ($ApiKey -ne "none") {
  [void]$ext_args.Add("--api-key")
  [void]$ext_args.Add($ApiKey)
}

# Authentication
if ($AuthUsername -ne "none") {
  [void]$ext_args.Add("--auth-username")
  [void]$ext_args.Add($AuthUsername)
}

if ($AuthPassword -ne "none") {
  [void]$ext_args.Add("--auth-password")
  [void]$ext_args.Add($AuthPassword)
}

# run train
# 先尝试从系统PATH查找uv
$uv_path = Get-Command uv -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $uv_path) {
    $uv_path = "$HOME\.local\bin\uv.exe"
    if (-not (Test-Path $uv_path)) {
        Write-Error "uv not found. Please install uv first."
        exit 1
    }
}
Write-Output "Using uv at: $uv_path"
# Use --no-sync to avoid reinstalling packages every time (fixes flash_attn reinstall issues)
[void]$uv_args.Add("--no-sync")
&amp; $uv_path run $uv_args acestep $ext_args

Write-Output "Start finished"
