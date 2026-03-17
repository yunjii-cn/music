#!/usr/bin/env powershell
# ACE-Step UI Launcher with embedded console

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 创建主窗口
$window = New-Object System.Windows.Window
$window.Title = "ACE-Step 启动器"
$window.Width = 800
$window.Height = 600
$window.WindowStartupLocation = "CenterScreen"
$window.ResizeMode = "NoResize"

# 创建网格布局
$grid = New-Object System.Windows.Controls.Grid
$grid.Margin = "10"

# 定义行和列
$row1 = New-Object System.Windows.Controls.RowDefinition
$row1.Height = "Auto"
$row2 = New-Object System.Windows.Controls.RowDefinition
$row2.Height = "*"
$row3 = New-Object System.Windows.Controls.RowDefinition
$row3.Height = "Auto"

$grid.RowDefinitions.Add($row1)
$grid.RowDefinitions.Add($row2)
$grid.RowDefinitions.Add($row3)

# 标题
$title = New-Object System.Windows.Controls.TextBlock
$title.Text = "ACE-Step 启动器"
$title.FontSize = 24
$title.FontWeight = "Bold"
$title.HorizontalAlignment = "Center"
$title.Margin = "0,10,0,20"
[System.Windows.Controls.Grid]::SetRow($title, 0)

# 命令行输出区域
$consoleOutput = New-Object System.Windows.Controls.TextBlock
$consoleOutput.Text = "命令行输出将显示在这里..."
$consoleOutput.FontFamily = "Consolas"
$consoleOutput.FontSize = 12
$consoleOutput.TextWrapping = "Wrap"
$consoleOutput.VerticalAlignment = "Top"

$scrollViewer = New-Object System.Windows.Controls.ScrollViewer
$scrollViewer.Content = $consoleOutput
$scrollViewer.VerticalScrollBarVisibility = "Auto"
$scrollViewer.HorizontalScrollBarVisibility = "Auto"
[System.Windows.Controls.Grid]::SetRow($scrollViewer, 1)

# 按钮面板
$buttonPanel = New-Object System.Windows.Controls.StackPanel
$buttonPanel.Orientation = "Horizontal"
$buttonPanel.HorizontalAlignment = "Center"
$buttonPanel.Margin = "0,20,0,10"

# 启动音乐演练场按钮
$btnMusic = New-Object System.Windows.Controls.Button
$btnMusic.Content = "启动音乐演练场"
$btnMusic.Width = 150
$btnMusic.Height = 40
$btnMusic.FontSize = 14
$btnMusic.Margin = "5"
$btnMusic.Background = "#FF4CAF50"
$btnMusic.Foreground = "#FFFFFFFF"

# 启动青龙 LoRA 训练器按钮
$btnLora = New-Object System.Windows.Controls.Button
$btnLora.Content = "启动青龙 LoRA 训练器"
$btnLora.Width = 180
$btnLora.Height = 40
$btnLora.FontSize = 14
$btnLora.Margin = "5"
$btnLora.Background = "#FF2196F3"
$btnLora.Foreground = "#FFFFFFFF"

# 退出按钮
$btnExit = New-Object System.Windows.Controls.Button
$btnExit.Content = "退出"
$btnExit.Width = 100
$btnExit.Height = 40
$btnExit.FontSize = 14
$btnExit.Margin = "5"
$btnExit.Background = "#FF9E9E9E"
$btnExit.Foreground = "#FFFFFFFF"

# 添加按钮到面板
$buttonPanel.Children.Add($btnMusic)
$buttonPanel.Children.Add($btnLora)
$buttonPanel.Children.Add($btnExit)

[System.Windows.Controls.Grid]::SetRow($buttonPanel, 2)

# 添加控件到网格
$grid.Children.Add($title)
$grid.Children.Add($scrollViewer)
$grid.Children.Add($buttonPanel)

# 添加网格到窗口
$window.Content = $grid

