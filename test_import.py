#!/usr/bin/env python3
"""
测试导入脚本，用于验证version_manager模块是否能正确导入
"""

import sys
import os

# 添加launcher目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'launcher'))

try:
    from version_manager import VersionManagerDialog
    print("✓ 成功导入 VersionManagerDialog")
    print(f"VersionManagerDialog 类型: {type(VersionManagerDialog)}")
    print("导入测试通过！")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
