# -*- coding: utf-8 -*-
"""构建驱动（发布版）：build_exe + post_build + 版本记录 + 部署到 dev/ + 复制到 dev/ver/。

与 dev/app/build-version.py 的 main() 等价，但**跳过 git 提交/推送**（沙箱里 push 会
失败且 git add . 会误带无关文件）。版本号与改动说明写进 version_history.json 与
versions.json，使「软件更新」页能识别新版本。

用法: D:\\Programs\\Python312\\python.exe _driver_build_release.py
"""
import importlib.util
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BV = os.path.join(_HERE, "dev", "app", "build-version.py")

spec = importlib.util.spec_from_file_location("build_version", _BV)
build_version = importlib.util.module_from_spec(spec)
sys.modules["build_version"] = build_version
spec.loader.exec_module(build_version)

CHANGES = [
    "修复打包态主窗口不显示：_deferred_init 加载阶段异常兜底，无条件显示主窗口",
    "修复固定名入口(云集智能音乐创意台.exe)永不自更新：经入口启动自动重链到最新版并重启",
]

print("STEP update_git_commits_json")
build_version.update_git_commits_json()

print("STEP build_exe")
exe_path = build_version.build_exe()
print("GOT_EXE", exe_path)

print("STEP post_build")
release_dir = build_version.post_build(exe_path)
print("GOT_RELEASE_DIR", release_dir)

print("STEP cleanup")
build_version.cleanup()

print("STEP version_history")
version_history = build_version.load_version_history()
release_name = release_dir.name
version_history[release_name] = {
    "version": release_name,
    "changes": CHANGES,
    "build_time": build_version.datetime.now().isoformat(),
    "version_number": build_version.VERSION,
}
build_version.save_version_history(version_history)

print("STEP update_versions_json")
build_version.update_versions_json(
    build_version.VERSION, CHANGES, f"{release_name}.exe")

print("STEP deploy_to_dev")
build_version._deploy_to_dev(release_dir)

print("STEP copy to dev/ver")
DEV_DIR = build_version.DEV_DIR
VER_DIR = DEV_DIR / "ver"
VER_DIR.mkdir(parents=True, exist_ok=True)
exe_in_dist = build_version.DIST_DIR / f"{release_name}.exe"
if exe_in_dist.exists():
    ver_target = VER_DIR / f"{release_name}.exe"
    if not ver_target.exists():
        shutil.copy2(str(exe_in_dist), str(ver_target))
        print(f"  ✓ 复制到 dev/ver/: {ver_target.name}")
    else:
        print(f"  - dev/ver/ 中已存在: {ver_target.name}")

print("BUILD_RELEASE_DONE", release_name, "VERSION", build_version.VERSION)
