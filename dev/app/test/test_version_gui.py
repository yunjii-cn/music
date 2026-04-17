
#!/usr/bin/env python3
"""测试版本管理器GUI"""

import sys
from pathlib import Path

base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

print("=" * 80)
print("测试版本管理器")
print("=" * 80)

from PyQt6.QtWidgets import QApplication
from version_manager import HybridVersionManagerDialog

app = QApplication(sys.argv)

# 创建测试窗口
class FakeMainWindow:
    def __init__(self):
        self.base_dir = str(base_dir)

fake_main = FakeMainWindow()

print("\n[1] 创建 HybridVersionManagerDialog (as_widget=True)...")
vm = HybridVersionManagerDialog(None, fake_main.base_dir, as_widget=True)

print(f"\n[2] 检查属性:")
print(f"  has versions_layout: {hasattr(vm, 'versions_layout')}")
print(f"  has version_history: {hasattr(vm, 'version_history')}")
if hasattr(vm, 'version_history'):
    print(f"  version_history size: {len(vm.version_history)}")

print(f"\n[3] 检查 _get_available_exe_versions:")
try:
    versions = vm._get_available_exe_versions()
    print(f"  找到 {len(versions)} 个版本")
    for v in versions[:5]:
        print(f"    - v{v['version']}: {v['name']}, available={v.get('available')}")
except Exception as e:
    print(f"  错误: {e}")
    import traceback
    traceback.print_exc()

print("\n[4] 检查 _load_exe_versions:")
try:
    vm._load_exe_versions()
    print("  _load_exe_versions 执行成功")
except Exception as e:
    print(f"  错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("完成")
print("=" * 80)
