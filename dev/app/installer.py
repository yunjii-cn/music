"""
installer.py — 品牌化自解压安装器（onefile 分发入口）
─────────────────────────────────────────────────────

分布式 EXE（PyInstaller onefile，品牌图标 icon.ico）双击后：

1. PyInstaller 解包自身（bootloader 阶段，短暂）
2. PyQt6 加载 → 显示品牌启动屏（与 app 完全相同的视觉：暗底+云标+渐变蓝条）
3. 从自身二进制尾部读取嵌入的 zip payload → 提取到 exe 同级「云集智能音乐创意台/」文件夹
   - 真实提取进度 0% → 50%（逐文件累计 + 缓动动画丝滑推进）
4. 提取完毕 → 自动启动 launcher.exe 并退出（零点击、无缝衔接）

后续 launcher.exe 启动后：品牌启动屏接棒 50% → 100%（yunji_splash 同一组件）。

Payload 嵌入格式（由 build_sfx_exe.py 构建）：
    [installer onefile 二进制] [zip payload] [uint64 LE: payload 字节数]

用法：
    python build_sfx_exe.py          # 构建完整分布式 EXE
    # 或手动测试：
    python installer.py              # 开发模式（从当前目录的 ../dist/onedir/ 读取 payload）
"""

import io
import os
import shutil
import struct
import subprocess
import sys
import time
import zipfile
import ctypes

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from yunji_splash import BrandedSplash

# ── 常量 ────────────────────────────────────────────
BRAND_DIR_NAME = "云集智能音乐创意台"
LAUNCHER_EXE_NAME = "云集智能音乐创意台.exe"

# 安装器进度范围：0.0 ~ 0.5（剩余 0.5~1.0 由 launcher 接棒）
INSTALL_MAX_PROGRESS = 0.5

# 以「与父进程分离」方式启动子进程，确保安装器退出（及 PyInstaller
# bootloader 清理 _MEIPASS）时不会误杀已拉起的 launcher。
_DETACH_FLAGS = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200) | 0x00000008  # DETACHED_PROCESS

def launch(exe, cwd):
    """分离式启动 launcher（windowed 子进程，不被父进程退出牵连）。"""
    return subprocess.Popen(
        [exe], cwd=cwd,
        creationflags=_DETACH_FLAGS,
        close_fds=True,
    )


def _candidate_exe_paths():
    """收集「可能是真正磁盘原 exe」的候选路径。

    PyInstaller onefile 下 sys.executable 一般指向磁盘原 exe（本机 6.20.0 实测如此），
    但为稳妥兼容不同版本/环境，额外用 GetModuleFileName(0) 取当前进程映像真实路径、
    sys.argv[0] 作为兜底，逐一尝试，谁尾部带合法 payload 就用谁。
    """
    paths = []
    try:
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetModuleFileNameW(0, buf, 1024)
        paths.append(buf.value)
    except Exception:
        pass
    if getattr(sys, 'frozen', False):
        paths.append(sys.executable)
    paths.append(os.path.abspath(sys.argv[0]))
    # 去重（保持顺序）
    seen, out = set(), []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def find_payload():
    """从安装器自身的二进制中读取嵌入的 zip payload。

    格式：[...installer binary...] [zip data] [uint64 LE: len(zip data)]
    返回 (zip_bytes: bytes) 或 None。
    """
    for self_path in _candidate_exe_paths():
        try:
            with open(self_path, "rb") as f:
                f.seek(-8, 2)           # 读最后 8 字节（payload 长度）
                length_bytes = f.read(8)
                if len(length_bytes) < 8:
                    continue
                payload_len = struct.unpack("<Q", length_bytes)[0]
                if payload_len < 100 or payload_len > 10_000_000_000:
                    continue            # 不合理大小
                f.seek(-(8 + payload_len), 2)
                payload = f.read(payload_len)
                if len(payload) != payload_len or payload[:4] != b"PK\x03\x04":
                    continue            # 不是有效 zip
            return payload
        except Exception:
            continue
    return None


