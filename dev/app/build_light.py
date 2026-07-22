#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量构建驱动：只跑 build_exe()（--onefile 单文件），跳过 6GB 的
post_build 运行时拷贝与 git 推送，构建完自动复制到 dev/dist/ 供快速验证。

用法（必须在 dev/app 目录、且用含 PyInstaller 6.20.0 的 Python 跑）：
    D:/Programs/Python312/python.exe build_light.py
"""
import importlib.util
import shutil

SPEC_PATH = r"E:/软件开发/云集智能音乐创意台/dev/app/build-version.py"
spec = importlib.util.spec_from_file_location("bv", SPEC_PATH)
bv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bv)

print(">>> 开始 PyInstaller 打包（仅单文件）...")
exe = bv.build_exe()
print(">>> EXE 生成：", exe)

# 复制到 dev/dist/
bv.DIST_DIR.mkdir(parents=True, exist_ok=True)
dst = bv.DIST_DIR / exe.name
if dst.exists():
    try:
        dst.unlink()
    except Exception:
        pass
shutil.copy2(str(exe), str(dst))
print(">>> 已部署到 dist：", dst)
print("BUILD_LIGHT_DONE")
