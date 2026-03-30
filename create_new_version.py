
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import shutil
import sys

# 源版本
source_name = "云集智能音乐创意台-v2026.03.30.0439"
src_dir = Path("build") / source_name

# 新版本
new_version = datetime.now().strftime("%Y.%m.%d.%H%M")
dst_name = f"云集智能音乐创意台-v{new_version}"
dst_dir = Path("build") / dst_name

print(f"从 {source_name}")
print(f"复制到 {dst_name}")

if src_dir.exists():
    shutil.copytree(src_dir, dst_dir)
    print(f"✓ 新版本文件夹创建成功: {dst_dir}")
    print(dst_dir)  # 输出路径供后续使用
else:
    print(f"✗ 源版本不存在: {src_dir}")
    sys.exit(1)

