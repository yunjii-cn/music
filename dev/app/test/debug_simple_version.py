
#!/usr/bin/env python3
"""简单调试版本列表"""

import sys
from pathlib import Path
import re
from datetime import datetime

base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

print("=" * 80)
print("调试版本列表加载 - 简化版")
print("=" * 80)

print(f"\nbase_dir = {base_dir}")

# 模拟 _get_available_exe_versions
print("\n[1] 检查可能的 ver 文件夹位置")
possible_ver_dirs = [
    base_dir / "ver",
    base_dir.parent / "ver",
    base_dir.parent / "app" / "ver",
]

for ver_dir in possible_ver_dirs:
    exists = ver_dir.exists()
    print(f"  {ver_dir} : {'✓ 存在' if exists else '✗ 不存在'}")
    if exists:
        print(f"    内容: {[f.name for f in ver_dir.glob('*.exe')]}")

# 模拟 _load_version_history
print("\n[2] 检查 version_history.json")
possible_history_paths = [
    base_dir / "version_history.json",
    base_dir / "dist" / "version_history.json",
    base_dir.parent / "app" / "version_history.json",
]

for hpath in possible_history_paths:
    exists = hpath.exists()
    print(f"  {hpath} : {'✓ 存在' if exists else '✗ 不存在'}")
    if exists:
        import json
        try:
            with open(hpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"    keys: {list(data.keys())[:10] if isinstance(data, dict) else type(data)}")
        except Exception as e:
            print(f"    读取错误: {e}")

print("\n" + "=" * 80)
print("完成")
