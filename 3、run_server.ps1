
<#
文件用途: 核心API服务启动脚本
项目名称: 云集智能音乐创意台 (ACE-Step)
版本: v2.8.3+

核心功能:
- 启动FastAPI后端服务
- 提供核心API接口

端口: 8001

技术栈: FastAPI + Python + Uvicorn

依赖文件:
- acestep/api/ (API接口代码)

被调用:
- launcher/main.py (启动器)
- 2、run_gradio.ps1 (Gradio界面)
- 4、run_npmgui.ps1 (青龙前端)
- 用户手动运行

修改注意事项:
- 尽量不要修改，除非API启动流程改变
- 修改前请查看FILE_INDEX.md了解用途

更多信息请参考:
- .ai-context/FILE_INDEX.md
- .ai-context/KNOWLEDGE_GRAPH.md
#>

# ============= Command Line Parameters | 命令行参数 =====================
param(
  [int]$Port = 8001,                          # Server port
  [string]$ServerHost = "127.0.0.1"                 # Server host
)

# ============= DO NOT MODIFY CONTENTS BELOW | 请勿修改下方内容 =====================
# Set environment variables
Set-Location $PSScriptRoot
$env:PYTHONPATH = "$PSScriptRoot$([System.IO.Path]::PathSeparator)$($env:PYTHONPATH)"

$Env:HF_HOME = "huggingface"
$Env:XFORMERS_FORCE_DISABLE_TRITON = "1"
$Env:HF_ENDPOINT = "https://hf-mirror.com"
$Env:PILLOW_IGNORE_XMP_DATA_IS_TOO_LONG = "1"
$Env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
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
[void]$ext_args.Add("--host")
[void]$ext_args.Add($ServerHost)

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
& $uv_path run $uv_args acestep/api_server.py $ext_args

Write-Output "Start finished"
