# 将logo512X512.png转换为ICO格式

Write-Host "检查logo512X512.png文件..." -ForegroundColor Yellow

if (Test-Path "logo512X512.png") {
    Write-Host "找到logo512X512.png文件" -ForegroundColor Green
    
    # 检查是否安装了Pillow
    if (-not (pip list | Select-String -Pattern "Pillow")) {
        Write-Host "正在安装Pillow..." -ForegroundColor Yellow
        pip install Pillow
    }
    
    # 创建Python脚本用于转换
    $convertScript = @"
from PIL import Image
import os

# 打开PNG图像
img = Image.open('logo512X512.png')

# 确保图像是RGB模式
if img.mode != 'RGB':
    img = img.convert('RGB')

# 保存为ICO格式
img.save('logo512X512.ico', format='ICO', sizes=[(512, 512), (256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

print('转换完成: logo512X512.ico')
"@
    
    # 写入转换脚本
    $convertScript | Out-File -FilePath "convert-icon.py" -Encoding utf8
    
    # 执行转换
    Write-Host "正在转换PNG到ICO..." -ForegroundColor Yellow
    python convert-icon.py
    
    # 检查转换结果
    if (Test-Path "logo512X512.ico") {
        Write-Host "转换成功！创建了logo512X512.ico文件" -ForegroundColor Green
        
        # 清理临时文件
        Remove-Item "convert-icon.py" -ErrorAction SilentlyContinue
    } else {
        Write-Host "转换失败！" -ForegroundColor Red
    }
} else {
    Write-Host "logo512X512.png文件不存在！" -ForegroundColor Red
}
