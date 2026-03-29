#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云集智能音乐创意台 - 版本化构建工具

使用方法：
  python build-version.py                    # 从最新版本创建新版本并构建
  python build-version.py <版本文件夹名>     # 使用指定版本文件夹构建
  python build-version.py --desc "描述内容" <版本文件夹名>  # 使用指定版本和描述
  python build-version.py --push             # 从最新版本创建新版本并自动推送
  python build-version.py -p <版本文件夹名>  # 使用指定版本构建并自动推送

选项：
  --push, -p    构建完成后自动提交并推送到远程仓库
  --desc, -d    指定版本描述（推荐用这个避免编码问题）
"""
import os
import sys
import subprocess
import shutil
import re
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
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"
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


def get_version_description():
    """获取版本描述"""
    # 检查是否在非交互式环境中（管道输入）
    import sys
    import io
    if not sys.stdin.isatty():
        # 从stdin读取版本描述 - 尝试多种编码
        try:
            # 尝试UTF-8
            try:
                stdin_content = sys.stdin.read()
                if stdin_content:
                    stdin_content = stdin_content.strip()
                    if stdin_content:
                        print()
                        print(f"使用管道输入的版本描述")
                        return [stdin_content]
            except:
                pass
            
            # 如果上面失败，尝试用GBK重新打开stdin
            try:
                # 重新打开stdin用GBK编码
                import os
                sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='gbk', errors='replace')
                stdin_content = sys.stdin.read().strip()
                if stdin_content:
                    print()
                    print(f"使用管道输入的版本描述 (GBK)")
                    return [stdin_content]
            except:
                pass
        except:
            pass
        
        print()
        print("非交互式环境，使用默认版本描述")
        return ["优化和修复"]
    
    print()
    print("=" * 60)
    print("  请输入本次版本的修改内容")
    print("=" * 60)
    print()
    print("请输入修改内容（每行一条，输入空行结束）：")
    print()
    
    changes = []
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
    return changes


def get_latest_version():
    """获取最新版本文件夹"""
    if not BUILD_DIR.exists():
        return None
    
    version_dirs = []
    for dir_path in BUILD_DIR.iterdir():
        if dir_path.is_dir() and dir_path.name.startswith("云集智能音乐创意台-v"):
            match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', dir_path.name)
            if match:
                version_str = match.group(1)
                version_dirs.append((version_str, dir_path))
    
    if not version_dirs:
        return None
    
    version_dirs.sort(key=lambda x: x[0], reverse=True)
    return version_dirs[0][1]


def create_new_version(source_version_dir):
    """从源版本创建新版本"""
    new_version_name = f"云集智能音乐创意台-v{VERSION}"
    new_version_dir = BUILD_DIR / new_version_name
    
    if new_version_dir.exists():
        print(f"新版本文件夹已存在：{new_version_dir}")
        return new_version_dir
    
    print(f"从 {source_version_dir.name} 创建新版本...")
    shutil.copytree(source_version_dir, new_version_dir)
    print(f"  新版本文件夹：{new_version_dir}")
    
    # 同时复制build-version.py到新版本文件夹，方便回滚
    build_script_source = ROOT_DIR / "build-version.py"
    build_script_target = new_version_dir / "build-version.py"
    try:
        shutil.copy2(build_script_source, build_script_target)
        print(f"  已复制构建脚本到：{build_script_target.name}")
    except Exception as e:
        print(f"  警告：复制构建脚本失败：{e}")
    
    return new_version_dir


def clean_build(version_dir):
    """清理构建目录"""
    print("清理构建目录...")
    build_dirs = [version_dir / "build", version_dir / "dist"]
    for dir_path in build_dirs:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  已删除：{dir_path.name}")
            except Exception as e:
                print(f"  跳过 {dir_path.name}：{e}")


def build_exe(version_dir):
    """构建EXE"""
    print(f"构建 EXE (v{VERSION})...")
    os.chdir(version_dir)
    
    # 检查并确保脚本文件存在
    scripts_to_include = []
    for script_name in ["install-env.ps1", "download_python_312.py", "start.ps1"]:
        script_path = version_dir / script_name
        if script_path.exists():
            scripts_to_include.append(script_name)
            print(f"  包含脚本: {script_name}")
        else:
            print(f"  警告: 脚本不存在: {script_name}")
    
    # 构建PyInstaller参数
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"云集智能音乐创意台-v{VERSION}",
        "--onefile", "--windowed",
        "--icon", "icon.ico",
        "--add-data", "icon.ico;.",
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
        "--exclude-module", "acestep",
        "main.py"
    ]
    
    # 添加脚本文件到打包
    for script_name in scripts_to_include:
        pyinstaller_args.extend(["--add-data", f"{script_name};."])
    
    print("  运行 PyInstaller...")
    subprocess.run(pyinstaller_args, check=True)


def move_to_dist(version_dir):
    """将构建的EXE移动到根目录dist文件夹（不自动复制到version文件夹）"""
    print("整理输出文件...")
    source_dist = version_dir / "dist"
    target_dist = DIST_DIR
    
    if not target_dist.exists():
        target_dist.mkdir(parents=True)
    
    exe_name = f"云集智能音乐创意台-v{VERSION}.exe"
    source_exe = source_dist / exe_name
    
    if source_exe.exists():
        target_exe = target_dist / exe_name
        
        # 尝试删除目标文件（如果存在）
        moved = False
        final_exe = source_exe
        
        if target_exe.exists():
            try:
                target_exe.unlink()
                print(f"  已删除旧版本：{target_exe.name}")
                shutil.move(str(source_exe), str(target_exe))
                final_exe = target_exe
                moved = True
            except Exception as e:
                print(f"  警告：无法移动到根目录dist（程序可能正在运行），保留在：{source_exe}")
        else:
            shutil.move(str(source_exe), str(target_exe))
            final_exe = target_exe
            moved = True
        
        if moved:
            print(f"  EXE已移动到：{final_exe}")
        else:
            print(f"  EXE保存在：{final_exe}")
        
        print("  [提示] version文件夹需要手动添加精选版本")
        
        size_mb = final_exe.stat().st_size / (1024 * 1024)
        print(f"  文件大小：{size_mb:.2f} MB")
        
        return True, final_exe
    
    return False, None


def cleanup_version_build(version_dir, keep_dist=False):
    """清理版本目录下的构建文件"""
    print("清理临时构建文件...")
    dirs_to_remove = [version_dir / "build"]
    
    if not keep_dist:
        dirs_to_remove.append(version_dir / "dist")
    
    for dir_path in dirs_to_remove:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
            except Exception:
                pass
    
    spec_files_to_remove = list(version_dir.glob("*.spec"))
    for spec_file in spec_files_to_remove:
        if spec_file.name != "launcher.spec":
            try:
                spec_file.unlink()
            except Exception:
                pass


def record_version(version_name, changes):
    """记录版本到历史"""
    history = load_version_history()
    
    version_info = {
        "version": version_name,
        "changes": changes,
        "build_time": datetime.now().isoformat(),
        "version_number": VERSION
    }
    
    history[version_name] = version_info
    save_version_history(history)
    
    # 同时复制到dist目录，让用户也能看到
    if DIST_DIR.exists():
        try:
            shutil.copy2(VERSION_HISTORY_FILE, DIST_DIR / "version_history.json")
        except Exception as e:
            print(f"警告：复制版本历史到dist失败：{e}")
    
    # 同时复制到version目录
    version_dir_target = ROOT_DIR / "version"
    if version_dir_target.exists():
        try:
            shutil.copy2(VERSION_HISTORY_FILE, version_dir_target / "version_history.json")
        except Exception as e:
            print(f"警告：复制版本历史到version失败：{e}")
    
    return version_info


def git_push_new_version(version_name, changes):
    """自动提交并推送到远程仓库"""
    import tempfile
    import os
    
    print()
    print("=" * 60)
    print("  准备推送到远程仓库...")
    print("=" * 60)
    
    os.chdir(ROOT_DIR)
    
    # 检查是否是git仓库
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip() != "true":
            print("  跳过：不在git仓库中")
            return False
    except Exception:
        print("  跳过：不在git仓库中")
        return False
    
    # 检查version目录是否有变化
    try:
        print("  检查version目录变化...")
        result = subprocess.run(
            ["git", "status", "--porcelain", "version/"],
            capture_output=True,
            text=True,
            check=True
        )
        version_changed = len(result.stdout.strip()) > 0
        
        # 检查其他文件是否有变化（源代码、构建脚本等）
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        other_changed = False
        for line in result.stdout.strip().split('\n'):
            if line and not line.startswith('?? version/') and not line.startswith(' M version/'):
                other_changed = True
                break
        
        if not version_changed and not other_changed:
            print("  没有需要提交的更改")
            return False
    except Exception as e:
        print(f"  检查git状态失败：{e}")
        return False
    
    # 添加所有更改（包括version目录和源代码）
    try:
        print("  添加更改到git...")
        subprocess.run(["git", "add", "-A"], check=True)
    except Exception as e:
        print(f"  添加更改失败：{e}")
        return False
    
    # 构建提交信息（直接使用版本描述）
    commit_message = "\n".join(changes)
    
    # 提交更改（使用临时文件避免编码问题）
    try:
        print("  提交更改...")
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(commit_message)
            temp_commit_file = f.name
        
        try:
            subprocess.run(["git", "commit", "-F", temp_commit_file], check=True)
        finally:
            try:
                os.unlink(temp_commit_file)
            except:
                pass
    except Exception as e:
        print(f"  提交失败：{e}")
        return False
    
    # 创建git标签（使用临时文件避免编码问题）
    try:
        tag_name = f"v{VERSION}"
        print(f"  创建git标签：{tag_name}")
        tag_message = f"版本 {version_name}\n\n" + "\n".join([f"- {c}" for c in changes])
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(tag_message)
            temp_tag_file = f.name
        
        try:
            subprocess.run(["git", "tag", "-a", tag_name, "-F", temp_tag_file], check=True)
        finally:
            try:
                os.unlink(temp_tag_file)
            except:
                pass
    except Exception as e:
        print(f"  创建标签失败：{e}")
    
    # 推送到远程仓库
    try:
        print("  推送到远程仓库...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        subprocess.run(["git", "push", "origin", "--tags"], check=True)
        print("  ✓ 成功推送到远程仓库！")
        return True
    except Exception as e:
        print(f"  推送失败：{e}")
        return False


def main():
    print("=" * 60)
    print("  云集智能音乐创意台 - 版本化构建工具")
    print("=" * 60)
    print()
    
    # 解析命令行参数
    auto_push = True  # 默认自动推送
    specified_version = None
    changes = None
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ["--no-push", "-np"]:
            auto_push = False
        elif arg in ["--desc", "-d"] and i + 1 < len(args):
            # 从--desc参数读取版本描述（用|分隔多行）
            changes = args[i + 1].split('|')
            i += 1
        else:
            specified_version = arg
        i += 1
    
    try:
        target_version_dir = None
        
        # 检查是否有指定版本参数
        if specified_version:
            version_dir = BUILD_DIR / specified_version
            if version_dir.exists() and version_dir.is_dir():
                target_version_dir = version_dir
                print(f"使用指定版本：{target_version_dir.name}")
                # 从指定版本名提取版本号
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', target_version_dir.name)
                if match:
                    global VERSION
                    VERSION = match.group(1)
            else:
                print(f"错误：指定的版本文件夹不存在：{specified_version}")
                sys.exit(1)
        else:
            # 默认模式：创建新版本
            print(f"  新版本：{VERSION}")
            print()
            latest_version = get_latest_version()
            if not latest_version:
                print("错误：未找到任何历史版本！")
                print(f"请确保 {BUILD_DIR} 目录下有版本文件夹")
                sys.exit(1)
            
            print(f"使用最新版本：{latest_version.name}")
            print()
            
            target_version_dir = create_new_version(latest_version)
        
        # 获取版本描述
        if changes is None:
            changes = get_version_description()
        
        print()
        
        clean_build(target_version_dir)
        print()
        
        build_exe(target_version_dir)
        print()
        
        success, exe_path = move_to_dist(target_version_dir)
        print()
        
        # 记录版本历史
        version_name = target_version_dir.name
        record_version(version_name, changes)
        
        # 如果EXE没有移动到根dist目录，则保留版本目录下的dist
        keep_dist = exe_path is not None and str(exe_path).startswith(str(target_version_dir))
        cleanup_version_build(target_version_dir, keep_dist=keep_dist)
        print()
        
        if success:
            print("=" * 60)
            print("  构建完成！")
            print(f"  源代码文件夹：{target_version_dir}")
            print(f"  EXE 文件：{exe_path}")
            print(f"  版本历史：{VERSION_HISTORY_FILE}")
            print("=" * 60)
            
            # 自动推送到远程仓库（如果启用）
            if auto_push:
                git_push_new_version(version_name, changes)
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
