#!/usr/bin/env powershell
# ACE-Step Full GUI Launcher
# 完整图形界面启动器，启动所有服务并自动打开浏览器

Add-Type -AssemblyName PresentationFramework

# 主窗口函数
function Show-ACELauncher {
    # 创建窗口
    $window = New-Object System.Windows.Window
    $window.Title = "ACE-Step 启动器"
    $window.Width = 400
    $window.Height = 280
    $window.WindowStartupLocation = "CenterScreen"
    $window.ResizeMode = "NoResize"
    
    # 创建网格布局
    $grid = New-Object System.Windows.Controls.Grid
    $grid.Margin = "20"
    
    # 定义行
    $row1 = New-Object System.Windows.Controls.RowDefinition
    $row1.Height = "Auto"
    $row2 = New-Object System.Windows.Controls.RowDefinition
    $row2.Height = "Auto"
    $row3 = New-Object System.Windows.Controls.RowDefinition
    $row3.Height = "Auto"
    $row4 = New-Object System.Windows.Controls.RowDefinition
    $row4.Height = "Auto"
    $row5 = New-Object System.Windows.Controls.RowDefinition
    $row5.Height = "Auto"
    
    $grid.RowDefinitions.Add($row1)
    $grid.RowDefinitions.Add($row2)
    $grid.RowDefinitions.Add($row3)
    $grid.RowDefinitions.Add($row4)
    $grid.RowDefinitions.Add($row5)
    
    # 标题
    $title = New-Object System.Windows.Controls.TextBlock
    $title.Text = "ACE-Step 启动器"
    $title.FontSize = 24
    $title.FontWeight = "Bold"
    $title.HorizontalAlignment = "Center"
    $title.Margin = "0,10,0,20"
    [System.Windows.Controls.Grid]::SetRow($title, 0)
    
    # 状态信息
    $status = New-Object System.Windows.Controls.TextBlock
    $status.Text = "点击按钮启动所有服务"
    $status.FontSize = 14
    $status.HorizontalAlignment = "Center"
    $status.Margin = "0,0,0,20"
    [System.Windows.Controls.Grid]::SetRow($status, 1)
    
    # 按钮1：一键启动所有服务
    $btnStart = New-Object System.Windows.Controls.Button
    $btnStart.Content = "一键启动所有服务"
    $btnStart.Width = 350
    $btnStart.Height = 50
    $btnStart.FontSize = 16
    $btnStart.FontWeight = "Bold"
    $btnStart.Margin = "0,5,0,5"
    $btnStart.Background = "#FF4CAF50"
    $btnStart.Foreground = "#FFFFFFFF"
    [System.Windows.Controls.Grid]::SetRow($btnStart, 2)
    
    # 按钮2：仅启动 Gradio
    $btnGradio = New-Object System.Windows.Controls.Button
    $btnGradio.Content = "仅启动 Gradio Web UI"
    $btnGradio.Width = 350
    $btnGradio.Height = 40
    $btnGradio.FontSize = 14
    $btnGradio.Margin = "0,5,0,5"
    [System.Windows.Controls.Grid]::SetRow($btnGradio, 3)
    
    # 按钮3：退出
    $btnExit = New-Object System.Windows.Controls.Button
    $btnExit.Content = "退出"
    $btnExit.Width = 350
    $btnExit.Height = 40
    $btnExit.FontSize = 14
    $btnExit.Margin = "0,10,0,0"
    $btnExit.Background = "#FFE0E0E0"
    [System.Windows.Controls.Grid]::SetRow($btnExit, 4)
    
    # 添加控件到网格
    $grid.Children.Add($title)
    $grid.Children.Add($status)
    $grid.Children.Add($btnStart)
    $grid.Children.Add($btnGradio)
    $grid.Children.Add($btnExit)
    
    # 添加网格到窗口
    $window.Content = $grid
    
    # 按钮点击事件
    $btnStart.Add_Click({
        $status.Text = "正在检查环境..."
        $window.Dispatcher.Invoke([Action]{}, "Normal")
        
        try {
            # 检查环境
            $uv_path = "$HOME\.local\bin\uv.exe"
            $env_exists = Test-Path $uv_path
            
            if (-not $env_exists) {
                $status.Text = "环境未安装，正在执行安装..."
                $window.Dispatcher.Invoke([Action]{}, "Normal")
                
                # 运行安装脚本
                & "$PSScriptRoot\1、install-uv-qinglong.ps1"
                
                if ($LASTEXITCODE -ne 0) {
                    $status.Text = "安装失败，请检查错误信息"
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
                $status.Text = "正在安装 bitsandbytes..."
                $window.Dispatcher.Invoke([Action]{}, "Normal")
                
                & $uv_path pip install bitsandbytes
            }
            
            # 启动所有服务
            $status.Text = "正在启动所有服务..."
            $window.Dispatcher.Invoke([Action]{}, "Normal")
            
            # 启动 Gradio Web UI
            $script_path = "$PSScriptRoot\2、run_gradio.ps1"
            Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\2、run_gradio.ps1'"
            
            # 等待 3 秒
            Start-Sleep -Seconds 3
            
            # 启动 API 服务器
            $api_script = "$PSScriptRoot\3、run_server.ps1"
            Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\3、run_server.ps1'"
            
            # 等待 3 秒
            Start-Sleep -Seconds 3
            
            # 启动 NPM GUI
            $npm_script = "$PSScriptRoot\4、run_npmgui.ps1"
            Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\4、run_npmgui.ps1'"
            
            # 等待 5 秒，然后打开浏览器
            Start-Sleep -Seconds 5
            Start-Process "http://127.0.0.1:7860"
            
            $status.Text = "所有服务已启动，浏览器已打开！"
        } catch {
            $status.Text = "启动失败: $($_.Exception.Message)"
        }
    })
    
    $btnGradio.Add_Click({
        $status.Text = "正在检查环境..."
        $window.Dispatcher.Invoke([Action]{}, "Normal")
        
        try {
            # 检查环境
            $uv_path = "$HOME\.local\bin\uv.exe"
            $env_exists = Test-Path $uv_path
            
            if (-not $env_exists) {
                $status.Text = "环境未安装，正在执行安装..."
                $window.Dispatcher.Invoke([Action]{}, "Normal")
                
                # 运行安装脚本
                & "$PSScriptRoot\1、install-uv-qinglong.ps1"
                
                if ($LASTEXITCODE -ne 0) {
                    $status.Text = "安装失败，请检查错误信息"
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
                $status.Text = "正在安装 bitsandbytes..."
                $window.Dispatcher.Invoke([Action]{}, "Normal")
                
                & $uv_path pip install bitsandbytes
            }
            
            # 启动 Gradio Web UI
            $status.Text = "正在启动 Gradio Web UI..."
            $window.Dispatcher.Invoke([Action]{}, "Normal")
            
            $script_path = "$PSScriptRoot\2、run_gradio.ps1"
            Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; . '.\2、run_gradio.ps1'"
            
            # 等待 5 秒，然后打开浏览器
            Start-Sleep -Seconds 5
            Start-Process "http://127.0.0.1:7860"
            
            $status.Text = "Gradio Web UI 已启动，浏览器已打开！"
        } catch {
            $status.Text = "启动失败: $($_.Exception.Message)"
        }
    })
    
    $btnExit.Add_Click({
        $window.Close()
    })
    
    # 显示窗口
    $window.ShowDialog() | Out-Null
}

# 运行启动器
Show-ACELauncher
