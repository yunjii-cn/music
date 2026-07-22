#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建产物校验：
  1) 整 exe 扫描，确认 pyi_splash / _PYI_SPLASH_IPC 字节数为 0（避免启动屏 IPC 崩溃）。
  2) 从 CArchive 取出 launcher 模块字节，确认打包进去的是修复后的版本
     （含 _parent_alive 父进程存活探测，不再误用 os.kill(ppid,0)）。
"""
import sys
from PyInstaller.archive.readers import CArchiveReader

exe = sys.argv[1]

with open(exe, "rb") as f:
    blob = f.read()
print("== 整 exe 字节扫描 ==")
print("  pyi_splash 字节数          :", blob.count(b"pyi_splash"))
print("  _PYI_SPLASH_IPC 字节数  :", blob.count(b"_PYI_SPLASH_IPC"))

print("\n== CArchive launcher 模块校验 ==")
car = CArchiveReader(exe)
mod_name = None
_toc = getattr(car, "toc", None) or getattr(car, "contents", None)
for n in _toc:
    if "launcher" in n:
        mod_name = n
        break
print("  launcher 模块名:", mod_name)
if not mod_name:
    print("  ✗ 未找到 launcher 模块！")
    sys.exit(2)

data = car.extract(mod_name)
print("  模块大小:", len(data), "字节")
has_parent_alive = b"_parent_alive" in data
has_splash_child = b"_run_splash_child" in data
has_progress_ready = b"YUNJI_PROGRESS_READY" in data
has_progress_arg = b"--progress-ready=" in data
no_old_ready = b"--ready-file=" not in data
print("  含 _parent_alive (父进程存活探测) :", has_parent_alive)
print("  含 _run_splash_child (子进程)    :", has_splash_child)
print("  含 YUNJI_PROGRESS_READY (进度就绪):", has_progress_ready)
print("  含 --progress-ready= (新触发参数):", has_progress_arg)
print("  已去除 --ready-file= (旧触发)    :", no_old_ready)

ok = (blob.count(b"pyi_splash") == 0 and has_parent_alive
      and has_splash_child and has_progress_ready and has_progress_arg and no_old_ready)

print("\n== main.py 是否随 exe 打包（关键！）==")
# 历史坑：main.py 没打进 exe，运行时 import main 命中磁盘旧版松文件，
# launcher 的「进度条就绪」哨兵逻辑不生效 -> 淡出交替失效。
mkey = [k for k in (getattr(car, "toc", None) or getattr(car, "contents", None))
        if k.lower().endswith("main.py")]
has_main_data = bool(mkey)
main_has_sentinel = False
if has_main_data:
    md = car.extract(mkey[0])
    main_has_sentinel = (b"YUNJI_PROGRESS_READY" in md) and (b"_mark_progress_ready" in md)
    print("  main.py 数据条目:", mkey, "大小:", len(md))
    print("  含延迟哨兵 (YUNJI_PROGRESS_READY + _mark_progress_ready):", main_has_sentinel)
else:
    print("  ✗ toc 中无 main.py！运行时将命中旧版松文件，哨兵失效")

ok = ok and has_main_data and main_has_sentinel
print("\n== 结论 ==", "✓ 通过" if ok else "✗ 不通过")
sys.exit(0 if ok else 1)
