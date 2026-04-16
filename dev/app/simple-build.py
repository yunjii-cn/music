#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的EXE构建脚本 - 直接输出到dev目录
支持自动Git提交和推送
"""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

# 强制设置编码为UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
ROOT_DIR = Path(__file__).resolve().parent
DEV_DIR = ROOT_DIR.parent
PROJECT_ROOT = ROOT_DIR.parent.parent
VERSION_HISTORY_FILE = ROOT_DIR / "version_history.json"


def load_version_history():
    """加载版本历史"""
    if VERSION_HISTORY_FILE.exists():
        try:
            with open(VERSION_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_version_history(history):
    """保存版本历史"""
    try:
        with open(VERSION_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"警告：保存版本历史失败：{e}")


def get_git_status():
    """获取Git状态"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"获取Git状态失败：{e}")
        return ""


def git_commit_and_push(commit_message):
    """Git提交和推送"""
    try:
        print("\n" + "=" * 60)
        print("  Git 提交和推送")
        print("=" * 60)
        
        # 检查是否有修改
        git_status = get_git_status()
        if not git_status:
            print("  没有需要提交的修改")
            return True
        
        print("  检测到修改，开始提交...")
        
        # 添加所有修改
        subprocess.run(
            ['git', 'add', '.'],
            cwd=PROJECT_ROOT, check=True, timeout=30
        )
        print("  ✓ 文件已添加")
        
        # 提交
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=PROJECT_ROOT, check=True, timeout=30
        )
        print("  ✓ 提交成功")
        
        # 推送
        print("  推送到远程仓库...")
        result = subprocess.run(
            ['git', 'push'],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print("  ✓ 推送成功")
            return True
        else:
            print(f"  警告：推送失败：{result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"  Git操作失败：{e}")
        return False
    except Exception as e:
        print(f"  Git操作异常：{e}")
        return False


def build_exe():
    """构建EXE - 直接输出到dev目录"""
    print(f"构建 EXE (v{VERSION})...")
    os.chdir(ROOT_DIR)
    
    exe_name = f"云集智能音乐创意台-v{VERSION}.exe"
    
    # 构建PyInstaller参数
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"云集智能音乐创意台-v{VERSION}",
        "--onefile", "--windowed",
        "--clean", "--noconfirm",
        "--distpath", str(DEV_DIR),
        "--workpath", str(ROOT_DIR / "build"),
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
    
    return DEV_DIR / exe_name


def main():
    print("=" * 60)
    print("  云集智能音乐创意台 - 简化构建工具")
    print("=" * 60)
    print()
    
    # 检查是否有命令行参数作为修改内容
    changes = []
    if len(sys.argv) > 1:
        # 从命令行参数获取修改内容
        changes = sys.argv[1:]
        print("使用命令行提供的修改内容：")
        for i, change in enumerate(changes, 1):
            print(f"  {i}. {change}")
        print()
    else:
        # 交互式获取提交信息
        print("请输入本次版本的修改内容：")
        print("（每行一条，输入空行结束）")
        print()
        
        line_num = 1
        try:
            while True:
                line = input(f"  {line_num}. ").strip()
                if not line:
                    break
                changes.append(line)
                line_num += 1
        except (EOFError, KeyboardInterrupt):
            pass
        
        if not changes:
            print()
            print("提示：未输入修改内容，将使用默认描述")
            changes = ["优化和修复"]
        
        print()
    
    try:
        # 1. 构建EXE（直接输出到dev目录）
        exe_path = build_exe()
        print()
        
        if not exe_path.exists():
            print("未找到生成的EXE文件")
            sys.exit(1)
        
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("=" * 60)
        print("  构建完成！")
        print(f"  EXE 文件：{exe_path}")
        print(f"  文件大小：{size_mb:.2f} MB")
        print("=" * 60)
        print()
        
        # 2. 复制一份到ver目录（作为稳定版本备份）
        ver_dir = DEV_DIR / "ver"
        ver_exe_path = ver_dir / exe_path.name
        print(f"复制到ver目录作为稳定版本...")
        ver_dir.mkdir(exist_ok=True)
        shutil.copy2(exe_path, ver_exe_path)
        print(f"  ✓ 已复制到：{ver_exe_path}")
        print()
        
        # 3. 更新version_history.json
        print("更新版本历史...")
        version_history = load_version_history()
        version_name = exe_path.stem
        version_history[version_name] = {
            "version": version_name,
            "changes": changes,
            "build_time": datetime.now().isoformat(),
            "version_number": VERSION
        }
        save_version_history(version_history)
        print("  ✓ 版本历史已更新")
        print()
        
        # 4. Git提交和推送
        commit_message = f"feat: 发布版本 v{VERSION}\n\n" + "\n".join([f"- {change}" for change in changes])
        git_commit_and_push(commit_message)
        print()
        
        print("=" * 60)
        print("  全部完成！")
        print("  提示：临时构建文件在 dev/app/build/，可手动清理")
        print("=" * 60)
        
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
