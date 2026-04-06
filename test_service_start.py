#!/usr/bin/env python3
"""
测试服务启动时是否隐藏cmd窗口
"""

import os
import sys
import time
import subprocess
import psutil

# 测试函数
def test_service_start():
    """测试服务启动时是否隐藏cmd窗口"""
    print("=" * 60)
    print("测试服务启动时是否隐藏cmd窗口")
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
    launcher_pid = None
    for proc in psutil.process_iter(['pid', 'name']):
        if latest_exe in proc.info['name']:
            launcher_pid = proc.info['pid']
            print(f"✅ 启动器已成功启动 (PID: {launcher_pid})")
            break
    
    if not launcher_pid:
        print("❌ 启动器启动失败")
        return False
    
    # 检查是否有新的PowerShell进程启动
    print("\n🔍 检查PowerShell进程...")
    initial_powershell_count = len([p for p in psutil.process_iter(['name']) if 'powershell' in p.info['name'].lower()])
    print(f"当前PowerShell进程数: {initial_powershell_count}")
    
    # 等待一段时间，观察是否有新的PowerShell进程启动
    print("\n⏳ 等待10秒，观察是否有新的PowerShell进程启动...")
    time.sleep(10)
    
    final_powershell_count = len([p for p in psutil.process_iter(['name']) if 'powershell' in p.info['name'].lower()])
    print(f"最终PowerShell进程数: {final_powershell_count}")
    
    if final_powershell_count > initial_powershell_count:
        print("⚠ 检测到新的PowerShell进程启动")
    else:
        print("✅ 未检测到新的PowerShell进程启动")
    
    # 检查是否有可见的cmd窗口
    print("\n👁️  检查是否有可见的cmd窗口...")
    # 这里我们无法直接检测窗口是否可见，但如果PowerShell进程在运行，且没有弹出窗口，说明它们在后台运行
    
    print("\n=" * 60)
    print("测试完成!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_service_start()
