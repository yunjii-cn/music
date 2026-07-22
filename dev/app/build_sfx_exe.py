#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXE 打包脚本（品牌化自解压安装器）—— 云集智能音乐创意台
==========================================================
目标：给用户一个【品牌化、零点击、真实进度条】的单文件分发 EXE。

架构（三段式无缝体验）：
  ┌─────────────────────────────────────────────────────┐
  │ ① 双击分布式EXE                                     │
  │    → bootloader 解包安装器自身（静态品牌LOGO闪现）     │
  │ ② 品牌启动屏出现（与app同款：暗底+云标+渐变蓝条）       │
  │    → 真实提取进度 0% → 50%（zipfile 逐字节累计）        │
  │    → 提取完毕自动启动 launcher.exe（零点击！）         │
  │ ③ launcher.exe 启动                                  │
  │    → 品牌启动屏接棒 50% → 100%                       │
  │    → 主界面就绪                                        │
  └─────────────────────────────────────────────────────┘

产物：
  - dev/dist/云集智能音乐创意台/          onedir 文件夹（launcher.exe + PyQt6）
  - dev/dist/云集智能音乐创意台-v<版本>.exe  最终分发 EXE（含嵌入式 zip payload）

用法：
  python dev/app/build_sfx_exe.py
"""
import io
import os
import shutil
import struct
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import zipfile

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── 路径常量 ────────────────────────────────────────
APP_NAME = "云集智能音乐创意台"
ROOT_DIR = Path(__file__).resolve().parent           # dev/app/
DEV_DIR = ROOT_DIR.parent                             # dev/
DIST_DIR = DEV_DIR / "dist"                          # dev/dist/  ← 发布产物目录
ONEDIR_NAME = APP_NAME                                # onedir 子文件夹名（固定名入口）
VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
RELEASE_EXE_NAME = f"{APP_NAME}-v{VERSION}.exe"

ICON_FILE = ROOT_DIR / "icon.ico"                     # 品牌 LOGO（红云标）
SPLASH_IMG = ROOT_DIR / "splash.png"                  # bootloader 静态启动图


def gen_version_info():
    """生成 Windows 版本信息资源。"""
    parts = [int(p) for p in VERSION.split(".")]
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
                        StringStruct(u'FileDescription', u'{APP_NAME}'),
                        StringStruct(u'FileVersion', u'{VERSION}'),
                        StringStruct(u'InternalName', u'installer'),
                        StringStruct(u'LegalCopyright', u'Copyright (c) Yunjii Intelligence'),
                        StringStruct(u'OriginalFilename', u'{RELEASE_EXE_NAME}'),
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


# ════════════════════════════════════════════════════
# Step 1: 构建 onedir launcher（固定名 云集智能音乐创意台.exe）
# ════════════════════════════════════════════════════
def build_onedir_launcher():
    """PyInstaller onedir 打包 launcher（不含重型 ML 依赖）。"""
    print(f"\n[Step 1/4] 构建 onedir launcher (v{VERSION})")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    onedir_dir = DIST_DIR / ONEDIR_NAME
    if onedir_dir.exists():
        shutil.rmtree(onedir_dir)
    os.chdir(str(ROOT_DIR))

    vi = gen_version_info()
    qt_conf = ROOT_DIR / "qt.conf"
    splash_png = SPLASH_IMG

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", ONEDIR_NAME,
        "--onedir", "--windowed",
        "--contents-directory", ".",   # 平铺：依赖直接放 exe 同目录，不生成 _internal 子目录
        "--icon", str(ICON_FILE),
        "--distpath", str(DIST_DIR),
        "--workpath", str(ROOT_DIR / "_pyinstaller_work"),
        "--specpath", str(ROOT_DIR / "_pyinstaller_work"),
        "--clean", "--noconfirm",
        # 必要 hidden-import
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "loguru",
        "--hidden-import", "psutil",
        "--hidden-import", "psutil._psutil_windows",
        "--hidden-import", "huggingface_hub",
        "--hidden-import", "yunji_splash",
        # 运行时懒加载的本地模块（函数内 import，PyInstaller 静态分析抓不到）：
        # main.py 里 from acestep.model_downloader / version_manager / init_wizard import ...
        # 必须显式 hidden-import，否则冻结 exe 启动即 ModuleNotFoundError 崩溃。
        "--hidden-import", "acestep",
        "--hidden-import", "acestep.model_downloader",
        "--hidden-import", "version_manager",
        "--hidden-import", "init_wizard",
    ]
    # UPX 可执行压缩
    upx_dir = ROOT_DIR / "build_tools" / "upx-4.2.4-win64"
    if upx_dir.exists():
        args += ["--upx-dir", str(upx_dir)]
    # 排除重型依赖（在 python_embeded 中运行时下载）
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
    # 排除不需要的 Qt 子模块（减小体积）
    for mod in (
        "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtQuick", "PyQt6.QtQml", "PyQt6.QtQuickWidgets",
        "PyQt6.QtQmlModels", "PyQt6.QtQmlWorkerScript",
        "PyQt6.Qt3DAnimation", "PyQt6.Qt3DCore", "PyQt6.Qt3DExtras",
        "PyQt6.Qt3DInput", "PyQt6.Qt3DLogic", "PyQt6.Qt3DRender",
        "PyQt6.Qt3DQuick", "PyQt6.QtPdf", "PyQt6.QtPdfWidgets",
        "PyQt6.QtDesigner", "PyQt6.QtDesignerComponents",
        "PyQt6.QtCharts", "PyQt6.QtDataVisualization",
        "PyQt6.QtBluetooth", "PyQt6.QtNfc",
        "PyQt6.QtPositioning", "PyQt6.QtLocation",
        "PyQt6.QtSensors", "PyQt6.QtSerialPort",
        "PyQt6.QtSerialBus", "PyQt6.QtWebChannel",
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebEngineQuick", "PyQt6.QtWebSockets",
        "PyQt6.QtWebAssembly", "PyQt6.QtTextToSpeech",
        "PyQt6.QtRemoteObjects", "PyQt6.QtScxml",
        "PyQt6.QtStateMachine", "PyQt6.QtGamepad",
        "PyQt6.QtAxContainer", "PyQt6.QtHelp",
    ):
        args += ["--exclude-module", mod]

    # 版本信息
    if vi.exists():
        args += ["--version-file", str(vi)]
    # 资源文件（datas）—— 平铺到 exe 同目录（开发指南目录规范）
    # 平铺模式（--contents-directory .）下 PyQt6 库位于 <root>/PyQt6/Qt6，
    # qt.conf 的 Prefix=PyQt6/Qt6 相对 exe 同目录，正好正确（与 _internal 模式相反）。
    if ICON_FILE.exists():
        args += ["--add-data", f"{ICON_FILE};."]
    if SPLASH_IMG.exists():
        args += ["--add-data", f"{SPLASH_IMG};."]
    if qt_conf.exists():
        args += ["--add-data", f"{qt_conf};."]
    # 共享的启动屏模块必须打入 onedir（平铺到 exe 同目录）
    args += ["--add-data", f"{ROOT_DIR / 'yunji_splash.py'};."]

    args.append("launcher.py")

    print(f"  入口: launcher.py  输出: {ONEDIR_NAME}/")
    subprocess.run(args, check=True)

    # 写入 version.txt
    try:
        with open(onedir_dir / "version.txt", "w", encoding="utf-8") as f:
            f.write(VERSION)
        print(f"  ✓ version.txt = {VERSION}")
    except Exception as e:
        print(f"  [!] version.txt 写入失败: {e}")

    # 应用文件夹（开发指南「用户运行环境目录结构」规范）：
    # 安装根/ app/ 含 python_embeded(运行时下载) / data(模型) / temp / logs。
    # 预建骨架并放 .gitkeep，使解压后的目录结构与文档完全一致。
    for _sub in ("app", "app/python_embeded", "app/data", "app/temp", "app/logs"):
        try:
            _d = onedir_dir / _sub
            _d.mkdir(parents=True, exist_ok=True)
            (_d / ".gitkeep").touch()
        except Exception:
            pass
    print("  ✓ app/ 骨架 (python_embeded/data/temp/logs)")

    launcher_exe = onedir_dir / f"{ONEDIR_NAME}.exe"
    if not launcher_exe.exists():
        raise FileNotFoundError(f"onedir 未生成: {launcher_exe}")
    mb = launcher_exe.stat().st_size / (1024 * 1024)
    print(f"  ✓ onedir OK ({mb:.1f} MB)")
    try:
        vi.unlink()
    except Exception:
        pass
    return onedir_dir


# ════════════════════════════════════════════════════
# Step 2: 将 onedir 文件夹打成 zip payload
# ════════════════════════════════════════════════════
def zip_payload(onedir_dir):
    """将整个 onedir 文件夹打成 zip（相对路径，顶层为 BRAND_NAME/）。"""
    print(f"\n[Step 2/4] 打包 zip payload")
    payload_zip = DIST_DIR / "_payload.zip"
    if payload_zip.exists():
        payload_zip.unlink()

    # 关键：进入 onedir 文件夹内部，arcname 取「文件夹内的相对路径」，
    # 不带顶层「云集智能音乐创意台/」前缀。否则 installer 解压到
    # exe_dir/云集智能音乐创意台/ 时会再次嵌套一层，导致 launcher_exe
    # 路径对不上（三层嵌套）而启动失败。
    prev_cwd = os.getcwd()
    os.chdir(str(onedir_dir))
    try:
        with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for root, dirs, files in os.walk("."):
                for fn in files:
                    fp = Path(root) / fn
                    arcname = str(fp).replace("\\", "/")
                    if arcname.startswith("./"):
                        arcname = arcname[2:]
                    zf.write(fp, arcname)
    finally:
        os.chdir(prev_cwd)

    sz_mb = payload_zip.stat().st_size / (1024 * 1024)
    file_count = sum(1 for _ in zipfile.ZipFile(payload_zip, "r").namelist())
    print(f"  ✓ _payload.zip = {sz_mb:.1f} MB ({file_count} 个条目)")
    return payload_zip


# ════════════════════════════════════════════════════
# Step 3: 构建品牌化自解压安装器（onefile，PyQt6）
# ════════════════════════════════════════════════════
def build_installer_onefile():
    """构建 installer.py 为 onefile EXE（品牌图标 + bootloader splash + 最小依赖）。"""
    print(f"\n[Step 3/4] 构建 brand-installer (onefile)")
    os.chdir(str(ROOT_DIR))

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile", "--windowed",
        "--icon", str(ICON_FILE),
        # bootloader 阶段显示静态品牌 LOGO（安装器自身解包期间）
        "--splash", str(SPLASH_IMG) if SPLASH_IMG.exists() else "",
        "--distpath", str(DIST_DIR),
        "--workpath", str(ROOT_DIR / "_pyinstaller_work_installer"),
        "--specpath", str(ROOT_DIR / "_pyinstaller_work_installer"),
        "--clean", "--noconfirm",
        # 安装器只需最少的 Qt 模块
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "yunji_splash",
    ]

    # UPX
    upx_dir = ROOT_DIR / "build_tools" / "upx-4.2.4-win64"
    if upx_dir.exists():
        args += ["--upx-dir", str(upx_dir)]

    # 安装器绝对不需要的重型依赖（比 launcher 更激进地排除）
    heavy_modules = [
        "torch", "torchaudio", "torchvision",
        "transformers", "diffusers", "accelerate",
        "gradio", "fastapi", "uvicorn", "peft",
        "lycoris", "safe_lora", "scipy", "numpy",
        "pandas", "matplotlib", "tkinter",
        "soundfile", "librosa", "einops", "modelscope",
        "safetensors", "onnxruntime", "tensorrt",
        "diskcache", "numba", "lightning", "tensorboard",
        "loguru", "psutil", "psutil._psutil_windows",
        "huggingface_hub", "tqdm", "requests", "packaging",
        "fsspec", "PIL", "pillow",
    ]
    for m in heavy_modules:
        args += ["--exclude-module", m]

    # 安装器也不需要大部分 Qt 子模块
    qt_exclude = [
        "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtQuick", "PyQt6.QtQml", "PyQt6.QtQuickWidgets",
        "PyQt6.QtQmlModels", "PyQt6.QtQmlWorkerScript",
        "PyQt6.Qt3DAnimation", "PyQt6.Qt3DCore", "PyQt6.Qt3DExtras",
        "PyQt6.Qt3DInput", "PyQt6.Qt3DLogic", "PyQt6.Qt3DRender",
        "PyQt6.Qt3DQuick", "PyQt6.QtPdf", "PyQt6.QtPdfWidgets",
        "PyQt6.QtDesigner", "PyQt6.QtDesignerComponents",
        "PyQt6.QtCharts", "PyQt6.QtDataVisualization",
        "PyQt6.QtBluetooth", "PyQt6.QtNfc",
        "PyQt6.QtPositioning", "PyQt6.QtLocation",
        "PyQt6.QtSensors", "PyQt6.QtSerialPort",
        "PyQt6.QtSerialBus", "PyQt6.QtWebChannel",
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebEngineQuick", "PyQt6.QtWebSockets",
        "PyQt6.QtWebAssembly", "PyQt6.QtTextToSpeech",
        "PyQt6.QtRemoteObjects", "PyQt6.QtScxml",
        "PyQt6.QtStateMachine", "PyQt6.QtGamepad",
        "PyQt6.QtAxContainer", "PyQt6.QtHelp",
    ]
    for m in qt_exclude:
        args += ["--exclude-module", m]

    # 版本信息
    vi = gen_version_info()
    if vi.exists():
        args += ["--version-file", str(vi)]
    # 资源
    if ICON_FILE.exists():
        args += ["--add-data", f"{ICON_FILE};."]
    # 共享启动屏模块
    args += ["--add-data", f"{ROOT_DIR / 'yunji_splash.py'};."]

    # 入口：installer.py（不是 launcher.py！）
    args.append("installer.py")

    print(f"  入口: installer.py  名称: {APP_NAME}.exe")
    subprocess.run(args, check=True)

    installer_exe = DIST_DIR / f"{APP_NAME}.exe"
    if not installer_exe.exists():
        raise FileNotFoundError(f"installer 未生成: {installer_exe}")
    mb = installer_exe.stat().st_size / (1024 * 1024)
    print(f"  ✓ installer OK ({mb:.1f} MB)")
    try:
        vi.unlink()
    except Exception:
        pass
    return installer_exe


# ════════════════════════════════════════════════════
# Step 4: 组装最终分发包（installer + embedded zip payload）
# ════════════════════════════════════════════════════
def assemble_final(installer_exe, payload_zip):
    """将 zip payload 追加到 installer exe 尾部，附加 8 字节长度标记。

    格式：[installer binary][zip data][uint64 LE: len(zip data)]
    installer.py 启动时读取尾部 8 字节定位 payload 并提取。
    """
    print(f"\n[Step 4/4] 组装最终分发 EXE")
    final_exe = DIST_DIR / RELEASE_EXE_NAME

    payload_data = payload_zip.read_bytes()
    length_footer = struct.pack("<Q", len(payload_data))

    with open(final_exe, "wb") as out:
        # 1) installer onefile 二进制
        with open(installer_exe, "rb") as inp:
            shutil.copyfileobj(inp, out)
        # 2) zip payload
        out.write(payload_data)
        # 3) 8 字节长度标记（供 installer.py 定位 payload）
        out.write(length_footer)

    # 保存尺寸信息（清理前）
    installer_mb = installer_exe.stat().st_size / (1024 * 1024)
    payload_mb = len(payload_data) / (1024 * 1024)

    # 清理中间产物
    try:
        payload_zip.unlink()
        installer_exe.unlink()
    except Exception:
        pass

    mb = final_exe.stat().st_size / (1024 * 1024)
    print(f"  ✓ {RELEASE_EXE_NAME} = {mb:.1f} MB")
    print(f"     ├─ installer onefile: {installer_mb:.1f} MB (已清理)")
    print(f"     ├─ zip payload:      {payload_mb:.1f} MB")
    print(f"     └─ 8-byte length footer")
    return final_exe


# ════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print(f"  {APP_NAME} - 品牌化自解压打包")
    print("  (零点击 · 真实进度条 · 同款品牌UI)")
    print("=" * 60)
    print(f"  版本: v{VERSION}")
    print(f"  图标: {ICON_FILE.name} (品牌LOGO)")
    print(f"  输出: {DIST_DIR}/{RELEASE_EXE_NAME}")
    print()

    try:
        # Step 1
        onedir_dir = build_onedir_launcher()

        # Step 2
        payload_zip = zip_payload(onedir_dir)

        # Step 3
        installer_exe = build_installer_onefile()

        # Step 4
        final_exe = assemble_final(installer_exe, payload_zip)

        print()
        print("=" * 60)
        print("  ✅ 构建完成！")
        print(f"  📦 分发包: {final_exe}")
        print(f"  📁 onedir : {onedir_dir}")
        print()
        print("  使用方式:")
        print(f"    双击 {RELEASE_EXE_NAME}")
        print("    → 品牌LOGO → 真实解压进度 0%~50% → 自动启动 → 50%~100%")
        print("=" * 60)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
