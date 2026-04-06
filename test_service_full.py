#!/usr/bin/env python3
"""
完整测试服务启动功能，验证所有输出是否显示在主窗口中
"""

import os
import sys
import time
import subprocess
import psutil

# 测试函数
def test_service_full():
    """完整测试服务启动功能"""
    print("=" * 60)
    print("完整测试服务启动功能")
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
    
    # 检查是否有可见的cmd窗口
    print("\n👁️  检查是否有可见的cmd窗口...")
    print("如果没有看到弹出的cmd窗口，说明隐藏成功")
    
    # 等待用户确认
    input("\n请确认启动器窗口是否正常显示，且没有弹出cmd窗口。按Enter键继续...")
    
    # 检查服务状态
    print("\n🔍 检查服务状态...")
    print("请在启动器窗口中点击'启动青龙训练器'或'启动音乐演练场'按钮，测试服务启动功能")
    print("观察是否有cmd窗口弹出，以及输出是否显示在主窗口中")
    
    # 等待用户测试
    input("\n测试完成后，按Enter键继续...")
    
    # 清理
    print("\n🧹 清理测试进程...")
    try:
        launcher_proc = psutil.Process(launcher_pid)
        launcher_proc.terminate()
        launcher_proc.wait(timeout=5)
        print("✅ 启动器进程已终止")
    except:
        print("⚠ 启动器进程终止失败")
    
    print("\n=" * 60)
    print("测试完成!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_service_full()
