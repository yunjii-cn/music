#!/usr/bin/env python3
"""
测试步骤状态显示和多线程并行启动功能
"""

import os
import sys
import time
import subprocess
import psutil

# 测试函数
def test_steps():
    """测试步骤状态显示和多线程并行启动功能"""
    print("=" * 60)
    print("测试步骤状态显示和多线程并行启动功能")
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
    
    # 测试步骤状态显示
    print("\n🔍 测试步骤状态显示...")
    print("请在启动器窗口中点击'启动所有服务'按钮，观察步骤状态显示是否正确")
    print("预期步骤状态:")
    print("1. 检查环境 - 完成")
    print("2. 启动音乐演练场 - 完成")
    print("3. 启动API服务 - 完成")
    print("4. 启动青龙前端 - 完成")
    print("5. 启动青龙后端 - 完成")
    print("\n同时观察是否有多个服务并行启动，启动速度是否更快")
    print("最后观察是否在所有服务就绪后才打开浏览器")
    
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
    test_steps()
