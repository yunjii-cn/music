#!/usr/bin/env python3
"""
ACE-Step Launcher 构建脚本
打包为 EXE 可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# 版本号基于打包日期和时间
VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  已删除: {dir_name}")
    
    # 删除 .spec 文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  已删除: {spec_file}")

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

def build_exe():
    """构建 EXE"""
    print("🔨 构建 EXE...")
    
    # PyInstaller 参数
    pyinstaller_args = [
        "pyinstaller",
        "--name", f"ACE-Step-Launcher-v{VERSION}",
        "--onefile",
        "--windowed",
        "--add-data", f"../2、run_gradio.ps1;.",
        "--add-data", f"../3、run_server.ps1;.",
        "--add-data", f"../4、run_npmgui.ps1;.",
        "--add-data", f"../ico.png;.",
        "--clean",
        "--noconfirm",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "psutil",
        "main.py"
    ]
    
    # 如果有图标，添加 --icon 参数
    if os.path.exists("icon.ico"):
        pyinstaller_args.insert(1, "--icon")
        pyinstaller_args.insert(2, "icon.ico")
    
    subprocess.run(pyinstaller_args, check=True)

def copy_to_parent():
    """复制到父目录"""
    print("📋 复制到父目录...")
    exe_name = f"ACE-Step-Launcher-v{VERSION}.exe"
    src = Path("dist") / exe_name
    dst = Path("..") / exe_name
    
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  已复制: {dst}")
    else:
        print(f"  [错误] 未找到: {src}")

def main():
    """主函数"""
    print("=" * 50)
    print(f"ACE-Step Launcher 构建脚本 v{VERSION}")
    print("=" * 50)
    print()
    
    try:
        clean_build()
        # install_dependencies()  # 跳过依赖安装，因为已经安装
        build_exe()
        copy_to_parent()
        
        print()
        print("=" * 50)
        print("✅ 构建完成!")
        print(f"📦 输出文件: ACE-Step-启动器-v{VERSION}.exe")
        print("=" * 50)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
