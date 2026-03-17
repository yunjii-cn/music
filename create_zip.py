#!/usr/bin/env python3
"""
创建发布ZIP包
"""

import zipfile
import os
from pathlib import Path

# 构建目录
build_dir = Path('build-release')
# ZIP文件路径
zip_name = 'qinglong-music-trainer-2.8.3-202603171444.zip'
zip_path = build_dir / 'dist' / zip_name

# 确保dist目录存在
os.makedirs(build_dir / 'dist', exist_ok=True)

print(f"创建ZIP包: {zip_path}")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(build_dir):
        # 排除不需要的目录
        if 'dist' in root or 'build' in root or '__pycache__' in root:
            continue
        
        for file in files:
            # 排除不需要的文件
            if file.endswith('.pyc') or file.endswith('.spec'):
                continue
            
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, build_dir)
            zipf.write(file_path, arcname)
            print(f"添加: {arcname}")

print(f"\n✅ 已创建: {zip_path}")
print(f"📦 输出文件: {zip_path}")