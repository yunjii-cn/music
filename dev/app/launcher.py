import sys
import os
import ctypes
import ctypes.wintypes
import time
import re
import shutil
import subprocess
import tempfile
from datetime import datetime

if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    class _NullWriter:
        def write(self, *args, **kwargs):
            return 0
        def flush(self):
            pass
        def isatty(self):
            return False
    if sys.stdout is None:
        sys.stdout = _NullWriter()
    if sys.stderr is None:
        sys.stderr = _NullWriter()


# ── 与 main.py 的 BRAND_NAME 保持一致（main.py:158）──
BRAND_NAME = "云集智能音乐创意台"
ENTRY_EXE_NAME = BRAND_NAME + ".exe"
VERSION_TXT = "version.txt"
VERSIONED_RE = re.compile(r'v(\d+\.\d+\.\d+(?:\.\d+)?)')

# 自部署时创建的二级目录结构：
#   app/            —— main.get_app_dir() 依赖，承载 acestep / ace-step-ui / scripts 等运行时
#   data/           —— 模型与用户数据（outputs/models/config）
#   ver/            —— 本便携版 exe 的归档副本（版本回滚用）
#   python_embeded/ —— 便携 AI 运行时骨架（torch/transformers 等重型依赖运行在独立的
#                      嵌入式 Python 中，首次运行按需下载到此目录）。注意拼写是 embeded
#                      单 d，与全项目约定一致，不要写成 python_embedded。
#   temp/           —— 解压 / 编译 / 任务临时目录
# version.txt 由 _self_relocate 写入（main.get_version_from_filename 读取）
_DEPLOY_SUBDIRS = ("app", "data", "ver", "python_embeded", "temp")


