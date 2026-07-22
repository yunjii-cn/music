#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXE 一键打包脚本 —— 云集智能音乐创意台
参考：云集智能视频创意站 dev/app/build-version.py 的「日期+时间版本号 + dev/dist 输出」套路
本项目约束（来自 docs/EXE 打包指南.md 与实际代码）：
  - 入口：launcher.py（再 import main，main.main() 拉起 PyQt6 GUI 与子进程）
  - 采用 --onefile 单文件（历史发布包均为 onefile，约 40MB）
  - 重型依赖（torch/transformers/gradio/diffusers 等）在 python_embeded 中运行，
    不进 launcher exe；launcher 只打包 PyQt6 + loguru + psutil + huggingface_hub
  - 版本号 = 日期+时间（%Y.%m.%d.%H%M），例如 2026.07.20.0105
  - 输出目录：<项目>/dev/dist/  文件名：云集智能音乐创意台-v<版本>.exe
用法：
  dev/data/.venv/Scripts/python.exe dev/app/build_onefile_exe.py
"""
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

APP_NAME = "云集智能音乐创意台"
ROOT_DIR = Path(__file__).resolve().parent        # dev/app/
DEV_DIR = ROOT_DIR.parent                          # dev/
DIST_DIR = DEV_DIR / "dist"                      # dev/dist/  ← 发布产物目录
VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
RELEASE_NAME = f"{APP_NAME}-v{VERSION}"


def gen_version_info():
    """生成带时间戳的 Windows 版本信息资源文件（不改动 release.spec 用的 version_info.txt）"""
    parts = [int(p) for p in VERSION.split(".")]     # [2026,7,20,105]
    ver_tuple = ", ".join(str(p) for p in parts)
    content = f'''# -*- coding: utf-8 -*-
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=({ver_tuple}),
        prodvers=({ver_tuple}),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'080404B0',
                    [
                        StringStruct(u'CompanyName', u'Yunjii Intelligence'),
                        StringStruct(u'FileDescription', u'云集智能音乐创意台 启动器'),
                        StringStruct(u'FileVersion', u'{VERSION}'),
                        StringStruct(u'InternalName', u'launcher'),
                        StringStruct(u'LegalCopyright', u'Copyright (c) Yunjii Intelligence'),
                        StringStruct(u'OriginalFilename', u'{RELEASE_NAME}.exe'),
                        StringStruct(u'ProductName', u'{APP_NAME}'),
                        StringStruct(u'ProductVersion', u'{VERSION}'),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [0x804, 0x4B0])]),
    ]
)
'''
    p = ROOT_DIR / "_build_version_info.txt"
    p.write_text(content, encoding="utf-8")
    return p


def build_exe():
    print(f"  PyInstaller 打包 (v{VERSION}) -> {DIST_DIR}")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(str(ROOT_DIR))

    vi = gen_version_info()
    icon = ROOT_DIR / "icon.ico"
    splash = ROOT_DIR / "splash.png"
    qt_conf = ROOT_DIR / "qt.conf"

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", RELEASE_NAME,
        "--onefile", "--windowed",
        "--icon", str(icon),
        "--distpath", str(DIST_DIR),
        "--workpath", str(ROOT_DIR / "_pyinstaller_work"),
        "--specpath", str(ROOT_DIR / "_pyinstaller_work"),
        "--clean", "--noconfirm",
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "loguru",
        "--hidden-import", "psutil",
        "--hidden-import", "psutil._psutil_windows",
        "--hidden-import", "huggingface_hub",
        "--hidden-import", "huggingface_hub.file_download",
        "--hidden-import", "huggingface_hub.snapshot_download",
        "--hidden-import", "filelock",
        "--hidden-import", "tqdm",
        "--hidden-import", "requests",
        "--hidden-import", "packaging",
        "--hidden-import", "fsspec",
    ]
    # UPX 可执行压缩（本机已下载到 build_tools/upx-4.2.4-win64）
    upx_dir = ROOT_DIR / "build_tools" / "upx-4.2.4-win64"
    if upx_dir.exists():
        args += ["--upx-dir", str(upx_dir)]
    # 重型依赖在 python_embeded 中运行，绝不打进 launcher exe
    args += [
        "--exclude-module", "torch",
        "--exclude-module", "torchaudio",
        "--exclude-module", "torchvision",
        "--exclude-module", "transformers",
        "--exclude-module", "diffusers",
        "--exclude-module", "accelerate",
        "--exclude-module", "gradio",
        "--exclude-module", "fastapi",
        "--exclude-module", "uvicorn",
        "--exclude-module", "peft",
        "--exclude-module", "lycoris",
        "--exclude-module", "safe_lora",
        "--exclude-module", "scipy",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        "--exclude-module", "soundfile",
        "--exclude-module", "librosa",
        "--exclude-module", "einops",
        "--exclude-module", "modelscope",
        "--exclude-module", "safetensors",
        "--exclude-module", "onnxruntime",
        "--exclude-module", "tensorrt",
        "--exclude-module", "diskcache",
        "--exclude-module", "numba",
        "--exclude-module", "lightning",
        "--exclude-module", "tensorboard",
    ]
    # 剔除 launcher 用不到的 Qt 子模块（其 hook 会拉进巨型 DLL：
    #   avcodec-61.dll≈14MB、Qt6Quick/Qml 各数 MB、Qt6Pdf/3D 等）
    # launcher 仅依赖 QtCore/QtGui/QtWidgets/QtSvg/QtNetwork/QtOpenGL/QtSvgWidgets
    args += [
        "--exclude-module", "PyQt6.QtMultimedia",
        "--exclude-module", "PyQt6.QtMultimediaWidgets",
        "--exclude-module", "PyQt6.QtQuick",
        "--exclude-module", "PyQt6.QtQml",
        "--exclude-module", "PyQt6.QtQuickWidgets",
        "--exclude-module", "PyQt6.QtQmlModels",
        "--exclude-module", "PyQt6.QtQmlWorkerScript",
        "--exclude-module", "PyQt6.Qt3DAnimation",
        "--exclude-module", "PyQt6.Qt3DCore",
        "--exclude-module", "PyQt6.Qt3DExtras",
        "--exclude-module", "PyQt6.Qt3DInput",
        "--exclude-module", "PyQt6.Qt3DLogic",
        "--exclude-module", "PyQt6.Qt3DRender",
        "--exclude-module", "PyQt6.Qt3DQuick",
        "--exclude-module", "PyQt6.QtPdf",
        "--exclude-module", "PyQt6.QtPdfWidgets",
        "--exclude-module", "PyQt6.QtDesigner",
        "--exclude-module", "PyQt6.QtDesignerComponents",
        "--exclude-module", "PyQt6.QtCharts",
        "--exclude-module", "PyQt6.QtDataVisualization",
        "--exclude-module", "PyQt6.QtBluetooth",
        "--exclude-module", "PyQt6.QtNfc",
        "--exclude-module", "PyQt6.QtPositioning",
        "--exclude-module", "PyQt6.QtLocation",
        "--exclude-module", "PyQt6.QtSensors",
        "--exclude-module", "PyQt6.QtSerialPort",
        "--exclude-module", "PyQt6.QtSerialBus",
        "--exclude-module", "PyQt6.QtWebChannel",
        "--exclude-module", "PyQt6.QtWebEngineCore",
        "--exclude-module", "PyQt6.QtWebEngineWidgets",
        "--exclude-module", "PyQt6.QtWebEngineQuick",
        "--exclude-module", "PyQt6.QtWebSockets",
        "--exclude-module", "PyQt6.QtWebAssembly",
        "--exclude-module", "PyQt6.QtTextToSpeech",
        "--exclude-module", "PyQt6.QtRemoteObjects",
        "--exclude-module", "PyQt6.QtScxml",
        "--exclude-module", "PyQt6.QtStateMachine",
        "--exclude-module", "PyQt6.QtGamepad",
        "--exclude-module", "PyQt6.QtAxContainer",
        "--exclude-module", "PyQt6.QtHelp",
    ]
    # 启动画面（onefile 解压期间显示，降低“卡住”观感）
    if splash.exists():
        args += ["--splash", str(splash)]
    # 版本信息
    if vi.exists():
        args += ["--version-file", str(vi)]
    # 资源文件
    if icon.exists():
        args += ["--add-data", f"{icon};."]
    if qt_conf.exists():
        args += ["--add-data", f"{qt_conf};PyQt6/Qt6"]

    args.append("launcher.py")
    print(f"  入口: launcher.py  名称: {RELEASE_NAME}.exe")
    subprocess.run(args, check=True)

    exe = DIST_DIR / f"{RELEASE_NAME}.exe"
    if not exe.exists():
        raise FileNotFoundError(f"EXE 未生成：{exe}")
    mb = exe.stat().st_size / (1024 * 1024)
    print(f"  ✓ 生成成功: {exe.name} ({mb:.1f} MB)")
    # 清理临时版本信息
    try:
        vi.unlink()
    except Exception:
        pass
    return exe


if __name__ == "__main__":
    print("=" * 60)
    print(f"  {APP_NAME} - 一键打包 (onefile / 日期+时间版本)")
    print("=" * 60)
    print(f"  版本: v{VERSION}")
    print(f"  输出: {DIST_DIR}")
    print()
    try:
        exe = build_exe()
        print()
        print("=" * 60)
        print("  构建完成！")
        print(f"  产物: {exe}")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
