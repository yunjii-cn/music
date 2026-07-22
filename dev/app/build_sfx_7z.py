#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXE 打包脚本（7z SFX 品牌化安装器）—— 云集智能音乐创意台
============================================================
参考 dev/app/build_onefile_exe.py 的「onefile 单文件 launcher（约 37MB）」思路，
但改为 7z SFX 安装器分发：

  · launcher 是 ONE-FILE 自包含 exe（PyQt6 + 轻量依赖全在 exe 内，~37MB），
    解压后的安装目录才是干净的「云集智能音乐创意台/」；
  · 安装目录只含 5 项（与用户要求一致）：
        云集智能音乐创意台.exe     ← onefile 固定名 launcher
        ver                      ← 版本号文件（内容即版本号）
        app/                     ← python_embeded 等运行时（运行时下载）
        data/
        temp/
  · 全程自动化：双击 云集智能音乐创意台-v<版本>.exe → 7zS 静默解压到 %TEMP%
    → 自动启动 云集智能音乐创意台.exe（--sfx-install）→ 自迁到持久目录
    → 确认启动后看门狗删除原版本号 exe。

架构约束（7zSD/7zS 9.20）：只认 InstallPath="."（解压 %TEMP% 并自动清理），
不支持持久 InstallPath / %%S 变量；故持久化由 launcher 的 --sfx-install 阶段完成搬迁。

产物：
  - dev/dist/云集智能音乐创意台-v<版本>.exe   7z 品牌安装包（分发用，启动后自删）

用法：
  python dev/app/build_sfx_7z.py
