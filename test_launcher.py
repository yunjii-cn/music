#!/usr/bin/env python3
"""
测试启动器的路径解析功能
"""

import os
import sys
import time
import subprocess
import psutil

# 测试函数
def test_launcher():
    """测试启动器的路径解析功能"""
    print("=" * 60)
    print("测试启动器路径解析功能")
    print("=" * 60)
    
    # 查找最新的启动器EXE
    exe_files = []
    for file in os.listdir('.'):
        if file.startswith('ACE-Step-Launcher-v') and file.endswith('.exe'):
            exe_files.append(file)
    
    if not exe_files:
        print("❌ 未找到启动器EXE文件")
        return False
    
    # 按版本号排序，取最新的
    exe_files.sort(reverse=True)
    latest_exe = exe_files[0]
    print(f"📦 找到最新的启动器: {latest_exe}")
    
    # 启动启动器
    print("🚀 启动启动器...")
    process = subprocess.Popen([latest_exe], cwd='.')
    
    # 等待启动器启动
    time.sleep(5)
    
    # 检查启动器是否在运行
    is_running = False
    for proc in psutil.process_iter(['pid', 'name']):
        if latest_exe in proc.info['name']:
            is_running = True
            print(f"✅ 启动器已成功启动 (PID: {proc.info['pid']})")
            break
    
    if not is_running:
        print("❌ 启动器启动失败")
        return False
    
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_launcher()