# 更新命令行输出
function Update-ConsoleOutput($message) {
    $consoleOutput.Dispatcher.Invoke([Action]{ $consoleOutput.Text += "$message`n" }, "Normal")
    $scrollViewer.Dispatcher.Invoke([Action]{ $scrollViewer.ScrollToBottom() }, "Normal")
}

# 按钮点击事件 - 启动音乐演练场
$btnMusic.Add_Click({
    Update-ConsoleOutput "正在启动音乐演练场..."
    
    try {
        # 创建批处理文件
        $batContent = @"
@echo off

:: 启动音乐演练场

echo 正在检查环境...

:: 检查 uv 是否安装
if not exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo 环境未安装，正在执行安装...
    call "$scriptDir\1、install-uv-qinglong.ps1"
    if errorlevel 1 (
        echo 安装失败，请检查错误信息
        pause
        exit /b 1
    )
    echo 环境安装成功！
)

:: 检查 bitsandbytes
powershell.exe -Command "& '%USERPROFILE%\.local\bin\uv.exe' pip list | Select-String 'bitsandbytes'" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 bitsandbytes...
    powershell.exe -Command "& '%USERPROFILE%\.local\bin\uv.exe' pip install bitsandbytes"
    echo bitsandbytes 安装成功！
) else (
    echo bitsandbytes 已安装
)

echo 正在启动 Gradio Web UI...
cd "$scriptDir"
powershell.exe -NoExit -Command ". '.\2、run_gradio.ps1'"

:: 等待 5 秒，然后打开浏览器
ping 127.0.0.1 -n 6 >nul
start "" "http://127.0.0.1:7860"

echo 音乐演练场已启动，浏览器已打开！
pause
"@
        
        $batFile = "$scriptDir\start-music-arena.bat"
        $batContent | Out-File -FilePath $batFile -Encoding UTF8
        
        # 执行批处理文件并捕获输出
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo.FileName = "cmd.exe"
        $process.StartInfo.Arguments = "/c $batFile"
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        $process.StartInfo.CreateNoWindow = $true
        
        $process.OutputDataReceived += { Update-ConsoleOutput $args[1].Data }
        $process.ErrorDataReceived += { Update-ConsoleOutput "错误: $($args[1].Data)" }
        
        $process.Start() | Out-Null
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        $process.WaitForExit()
        
        Update-ConsoleOutput "音乐演练场启动完成！"
    } catch {
        Update-ConsoleOutput "启动失败: $($_.Exception.Message)"
    }
})

# 按钮点击事件 - 启动青龙 LoRA 训练器
$btnLora.Add_Click({
    Update-ConsoleOutput "正在启动青龙 LoRA 训练器..."
    
    try {
        # 创建批处理文件
        $batContent = @"
@echo off

:: 启动青龙 LoRA 训练器

echo 正在启动 NPM GUI...
cd "$scriptDir"
powershell.exe -NoExit -Command ". '.\4、run_npmgui.ps1'"

:: 等待 5 秒，然后打开浏览器
ping 127.0.0.1 -n 6 >nul
start "" "http://localhost:3000"

echo 青龙 LoRA 训练器已启动，浏览器已打开！
pause
"@
        
        $batFile = "$scriptDir\start-lora-trainer.bat"
        $batContent | Out-File -FilePath $batFile -Encoding UTF8
        
        # 执行批处理文件并捕获输出
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo.FileName = "cmd.exe"
        $process.StartInfo.Arguments = "/c $batFile"
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        $process.StartInfo.CreateNoWindow = $true
        
        $process.OutputDataReceived += { Update-ConsoleOutput $args[1].Data }
        $process.ErrorDataReceived += { Update-ConsoleOutput "错误: $($args[1].Data)" }
        
        $process.Start() | Out-Null
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        $process.WaitForExit()
        
        Update-ConsoleOutput "青龙 LoRA 训练器启动完成！"
    } catch {
        Update-ConsoleOutput "启动失败: $($_.Exception.Message)"
    }
})

# 按钮点击事件 - 退出
$btnExit.Add_Click({
    $window.Close()
})

# 显示窗口
$window.ShowDialog() | Out-Null
