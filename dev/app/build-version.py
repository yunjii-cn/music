#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXE构建脚本 - 云集智能音乐创意台
--onefile 模式打包（单文件，稳定可靠）

架构说明：
  - --onefile 模式打包
  - launcher.py 作为入口（简洁设计，不 monkey-patch subprocess）
  - 三目录原则：
    dev/*.exe           = 启动器（gitignore）
    dev/app/            = 应用代码 + 脚本（git 管理）
    dev/data/           = 用户数据（gitignore）
"""
import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
ROOT_DIR = Path(__file__).resolve().parent
DEV_DIR = ROOT_DIR.parent
PROJECT_ROOT = ROOT_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
VERSION_HISTORY_FILE = ROOT_DIR / "version_history.json"
APP_NAME = "".join(chr(c) for c in [0x4e91, 0x96c6, 0x667a, 0x80fd, 0x97f3, 0x4e50, 0x521b, 0x610f, 0x53f0])


def load_version_history():
    if VERSION_HISTORY_FILE.exists():
        try:
            with open(VERSION_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_version_history(history):
    try:
        with open(VERSION_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"警告：保存版本历史失败：{e}")


def get_git_status():
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
    try:
        print("\n" + "=" * 60)
        print("  Git 提交和推送")
        print("=" * 60)

        git_status = get_git_status()
        if not git_status:
            print("  没有需要提交的修改")
            return True

        print("  检测到修改，开始提交...")

        subprocess.run(
            ['git', 'add', '.'],
            cwd=PROJECT_ROOT, check=True, timeout=30
        )
        print("  ✓ 文件已添加")

        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=PROJECT_ROOT, check=True, timeout=30
        )
        print("  ✓ 提交成功")

        print("  推送到远程仓库...")
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                result = subprocess.run(
                    ['git', 'push'],
                    cwd=PROJECT_ROOT, capture_output=True, text=True,
                    timeout=180
                )
                if result.returncode == 0:
                    print("  ✓ 推送成功")
                    return True
                else:
                    print(f"  警告：推送失败（第{attempt + 1}次尝试）：{result.stderr}")
                    if attempt < max_attempts - 1:
                        print("  重试中...")
                        time.sleep(3)
            except subprocess.TimeoutExpired:
                print(f"  警告：推送超时（第{attempt + 1}次尝试）")
                if attempt < max_attempts - 1:
                    print("  重试中...")
                    time.sleep(3)

        print("  ✗ 推送失败，请稍后手动推送")
        return False

    except subprocess.CalledProcessError as e:
        print(f"  Git操作失败：{e}")
        return False
    except Exception as e:
        print(f"  Git操作异常：{e}")
        import traceback
        traceback.print_exc()
        return False


def update_versions_json(version, changes, exe_name):
    try:
        versions_file = ROOT_DIR / "versions.json"
        versions = []
        if versions_file.exists():
            with open(versions_file, 'r', encoding='utf-8') as f:
                versions = json.load(f)

        new_entry = {
            "version": version,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "message": changes[0] if changes else "优化和修复",
            "changes": changes,
            "name": exe_name,
            "download_url": ""
        }

        versions.insert(0, new_entry)

        with open(versions_file, 'w', encoding='utf-8') as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)

        print("  ✓ versions.json 已更新")
        return True

    except Exception as e:
        print(f"  ✗ 更新 versions.json 失败: {e}")
        return False


def _kill_running_exe():
    current_pid = os.getpid()
    killed = []
    try:
        import psutil as _ps
        for proc in _ps.process_iter(['pid', 'name', 'exe']):
            try:
                pname = (proc.info.get('name') or '').lower()
                if pname.startswith(APP_NAME.lower()) and proc.info['pid'] != current_pid:
                    proc.terminate()
                    killed.append(pname)
            except (_ps.NoSuchProcess, _ps.AccessDenied):
                pass
    except ImportError:
        pass
    if killed:
        print(f"  已终止旧版进程: {', '.join(killed)}")
        time.sleep(1)
    return len(killed)


def build_exe():
    print(f"  PyInstaller 打包 (v{VERSION})...")

    release_name = f"{APP_NAME}-v{VERSION}"

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    os.chdir(str(ROOT_DIR))

    icon_path = str(ROOT_DIR / "icon.ico")

    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", release_name,
        "--onefile", "--console",
        "--icon", icon_path,
        "--distpath", str(BUILD_DIR),
        "--workpath", str(BUILD_DIR / "_pyinstaller_work"),
        "--specpath", str(BUILD_DIR / "_pyinstaller_work"),
        "--clean", "--noconfirm",
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "psutil",
        "--hidden-import", "psutil._psutil_windows",
        "--hidden-import", "psutil._pswindows",
        "--hidden-import", "psutil._common",
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
        "--exclude-module", "git",
        "--exclude-module", "gitdb",
        "--exclude-module", "gitpython",
        "--exclude-module", "psutil._pslinux",
        "--exclude-module", "psutil._psosx",
        "--exclude-module", "psutil._psbsd",
        "--exclude-module", "psutil._pssunos",
    ]

    if os.path.exists(icon_path):
        pyinstaller_args.extend(["--add-data", f"{icon_path};."])
        print(f"  已添加图标: {icon_path}")

    icon_png = str(ROOT_DIR / "icon.png")
    if os.path.exists(icon_png):
        pyinstaller_args.extend(["--add-data", f"{icon_png};."])
        print(f"  已添加图标PNG: {icon_png}")

    qt_conf = ROOT_DIR / "qt.conf"
    if qt_conf.exists():
        pyinstaller_args.extend(["--add-data", f"{str(qt_conf)};PyQt6/Qt6"])
        print(f"  已添加Qt配置: {qt_conf}")

    splash_path = ROOT_DIR / "splash.png"
    if splash_path.exists():
        pyinstaller_args.extend(["--splash", str(splash_path)])
        print(f"  已添加启动画面: {splash_path}")

    vh_file = ROOT_DIR / "version_history.json"
    if vh_file.exists():
        pyinstaller_args.extend(["--add-data", f"{str(vh_file)};."])
        print(f"  已添加版本历史")

    scripts_dir = ROOT_DIR / "scripts"
    if scripts_dir.exists():
        ps1_scripts = list(scripts_dir.glob("*.ps1"))
        for ps1 in ps1_scripts:
            pyinstaller_args.extend(["--add-data", f"{str(ps1)};."])
            print(f"  已添加脚本: {ps1.name}")

    pyinstaller_args.append("launcher.py")
    print(f"  使用 launcher.py 作为入口")

    print("  运行 PyInstaller (--onefile)...")
    subprocess.run(pyinstaller_args, check=True)

    exe_path = BUILD_DIR / f"{release_name}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ EXE 生成成功: {exe_path.name} ({size_mb:.1f} MB)")
    else:
        print(f"  ✗ EXE 未生成，请检查 PyInstaller 输出")
        raise FileNotFoundError(f"EXE not found: {exe_path}")

    return exe_path


def post_build(exe_path: Path):
    print("  打包后处理...")

    release_name = exe_path.stem
    release_dir = BUILD_DIR / release_name
    if release_dir.exists():
        shutil.rmtree(str(release_dir), ignore_errors=True)
    release_dir.mkdir(parents=True, exist_ok=True)

    shutil.move(str(exe_path), str(release_dir / exe_path.name))
    print(f"  ✓ 移动 EXE -> {release_dir.name}/")

    _IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")

    scripts_src = ROOT_DIR / "scripts"
    scripts_dst = release_dir / "app" / "scripts"
    if scripts_src.exists():
        if scripts_dst.exists():
            shutil.rmtree(str(scripts_dst), ignore_errors=True)
        shutil.copytree(str(scripts_src), str(scripts_dst), ignore=_IGNORE)
        print("  ✓ 复制 scripts/")

    acestep_src = ROOT_DIR / "acestep"
    acestep_dst = release_dir / "app" / "acestep"
    if acestep_src.exists():
        if acestep_dst.exists():
            shutil.rmtree(str(acestep_dst), ignore_errors=True)
        shutil.copytree(str(acestep_src), str(acestep_dst), ignore=_IGNORE)
        print("  ✓ 复制 acestep/")

    ace_step_ui_src = ROOT_DIR / "ace-step-ui"
    ace_step_ui_dst = release_dir / "app" / "ace-step-ui"
    if ace_step_ui_src.exists():
        if ace_step_ui_dst.exists():
            shutil.rmtree(str(ace_step_ui_dst), ignore_errors=True)
        shutil.copytree(str(ace_step_ui_src), str(ace_step_ui_dst), ignore=_IGNORE)
        print("  ✓ 复制 ace-step-ui/")

    data_dir = release_dir / "data"
    for sub in ("outputs", "models", "config"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    print("  ✓ 创建 data/ 目录结构")

    total_size = sum(f.stat().st_size for f in release_dir.rglob("*") if f.is_file())
    size_mb = total_size / (1024 * 1024)
    print(f"  发布目录大小: {size_mb:.1f} MB")

    return release_dir


def cleanup():
    work_dir = BUILD_DIR / "_pyinstaller_work"
    if work_dir.exists():
        try:
            shutil.rmtree(str(work_dir), ignore_errors=True)
            print("  清理 PyInstaller 临时文件")
        except Exception:
            pass


def _deploy_to_dev(release_dir: Path):
    release_name = release_dir.name
    exe_name = f"{release_name}.exe"

    _kill_running_exe()

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    src_exe = release_dir / exe_name
    if src_exe.exists():
        existing = DIST_DIR / exe_name
        if existing.exists():
            try:
                existing.unlink()
            except PermissionError:
                print(f"  ⚠ EXE 被占用，尝试重命名旧文件...")
                backup_name = existing.stem + "_old" + existing.suffix
                backup_path = DIST_DIR / backup_name
                if backup_path.exists():
                    try:
                        backup_path.unlink()
                    except PermissionError:
                        pass
                try:
                    existing.rename(str(backup_path))
                    print(f"  旧 EXE 重命名为: {backup_name}")
                except PermissionError:
                    print(f"  ✗ 无法重命名旧 EXE，请手动关闭正在运行的应用后重试")
                    return
        shutil.copy2(str(src_exe), str(DIST_DIR / exe_name))
        print(f"  ✓ 复制 EXE: {exe_name}")

    for sub in ("outputs", "models", "config"):
        (DEV_DIR / "data" / sub).mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 确保 data/ 目录结构存在")

    print(f"  ✓ 部署完成，EXE 在 {DIST_DIR}")


def main():
    print("=" * 60)
    print(f"  {APP_NAME} - 版本化构建工具")
    print("=" * 60)
    print()
    print(f"  版本: {VERSION}")
    print(f"  源码: {ROOT_DIR}")
    print(f"  输出: {BUILD_DIR}")
    print(f"  模式: --onefile (单文件)")
    print()

    changes = []
    if len(sys.argv) > 1:
        changes = sys.argv[1:]
        print("使用命令行提供的修改内容：")
        for i, change in enumerate(changes, 1):
            print(f"  {i}. {change}")
        print()
    else:
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
        print("── Step 1: PyInstaller 打包 (--onefile) ──")
        exe_path = build_exe()
        print()

        print("── Step 2: 打包后处理 ──")
        release_dir = post_build(exe_path)
        print()

        print("── Step 3: 清理 ──")
        cleanup()
        print()

        print("── Step 4: 记录版本 ──")
        version_history = load_version_history()
        version_name = release_dir.name
        version_history[version_name] = {
            "version": version_name,
            "changes": changes,
            "build_time": datetime.now().isoformat(),
            "version_number": VERSION
        }
        save_version_history(version_history)
        print("  ✓ 版本历史已更新")

        update_versions_json(VERSION, changes, f"{version_name}.exe")
        print()

        print("── Step 5: 部署到 dev/ ──")
        try:
            _deploy_to_dev(release_dir)
        except Exception as deploy_err:
            print(f"  ⚠ 部署到 dev/ 部分失败: {deploy_err}")
            print(f"  EXE 和发布包已生成，请关闭旧版 EXE 后重新运行部署")
        print()

        exe_in_dist = DIST_DIR / f"{version_name}.exe"

        # Also copy to dev/ver/ for release publishing
        VER_DIR = DEV_DIR / "ver"
        VER_DIR.mkdir(parents=True, exist_ok=True)
        if exe_in_dist.exists():
            ver_target = VER_DIR / f"{version_name}.exe"
            if not ver_target.exists():
                import shutil as _shutil
                _shutil.copy2(str(exe_in_dist), str(ver_target))
                print(f"  ✓ 复制到 dev/ver/: {ver_target.name}")
            else:
                print(f"  - dev/ver/ 中已存在: {ver_target.name}")

        print("=" * 60)
        print("  构建完成！")
        print(f"  发布目录: {release_dir}")
        print(f"  分发目录: {DIST_DIR}")
        if exe_in_dist.exists():
            size_mb = exe_in_dist.stat().st_size / (1024 * 1024)
            print(f"  EXE 文件: {exe_in_dist}")
            print(f"  EXE 大小: {size_mb:.1f} MB")
        print("=" * 60)

        commit_message = f"feat: 发布版本 v{VERSION}\n\n" + "\n".join([f"- {change}" for change in changes])
        git_commit_and_push(commit_message)

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
