#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试版本列表问题
"""

import sys
from pathlib import Path
import re

# 添加 app 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from version_manager import HybridVersionManagerDialog

def test_version_loading():
    """测试版本加载"""
    base_dir = str(Path(__file__).parent.parent)
    print(f"Base directory: {base_dir}")
    
    dialog = HybridVersionManagerDialog(None, base_dir, as_widget=True)
    
    print("\n--- Version history ---")
    print(f"Number of versions in history: {len(dialog.version_history)}")
    for v in list(dialog.version_history.keys())[:5]:
        print(f"  {v}")
    
    print("\n--- Getting available EXE versions ---")
    versions = dialog._get_available_exe_versions()
    print(f"Number of available versions: {len(versions)}")
    for v in versions:
        print(f"  v{v['version']} - available: {v['available']} - name: {v['name']}")
    
    print("\n--- Testing _load_exe_versions ---")
    dialog._load_exe_versions()

if __name__ == "__main__":
    test_version_loading()
