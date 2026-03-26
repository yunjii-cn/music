#!/usr/bin/env python3
import os, sys, subprocess, shutil
from pathlib import Path
from datetime import datetime

VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
ROOT_DIR = Path(__file__).resolve().parent
LAUNCHER_DIR = ROOT_DIR / "launcher"

def clean_build():
    print(" 清理构建目录...")
    for dir_name in ['build']:
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除：{dir_name}")

def build_exe():
    print(" 构建 EXE...")
    os.chdir(ROOT_DIR)
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"云集智能音乐创意台-v{VERSION}",
        "--onefile", "--windowed",
        "--icon", str(ROOT_DIR / "ico.png"),
        "--add-data", f"{ROOT_DIR / 'ico.png'};.",
        "--add-data", f"{ROOT_DIR / '1、install-uv-qinglong.ps1'};.",
        "--add-data", f"{ROOT_DIR / '2、run_gradio.ps1'};.",
        "--add-data", f"{ROOT_DIR / '3、run_server.ps1'};.",
        "--add-data", f"{ROOT_DIR / '4、run_npmgui.ps1'};.",
        "--clean", "--noconfirm",
        "--hidden-import", "PyQt6.sip", "--hidden-import", "psutil",
        "--hidden-import", "PyQt6.QtCore", "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--exclude-module", "matplotlib", "--exclude-module", "scipy",
        "--exclude-module", "numpy", "--exclude-module", "tkinter",
        "--exclude-module", "tensorflow", "--exclude-module", "torch",
        "--exclude-module", "modelscope", "--exclude-module", "transformers",
        "--exclude-module", "datasets", "--exclude-module", "acestep",
        str(LAUNCHER_DIR / "main.py")
    ]
    print("  运行 PyInstaller...")
    subprocess.run(pyinstaller_args, check=True)

def check_output():
    print(" 检查输出文件...")
    exe_path = ROOT_DIR / "dist" / f"云集智能音乐创意台-v{VERSION}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"   EXE 文件已生成：{exe_path}")
        print(f"   文件大小：{size_mb:.2f} MB")
        return True, exe_path
    return False, None

def commit_and_push_to_main():
    print(" 提交并推送到 main 分支...")
    try:
        os.chdir(ROOT_DIR)
        print("  切换到 main 分支...")
        subprocess.run(['git', 'checkout', 'main'], check=True, capture_output=True)
        print("  获取更改信息...")
        status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=False)
        change_description = "版本更新"
        if status_result.stdout.strip():
            changes = []
            for line in status_result.stdout.strip().split('\n'):
                if line.strip():
                    status_code = line[:2].strip()
                    file_path = line[3:].strip()
                    status_desc = {'M': '修改', 'A': '新增', 'D': '删除', 'R': '重命名', 'C': '复制'}.get(status_code, '更新')
                    changes.append(f"- {status_desc}: {file_path}")
            if changes:
                change_description = '\n'.join(changes)
        commit_message = f"发布新版本 v{VERSION}\n\n{change_description}"
        print(f"\n 提交信息：\n{'='*60}\n{commit_message}\n{'='*60}\n")
        print("  添加 EXE 文件到 Git...")
        exe_path = ROOT_DIR / "dist" / f"云集智能音乐创意台-v{VERSION}.exe"
        subprocess.run(['git', 'add', str(exe_path)], check=True)
        print("  提交更改...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print("  推送到远程 main 分支...")
        push_result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        if push_result.returncode == 0:
            print(f"   成功推送到 main 分支")
            return True
        else:
            print(f"   推送失败：{push_result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"   Git 操作失败：{e}")
        return False
    except Exception as e:
        print(f"   提交过程出错：{e}")
        return False

def main():
    print("="*60)
    print("  云集智能音乐创意台 - 新版打包工具")
    print(f"  版本：{VERSION}")
    print("="*60)
    print()
    try:
        clean_build()
        print()
        build_exe()
        print()
        success, exe_path = check_output()
        if success:
            print()
            print("="*60)
            print(" 打包完成！")
            print(f" EXE 文件：{exe_path}")
            print("="*60)
            print()
            print(" 自动提交并推送到 main 分支...")
            print()
            if commit_and_push_to_main():
                print()
                print("="*60)
                print(" 全部完成！")
                print("="*60)
            else:
                print()
                print("="*60)
                print(" 打包完成，但 Git 上传失败")
                print("="*60)
        else:
            print("\n 打包失败")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n 打包失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
