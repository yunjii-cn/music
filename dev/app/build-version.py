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


def update_git_commits_json():
    """从 git 仓库提取最近 60 条提交，生成内置的 git_commits.json。

    该文件随 exe 打包，开发动态页面离线秒开显示（无需联网/弹窗）。
    远程最新的提交历史由用户在软件内点「远程获取」按钮手动拉取。
    """
    try:
        # 向上查找 .git 根目录
        cur = PROJECT_ROOT
        git_root = None
        guard = 0
        while cur.parent != cur and guard < 20:
            if (cur / ".git").exists():
                git_root = cur
                break
            cur = cur.parent
            guard += 1
        if not git_root:
            print("  ⚠ 未找到 .git，跳过生成 git_commits.json（保留现有文件）")
            return

        # 紧凑字段分隔（U+001F）：哈希 / 短哈希 / 标题 / 作者 / 邮箱 / 日期
        fmt = "%H%x1f%h%x1f%s%x1f%an%x1f%ae%x1f%ad"
        out = subprocess.run(
            ["git", "-C", str(git_root), "log",
             f"--pretty=format:{fmt}",
             "--date=format:%Y-%m-%d %H:%M:%S", "-n", "60"],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30
        )
        if out.returncode != 0:
            print(f"  ⚠ git log 失败：{(out.stderr or '').strip()[:200]}")
            return

        commits = []
        for line in out.stdout.split("\n"):
            line = line.strip("\r")
            if not line:
                continue
            parts = line.split("\x1f")
            if len(parts) < 6:
                continue
            h, h_short, subject, author, email, date = parts[:6]
            commits.append({
                "hash": h,
                "short_hash": h_short,
                "message": subject,
                "author": author,
                "email": email,
                "date": date,
            })

        target = ROOT_DIR / "git_commits.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(commits, f, ensure_ascii=False, indent=2)
        print(f"  ✓ git_commits.json 已生成（{len(commits)} 条提交）")
    except Exception as e:
        print(f"  ⚠ 生成 git_commits.json 失败: {e}")


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
        "--onefile", "--windowed",
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
        # 启动画面 pyi_splash 在用户 Windows 上会因 _PYI_SPLASH_IPC 连接失败
        # 直接崩掉整个 exe（KeyError: '_PYI_SPLASH_IPC'）。彻底排除该模块。
        "--exclude-module", "pyi_splash",
    ]

    if os.path.exists(icon_path):
        pyinstaller_args.extend(["--add-data", f"{icon_path};."])
        print(f"  已添加图标: {icon_path}")

    icon_png = str(ROOT_DIR / "icon.png")
    if os.path.exists(icon_png):
        pyinstaller_args.extend(["--add-data", f"{icon_png};."])
        print(f"  已添加图标PNG: {icon_png}")

    logo_png = str(ROOT_DIR / "logo.png")
    if os.path.exists(logo_png):
        pyinstaller_args.extend(["--add-data", f"{logo_png};."])
        print(f"  已添加品牌LOGO: {logo_png}")

    # 关键：把 main.py 自身也打进 exe（--add-data，作为数据文件随 exe 释放到
    # _MEI 目录）。否则运行时 import main 依赖磁盘上的松文件 app/main.py，
    # 轻量构建不拷贝 app/ 时会命中旧版、launcher 的进度条就绪哨兵逻辑不生效。
    # import main 在 launcher 里执行时 app/ 尚未入 sys.path，故打包这份必然优先命中。
    main_py = ROOT_DIR / "main.py"
    if main_py.exists():
        pyinstaller_args.extend(["--add-data", f"{str(main_py)};."])
        print(f"  已打包应用主体: {main_py}")

    # 模型管理器 UI 在 version_manager.py，由 main.py 懒加载导入（PyInstaller 静态分析
    # 不会收集），单独 --add-data 打进 exe，确保 UI 修复随 exe 分发、不依赖磁盘松文件。
    version_manager_py = ROOT_DIR / "version_manager.py"
    if version_manager_py.exists():
        pyinstaller_args.extend(["--add-data", f"{str(version_manager_py)};."])
        print(f"  已打包模型管理器: {version_manager_py}")

    ico_png = str(ROOT_DIR / "ico.png")
    if os.path.exists(ico_png):
        pyinstaller_args.extend(["--add-data", f"{ico_png};."])
        print(f"  已添加品牌LOGO(ico.png): {ico_png}")

    qt_conf = ROOT_DIR / "qt.conf"
    if qt_conf.exists():
        pyinstaller_args.extend(["--add-data", f"{str(qt_conf)};PyQt6/Qt6"])
        print(f"  已添加Qt配置: {qt_conf}")

    # 启动画面（--splash）在用户 Windows + PyInstaller 6.20.0 上会导致
    # _PYI_SPLASH_IPC 连接失败、整个 exe 崩溃（KeyError: '_PYI_SPLASH_IPC'）。
    # 启动画面仅为装饰，去掉不影响应用打开，故不再注入。
    splash_path = ROOT_DIR / "splash.png"
    if splash_path.exists():
        print(f"  跳过启动画面（splash.png 存在但已禁用，避免 _PYI_SPLASH_IPC 崩溃）")

    vh_file = ROOT_DIR / "version_history.json"
    if vh_file.exists():
        pyinstaller_args.extend(["--add-data", f"{str(vh_file)};."])
        print(f"  已添加版本历史")

    # 历史版本列表文件：打进 exe 后，即使所有远程源不可达（离线），
    # 软件版本页也能用内置 versions.json 兜底显示完整历史列表。
    versions_json = ROOT_DIR / "versions.json"
    if versions_json.exists():
        pyinstaller_args.extend(["--add-data", f"{str(versions_json)};."])
        print(f"  已打包历史版本列表: {versions_json}")

    # 开发动态页内置 git 提交历史：打进 exe 后离线秒开，无需联网/弹窗。
    git_commits_json = ROOT_DIR / "git_commits.json"
    if git_commits_json.exists():
        pyinstaller_args.extend(["--add-data", f"{str(git_commits_json)};."])
        print(f"  已打包 git 提交历史: {git_commits_json}")

    scripts_dir = ROOT_DIR / "scripts"
    if scripts_dir.exists():
        ps1_scripts = list(scripts_dir.glob("*.ps1"))
        # 打包前强制校验所有 .ps1 语法（历史教训：try/catch 括号配对错，
        # ParserError 会让整个部署脚本一行都不执行；宁可拒绝构建也不出坏包）
        if ps1_scripts:
            import subprocess as _sp
            _paths = ";".join(str(p) for p in ps1_scripts)
            _check = (
                "$bad=0; '" + _paths + "'.Split(';') | ForEach-Object { "
                "$e=$null; $t=$null; "
                "[System.Management.Automation.Language.Parser]::ParseFile($_, [ref]$t, [ref]$e) | Out-Null; "
                "if ($e) { $bad=1; Write-Output (\"PS1-SYNTAX-ERROR: \" + $_ + \" -> \" + $e[0].Message) } }; exit $bad"
            )
            _r = _sp.run(["powershell", "-NoProfile", "-Command", _check],
                         capture_output=True, text=True)
            if _r.returncode != 0:
                print("  ❌ PowerShell 脚本语法校验失败，终止构建：")
                print((_r.stdout or "") + (_r.stderr or ""))
                sys.exit(1)
            print(f"  ✓ {len(ps1_scripts)} 个 .ps1 语法校验通过")
        for ps1 in ps1_scripts:
            pyinstaller_args.extend(["--add-data", f"{str(ps1)};."])
            print(f"  已添加脚本: {ps1.name}")

    # ── payload.zip：把 acestep/ 和 ace-step-ui/ 精简源码打包进 exe，
    #    launcher 首次运行时自动解压到部署目录的 app/ 下。
    #    这样裸 exe 单独拿出去也能跑（不依赖外部发布文件夹）。
    #    排除：__pycache__、*.pyc、node_modules、docs、server/public（运行时音频数据）、
    #    server/data（SQLite DB 等运行时数据）。
    payload_path = ROOT_DIR / "payload.zip"
    import zipfile as _zf
    _EXCLUDE_DIR_NAMES = {"__pycache__", "node_modules", "docs", ".git", ".vscode", ".venv", "venv"}
    _EXCLUDE_SERVER_SUBDIRS = {"public", "data", "node_modules"}
    with _zf.ZipFile(str(payload_path), "w", _zf.ZIP_DEFLATED) as zf:
        # acestep/
        acestep_src = ROOT_DIR / "acestep"
        if acestep_src.exists():
            for root, dirs, files in os.walk(acestep_src):
                dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIR_NAMES]
                for f in files:
                    if f.endswith(".pyc"):
                        continue
                    full = os.path.join(root, f)
                    zf.write(full, os.path.relpath(full, ROOT_DIR))
            print(f"  已打包 payload: acestep/")
        # ace-step-ui/（排除重型目录）
        ui_src = ROOT_DIR / "ace-step-ui"
        if ui_src.exists():
            for root, dirs, files in os.walk(ui_src):
                rel = os.path.relpath(root, ui_src)
                parts = rel.split(os.sep)
                # 排除 server/public、server/data、server/node_modules
                if len(parts) >= 2 and parts[0] == "server" and parts[1] in _EXCLUDE_SERVER_SUBDIRS:
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIR_NAMES]
                for f in files:
                    if f.endswith(".pyc"):
                        continue
                    full = os.path.join(root, f)
                    zf.write(full, os.path.relpath(full, ROOT_DIR))
            print(f"  已打包 payload: ace-step-ui/ (精简)")
        # scripts/（受控维护脚本：install-env.ps1 等）：始终随 payload 分发，
        # 与用户"一键部署维护无法覆盖的目录文件应该打包在 exe 中"的原则一致。
        # launcher 首次运行会把 scripts/ 从 payload 刷新到 app/scripts/（覆盖式，确保修复可达）。
        scripts_src = ROOT_DIR / "scripts"
        if scripts_src.exists():
            # 只打包维护脚本与小配置，绝不带重型产物：
            # 排除 .venv(62GB)、lora_data_prepare(2GB 训练数据)、flash_attn wheel(239MB) 等。
            _SCRIPTS_EXCLUDE_DIRS = _EXCLUDE_DIR_NAMES | {"lora_data_prepare"}
            _SCRIPTS_EXCLUDE_EXT = {".whl", ".exe", ".zip", ".7z", ".gz",
                                     ".pt", ".safetensors", ".ckpt", ".bin", ".onnx"}
            for root, dirs, files in os.walk(scripts_src):
                dirs[:] = [d for d in dirs if d not in _SCRIPTS_EXCLUDE_DIRS]
                for f in files:
                    if f.endswith(".pyc"):
                        continue
                    if os.path.splitext(f)[1].lower() in _SCRIPTS_EXCLUDE_EXT:
                        continue
                    full = os.path.join(root, f)
                    zf.write(full, os.path.relpath(full, ROOT_DIR))
            print(f"  已打包 payload: scripts/ (仅 .ps1 + 维护小文件)")
    payload_size_mb = payload_path.stat().st_size / (1024 * 1024)
    print(f"  payload.zip 大小: {payload_size_mb:.1f} MB")
    pyinstaller_args.extend(["--add-data", f"{str(payload_path)};."])

    pyinstaller_args.append("launcher.py")
    print(f"  使用 launcher.py 作为入口")

    print("  运行 PyInstaller (--onefile)...")
    subprocess.run(pyinstaller_args, check=True)

    # 清理临时 payload.zip（已打进 exe，不再需要磁盘松文件）
    try:
        payload_path.unlink()
    except Exception:
        pass

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

    # 发布目录只携带源码与维护脚本，绝不带 venv / 训练数据 / node_modules /
    # 重型二进制等运行时产物（venv 由 install-env.ps1 在用户机器上创建，
    # node_modules 由 npm install 创建，模型权重由 model_downloader 下载）。
    # 历史教训：曾因 _IGNORE 只排除 __pycache__/*.pyc，导致每个发布目录
    # 携带 5.4G 的 scripts/.venv（含 torch CUDA 库），7 个版本堆积 46G+。
    _IGNORE_DIRS = {
        "__pycache__", ".venv", "venv", "node_modules",
        "lora_data_prepare", ".git", ".vscode", ".next",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
    }
    _IGNORE_EXTS = {
        ".pyc", ".pyo", ".whl", ".exe", ".zip", ".7z", ".gz",
        ".pt", ".safetensors", ".ckpt", ".bin", ".onnx",
    }

    def _make_ignore(src_dir_name: str):
        """构造 shutil.copytree 的 ignore 回调。
        src_dir_name 用于按目录定制排除规则（如 ace-step-ui 排除 server/data）。"""
        def _ignore(directory, names):
            ignored = set()
            for name in names:
                full = os.path.join(directory, name)
                if os.path.isdir(full) and name in _IGNORE_DIRS:
                    ignored.add(name)
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext in _IGNORE_EXTS:
                    ignored.add(name)
                    continue
            # ace-step-ui/server/public 运行时音频文件（~92MB）与
            # server/data SQLite 等运行时数据不应打包
            if src_dir_name == "ace-step-ui":
                norm = os.path.normpath(directory)
                if os.sep + "server" + os.sep + "public" in norm + os.sep or \
                   norm.endswith(os.sep + "server" + os.sep + "public") or \
                   norm.endswith(os.sep + "server" + os.sep + "public" + os.sep):
                    ignored.update(names)
                if os.sep + "server" + os.sep + "data" in norm + os.sep or \
                   norm.endswith(os.sep + "server" + os.sep + "data") or \
                   norm.endswith(os.sep + "server" + os.sep + "data" + os.sep):
                    ignored.update(names)
            return ignored
        return _ignore

    scripts_src = ROOT_DIR / "scripts"
    scripts_dst = release_dir / "app" / "scripts"
    if scripts_src.exists():
        if scripts_dst.exists():
            shutil.rmtree(str(scripts_dst), ignore_errors=True)
        shutil.copytree(str(scripts_src), str(scripts_dst), ignore=_make_ignore("scripts"))
        print("  ✓ 复制 scripts/ (排除 .venv / lora_data_prepare / 重型二进制)")

    acestep_src = ROOT_DIR / "acestep"
    acestep_dst = release_dir / "app" / "acestep"
    if acestep_src.exists():
        if acestep_dst.exists():
            shutil.rmtree(str(acestep_dst), ignore_errors=True)
        shutil.copytree(str(acestep_src), str(acestep_dst), ignore=_make_ignore("acestep"))
        print("  ✓ 复制 acestep/ (排除 __pycache__ / 重型二进制)")

    ace_step_ui_src = ROOT_DIR / "ace-step-ui"
    ace_step_ui_dst = release_dir / "app" / "ace-step-ui"
    if ace_step_ui_src.exists():
        if ace_step_ui_dst.exists():
            shutil.rmtree(str(ace_step_ui_dst), ignore_errors=True)
        shutil.copytree(str(ace_step_ui_src), str(ace_step_ui_dst), ignore=_make_ignore("ace-step-ui"))
        print("  ✓ 复制 ace-step-ui/ (排除 node_modules / server/public / server/data)")

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
        print("── Step 0: 生成内置 git 提交历史 ──")
        update_git_commits_json()
        print()

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