def _kill_old_instances():
    if sys.platform != 'win32' or not getattr(sys, 'frozen', False):
        return

    my_exe = os.path.normcase(os.path.abspath(sys.executable))
    my_name = os.path.basename(my_exe)

    dash_v = my_name.find('-v')
    if dash_v <= 0:
        return
    base_name = my_name[:dash_v].lower()

    kernel32 = ctypes.windll.kernel32

    TH32CS_SNAPPROCESS = 0x00000002
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.wintypes.DWORD),
            ("cntUsage", ctypes.wintypes.DWORD),
            ("th32ProcessID", ctypes.wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.wintypes.DWORD),
            ("cntThreads", ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE:
        return

    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

    my_pid = kernel32.GetCurrentProcessId()
    pids_to_kill = []

    if kernel32.Process32FirstW(snap, ctypes.byref(entry)):
        while True:
            pid = entry.th32ProcessID
            exe_name = entry.szExeFile.lower()
            if pid != my_pid and exe_name.startswith(base_name) and exe_name.endswith('.exe'):
                pids_to_kill.append(pid)
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not kernel32.Process32NextW(snap, ctypes.byref(entry)):
                break

    kernel32.CloseHandle(snap)

    PROCESS_TERMINATE = 0x0001
    for pid in pids_to_kill:
        handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            kernel32.TerminateProcess(handle, 0)
            kernel32.CloseHandle(handle)

    if pids_to_kill:
        time.sleep(0.5)

def _resolve_deploy_dir(exe_path):
    """解析安装根目录（云集智能音乐创意台/）。

    与 main.py:get_install_root 同源逻辑：
      - 从 exe 位置**逐级向上**查找已存在的品牌目录（已部署时命中，
        避免把部署目录算成自身子目录导致无限嵌套 → WinError 206）；
      - 找不到（尚未搬迁的便携副本，如 Downloads）则回退到 exe 同级。
    """
    exe_dir = os.path.dirname(os.path.abspath(exe_path))
    d = exe_dir
    while True:
        if os.path.basename(d) == BRAND_NAME:
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.join(exe_dir, BRAND_NAME)

def _safe_delete(path):
    """带重试地删除文件（Windows 偶发 PermissionError）。"""
    for _ in range(15):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError:
            time.sleep(0.3)
        except Exception:
            return


def _self_relocate():
    """首次运行闭环（对应 2309 时代的 launcher._self_relocate）。

    由 main.py 约定（get_install_root / get_version_from_filename）调用：
      - 便携版本号 exe 首次运行 → 在同级建 云集智能音乐创意台/（含 app/data/ver/
        python_embeded/temp）+ version.txt，复制自身进 ver/，生成固定名入口，
        设 YUNJI_INSTALL_ROOT，分离式拉起入口并删除原便携 exe；
      - 固定名入口 / 已部署运行 → 解析到品牌目录，设 YUNJI_INSTALL_ROOT，
        直接落回 import main（不再嵌套）。
    """
    if not getattr(sys, 'frozen', False):
        return

    exe = os.path.abspath(sys.executable)
    exe_name = os.path.basename(exe)

    # --cleanup=<path>：入口被拉起时，删除原始便携 exe
    cleanup_target = None
    for a in sys.argv[1:]:
        if a.startswith("--cleanup="):
            cleanup_target = a.split("=", 1)[1]
            break

    deploy_dir = _resolve_deploy_dir(exe)
    already = os.path.isdir(deploy_dir) and os.path.isfile(
        os.path.join(deploy_dir, VERSION_TXT))
    if already:
        os.environ["YUNJI_INSTALL_ROOT"] = deploy_dir
        if cleanup_target:
            _safe_delete(cleanup_target)
        return

    # ── 尚未部署：便携版本号 exe → 首次自部署 ──
    os.makedirs(deploy_dir, exist_ok=True)
    for sub in _DEPLOY_SUBDIRS:
        os.makedirs(os.path.join(deploy_dir, sub), exist_ok=True)

    # 复制自身进 ver/
    ver_exe = os.path.join(deploy_dir, "ver", exe_name)
    if not os.path.exists(ver_exe) and os.path.abspath(ver_exe) != exe:
        try:
            shutil.copy2(exe, ver_exe)
        except Exception:
            pass

    # 写 version.txt（仅版本号，main.py 按 ^\d+\.\d+\.\d+(\.\d+)?$ 解析）
    m = VERSIONED_RE.search(exe_name)
    version = m.group(1) if m else datetime.now().strftime("%Y.%m.%d.%H%M")
    try:
        with open(os.path.join(deploy_dir, VERSION_TXT), "w", encoding="utf-8") as f:
            f.write(version)
    except Exception:
        pass

    # 生成固定名入口（硬链接优先，失败回退复制）
    entry_exe = os.path.join(deploy_dir, ENTRY_EXE_NAME)
    if not os.path.exists(entry_exe) and os.path.abspath(entry_exe) != exe:
        try:
            os.link(exe, entry_exe)
        except Exception:
            try:
                shutil.copy2(exe, entry_exe)
            except Exception:
                entry_exe = None

    os.environ["YUNJI_INSTALL_ROOT"] = deploy_dir
    # 分离式拉起固定名入口，并删除原始便携 exe
    if entry_exe and os.path.exists(entry_exe) and os.path.abspath(entry_exe) != exe:
        try:
            subprocess.Popen(
                [entry_exe, "--cleanup=" + exe],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass
    os._exit(0)


# ─────────────────────────────────────────────────────────────────────────────
# 崩溃日志（写到用户实际 exe 所在目录，而非 PyInstaller 解压的临时 _MEI 路径）
# ─────────────────────────────────────────────────────────────────────────────
def _crash_log_path():
    try:
        return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "crash.log")
    except Exception:
        return "crash.log"


def _write_crash(header):
    import traceback
    try:
        with open(_crash_log_path(), "a", encoding="utf-8") as f:
            f.write(header + "\n" + traceback.format_exc() + "\n")
    except Exception:
        pass


def _signal_child(ready_file):
    try:
        with open(ready_file, "w", encoding="utf-8") as f:
            f.write("1")
    except Exception:
        pass


def _try_wait(child):
    try:
        child.wait(timeout=3)
    except Exception:
        try:
            child.kill()
        except Exception:
            pass


def _parent_alive(ppid):
    """跨平台安全地探测父进程是否还活着（Windows 上 os.kill(pid,0)
    会抛 ValueError，故改用 ctypes 的 OpenProcess + GetExitCodeProcess）。"""
    try:
        k32 = ctypes.windll.kernel32
        # PROCESS_QUERY_INFORMATION = 0x400
        h = k32.OpenProcess(0x400, False, ppid)
        if not h:
            return False
        ec = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(ec))
        k32.CloseHandle(h)
        if not ok:
            return False
        return ec.value == 259        # STILL_ACTIVE
    except Exception:
        return True                     # 探测失败时保守认为存活


