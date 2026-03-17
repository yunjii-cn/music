#!/usr/bin/env powershell
# ACE-Step Basic Launcher
# 基本启动器

Add-Type -AssemblyName System.Windows.Forms

# 创建主窗口
$form = New-Object System.Windows.Forms.Form
$form.Text = "ACE-Step 启动器"
$form.Width = 400
$form.Height = 200
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false

# 创建标题标签
$label = New-Object System.Windows.Forms.Label
$label.Text = "ACE-Step 启动器"
$label.Font = New-Object System.Drawing.Font("Arial", 16, [System.Drawing.FontStyle]::Bold)
$label.Location = New-Object System.Drawing.Point(100, 20)
$label.Size = New-Object System.Drawing.Size(200, 30)
$label.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($label)

# 创建状态标签
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "点击按钮启动服务"
$statusLabel.Location = New-Object System.Drawing.Point(50, 60)
$statusLabel.Size = New-Object System.Drawing.Size(300, 30)
$statusLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($statusLabel)

# 创建启动按钮
$startButton = New-Object System.Windows.Forms.Button
$startButton.Text = "启动 ACE-Step"
$startButton.Location = New-Object System.Drawing.Point(100, 100)
$startButton.Size = New-Object System.Drawing.Size(200, 40)
$startButton.Font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
$startButton.BackColor = [System.Drawing.Color]::FromArgb(76, 175, 80)
$startButton.ForeColor = [System.Drawing.Color]::White

# 按钮点击事件
$startButton.Add_Click({
    $statusLabel.Text = "正在检查环境..."
    $form.Refresh()
    
    try {
        # 检查环境
        $uv_path = "$HOME\.local\bin\uv.exe"
        $env_exists = Test-Path $uv_path
        
        if (-not $env_exists) {
            $statusLabel.Text = "环境未安装，正在执行安装..."
            $form.Refresh()
            
            # 运行安装脚本
            & "$PSScriptRoot\1、install-uv-qinglong.ps1"
            
            if ($LASTEXITCODE -ne 0) {
                $statusLabel.Text = "安装失败，请检查错误信息"
                return
            }
        }
        
        # 检查 bitsandbytes
        $bitsandbytes_installed = $false
        try {
            $output = & $uv_path pip list | Select-String "bitsandbytes"
            if ($output) {
                $bitsandbytes_installed = $true
            }
        } catch {
            # 忽略错误
        }
        
        if (-not $bitsandbytes_installed) {
            $statusLabel.Text = "正在安装 bitsandbytes..."
            $form.Refresh()
            
            & $uv_path pip install bitsandbytes
        }
        
        # 启动所有服务
        $statusLabel.Text = "正在启动所有服务..."
        $form.Refresh()
        
        # 启动 Gradio Web UI
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\2、run_gradio.ps1'"
        
        # 等待 3 秒
        Start-Sleep -Seconds 3
        
        # 启动 API 服务器
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\3、run_server.ps1'"
        
        # 等待 3 秒
        Start-Sleep -Seconds 3
        
        # 启动 NPM GUI
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\4、run_npmgui.ps1'"
        
        # 等待 5 秒，然后打开浏览器
        Start-Sleep -Seconds 5
        Start-Process "http://127.0.0.1:7860"
        
        $statusLabel.Text = "所有服务已启动，浏览器已打开！"
        $form.Refresh()
    } catch {
        $statusLabel.Text = "启动失败: $($_.Exception.Message)"
        $form.Refresh()
    }
})

$form.Controls.Add($startButton)

# 显示窗口
$form.ShowDialog() | Out-Null
