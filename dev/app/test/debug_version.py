
#!/usr/bin/env python3
"""调试版本列表加载"""

import sys
from pathlib import Path

base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

print("=" * 80)
print("调试版本列表加载")
print("=" * 80)

print(f"\nbase_dir = {base_dir}")
print(f"base_dir exists: {base_dir.exists()}")

# 导入版本管理器
try:
    from version_manager import HybridVersionManagerDialog
    
    print("\n[1] 测试 HybridVersionManagerDialog 初始化")
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # 创建一个测试用的假 main_window
    class FakeMainWindow:
        def __init__(self):
            self.base_dir = str(base_dir)
    
    fake_main = FakeMainWindow()
    
    # 创建版本管理器
    print("  创建 HybridVersionManagerDialog...")
    vm = HybridVersionManagerDialog(fake_main, fake_main)
    
    print("\n[2] 检查 _load_version_history")
    print(f"  version_history keys: {list(vm.version_history.keys())[:5] if vm.version_history else '空'}")
    
    print("\n[3] 检查 _get_available_exe_versions")
    versions = vm._get_available_exe_versions()
    print(f"  找到 {len(versions)} 个EXE版本:")
    for v in versions[:10]:
        print(f"    - v{v['version']} ({v['name']}): available={v.get('available')}, path={v.get('path')}")
    
    print("\n[4] 检查可能的路径")
    print(f"  Path(self.base_dir): {Path(fake_main.base_dir)}")
    print(f"  Path(self.base_dir)/ver: {Path(fake_main.base_dir)/'ver'} exists? {(Path(fake_main.base_dir)/'ver').exists()}")
    print(f"  Path(self.base_dir).parent: {Path(fake_main.base_dir).parent}")
    print(f"  Path(self.base_dir).parent/ver: {Path(fake_main.base_dir).parent/'ver'} exists? {(Path(fake_main.base_dir).parent/'ver').exists()}")
    
    if (Path(fake_main.base_dir).parent/'ver').exists():
        print(f"\n  ver 文件夹内容:")
        for f in (Path(fake_main.base_dir).parent/'ver').iterdir():
            print(f"    - {f.name}")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
