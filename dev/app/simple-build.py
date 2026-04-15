#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的EXE构建脚本 - 直接在dev/app目录下构建
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# 强制设置编码为UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"


def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    build_dirs = [ROOT_DIR / "build", ROOT_DIR / "dist"]
    for dir_path in build_dirs:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  已删除：{dir_path.name}")
            except Exception as e:
                print(f"  跳过 {dir_path.name}：{e}")


def build_exe():
    """构建EXE"""
    print(f"构建 EXE (v{VERSION})...")
    os.chdir(ROOT_DIR)
    
    # 构建PyInstaller参数
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"云集智能音乐创意台-v{VERSION}",
        "--onefile", "--windowed",
        "--clean", "--noconfirm",
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "psutil",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "numpy",
        "--exclude-module", "tkinter",
        "--exclude-module", "tensorflow",
        "--exclude-module", "torch",
        "--exclude-module", "modelscope",
        "--exclude-module", "transformers",
        "--exclude-module", "datasets",
        "--exclude-module", "acestep"
    ]
    
    # 检查是否有icon.ico
    icon_path = ROOT_DIR / "icon.ico"
    if icon_path.exists():
        pyinstaller_args.append("--icon")
        pyinstaller_args.append("icon.ico")
        pyinstaller_args.append("--add-data")
        pyinstaller_args.append("icon.ico;.")
        print(f"  已添加图标: icon.ico")
    
    # 最后添加main.py
    pyinstaller_args.append("main.py")
    
    print("  运行 PyInstaller...")
    subprocess.run(pyinstaller_args, check=True)


def main():
    print("=" * 60)
    print("  云集智能音乐创意台 - 简化构建工具")
    print("=" * 60)
    print()
    
    try:
        clean_build()
        print()
        
        build_exe()
        print()
        
        exe_name = f"云集智能音乐创意台-v{VERSION}.exe"
        exe_path = DIST_DIR / exe_name
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("=" * 60)
            print("  构建完成！")
            print(f"  EXE 文件：{exe_path}")
            print(f"  文件大小：{size_mb:.2f} MB")
            print("=" * 60)
        else:
            print("\n打包失败：未找到生成的EXE文件")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