def extract_payload(zip_data, target_dir, splash):
    """用 zipfile 将 payload 解压到 target_dir，通过 splash 回报真实进度。"""
    total_uncompressed = sum(zi.file_size for zi in zipfile.ZipFile(io.BytesIO(zip_data)).infolist())
    extracted = 0

    zf = zipfile.ZipFile(io.BytesIO(zip_data))
    # 按路径排序确保目录先于文件创建
    names = sorted(zf.namelist())
    for name in names:
        target_path = os.path.join(target_dir, name)
        # 跳过绝对路径攻击和目录遍历
        if not os.path.abspath(target_path).startswith(os.path.abspath(target_dir)):
            continue
        if name.endswith("/"):
            os.makedirs(target_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zf.open(name) as src, open(target_path, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 256)
                    if not chunk:
                        break
                    dst.write(chunk)
                    extracted += len(chunk)

                    # 更新提取进度（映射到 0.0 ~ INSTALL_MAX_PROGRESS）
                    frac = min(extracted / max(total_uncompressed, 1), 1.0)
                    splash.set_progress(frac * INSTALL_MAX_PROGRESS,
                                       f"正在解压运行环境… {int(frac * 100)}%")

    zf.close()


def main():
    """安装器主流程：显示品牌启动屏 → 提取 payload → 启动 launcher → 退出"""
    app = QApplication(sys.argv)
    app.setApplicationName(BRAND_DIR_NAME)

    # ── 单实例保护 ──
    instance_lock = None
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = f"Local\\{BRAND_DIR_NAME}_Installer"
        instance_lock = kernel32.CreateMutexW(None, True, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            # 已有安装器在运行，直接尝试启动已有的 launcher
            exe_dir = os.path.dirname(sys.executable)
            existing_launcher = os.path.join(exe_dir, BRAND_DIR_NAME, LAUNCHER_EXE_NAME)
            if os.path.exists(existing_launcher):
                launch(existing_launcher, os.path.join(exe_dir, BRAND_DIR_NAME))
            sys.exit(0)
    except Exception:
        pass

    # 确定安装目标目录（exe 所在目录下的品牌子文件夹）
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    install_dir = os.path.join(exe_dir, BRAND_DIR_NAME)
    launcher_exe = os.path.join(install_dir, LAUNCHER_EXE_NAME)

    # ── 快速路径：已安装则直接启动 ──
    if os.path.isfile(launcher_exe):
        launch(launcher_exe, install_dir)
        sys.exit(0)

    # ── 正式安装流程：品牌启动屏 + 提取 ──
    splash = BrandedSplash()
    splash.show()
    splash.repaint()
    app.processEvents()

    splash.set_progress(0.0, "正在准备解压…")
    app.processEvents()
    QTimer.singleShot(100, lambda: None)
    app.processEvents()

    # 读取嵌入的 payload
    payload = find_payload()
    if payload is None:
        # 开发模式 fallback：从构建输出读取
        dev_payload_path = os.path.join(
            exe_dir if not getattr(sys, 'frozen', False) else exe_dir,
            "..", "dev", "dist", "_payload.zip"
        )
        if os.path.isfile(dev_payload_path):
            with open(dev_payload_path, "rb") as f:
                payload = f.read()

    if payload is None:
        splash.set_progress(INSTALL_MAX_PROGRESS, "未找到安装数据包")
        app.processEvents()
        # 弹窗提示后退出
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, "安装数据包损坏或缺失。\n请重新下载完整安装包。",
            BRAND_DIR_NAME, 0x10  # MB_ICONERROR
        )
        sys.exit(1)

    # 执行提取（带实时进度）
    try:
        os.makedirs(install_dir, exist_ok=True)
        extract_payload(payload, install_dir, splash)

        # 进度到达 50%（安装器完成）
        splash.set_progress(INSTALL_MAX_PROGRESS, "启动中…")
        app.processEvents()

        # 写入 version.txt（供 launcher 读取版本号）
        version_file = os.path.join(install_dir, "version.txt")
        if not os.path.exists(version_file):
            # 尝试从 payload 中找 version.txt（已在 install_dir 中了）
            pass  # version.txt 应该已由 zip 解压出来

        # 启动 launcher（零点击！）
        splash.set_indeterminate("正在启动…")
        app.processEvents()
        time.sleep(0.3)   # 让用户看到"启动中…"一瞬间
        launch(launcher_exe, install_dir)

    except Exception as e:
        import traceback
        traceback.print_exc()
        # 清理失败的安装目录
        try:
            if os.path.isdir(install_dir):
                shutil.rmtree(install_dir)
        except Exception:
            pass
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, f"安装失败：{e}\n\n请检查磁盘空间或权限后重试。",
            BRAND_DIR_NAME, 0x10
        )
        sys.exit(1)
    finally:
        # 关闭启动屏并退出安装器进程
        splash.finish(None)
        # 给 launcher 一点时间接管前台
        time.sleep(0.15)


if __name__ == "__main__":
    main()
