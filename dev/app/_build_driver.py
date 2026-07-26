import sys, os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_version_mod", os.path.join(HERE, "build-version.py"))
bv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bv)

print("== build_exe ==")
exe_path = bv.build_exe()
print("exe ->", exe_path)
print("== post_build ==")
release_dir = bv.post_build(exe_path)
print("release ->", release_dir)
print("== _deploy_to_dev ==")
bv._deploy_to_dev(release_dir)
print("== done ==")