# ─────────────────────────────────────────────────────────────────────────────
# 子进程：纯品牌启动屏（只加载 PyQt6 + yunji_splash，绝不 import main）
#
# 为什么必须是独立进程：import main（PyQt6 冷加载 + 7838 行主模块）会长时间
# 占用 GIL；若启动屏与主进程同体，GUI 线程拿不到 GIL 片 → 动画卡顿/跳帧。
# 拆成独立进程后，启动屏进程 0 重型 import、0 GIL 争用 → 转圈光带绝对丝滑。
# 主进程在后台默默 import main，完成后写一个 sentinel 文件，子进程轮询到即收起。
# ─────────────────────────────────────────────────────────────────────────────
def _run_splash_child(progress_ready, ppid):
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from yunji_splash import BrandedSplash

    app = QApplication([sys.argv[0]])
    splash = BrandedSplash()
    splash.set_indeterminate("正在自动安装...")
    splash.show()
    splash.repaint()

    # 收屏 / 淡出必须在 GUI 线程的事件循环里驱动。
    # （历史 bug：用工作线程里的 QTimer.singleShot 收屏——工作线程没有 Qt
    #  事件循环，定时器永不触发 -> app.quit() 从不执行 -> 启动屏关不掉。）
    state = {"deadline": time.time() + 180, "fading": False}

    def _start_fade():
        """淡出交替：主进程的启动进度条出现时，本启动屏平滑淡出后退出，
        与之无缝交替，避免两个窗口硬切/叠加。

        淡出前先把本屏 raise_ 到最前——因为主进程的进度条也是
        WindowStaysOnTopHint，若本屏不主动置顶，进度条会盖在它上面、
        淡出过程就看不见了。置顶后透明度递减，露出下方已就位的进度条。
        """
        if state["fading"]:
            return
        state["fading"] = True
        try:
            splash.raise_()                 # 淡出期间盖在进度条之上 -> 可见交替
            splash.activateWindow()
        except Exception:
            pass
        op = {"v": 1.0}

        def _step():
            op["v"] -= 0.05                 # ~0.6s 淡出（12 步 × 50ms）
            if op["v"] <= 0.0:
                fade_timer.stop()
                try:
                    splash.close()
                except Exception:
                    pass
                app.quit()
            else:
                try:
                    splash.setWindowOpacity(op["v"])
                except Exception:
                    pass

        fade_timer = QTimer()
        fade_timer.setInterval(50)
        fade_timer.timeout.connect(_step)
        fade_timer.start()
        state["fade_timer"] = fade_timer    # 持有引用，防止被 GC

    def _poll():
        if state["fading"]:
            return
        done = bool(progress_ready and os.path.exists(progress_ready))
        if not done and not _parent_alive(ppid):   # 父进程已退出 -> 收起，避免孤儿启动屏
            done = True
        if not done and time.time() > state["deadline"]:
            done = True
        if done:
            _start_fade()

    poll_timer = QTimer()
    poll_timer.setInterval(80)
    poll_timer.timeout.connect(_poll)
    poll_timer.start()

    app.exec()
    try:
        if progress_ready and os.path.exists(progress_ready):
            os.remove(progress_ready)
    except Exception:
        pass
    sys.exit(0)


# ─────────────────────────────────────────────────────────────────────────────
# 主进程（supervisor）：自部署 -> 拉起纯启动屏子进程 -> import main -> 运行 app
# ─────────────────────────────────────────────────────────────────────────────
def _run_supervisor():
    if not getattr(sys, 'frozen', False):
        # 开发模式（未打包）：直接跑，不需要独立启动屏子进程
        import main as _m
        _m.main()
        return

    # 仅在 supervisor（真实入口）里做单实例清理 + 自部署；
    # --splash-child 子进程必须跳过，否则会误杀 supervisor 自身。
    _kill_old_instances()
    try:
        _self_relocate()
    except Exception:
        _write_crash("=== launcher._self_relocate 异常 ===")

    exe = os.path.abspath(sys.executable)
    ppid = os.getpid()
    # 「进度条就绪」哨兵：main.main() 在**真正显示**自己的品牌进度条时写入，
    # 子进程轮询到即淡出 —— 实现「正在自动安装」与「启动进度条」的平滑交替。
    # 此前用 import 完成作为触发，导致进度条尚未出现、动态就提前淡出、中间留黑屏空档。
    progress_ready = os.path.join(
        tempfile.gettempdir(), "yunji_progress_ready_%d.tmp" % ppid)
    try:
        if os.path.exists(progress_ready):
            os.remove(progress_ready)
    except Exception:
        pass
    # 透传给 main.main，供其在显示进度条后回写该哨兵
    os.environ["YUNJI_PROGRESS_READY"] = progress_ready

    # 拉起纯启动屏子进程（无重型 import -> 动画绝对丝滑）
    child = None
    try:
        child = subprocess.Popen(
            [exe, "--splash-child", "--progress-ready=" + progress_ready],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        child = None

    # 主进程在后台默默 import main（此处无 GUI，阻塞也无妨）
    main_mod = None
    try:
        import main as _m
        main_mod = _m
    except Exception:
        _signal_child(progress_ready)   # import 失败也释放子进程，避免孤儿启动屏
        _write_crash("=== import main 异常 ===")
        if child is not None:
            _try_wait(child)
        raise

    # 不再在这里提前收起子进程：交由 main.main() 显示真实进度条后写入
    # progress_ready 触发淡出，与进度条无缝交替（详见 main.py 的 YUNJI_PROGRESS_READY 处理）。
    try:
        main_mod.main()
    except Exception:
        _write_crash("=== main.main 异常 ===")
        raise
    finally:
        if child is not None:
            _try_wait(child)


if __name__ == "__main__":
    if "--splash-child" in sys.argv:
        # 解析 --progress-ready=<path>（main.main 显示进度条后写入）
        _ready = ""
        for _a in sys.argv[1:]:
            if _a.startswith("--progress-ready="):
                _ready = _a.split("=", 1)[1]
        _run_splash_child(_ready, os.getppid())
    else:
        _run_supervisor()
