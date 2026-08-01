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

def _launch_trace(step):
    """首跑轨迹：与 main._launch_trace 协同，记录 launcher 自身（supervisor / 入口进程）
    在 import main 之前的关键步骤——首跑“什么都不显示”往往死在进入 main 之前，此处补盲。
    双写：%TEMP% 与 exe 同目录（yunji_launch_trace.log），后者用户最易找到。"""
    try:
        line = datetime.now().strftime("%H:%M:%S.%f") + " [launcher] %s | exe=%s pid=%d\n" % (
            step, os.path.basename(os.path.abspath(sys.executable)), os.getpid())
        for _p in (os.path.join(tempfile.gettempdir(), "yunji_launch_trace.log"),
                   os.path.join(os.path.dirname(os.path.abspath(sys.executable)),
                                "yunji_launch_trace.log")):
            try:
                with open(_p, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception:
                pass
    except Exception:
        pass


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


def _find_newest_versioned_exe(deploy_dir, current_exe):
    """在 ver/ 中找出版本号最大的版本号 exe；当前运行的版本号 exe 也参与比较。

    返回该 exe 的绝对路径；未找到任何版本号 exe 时返回 None。
    """
    candidates = []
    ver_dir = os.path.join(deploy_dir, "ver")
    if os.path.isdir(ver_dir):
        for name in os.listdir(ver_dir):
            if name.lower().endswith(".exe") and VERSIONED_RE.search(name):
                candidates.append((VERSIONED_RE.search(name).group(1),
                                   os.path.join(ver_dir, name)))
    cur_m = VERSIONED_RE.search(os.path.basename(current_exe))
    if cur_m:
        candidates.append((cur_m.group(1), os.path.abspath(current_exe)))
    if not candidates:
        return None

    def _vt(v):
        try:
            return tuple(int(x) for x in v.split("."))
        except Exception:
            return (0,)

    best = max(candidates, key=lambda c: _vt(c[0]))
    return best[1]


def _entry_points_to(entry_exe, target_exe):
    """判断 entry_exe 是否已硬链接/指向 target_exe（按 st_dev+st_ino 文件标识）。"""
    try:
        s1 = os.stat(entry_exe)
        s2 = os.stat(target_exe)
        return (s1.st_dev, s1.st_ino) == (s2.st_dev, s2.st_ino)
    except Exception:
        return False


def _ensure_entry_current(deploy_dir, current_exe):
    """确保固定名入口始终指向 ver/ 中最新的版本号 exe。

    根因修复：旧逻辑在「入口路径 == 当前运行路径」时直接 return，导致用户经
    固定名入口（云集智能音乐创意台.exe）双击启动时，入口永远停留在首次部署的
    旧版本，新构建下载后也跑旧代码（表现「重打包也不生效」）。

    现策略：在 ver/ 中找出最新版本号 exe，若入口不存在或已指向的旧版本 != 最新，
    则删旧入口、重建硬链接指向最新版本。调用方(_self_relocate)负责在「当前进程
    运行的镜像不是最新版」时重新拉起最新版。
    """
    entry_exe = os.path.join(deploy_dir, ENTRY_EXE_NAME)
    newest = _find_newest_versioned_exe(deploy_dir, current_exe)
    if newest is None:
        # 极端情况：没有任何版本号 exe 可指向，保持现状
        return entry_exe if os.path.exists(entry_exe) else None
    # 入口已存在且已指向最新版本 -> 无需动作
    if os.path.exists(entry_exe) and _entry_points_to(entry_exe, newest):
        return entry_exe
    # 否则 (重)建入口指向最新版本
    try:
        if os.path.exists(entry_exe):
            _safe_delete(entry_exe)
        try:
            os.link(newest, entry_exe)
        except Exception:
            shutil.copy2(newest, entry_exe)
    except Exception:
        pass
    return entry_exe if os.path.exists(entry_exe) else None


def _archive_to_ver(deploy_dir, src_exe):
    """入口文件职责：把“打包的版本 exe”（--cleanup 指向的原始 exe）复制进
    ver/ 归档（版本回滚用）。仅在缺失时复制，避免重复 53MB。

    按既定架构：“入口文件会…复制 打包的版本exe到ver”，此步骤由入口进程在
    删除原始 exe 之前完成，确保 ver/ 始终留有可回滚的版本副本。"""
    try:
        if not src_exe or not os.path.exists(src_exe):
            return
        ver_dir = os.path.join(deploy_dir, "ver")
        os.makedirs(ver_dir, exist_ok=True)
        dst = os.path.join(ver_dir, os.path.basename(src_exe))
        if not os.path.exists(dst):
            shutil.copy2(src_exe, dst)
            _launch_trace("entry: archived %s -> ver/" % os.path.basename(src_exe))
    except Exception:
        pass


def _self_relocate():
    """首次运行闭环（对应 2309 时代的 launcher._self_relocate）。

    由 main.py 约定（get_install_root / get_version_from_filename）调用：
      - 便携版本号 exe 首次运行 → 在同级建 云集智能音乐创意台/（含 app/data/ver/
        python_embeded/temp）+ version.txt，复制自身进 ver/，生成固定名入口，
        设 YUNJI_INSTALL_ROOT，标记 YUNJI_PORTABLE_EXE 后【直接落回 _run_supervisor
        主流程在本进程（Explorer 拉起、带前台权）里跑 main()】，退出后由
        self-delete-helper 删便携 exe（entry 硬链接保活数据）；
      - 固定名入口 / 已部署运行 → 解析到品牌目录，设 YUNJI_INSTALL_ROOT，
        先归档版本 exe 进 ver/ 再删原始便携 exe，直接落回 import main（不再嵌套）。
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
        _launch_trace("entry: _self_relocate already-deployed start")
        os.environ["YUNJI_INSTALL_ROOT"] = deploy_dir
        # 幂等补全子目录（防止个别旧部署缺目录导致后续 import 失败）
        for sub in _DEPLOY_SUBDIRS:
            try:
                os.makedirs(os.path.join(deploy_dir, sub), exist_ok=True)
            except Exception:
                pass
        # 入口被拉起：先把“打包的版本 exe”归档进 ver/，再删除最开始的版本 exe 自身
        # （f7d9105 proven 机制：os.remove 无需管理员、不触发杀软）。
        # 注意：删除必须无条件执行——之前误改为「仅当 ver/ 中无新版时才删」，导致
        # 正常升级/首跑后原始便携 exe 永远留在下载目录（用户反馈“能打开但不删自身”）。
        if cleanup_target:
            _archive_to_ver(deploy_dir, cleanup_target)
            _safe_delete(cleanup_target)
            _launch_trace("entry: deleted original %s" % cleanup_target)
        # 首跑 fallback 遗留清理：若上次首跑 entry 被杀软拦截未能立即删除，
        # 此处（已部署态、文件已不在运行）安全删除 —— 无需管理员、不触发杀软。
        _pending = os.path.join(deploy_dir, ".cleanup_pending")
        if os.path.exists(_pending):
            try:
                with open(_pending, "r", encoding="utf-8") as _f:
                    _target = _f.read().strip()
                if _target and os.path.exists(_target):
                    _safe_delete(_target)
                    _launch_trace("entry: pending-cleanup deleted %s" % _target)
                try:
                    os.remove(_pending)
                except Exception:
                    pass
            except Exception:
                pass
        return

    # ── 尚未部署：便携版本号 exe → 首次自部署 ──
    os.makedirs(deploy_dir, exist_ok=True)
    for sub in _DEPLOY_SUBDIRS:
        os.makedirs(os.path.join(deploy_dir, sub), exist_ok=True)

    # 注：原始（打包的版本 exe）首跑负责“建文件夹 + 建入口 + 打开入口”；
    # ver/ 归档由入口进程 _archive_to_ver 负责（此处仅顺带建好 ver/ 目录，
    # 归档动作在入口删除原始 exe 前完成，符合既定架构）。

    # 写 version.txt（仅版本号，main.py 按 ^\d+\.\d+\.\d+(\.\d+)?$ 解析）
    m = VERSIONED_RE.search(exe_name)
    version = m.group(1) if m else datetime.now().strftime("%Y.%m.%d.%H%M")
    try:
        with open(os.path.join(deploy_dir, VERSION_TXT), "w", encoding="utf-8") as f:
            f.write(version)
    except Exception:
        pass

    # 生成固定名入口（硬链接优先，失败回退复制）—— 简单直接的相对路径操作，
    # 与 f7d9105 一致：入口 = 部署目录/品牌名.exe，直接 os.link 便携 exe。
    entry_exe = os.path.join(deploy_dir, ENTRY_EXE_NAME)
    if not os.path.exists(entry_exe) and os.path.abspath(entry_exe) != exe:
        try:
            os.link(exe, entry_exe)
        except Exception:
            try:
                shutil.copy2(exe, entry_exe)
            except Exception:
                entry_exe = None
    # 同时归档一份进 ver/（供 _ensure_entry_current 后续指向最新版、入口稳定）
    ver_dir = os.path.join(deploy_dir, "ver")
    os.makedirs(ver_dir, exist_ok=True)
    ver_target = os.path.join(ver_dir, exe_name)
    if not os.path.exists(ver_target):
        try:
            shutil.copy2(exe, ver_target)
        except Exception:
            pass

    os.environ["YUNJI_INSTALL_ROOT"] = deploy_dir

    # 记录原始便携 exe 绝对路径，供「首跑 main 成功运行后」由 self-delete-helper 删除。
    # 若删除失败（杀软拦截），下次启动的 already 分支仍会读 .cleanup_pending 兜底清理。
    try:
        with open(os.path.join(deploy_dir, ".cleanup_pending"), "w", encoding="utf-8") as _f:
            _f.write(exe)
    except Exception:
        pass

    # ── 首跑关键修复：直接在【拥有前台权的便携 exe 进程】里跑 main() ──
    # 旧实现（含 f7d9105 及此前各版）首跑用 Popen 拉起独立 entry 进程、再 os._exit
    # 自身。但 Popen 子进程【不继承前台权限】，其窗口被 Windows 前台锁静默拒绝
    # 置顶/激活 -> 「Qt 报 visible=True、用户却只看到托盘、看不到窗口」。而二次双击
    # 入口（Explorer 直接拉起，自带前台权）、开发模式（终端拉起）都带前台权，故正常。
    # 二者首跑/二次除「进程是否被 Popen 拉起」外代码完全一致 —— 这正是用户观察到的
    # “第一次不行、第二次就行”的唯一差异。
    # 现改为：首跑【不 spawn 独立进程】，而是让本进程（Explorer 拉起、带前台权）直接
    # 落回 _run_supervisor 的「解压→启动屏→import main→main.main」主流程，在【与二次
    # 运行完全一致的、带前台权的进程】里显示窗口。entry 硬链接仅作未来常驻入口，不在此
    # 刻运行；便携 exe 自身由 _run_supervisor 末尾的 self-delete-helper 在退出后删除
    # （entry 为硬链接，删便携 exe 的【文件名】不影响数据，运行中的进程由 entry 名保活，
    # 与自解压安装器同款做法：无需管理员、不触发杀软）。从此首跑==二次的显示路径，根除差异。
    os.environ["YUNJI_PORTABLE_EXE"] = exe
    _launch_trace("first-run: deploy done -> will run main() in THIS (foreground-capable) process")
    return


def _extract_payload():
    """首次运行时从 exe 内置的 payload.zip 解压 acestep/ 和 ace-step-ui/ 到部署目录 app/。

    裸 exe 单独拿出去也能跑的关键：acestep/（模型下载/推理必需）和 ace-step-ui/
    （Web 前端）在构建时打包进 exe 的 _MEIPASS/payload.zip，首次运行自动解压。
    若 app/acestep/ 已存在且含 __init__.py，跳过（不覆盖用户已有文件）。
    """
    if not getattr(sys, 'frozen', False):
        return

    deploy_root = os.environ.get("YUNJI_INSTALL_ROOT")
    if not deploy_root:
        return

    app_dir = os.path.join(deploy_root, "app")

    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return

    payload_zip = os.path.join(meipass, "payload.zip")
    if not os.path.isfile(payload_zip):
        return

    import zipfile
    try:
        with zipfile.ZipFile(payload_zip, 'r') as z:
            names = z.namelist()
            # 1) scripts/ 始终刷新（受控维护脚本，含 install-env.ps1）：
            #    与用户"维护无法覆盖的文件应打包进 exe"的原则一致，确保修复可达旧部署。
            for m in [n for n in names if n.startswith("scripts/")]:
                z.extract(m, app_dir)
            # 2) acestep/ + ace-step-ui/ 仅在缺失时解压：
            #    避免每次启动重复解压 390+ 文件，且不覆盖用户已部署内容。
            acestep_dir = os.path.join(app_dir, "acestep")
            if not (os.path.isdir(acestep_dir) and os.path.isfile(os.path.join(acestep_dir, "__init__.py"))):
                for m in names:
                    if m.startswith("acestep/") or m.startswith("ace-step-ui/"):
                        z.extract(m, app_dir)
    except Exception:
        pass


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
def _pid_alive(pid):
    """探测进程是否仍存活（Windows 用 OpenProcess + GetExitCodeProcess）。"""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        ec = ctypes.c_uint()
        k32.GetExitCodeProcess(h, ctypes.byref(ec))
        k32.CloseHandle(h)
        return ec.value == 259  # STILL_ACTIVE
    except Exception:
        return False


def _run_self_delete_helper():
    """轻量「删除自身」助手：由主进程（supervisor）在窗口显示后派生，等待主进程
    退出后再删原始便携 exe。主进程退出后文件不再被占用，os.remove 即可成功
    （无需管理员）。此助手在显示之后才派生 —— 即便被安全软件拦截，也只损失
    「立即删除」、不影响已显示的启动器；若被拦截，下次启动的 .cleanup_pending
    机制仍会兜底删除。"""
    try:
        import time
        _i = sys.argv.index("--self-delete-helper") + 1
        _pid = int(sys.argv[_i])
        _target = sys.argv[_i + 1]
        _deadline = time.time() + 120
        while time.time() < _deadline:
            if not _pid_alive(_pid):
                break
            time.sleep(0.3)
        time.sleep(0.5)
        if os.path.exists(_target):
            _safe_delete(_target)
    except Exception:
        pass
    sys.exit(0)


def _wait_entry_ready(child, timeout=4.0):
    """看门狗：等待被 spawn 的入口进程确认存活。存活（未被杀软杀掉）返回 True，
    否则（已退出/被杀）返回 False。避免「入口被拦杀 -> 父进程已 os._exit -> 全黑」。"""
    import time
    _step = 0.2
    _elapsed = 0.0
    while _elapsed < timeout:
        if child.poll() is not None:
            return False
        time.sleep(_step)
        _elapsed += _step
    return child.poll() is None


def _run_supervisor():
    # 「删除自身」助手模式：不显示界面，仅等待主进程退出后删除原始便携 exe。
    if "--self-delete-helper" in sys.argv:
        _run_self_delete_helper()
        return
    _launch_trace("supervisor: _run_supervisor enter (frozen=%s)" % getattr(sys, 'frozen', False))
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

    # 首次运行时从 exe 内解压 acestep/ 和 ace-step-ui/ 到部署目录
    try:
        _extract_payload()
        _launch_trace("supervisor/entry: payload extracted")
    except Exception:
        _launch_trace("supervisor/entry: _extract_payload EXCEPTION")
        _write_crash("=== launcher._extract_payload 异常 ===")

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
        main_mod.main(child_proc=child)
    except Exception:
        _write_crash("=== main.main 异常 ===")
        raise
    finally:
        if child is not None:
            _try_wait(child)
        # 首跑：main 成功运行完毕后，派生子进程在【自身退出后】删除原始便携 exe。
        # entry 为硬链接，删便携 exe 的【文件名】不影响数据，运行中的进程由 entry 名
        # 保活（自解压安装器同款做法）。仅当 main 成功跑完才删 —— 崩溃则不删，保留
        # 便携 exe 以便重试/排查。删除从【独立子进程、退出后】执行，与旧 --cleanup
        # 机制等价（无需管理员、不触发杀软）。
        _portable = os.environ.get("YUNJI_PORTABLE_EXE")
        if _portable and os.path.exists(_portable):
            try:
                subprocess.Popen(
                    [sys.executable, "--self-delete-helper",
                     str(os.getpid()), _portable],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                _launch_trace("supervisor: spawned self-delete-helper for %s" % _portable)
            except Exception as _e:
                _launch_trace("supervisor: self-delete-helper spawn FAILED: %r" % _e)


if __name__ == "__main__":
    if "--splash-child" in sys.argv:
        # 解析 --progress-ready=<path>（main.main 显示进度条后写入）
        _ready = ""
        for _a in sys.argv[1:]:
            if _a.startswith("--progress-ready="):
                _ready = _a.split("=", 1)[1]
        _run_splash_child(_ready, os.getppid())
    else:
        _launch_trace("__main__: launching supervisor (argv=%s)" % sys.argv[:3])
        _run_supervisor()
