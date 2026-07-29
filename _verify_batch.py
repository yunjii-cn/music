# -*- coding: utf-8 -*-
import os, sys, zlib
from PyInstaller.archive.readers import CArchiveReader

REL = r"build\云集智能音乐创意台-v2026.07.29.0431\云集智能音乐音乐创意台-v2026.07.29.0431.exe".replace("云集智能音乐音乐创意台", "云集智能音乐创意台")
# 上面替换防御笔误，直接用准确路径
REL_EXE = r"build\云集智能音乐创意台-v2026.07.29.0431\云集智能音乐创意台-v2026.07.29.0431.exe"
EXE = os.path.join(r"E:\软件开发\云集智能音乐创意台", REL_EXE)

checks_main = [
    "self.downloading_models = set()",
    "self.model_download_threads = {}",
    "self._cancelled_downloads = set()",
    "def _download_model(self, model_name, force: bool = False)",
    "def _pause_download(self, model_name=None)",
    "def _on_download_progress_updated(self, model_name: str, value: int, desc: str)",
    "thread.progress_updated.connect(",
]
checks_vm = [
    "is_downloading = _dl_target in getattr(self.main_window, 'downloading_models', set())",
    "def show_progress(self, model_name: str, text: str =",
    "def update_progress(self, model_name: str, value: int, desc: str =",
    "def hide_progress(self, model_name=None):",
    "_dl_target in getattr(self.main_window, 'downloading_models'",
]

ok = True
r = CArchiveReader(EXE)
m = r.extract("main.py").decode("utf-8", "replace")
v = r.extract("version_manager.py").decode("utf-8", "replace")
for s in checks_main:
    f = s in m
    print("main.py :", "OK " if f else "MISS", s)
    ok &= f
for s in checks_vm:
    f = s in v
    print("version_manager.py:", "OK " if f else "MISS", s)
    ok &= f

# 发布文件夹松文件
rel_dir = os.path.join(r"E:\软件开发\云集智能音乐创意台\build\云集智能音乐创意台-v2026.07.29.0431")
for fn, needle in [("app/main.py", "self.downloading_models = set()"),
                   ("app/version_manager.py", "downloading_models', set())")]:
    p = os.path.join(rel_dir, fn)
    if not os.path.exists(p):
        print("REL MISS file", p); ok = False; continue
    txt = open(p, encoding="utf-8").read()
    f = needle in txt
    print(f"release {fn}:", "OK " if f else "MISS", needle)
    ok &= f

print("VERIFY", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
