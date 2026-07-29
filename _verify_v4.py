import sys
from PyInstaller.archive.readers import CArchiveReader
exe = r"E:/软件开发/云集智能音乐创意台/build/云集智能音乐创意台-v2026.07.29.0702/云集智能音乐创意台-v2026.07.29.0702.exe"
r = CArchiveReader(exe)
ok = True
def get(name):
    return r.extract(name).decode("utf-8", "replace")
vm = get("version_manager.py")
checks = {
    "秒开内置渲染": "先用 exe 内置的 versions.json 立即渲染",
    "确定性Gitee地址+编码": "download_tpl.format(filename=quote(fn), version=ver)",
    "下载时路径编码兜底": "_enc_path = quote(_pu.path, safe=\"/\")",
    "winner=gitee内置": 'self.data_ready.emit(current, builtin, local, "gitee")',
}
for k, s in checks.items():
    f = s in vm
    print(("OK " if f else "MISS"), k, "->", f)
    ok &= f
# versions.json 内置
try:
    vj = get("versions.json")
    print("OK versions.json 内置, len=", len(vj))
except Exception as e:
    print("MISS versions.json:", e)
    ok = False
# main.py 改名/默认
mp = get("main.py")
for k, s in {"默认exe模式": "btn_mode_exe.setChecked(True)"}:
    f = s in mp
    print(("OK " if f else "MISS"), k, "->", f)
    ok &= f
print("VERIFY", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
