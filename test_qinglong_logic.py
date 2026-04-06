#!/usr/bin/env python3
"""
测试青龙训练器启动逻辑
"""

import os
import sys
import time
import subprocess
import psutil

# 测试函数
def test_qinglong_logic():
    """测试青龙训练器启动逻辑"""
    print("=" * 60)
    print("测试青龙训练器启动逻辑")
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
    
    # 测试青龙训练器启动逻辑
    print("\n🔍 测试青龙训练器启动逻辑...")
    print("请在启动器窗口中点击'🎨 启动青龙训练器'按钮，观察启动逻辑是否正确")
    print("预期行为:")
    print("1. 步骤1: 检查环境")
    print("2. 步骤1: 安装依赖（运行1、install-uv-qinglong.ps1）")
    print("3. 步骤4: 启动青龙前端")
    print("4. 步骤5: 启动青龙后端")
    print("5. 等待所有服务就绪后打开浏览器")
    print("\n观察是否有安装依赖的步骤，以及服务启动顺序是否正确")
    
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
    test_qinglong_logic()
