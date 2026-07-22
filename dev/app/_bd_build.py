import importlib.util, sys, os, shutil
from pathlib import Path

APP = Path(r"E:/软件开发/云集智能音乐创意台/dev/app")

# 按路径加载 build-version.py（文件名带连字符，无法用 import）
spec = importlib.util.spec_from_file_location("bv", str(APP / "build-version.py"))
bv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bv)

print("VERSION =", bv.VERSION)
print("ROOT_DIR =", bv.ROOT_DIR)
print("BUILD_DIR =", bv.BUILD_DIR)
print("DIST_DIR =", bv.DIST_DIR)

# Step1: PyInstaller 打包（与 2309 同配置：--windowed + --splash）
exe = bv.build_exe()
print("build_exe ->", exe)

# Step2: 后处理（移动到发布目录 + 复制 app/ 资源）
rel = bv.post_build(exe)
print("post_build ->", rel)

# Step3: 清理临时
bv.cleanup()

# 复制到 dev/dist/（与 2309 并排，便于对比）
dev_dist = APP.parent / "dist"
dev_dist.mkdir(parents=True, exist_ok=True)
src = rel / exe.name
dst = dev_dist / exe.name
if dst.exists():
    dst.unlink()
shutil.copy2(str(src), str(dst))
print("COPIED ->", dst)

# 同时放一份到项目根 dist（脚本原生 DIST_DIR 行为）
bv._deploy_to_dev(rel)
print("DONE")
