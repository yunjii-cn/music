#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

now = datetime.now()
VERSION = now.strftime("%Y.%m.%d.%H%M")
ROOT_DIR = Path(__file__).resolve().parent
LAUNCHER_DIR = ROOT_DIR / "launcher"

def clean_build():
    print("🧹 清理构建目录...")
    dirs_to_remove = ['build']
    for dir_name in dirs_to_remove:
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_name}")

def build_exe():
    print("🔨 构建 EXE...")
    os.chdir(ROOT_DIR)
    
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"云集智能音乐创意台-v{VERSION}-NEW",
        "--onefile",
        "--windowed",
        "--icon", str(ROOT_DIR / "ico.png"),
        "--add-data", f"{ROOT_DIR / 'ico.png'};.",
        "--add-data", f"{ROOT_DIR / '1、install-uv-qinglong.ps1'};.",
        "--add-data", f"{ROOT_DIR / '2、run_gradio.ps1'};.",
        "--add-data", f"{ROOT_DIR / '3、run_server.ps1'};.",
        "--add-data", f"{ROOT_DIR / '4、run_npmgui.ps1'};.",
        "--clean",
        "--noconfirm",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "psutil",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "numpy",
        "--exclude-module", "tkinter",
        "--exclude-module", "tensorflow",
        "--exclude-module", "torch",
        "--exclude-module", "modelscope",
        "--exclude-module", "transformers",
        "--exclude-module", "datasets",
        "--exclude-module", "acestep",
        str(LAUNCHER_DIR / "main.py")
    ]
    
    print("  运行 PyInstaller...")
    subprocess.run(pyinstaller_args, check=True)

def check_output():
    print("📦 检查输出文件...")
    exe_path = ROOT_DIR / "dist" / f"云集智能音乐创意台-v{VERSION}-NEW.exe"
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        print(f"  ✓ EXE 文件已生成: {exe_path}")
        print(f"  ✓ 文件大小: {size_mb:.2f} MB")
        return True, size_mb, exe_path
    else:
        print(f"  ❌ 未找到 EXE 文件")
        return False, 0, None

def main():
    print("=" * 60)
    print("  云集智能音乐创意台 - 打包工具 (仅打包)")
    print(f"  版本: {VERSION}")
    print("=" * 60)
    print()
    
    try:
        clean_build()
        print()
        
        build_exe()
        print()
        
        success, size_mb, exe_path = check_output()
        if success:
            print()
            print("=" * 60)
            print("✅ 打包完成！")
            print(f"📦 EXE 文件: {exe_path}")
            print(f"📦 文件大小: {size_mb:.2f} MB")
            print("=" * 60)
            
            original_exe = ROOT_DIR / "dist" / "云集智能音乐创意台-v2026.03.20.1348.exe"
            if original_exe.exists():
                original_size = original_exe.stat().st_size / (1024 * 1024)
                print()
                print("📊 版本对比:")
                print(f"  原版1348: {original_size:.2f} MB")
                print(f"  新版本:   {size_mb:.2f} MB")
                print(f"  差异:     {abs(size_mb - original_size):.2f} MB")
        else:
            print("\n❌ 打包失败")
            sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
