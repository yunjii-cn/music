import os, time

# Windows 扩展长度前缀，绕过 MAX_PATH(260) 限制
P = "\\\\?\\"

dirs = [
    r"D:\Temp\yj_real",
    r"D:\Temp\yj_first",
    r"D:\Temp\yj_v2",
    r"D:\Temp\yj_firstrun",
]

for d in dirs:
    if not os.path.exists(d):
        print("已不存在", d)
        continue
    pd = P + d
    print("扫描", d, "...")
    files = []
    for root, _, fnames in os.walk(pd):
        for fn in fnames:
            fp = os.path.join(root, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                sz = 0
            files.append((fp, sz))
    files.sort(key=lambda x: -x[1])  # 大文件优先 -> 最快释放空间
    total = sum(s for _, s in files)
    print("  %d 个文件, 共 %.1f GB" % (len(files), total / 1e9))
    t0 = time.time()
    reclaimed = 0
    n = 0
    for fp, sz in files:
        try:
            os.remove(fp)
        except OSError:
            pass
        reclaimed += sz
        n += 1
        if n % 500 == 0:
            print("  %.1f%% 已删%d文件 已释放%.1fGB 用时%d秒"
                  % (100 * n / len(files), n, reclaimed / 1e9, time.time() - t0))
    # 清理残留空目录
    try:
        os.rmdir(pd)
    except OSError:
        for root, dirs_, _ in os.walk(pd, topdown=False):
            for dn in dirs_:
                try:
                    os.rmdir(os.path.join(root, dn))
                except OSError:
                    pass
        try:
            os.rmdir(pd)
        except OSError:
            pass
    print("完成 %s 释放 %.1f GB 用时%d秒" % (d, total / 1e9, time.time() - t0))

print("CLEANUP_DONE")
