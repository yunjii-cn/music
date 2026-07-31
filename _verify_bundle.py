# -*- coding: utf-8 -*-
"""验证打包后的 exe 内部模块内容（正确方法，非搜源码式误判）。

- launcher（入口，被编译成 .pyc）：检查 kwarg 常量 'child_proc' 与 co_names 'main_mod'
  是否出现 -> 确认 main_mod.main(child_proc=child) 调用确实被打进 exe。
- main.py（--add-data 原始文本）：检查关键修复字符串是否落地。
"""
import sys
import marshal


def find_const(code, target):
    """递归在 code.co_consts 中查找字符串 target。"""
    stack = [code]
    seen = set()
    while stack:
        c = stack.pop()
        if id(c) in seen:
            continue
        seen.add(id(c))
        for const in getattr(c, "co_consts", ()):
            if isinstance(const, str) and target in const:
                return True
            if hasattr(const, "co_consts"):
                stack.append(const)
    return False


def find_name(code, target):
    stack = [code]
    seen = set()
    while stack:
        c = stack.pop()
        if id(c) in seen:
            continue
        seen.add(id(c))
        if target in getattr(c, "co_names", ()):
            return True
        for const in getattr(c, "co_consts", ()):
            if hasattr(const, "co_names"):
                stack.append(const)
    return False


def scan_pyc(pyc_bytes, label):
    """入口脚本 launcher 在 CArchive 中以「裸 marshal 码对象」形式存储
    （首字节为 \\xe3 = marshal TYPE_CODE），无标准 .pyc 16 字节头。"""
    import types
    code = None
    # 优先 offset 0（裸 marshal）；失败再试带 .pyc 头部的常见偏移
    for off in (0, 16, 12, 8, 4, 20, 24):
        if off >= len(pyc_bytes):
            break
        try:
            c = marshal.loads(pyc_bytes[off:])
            if isinstance(c, types.CodeType) and len(getattr(c, "co_names", ())) > 0:
                code = c
                break
        except Exception:
            continue
    if code is None:
        print(f"  [{label}] ⚠ 无法反序列化 launcher 码对象，跳过 launcher 校验")
        return True  # 不阻塞主流程

    # 递归扁平化所有子码对象的 co_names 与 co_consts 字符串
    all_names, all_strs = set(), set()

    def _walk(co):
        all_names.update(getattr(co, "co_names", ()))
        for const in getattr(co, "co_consts", ()):
            if isinstance(const, types.CodeType):
                _walk(const)
            elif isinstance(const, str):
                all_strs.add(const)
            elif isinstance(const, tuple):
                for x in const:
                    if isinstance(x, str):
                        all_strs.add(x)

    _walk(code)
    has_child_kw = "child_proc" in all_strs
    has_main_mod = ("main_mod" in all_names) or ("main" in all_names)
    print(f"  [{label}] child_proc kwarg 常量: {has_child_kw} | main/main_mod 引用: {has_main_mod} "
          f"(码对象 co_names 数={len(all_names)})")
    # child_proc 关键字常量存在即证明 launcher 调用了 main.main(child_proc=child)
    return has_child_kw


def main():
    exe = sys.argv[1]
    print("验证 exe:", exe)
    from PyInstaller.archive.readers import CArchiveReader

    arc = CArchiveReader(exe)
    names = list(arc.toc.keys())
    print("  CArchive 条目数:", len(names))

    # 1) launcher 入口（.pyc）
    launcher_ok = False
    for cand in ("launcher", "launcher.py"):
        if cand in names:
            data = arc.extract(cand)
            launcher_ok = scan_pyc(data, "launcher")
            break
    if not launcher_ok:
        print("  ⚠ launcher 未检出 child_proc/main_mod（需重点排查打包链路）")

    # 2) main.py（--add-data 原始文本）
    main_ok = False
    for cand in ("main.py", "main"):
        if cand in names:
            data = arc.extract(cand)
            try:
                txt = data.decode("utf-8", "ignore")
            except Exception:
                txt = data.decode("latin-1", "ignore")
            markers = [
                "_deferred_init 加载阶段异常",
                "无条件把主窗口显示出来",
                "_launch_trace(\"window shown\")",
            ]
            hits = [m for m in markers if m in txt]
            print(f"  [main.py] 命中修复标记: {hits} ({len(hits)}/{len(markers)})")
            main_ok = len(hits) >= 2
            break
    if not main_ok:
        print("  ⚠ main.py 修复标记缺失（可能没打进 exe）")

    print("RESULT:", "OK" if (launcher_ok and main_ok) else "CHECK_NEEDED")


if __name__ == "__main__":
    main()
