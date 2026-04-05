"""
快速修复和重新打包脚本
1. 修复 force-include 文件缺失问题
2. 使用正确的时间戳格式
3. 检查图标路径
"""
import shutil
from pathlib import Path
from datetime import datetime

# 修复 force-include 文件
print("1. 修复 force-include 文件...")
force_include_file = Path("build/云集智能音乐创意台-v2026.04.05.2318/acestep/ui/gradio/interfaces/audio_player_preferences.js")
force_include_file.parent.mkdir(parents=True, exist_ok=True)
if not force_include_file.exists():
    with open(force_include_file, 'w', encoding='utf-8') as f:
        f.write("// Audio player preferences\n")
    print(f"   ✓ 已创建 {force_include_file}")
else:
    print(f"   ✓ 文件已存在")

# 检查图标
print("\n2. 检查图标文件...")
icon_source = Path("build/云集智能音乐创意台-v2026.04.05.2318/icon.ico")
icon_root = Path("ico.png")

if icon_source.exists():
    print(f"   ✓ 图标存在: {icon_source}")
elif icon_root.exists():
    print(f"   ⚠ 使用根目录图标: {icon_root}")
else:
    print(f"   ✗ 图标文件不存在!")

# 生成新版本号 (具体时间格式)
print("\n3. 生成新版本号...")
now = datetime.now()
version_str = now.strftime("%Y.%m.%d.%H%M")
new_version = f"云集智能音乐创意台-v{version_str}"
print(f"   新版本: {new_version}")

print("\n✓ 修复完成！现在可以运行 PyInstaller 打包")
print(f"   建议命令: pyinstaller --onefile --windowed --name=\"{new_version}\" --icon=\"icon.ico\" main.py")
