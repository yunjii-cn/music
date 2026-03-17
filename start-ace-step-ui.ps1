#!/usr/bin/env powershell
# ACE-Step UI Launcher
# 图形界面启动器，支持分别启动不同的前端

Add-Type -AssemblyName System.Windows.Forms

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 创建主窗口
$form = New-Object System.Windows.Forms.Form
$form.Text = "ACE-Step UI 启动器"
$form.Width = 450
$form.Height = 320
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false

# 创建标题标签
$label = New-Object System.Windows.Forms.Label
$label.Text = "ACE-Step UI 启动器"
$label.Font = New-Object System.Drawing.Font("Arial", 18, [System.Drawing.FontStyle]::Bold)
$label.Location = New-Object System.Drawing.Point(100, 20)
$label.Size = New-Object System.Drawing.Size(250, 40)
$label.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($label)

# 创建状态标签
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "请选择要启动的UI界面"
$statusLabel.Location = New-Object System.Drawing.Point(50, 70)
$statusLabel.Size = New-Object System.Drawing.Size(350, 30)
$statusLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($statusLabel)

# 创建启动音乐演练场按钮
$btnMusic = New-Object System.Windows.Forms.Button
$btnMusic.Text = "启动音乐演练场 (Gradio UI)"
$btnMusic.Location = New-Object System.Drawing.Point(75, 120)
$btnMusic.Size = New-Object System.Drawing.Size(300, 50)
$btnMusic.Font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
$btnMusic.BackColor = [System.Drawing.Color]::FromArgb(76, 175, 80)
$btnMusic.ForeColor = [System.Drawing.Color]::White

# 创建启动青龙 LoRA 训练器按钮
$btnLora = New-Object System.Windows.Forms.Button
$btnLora.Text = "启动青龙 LoRA 训练器 (NPM UI)"
$btnLora.Location = New-Object System.Drawing.Point(75, 180)
$btnLora.Size = New-Object System.Drawing.Size(300, 50)
$btnLora.Font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
$btnLora.BackColor = [System.Drawing.Color]::FromArgb(33, 150, 243)
$btnLora.ForeColor = [System.Drawing.Color]::White

# 创建退出按钮
$btnExit = New-Object System.Windows.Forms.Button
$btnExit.Text = "退出"
$btnExit.Location = New-Object System.Drawing.Point(75, 240)
$btnExit.Size = New-Object System.Drawing.Size(300, 40)
$btnExit.Font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
$btnExit.BackColor = [System.Drawing.Color]::FromArgb(244, 67, 54)
$btnExit.ForeColor = [System.Drawing.Color]::White

# 按钮点击事件 - 启动音乐演练场
$btnMusic.Add_Click({
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
            & "$scriptDir\1、install-uv-qinglong.ps1"
            
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
        
        # 启动音乐演练场
        $statusLabel.Text = "正在启动音乐演练场..."
        $form.Refresh()
        
        # 启动 Gradio Web UI
        $cmd = "cd '$scriptDir'; . '.\2、run_gradio.ps1'"
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $cmd
        
        # 等待 5 秒，然后打开浏览器
        Start-Sleep -Seconds 5
        Start-Process "http://127.0.0.1:7860"
        
        $statusLabel.Text = "音乐演练场已启动，浏览器已打开！"
        $form.Refresh()
    } catch {
        $statusLabel.Text = "启动失败: $($_.Exception.Message)"
        $form.Refresh()
    }
})

# 按钮点击事件 - 启动青龙 LoRA 训练器
$btnLora.Add_Click({
    $statusLabel.Text = "正在启动青龙 LoRA 训练器..."
    $form.Refresh()
    
    try {
        # 启动 NPM GUI
        $cmd = "cd '$scriptDir'; . '.\4、run_npmgui.ps1'"
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $cmd
        
        # 等待 5 秒，然后打开浏览器
        Start-Sleep -Seconds 5
        Start-Process "http://localhost:3000"
        
        $statusLabel.Text = "青龙 LoRA 训练器已启动，浏览器已打开！"
        $form.Refresh()
    } catch {
        $statusLabel.Text = "启动失败: $($_.Exception.Message)"
        $form.Refresh()
    }
})

# 按钮点击事件 - 退出
$btnExit.Add_Click({
    $form.Close()
})

# 添加按钮到窗口
$form.Controls.Add($btnMusic)
$form.Controls.Add($btnLora)
$form.Controls.Add($btnExit)

# 显示窗口
$form.ShowDialog() | Out-Null
