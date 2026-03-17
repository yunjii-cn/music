#!/usr/bin/env powershell
# ACE-Step Launcher - 无弹出窗口版本

Add-Type -AssemblyName PresentationFramework

# 主窗口 XAML
$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="ACE-Step 启动器"
        Width="800"
        Height="600"
        WindowStartupLocation="CenterScreen"
        ResizeMode="NoResize">
    <Grid Margin="10">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        
        <!-- 标题 -->
        <TextBlock Grid.Row="0" Text="ACE-Step 启动器" FontSize="24" FontWeight="Bold" 
                   HorizontalAlignment="Center" Margin="0,10,0,20"/>
        
        <!-- 命令行输出 -->
        <ScrollViewer Grid.Row="1" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Auto">
            <TextBlock x:Name="ConsoleOutput" FontFamily="Consolas" FontSize="12" TextWrapping="Wrap"/>
        </ScrollViewer>
        
        <!-- 按钮面板 -->
        <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Center" Margin="0,20,0,10">
            <Button x:Name="BtnMusic" Content="启动音乐演练场" Width="150" Height="40" 
                    FontSize="14" Margin="5" Background="#FF4CAF50" Foreground="#FFFFFFFF"/>
            <Button x:Name="BtnLora" Content="启动青龙 LoRA 训练器" Width="180" Height="40" 
                    FontSize="14" Margin="5" Background="#FF2196F3" Foreground="#FFFFFFFF"/>
            <Button x:Name="BtnExit" Content="退出" Width="100" Height="40" 
                    FontSize="14" Margin="5" Background="#FF9E9E9E" Foreground="#FFFFFFFF"/>
        </StackPanel>
    </Grid>
</Window>
"@

# 解析 XAML
$reader = [System.Xml.XmlReader]::Create([System.IO.StringReader]$xaml)
$window = [System.Windows.Markup.XamlReader]::Load($reader)

# 获取控件引用
$consoleOutput = $window.FindName("ConsoleOutput")
$btnMusic = $window.FindName("BtnMusic")
$btnLora = $window.FindName("BtnLora")
$btnExit = $window.FindName("BtnExit")

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 更新命令行输出
function Update-Output($message) {
    $consoleOutput.Dispatcher.Invoke([Action]{ $consoleOutput.Text += "$message`n" }, "Normal")
}

# 启动音乐演练场
$btnMusic.Add_Click({
    Update-Output "正在启动音乐演练场..."
    
    # 创建临时批处理文件
    $batContent = @"
@echo off
setlocal

:: 启动音乐演练场
echo 正在检查环境...

:: 检查 uv 是否安装
if not exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo 环境未安装，正在执行安装...
    powershell.exe -ExecutionPolicy Bypass -File "$scriptDir\1、install-uv-qinglong.ps1"
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
start powershell.exe -NoExit -Command ". '.\2、run_gradio.ps1'"

:: 等待 5 秒，然后打开浏览器
ping 127.0.0.1 -n 6 >nul
start "" "http://127.0.0.1:7860"

echo 音乐演练场已启动，浏览器已打开！
"@
    
    $batFile = "$env:TEMP\start-music-arena.bat"
    $batContent | Out-File -FilePath $batFile -Encoding UTF8
    
    # 执行批处理文件
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c $batFile" -WindowStyle Hidden
    
    Update-Output "音乐演练场已启动，正在打开浏览器..."
})

# 启动青龙 LoRA 训练器
$btnLora.Add_Click({
    Update-Output "正在启动青龙 LoRA 训练器..."
    
    # 创建临时批处理文件
    $batContent = @"
@echo off
setlocal

:: 启动青龙 LoRA 训练器
echo 正在启动 NPM GUI...
cd "$scriptDir"
start powershell.exe -NoExit -Command ". '.\4、run_npmgui.ps1'"

:: 等待 5 秒，然后打开浏览器
ping 127.0.0.1 -n 6 >nul
start "" "http://localhost:3000"

echo 青龙 LoRA 训练器已启动，浏览器已打开！
"@
    
    $batFile = "$env:TEMP\start-lora-trainer.bat"
    $batContent | Out-File -FilePath $batFile -Encoding UTF8
    
    # 执行批处理文件
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c $batFile" -WindowStyle Hidden
    
    Update-Output "青龙 LoRA 训练器已启动，正在打开浏览器..."
})

# 退出
$btnExit.Add_Click({
    $window.Close()
})

# 显示窗口
$window.ShowDialog() | Out-Null