"""
import os
import sys
import io
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── 路径常量 ───────────────────────────────────────
APP_NAME = "云集智能音乐创意台"
ROOT_DIR = Path(__file__).resolve().parent           # dev/app/
DEV_DIR = ROOT_DIR.parent                             # dev/
DIST_DIR = DEV_DIR / "dist"                          # dev/dist/
LAUNCHER_NAME = f"{APP_NAME}.exe"                  # 固定名 onefile launcher
VERSION = datetime.now().strftime("%Y.%m.%d.%H%M")
RELEASE_EXE_NAME = f"{APP_NAME}-v{VERSION}.exe"    # 版本化分发包（自删对象）

# 7z 静默安装器模块（来自 MindPlay 的 7-zip 9.20 扩展包，已验证可用）
SFX_MODULE = Path(r"E:/游戏开发/MindPlay/sfx-work/extra920/7zS.sfx")
RCEDIT = Path(r"E:/游戏开发/MindPlay/sfx-work/rcedit.exe")
ICON_FILE = ROOT_DIR / "icon.ico"                   # 品牌 LOGO（红云标）
SPLASH_FILE = ROOT_DIR / "splash.png"
QT_CONF = ROOT_DIR / "qt.conf"
SEVEN = r"c:/Program Files/7-Zip/7z.exe"
UPX_DIR = ROOT_DIR / "build_tools" / "upx-4.2.4-win64"


# ── 版本信息资源（给 onefile launcher 写入 Windows 版本号）──────
def gen_version_info():
    parts = [int(p) for p in VERSION.split(".")]      # [2026,7,21,1636]
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
                        StringStruct(u'OriginalFilename', u'{LAUNCHER_NAME}'),
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
    p = ROOT_DIR / "_sfx_version_info.txt"
    p.write_text(content, encoding="utf-8")
    return p


def build_launcher_onefile():
    """构建 ONE-FILE 固定名 launcher（PyQt6 + 轻量依赖自包含，~37MB）。

    复用 build_onefile_exe.py 的排除策略：重型依赖（torch/gradio/transformers 等）
    在 python_embeded 中运行，绝不打进 launcher；剔除 launcher 用不到的 Qt 子模块。
    输出到临时目录，返回 exe 路径。
    """
    print(f"\n[Step 1/5] 构建 ONE-FILE launcher (v{VERSION})")
    onefile_dir = DIST_DIR / "_sfx_onefile"
    if onefile_dir.exists():
        shutil.rmtree(onefile_dir)
    onefile_dir.mkdir(parents=True, exist_ok=True)

    vi = gen_version_info()
    os.chdir(str(ROOT_DIR))

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,            # → 云集智能音乐创意台.exe（固定名）
        "--onefile", "--windowed",
        "--icon", str(ICON_FILE),
        "--distpath", str(onefile_dir),
        "--workpath", str(ROOT_DIR / "_sfx_pyi_work"),
        "--specpath", str(ROOT_DIR / "_sfx_pyi_work"),
        "--clean", "--noconfirm",
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "PyQt6.QtSvg",
        "--hidden-import", "yunji_splash",
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
    # UPX 可执行压缩
    if UPX_DIR.exists():
        args += ["--upx-dir", str(UPX_DIR)]
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
    # 剔除 launcher 用不到的 Qt 子模块（其 hook 会拉进巨型 DLL）
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
    if SPLASH_FILE.exists():
        args += ["--splash", str(SPLASH_FILE)]
    # 版本信息
    if vi.exists():
        args += ["--version-file", str(vi)]
    # 资源：icon 平铺到 exe 内；qt.conf 进 bundle 内部 PyQt6/Qt6（onefile 内生效）
    if ICON_FILE.exists():
        args += ["--add-data", f"{ICON_FILE};."]
    if QT_CONF.exists():
        args += ["--add-data", f"{QT_CONF};PyQt6/Qt6"]

    args.append("launcher.py")
    print(f"  入口: launcher.py  名称: {LAUNCHER_NAME}")
    subprocess.run(args, check=True)

    exe = onefile_dir / LAUNCHER_NAME
    if not exe.exists():
        raise FileNotFoundError(f"launcher 未生成：{exe}")
    mb = exe.stat().st_size / (1024 * 1024)
    print(f"  ✓ 生成成功: {exe.name} ({mb:.1f} MB)")
    try:
        vi.unlink()
    except Exception:
        pass
    return exe


def make_payload(launcher_exe):
    """构造干净的安装目录镜像（5 项），返回该目录。"""
    print(f"\n[Step 2/5] 构造安装目录镜像（5 项）")
    payload = DIST_DIR / "_sfx_payload"
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir(parents=True, exist_ok=True)

    # ① 固定名 onefile launcher
    shutil.copy2(str(launcher_exe), str(payload / LAUNCHER_NAME))

    # ② ver 版本号文件
    (payload / "ver").write_text(VERSION, encoding="utf-8")

    # ③ app/ 运行时骨架（python_embeded 运行时下载）
    app_dir = payload / "app"
    app_dir.mkdir(exist_ok=True)
    pe = app_dir / "python_embeded"
    pe.mkdir(exist_ok=True)
    (pe / ".gitkeep").write_text("", encoding="utf-8")

    # ④ ⑤ data/ 与 temp/（顶层）
    for d in ("data", "temp"):
        dd = payload / d
        dd.mkdir(exist_ok=True)
        (dd / ".gitkeep").write_text("", encoding="utf-8")

    print(f"  ✓ payload: {payload}")
    for p in sorted(payload.iterdir()):
        if p.is_dir():
            print(f"      📁 {p.name}/")
        else:
            print(f"      📄 {p.name}")
    return payload


def make_archive(payload_dir):
    """把 payload 内容平铺打成 archive.7z（LZMA2 高压缩）。"""
    print(f"\n[Step 3/5] 打包 archive.7z (LZMA2 -mx9, 平铺)")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    arc = DIST_DIR / "_sfx_archive.7z"
    if arc.exists():
        arc.unlink()
    # 平铺：归档 payload 内全部内容（无顶层目录前缀）
    cmd = [
        SEVEN, "a", str(arc),
        f"{payload_dir}\\*",
        "-t7z", "-mx9", "-mmt", "-snh", "-sccUTF-8",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise RuntimeError("7z 归档失败")
    mb = arc.stat().st_size / (1024 * 1024)
    print(f"  ✓ {arc.name} = {mb:.1f} MB")
    return arc


def brand_sfx():
    """用 rcedit 把品牌图标写进 7zS.sfx 副本。"""
    print(f"\n[Step 4/5] rcedit 品牌化 7zS 图标")
    branded = DIST_DIR / "_7zS_branded.sfx"
    if branded.exists():
        branded.unlink()
    shutil.copy2(str(SFX_MODULE), str(branded))
    if ICON_FILE.exists() and RCEDIT.exists():
        cmd = [str(RCEDIT), str(branded), "--set-icon", str(ICON_FILE)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  rcedit exit={r.returncode}")
        if r.returncode != 0:
            print(r.stdout)
            print(r.stderr)
    else:
        print("  [!] 图标/ rcedit 缺失，跳过换图标")
    print(f"  ✓ {branded.name}")
    return branded


def write_config():
    """生成 7z SFX 安装器配置：静默解压 %TEMP% + 自动运行 launcher。"""
    print(f"\n[Step 5/5] 生成 config.txt")
    cfg = (
        ';!@Install@!UTF-8!\r\n'
        f'Title="{APP_NAME}"\r\n'
        'InstallPath="."\r\n'
        f'RunProgram="{LAUNCHER_NAME} --sfx-install"\r\n'
        ';!@InstallEnd@!\r\n'
    )
    cfg_path = DIST_DIR / "_sfx_config.txt"
    cfg_path.write_bytes(cfg.encode("utf-8-sig"))
    print(f"  ✓ {cfg_path.name}")
    print("     " + repr(cfg))
    return cfg_path


def assemble(final_exe, branded_sfx, cfg, arc):
    """拼接：7zS-branded.sfx + config.txt + archive.7z → 最终 SFX exe。"""
    print(f"\n[Assemble] 组装最终分发 EXE")
    with open(final_exe, "wb") as out:
        with open(branded_sfx, "rb") as f:
            shutil.copyfileobj(f, out)
        with open(cfg, "rb") as f:
            shutil.copyfileobj(f, out)
        with open(arc, "rb") as f:
            shutil.copyfileobj(f, out)
    mb = final_exe.stat().st_size / (1024 * 1024)
    print(f"  ✓ {final_exe.name} = {mb:.1f} MB")
    # 清理中间产物
    for p in (branded_sfx, cfg, arc):
        try:
            p.unlink()
        except Exception:
            pass
    # 清理 onefile 临时构建目录
    for d in (DIST_DIR / "_sfx_onefile", ROOT_DIR / "_sfx_pyi_work"):
        try:
            if d.exists():
                shutil.rmtree(d)
        except Exception:
            pass
    return final_exe


if __name__ == "__main__":
    print("=" * 60)
    print(f"  {APP_NAME} - 7z SFX 品牌化打包（onefile launcher）")
    print("  (原生 7z 解压 · 干净 5 项目录 · 启动后删原 exe)")
    print("=" * 60)
    print(f"  版本: v{VERSION}")
    print(f"  输出: {DIST_DIR}/{RELEASE_EXE_NAME}")
    print()

    try:
        launcher_exe = build_launcher_onefile()
        payload = make_payload(launcher_exe)
        arc = make_archive(payload)
        branded = brand_sfx()
        cfg = write_config()
        final = assemble(DIST_DIR / RELEASE_EXE_NAME, branded, cfg, arc)
        # 清理 payload 临时目录
        try:
            if payload.exists():
                shutil.rmtree(payload)
        except Exception:
            pass

        print()
        print("=" * 60)
        print("  ✅ 构建完成！")
        print(f"  📦 分发包: {final}")
        print()
        print("  安装目录（解压后 / SFX 同级 云集智能音乐创意台/）:")
        print("    ├─ 云集智能音乐创意台.exe   (onefile launcher, 固定名)")
        print("    ├─ ver                    (版本号文件)")
        print("    ├─ app/                   (python_embeded 运行时)")
        print("    ├─ data/")
        print("    └─ temp/")
        print()
        print("  使用方式:")
        print(f"    双击 {RELEASE_EXE_NAME}")
        print("    → 7z 静默解压(%TEMP%) → 自动启动 launcher")
        print("    → launcher 自迁到持久目录 → 启动后删除原 exe")
        print("=" * 60)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
