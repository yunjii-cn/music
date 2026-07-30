"""
版本管理器模块 - 混合模式版本管理器
支持Git开发版（Gitee API）和EXE稳定版管理
所有远程数据获取均通过 urlopen，零 subprocess，零弹窗
"""

import sys
import os
import re
import base64
import threading
import time as time_module
from datetime import datetime
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote, urlparse, urlunparse

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QWidget, QMessageBox, QFrame, QApplication,
    QComboBox, QTabWidget, QProgressBar, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, QPointF
from PyQt6.QtGui import QFont, QDesktopServices, QColor


# ── 品牌 & 仓库坐标 ──
BRAND_NAME = "云集智能音乐创意台"
APP_NAME = BRAND_NAME

GITEE_OWNER = "yunjii"
GITEE_REPO = "music"
GITHUB_OWNER = "yunjii-cn"
GITHUB_REPO = "music"

REMOTE_REPO_OWNER = GITEE_OWNER
REMOTE_REPO_NAME = GITEE_REPO
REMOTE_COMMITS_URL = f"https://gitee.com/api/v5/repos/{REMOTE_REPO_OWNER}/{REMOTE_REPO_NAME}/commits"
REMOTE_VERSIONS_API = f"https://gitee.com/api/v5/repos/{REMOTE_REPO_OWNER}/{REMOTE_REPO_NAME}/contents/dev/app/versions.json"

DARK_BTN_STYLE = """
    QPushButton {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3A3A3A;
        border-radius: 4px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #3A3A3A;
        border-color: #4A4A4A;
        color: #FFFFFF;
    }
    QPushButton:pressed {
        background-color: #1A1A1A;
    }
"""

# ── 配色 token（暗色 · 品牌红 #CC0000，对齐视频创意站软件更新布局）──
C_BG = "#111113"
C_SURFACE = "#1A1A1A"
C_SURFACE_2 = "#141414"
C_SURFACE_3 = "#111113"
C_SURFACE_CUR = "#1A1A1A"
C_BORDER = "#333333"
C_BORDER_SOFT = "#222222"
C_BORDER_HOVER = "#444444"
C_ACCENT = "#CC0000"          # 品牌主色（选中 tab / 主操作 / 取消）
C_ACCENT_HOVER = "#FF0000"
C_ACCENT_PRESS = "#DD0000"
C_ACCENT_SOFT = "rgba(204,0,0,0.16)"
C_GREEN = "#2E7D32"           # 正面操作（下载 / 检查更新）
C_GREEN_HOVER = "#388E3C"
C_GREEN_TXT = "#FFFFFF"
C_GOLD = "#FBBF24"            # 保留（备用）
C_GOLD_TXT = "#3A2E00"
C_TEXT = "#F4F4F5"
C_TEXT_2 = "#CCCCCC"
C_TEXT_3 = "#888888"

# ── 复用视频创意站软件更新布局的 Tab / 按钮样式 ──
TAB_ACTIVE_STYLE = (
    "QPushButton { background-color: #CC0000; color: #FFFFFF; border: none; border-radius: 6px;"
    " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold;"
    " padding: 6px 8px; min-width: 92px; }"
    " QPushButton:hover { background-color: #FF0000; }"
    " QPushButton:pressed { background-color: #DD0000; }"
)
TAB_INACTIVE_STYLE = (
    "QPushButton { background-color: #333333; color: #AAAAAA; border: 1px solid #444444; border-radius: 6px;"
    " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold;"
    " padding: 6px 8px; min-width: 92px; }"
    " QPushButton:hover { background-color: #444444; color: #DDDDDD; }"
)
# 注意：按钮文字宽度 = 文字 + 左右 padding。固定尺寸必须 > 该值，否则 Qt 会直接裁切文字
# 边缘（不显示省略号）。这里用 9pt + padding 6px/14px + 固定 64×32，对「运行/下载」(2 字) 留足余量。
BTN_RED_STYLE = (
    "QPushButton { background-color: #CC0000; color: #FFFFFF; border: none; border-radius: 6px;"
    " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold;"
    " padding: 6px 14px; min-width: 56px; }"
    " QPushButton:hover { background-color: #FF0000; }"
    " QPushButton:pressed { background-color: #DD0000; }"
)
BTN_GREEN_STYLE = (
    "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; border-radius: 6px;"
    " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold;"
    " padding: 6px 14px; min-width: 56px; }"
    " QPushButton:hover { background-color: #388E3C; }"
    " QPushButton:pressed { background-color: #1B5E20; }"
)

# 「加载更多」按钮（底部懒加载触发）
LOAD_MORE_STYLE = (
    "QPushButton { background-color: #1A1A1A; color: #888888; border: 1px solid #2A2A2A; border-radius: 6px;"
    " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold; }"
    " QPushButton:hover { background-color: #222222; color: #BBBBBB; border-color: #3A3A3A; }"
    " QPushButton:pressed { background-color: #151515; }"
)


class VersionCard(QFrame):
    """带悬停发光的高级版本卡片（品牌红微光）。

    - 鼠标进入：阴影模糊半径 0→18、偏移 0→(0,3)，OutCubic 缓动（60fps 丝滑抬升）。
    - 当前版本：静态品牌红微光，使其在列表中自然跳脱。
    """

    def __init__(self, parent=None, is_current=False):
        super().__init__(parent)
        self._is_current = is_current
        self._glow = QColor(204, 0, 0, 75) if is_current else QColor(170, 170, 185, 55)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(16 if is_current else 0)
        self._shadow.setOffset(0, 2 if is_current else 0)
        self._shadow.setColor(self._glow)
        self.setGraphicsEffect(self._shadow)
        self._anims = []

    def enterEvent(self, event):
        super().enterEvent(event)
        self._animate(20, 4)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._is_current:
            self._animate(16, 2)
        else:
            self._animate(0, 0)

    def _animate(self, blur, dy):
        for prop in (b"blurRadius", b"offset"):
            anim = QPropertyAnimation(self._shadow, prop)
            anim.setDuration(220)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            if prop == b"blurRadius":
                anim.setStartValue(self._shadow.blurRadius())
                anim.setEndValue(blur)
            else:
                anim.setStartValue(self._shadow.offset())
                anim.setEndValue(QPointF(0, dy))
            anim.start()
            self._anims.append(anim)

DARK_BTN_PRIMARY = """
    QPushButton {
        background-color: #1565C0;
        color: #FFFFFF;
        border: 1px solid #1976D2;
        border-radius: 4px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1976D2;
        border-color: #2196F3;
    }
    QPushButton:pressed {
        background-color: #0D47A1;
    }
    QPushButton:disabled {
        background-color: #2A2F38;
        color: #777777;
        border-color: #3A3F48;
    }
"""

DARK_BTN_SUCCESS = """
    QPushButton {
        background-color: #2E7D32;
        color: #FFFFFF;
        border: 1px solid #388E3C;
        border-radius: 4px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #388E3C;
        border-color: #43A047;
    }
    QPushButton:pressed {
        background-color: #1B5E20;
    }
"""

DARK_BTN_DANGER = """
    QPushButton {
        background-color: #C62828;
        color: #FFFFFF;
        border: 1px solid #D32F2F;
        border-radius: 4px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #D32F2F;
        border-color: #E53935;
    }
    QPushButton:pressed {
        background-color: #B71C1C;
    }
    QPushButton:disabled {
        background-color: #382A2A;
        color: #777777;
        border-color: #483A3A;
    }
"""

def _get_gitee_token():
    if hasattr(sys, '_MEIPASS'):
        token_file = Path(sys._MEIPASS) / ".gitee_token"
    else:
        token_file = Path(__file__).parent / ".gitee_token"
    if token_file.exists():
        return token_file.read_text(encoding='utf-8').strip()
    return ""


def _get_github_token():
    if hasattr(sys, '_MEIPASS'):
        token_file = Path(sys._MEIPASS) / ".github_token"
    else:
        token_file = Path(__file__).parent / ".github_token"
    if token_file.exists():
        return token_file.read_text(encoding='utf-8').strip()
    return ""


def _build_api_url(base_url):
    token = _get_gitee_token()
    if token:
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}access_token={token}"
    return base_url


# ── 更新源配置 ──
def _get_gitee_token_param():
    token = _get_gitee_token()
    if token:
        return f"&access_token={token}"
    return ""

_GITEE_TOKEN_PARAM = _get_gitee_token_param()

UPDATE_SOURCES = {
    "github_mirror": {
        "name": "GitHub镜像(ghproxy)",
        "version_url": f"https://ghproxy.net/https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/dev/app/versions.json",
        "download_url_tpl": f"https://ghproxy.net/https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{{version}}/{{filename}}",
        "releases_url": f"https://ghproxy.net/https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
        "is_api": False,
    },
    "github": {
        "name": "GitHub",
        "version_url": f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/dev/app/versions.json",
        "download_url_tpl": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{{version}}/{{filename}}",
        "releases_url": f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
        "is_api": False,
    },
    "gitee": {
        "name": "Gitee",
        "version_url": f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/dev/app/versions.json?ref=main{_GITEE_TOKEN_PARAM}",
        "download_url_tpl": f"https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/releases/download/v{{version}}/{{filename}}{_GITEE_TOKEN_PARAM}",
        "releases_url": f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/releases?per_page=10{_GITEE_TOKEN_PARAM}",
        "is_api": True,
    },
}


class _RemoteFetchThread(QThread):
    """远程获取线程（仅用户点「🌐 远程获取」时启动）。

    全程 urlopen，零 subprocess、零弹窗（对齐视频创意站「本地优先、远程手动」）。
    打开页面**不走此线程**——直接同步读 exe 内置静态列表渲染，零线程零网络。
    合并原 _ExeFetchWorker / _GitCommitsFetchWorker，统一一个线程处理两种模式。
    """
    # (mode, current, versions, local, winner)
    data_ready = pyqtSignal(str, object, object, object, str)

    def __init__(self, dialog, mode, auto_remote=False):
        super().__init__()
        self.dialog = dialog
        self.mode = mode  # "exe" | "git"
        self.auto_remote = auto_remote
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _fetch_url(self, url, is_api=False, timeout=12):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urlopen(req, timeout=timeout)
            raw = resp.read().decode("utf-8")
            if is_api:
                api_data = json.loads(raw)
                if isinstance(api_data, list):
                    file_data = api_data[0] if api_data else {}
                else:
                    file_data = api_data
                content_b64 = file_data.get("content", "")
                decoded = base64.b64decode(content_b64).decode("utf-8")
                return json.loads(decoded), None
            return json.loads(raw), None
        except Exception as e:
            return None, str(e)

    def run(self):
        try:
            current = self.dialog._get_current_exe_version()
            if self._cancelled:
                return
            if self.mode == "exe":
                builtin = self.dialog._get_builtin_versions()
                if builtin and not self._cancelled:
                    self.data_ready.emit("exe", current, builtin, {}, "github_mirror")
                if not self.auto_remote or self._cancelled:
                    return
                # 多源竞速拉远程版本列表
                sources = UPDATE_SOURCES
                result, winner = None, None
                results_lock = threading.Lock()
                done_event = threading.Event()

                def try_source(key):
                    nonlocal result, winner
                    if done_event.is_set() or self._cancelled:
                        return
                    source = sources[key]
                    data, _err = self._fetch_url(source["version_url"], source.get("is_api", False))
                    if data is not None and not done_event.is_set() and not self._cancelled:
                        with results_lock:
                            if not done_event.is_set():
                                result, winner = data, key
                                done_event.set()

                threads = []
                for key in sources:
                    t = threading.Thread(target=try_source, args=(key,), daemon=True)
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join(timeout=20)
                if self._cancelled:
                    return
                remote = result if result else self.dialog._fetch_remote_versions(fallback=True)
                remote = remote if isinstance(remote, list) else []
                if remote and not self._cancelled:
                    self.data_ready.emit("exe", current, remote, {}, winner or "github_mirror")
            else:  # git
                builtin = self.dialog._get_builtin_commits()
                if builtin and not self._cancelled:
                    self.data_ready.emit("git", current, builtin, None, "builtin")
                if not self.auto_remote or self._cancelled:
                    return
                for url in (GITHUB_COMMITS_MIRROR, GITHUB_COMMITS_URL, GITEE_COMMITS_URL):
                    if self._cancelled:
                        return
                    data, _err = self._fetch_url(url)
                    if isinstance(data, list):
                        commits = [self.dialog._normalize_commit(c) for c in data if c]
                        if commits and not self._cancelled:
                            self.data_ready.emit("git", current, commits, None, url)
                            return
        except Exception as e:
            print(f"远程获取失败: {e}")
            if not self._cancelled:
                if self.mode == "exe":
                    builtin = self.dialog._get_builtin_versions()
                    self.data_ready.emit("exe", None, builtin or [], {}, "gitee")
                else:
                    builtin = self.dialog._get_builtin_commits()
                    if builtin:
                        self.data_ready.emit("git", None, builtin, None, "builtin")


# ── 远程提交历史源（仅用户手动点「远程获取」时拉取）──
GITEE_COMMITS_URL = f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/commits?per_page=60&sha=main{_GITEE_TOKEN_PARAM}"
GITHUB_COMMITS_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=60"
GITHUB_COMMITS_MIRROR = f"https://ghproxy.net/https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=60"


# 注：原 _GitCommitsFetchWorker 已合并进上方的 _RemoteFetchThread（mode="git"）。




class HybridVersionManagerDialog(QWidget):
    """软件更新栏目（纯净版，零子进程）。

    设计原则（对齐视频创意站「本地优先、远程手动」）：
    - 打开页面：同步读 exe 内置 versions.json / git_commits.json，直接渲染。
      零线程、零网络、零子进程、零弹窗。
    - 远程获取：仅用户点「🌐 远程获取」按钮时，由 _RemoteFetchThread 走 urlopen 拉取，
      不 spawn 任何进程、不弹任何窗口。
    - 打开/运行版本、下载：仅用户主动点击按钮时触发；启动本地 exe 一律 CREATE_NO_WINDOW，
      下载走浏览器（QDesktopServices，无窗口、无子进程）。
    """

    def __init__(self, parent=None, project_root=None, as_widget=False):
        super().__init__(parent)
        self.project_root = project_root
        self.as_widget = as_widget
        self.setObjectName("versionManagerPage")
        self.setWindowTitle("版本管理器")
        if not as_widget:
            self.setMinimumSize(950, 650)
            self.resize(1050, 750)
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("QWidget#versionManagerPage { background-color: #111113; }")

        self.current_mode = "exe"
        self._versions_loaded = False
        self._git_repo_checked = False
        self.has_git_repo = False
        self._remote_worker = None
        self._remote_versions_cache = None
        self.version_history = {}

        # ── 视图模式（详情 / 列表）+ 懒加载分页 ──
        # 默认详情模式；详情一次 10 条，列表一次 20 条（对齐视频创意站）
        self._detail_mode = True
        self._detail_page_size = 10
        self._list_page_size = 20
        self._rendered_count = 0
        self._data_cache = []
        self._render_is_exe = True
        self._current_exe_version = None
        self._load_more_btn = None

        self._setup_ui()
        self._load_local_version_history()

    # ───────────────────────── 本地数据（纯文件读，零子进程） ─────────────────────────
    def _load_local_version_history(self):
        self.version_history = {}
        candidates = []
        if self.project_root:
            candidates.append(Path(self.project_root) / 'app' / 'version_history.json')
            candidates.append(Path(self.project_root).parent / 'dist' / 'version_history.json')
        if hasattr(sys, '_MEIPASS'):
            candidates.append(Path(sys._MEIPASS) / 'version_history.json')
        for p in candidates:
            if p and p.exists():
                try:
                    self.version_history = json.loads(Path(p).read_text(encoding='utf-8'))
                    break
                except Exception as e:
                    print(f"加载版本历史失败：{e}")

    def _get_version_changes(self, version_name):
        if version_name in self.version_history:
            return self.version_history[version_name].get('changes', [])
        name_without_ext = version_name.replace('.exe', '')
        if name_without_ext in self.version_history:
            return self.version_history[name_without_ext].get('changes', [])
        return []

    @staticmethod
    def _parse_ver(ver):
        try:
            return tuple(int(x) for x in re.findall(r'\d+', ver)[:4])
        except Exception:
            return (0,)

    def _is_newer(self, ver, cur):
        if not cur:
            return False
        try:
            return self._parse_ver(ver) > self._parse_ver(cur)
        except Exception:
            return False

    def _check_git_repo(self):
        try:
            current_dir = Path(self.project_root) if self.project_root else Path.cwd()
            while current_dir.parent != current_dir:
                if (current_dir / ".git").exists():
                    return True
                current_dir = current_dir.parent
            return False
        except Exception:
            return False

    def _get_current_exe_version(self):
        try:
            if hasattr(sys, 'frozen'):
                exe_path = sys.executable
                exe_name = os.path.basename(exe_path)
            else:
                if self.version_history:
                    latest_version = sorted(self.version_history.keys(), reverse=True)[0]
                    match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', latest_version)
                    if match:
                        version = match.group(1)
                        return {
                            'version': version,
                            'name': latest_version,
                            'size': "开发模式",
                            'path': os.path.abspath(__file__)
                        }
                return None

            match = re.search(r'v(\d{4}\.\d{2}\.\d{2}\.\d{4})', exe_name)
            if not match:
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_name)

            if match:
                version = match.group(1)
                file_size = os.path.getsize(exe_path) / (1024 * 1024)
                return {
                    'version': version,
                    'name': exe_name,
                    'size': f"{file_size:.2f} MB",
                    'path': exe_path
                }
            return None
        except Exception as e:
            print(f"获取当前EXE版本失败：{e}")
            return None

    def _fetch_remote_versions(self, fallback=False):
        if not fallback and self._remote_versions_cache is not None:
            return self._remote_versions_cache
        try:
            url = _build_api_url(REMOTE_VERSIONS_API)
            req = Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            content_b64 = data.get('content', '')
            content = base64.b64decode(content_b64).decode('utf-8')
            versions = json.loads(content)
            if not fallback:
                self._remote_versions_cache = versions
            return versions
        except HTTPError as e:
            print(f"远程稳定版获取失败 (HTTP {e.code}): {e.reason}")
            return []
        except URLError as e:
            print(f"远程稳定版获取失败 (网络错误): {e.reason}")
            return []
        except Exception as e:
            print(f"远程稳定版获取失败: {e}")
            return []

    def _get_builtin_versions(self):
        candidates = []
        if hasattr(sys, '_MEIPASS'):
            candidates.append(Path(sys._MEIPASS) / "versions.json")
        candidates.append(Path(os.path.dirname(sys.executable)) / "versions.json")
        if self.project_root:
            candidates.append(Path(self.project_root) / "versions.json")
        for p in candidates:
            try:
                if p.exists():
                    data = json.loads(Path(p).read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        return data
            except Exception as e:
                print(f"读取内置 versions.json 失败 ({p}): {e}")
        return []

    def _get_builtin_commits(self):
        candidates = []
        if hasattr(sys, '_MEIPASS'):
            candidates.append(Path(sys._MEIPASS) / "git_commits.json")
        candidates.append(Path(os.path.dirname(sys.executable)) / "git_commits.json")
        if self.project_root:
            candidates.append(Path(self.project_root) / "git_commits.json")
        candidates.append(Path(__file__).parent / "git_commits.json")
        for p in candidates:
            try:
                if p.exists():
                    data = json.loads(Path(p).read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        return data
            except Exception as e:
                print(f"读取内置 git_commits.json 失败 ({p}): {e}")
        return []

    def _normalize_commit(self, raw):
        c = raw.get("commit", {}) or {}
        author = c.get("author", {}) or {}
        msg = c.get("message", "") or ""
        return {
            "hash": raw.get("sha", ""),
            "short_hash": (raw.get("sha", "") or "")[:8],
            "message": msg.split("\n", 1)[0],
            "body": msg,
            "author": author.get("name", ""),
            "email": author.get("email", ""),
            "date": (author.get("date", "") or "")[:19].replace("T", " "),
        }

    def _get_local_version_string(self):
        try:
            if hasattr(sys, 'frozen'):
                exe_name = os.path.basename(sys.executable)
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_name)
                if match:
                    return match.group(1)
            return None
        except Exception:
            return None

    # ───────────────────────── UI（复用视频创意站软件更新布局） ─────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 顶部「当前版本」卡片（#1A1A1A / 边框 #333）──
        current_card = QFrame()
        current_card.setStyleSheet(
            "QFrame { background-color: #1A1A1A; border: 1px solid #333333; border-radius: 8px; }")
        current_card.setContentsMargins(0, 0, 0, 0)
        cc_layout = QVBoxLayout(current_card)
        cc_layout.setContentsMargins(16, 12, 16, 12)
        cc_layout.setSpacing(6)
        cc_top = QHBoxLayout()
        cc_top.setSpacing(12)
        cur = self._get_current_exe_version()
        cur_ver = (cur or {}).get('version', '开发模式') if cur else '开发模式'
        cc_ver = QLabel(f"当前版本  v{cur_ver}")
        cc_ver.setStyleSheet(
            "font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;"
            " font-size: 11pt; font-weight: bold; color: #DDDDDD; border: none;")
        cc_top.addWidget(cc_ver)
        cc_top.addStretch()

        self.refresh_btn = QPushButton("检查更新")
        self.refresh_btn.setFixedSize(104, 32)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #fff; border: none; border-radius: 6px;"
            " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold;"
            " padding: 6px 10px; }"
            " QPushButton:hover { background-color: #388E3C; }"
            " QPushButton:pressed { background-color: #1B5E20; }")
        self.refresh_btn.clicked.connect(self._on_remote_fetch_clicked)
        cc_top.addWidget(self.refresh_btn)
        cc_layout.addLayout(cc_top)

        self.current_info_label = QLabel("")
        self.current_info_label.setWordWrap(True)
        self.current_info_label.setStyleSheet(
            "font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;"
            " font-size: 9pt; color: #AAAAAA; border: none;")
        cc_layout.addWidget(self.current_info_label)
        root.addWidget(current_card)

        # ── Tab 栏（#1A1A1A / 高 44）：软件版本 / 开发动态 + 右侧状态 ──
        self.mode_buttons_widget = QFrame()
        self.mode_buttons_widget.setStyleSheet("background-color: #1A1A1A; border: none;")
        self.mode_buttons_widget.setFixedHeight(44)
        tab_layout = QHBoxLayout(self.mode_buttons_widget)
        tab_layout.setContentsMargins(10, 5, 10, 5)
        tab_layout.setSpacing(4)

        self.btn_mode_exe = QPushButton("软件版本")
        self.btn_mode_exe.setFixedSize(100, 32)
        self.btn_mode_exe.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_exe.setStyleSheet(TAB_ACTIVE_STYLE)
        self.btn_mode_exe.clicked.connect(lambda: self._on_mode_changed("exe"))
        tab_layout.addWidget(self.btn_mode_exe)

        self.btn_mode_git = QPushButton("开发动态")
        self.btn_mode_git.setFixedSize(100, 32)
        self.btn_mode_git.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_git.setStyleSheet(TAB_INACTIVE_STYLE)
        self.btn_mode_git.clicked.connect(lambda: self._on_mode_changed("git"))
        tab_layout.addWidget(self.btn_mode_git)

        tab_layout.addStretch()
        # ── 详情 / 列表 视图模式切换（默认详情）──
        self.view_toggle = self._build_view_toggle()
        tab_layout.addWidget(self.view_toggle)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 8pt; color: #888; border: none;")
        tab_layout.addWidget(self._status_label)
        root.addWidget(self.mode_buttons_widget)

        # ── 列表滚动区（#111113 深底 + 自定义滚动条）──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #111113; border: none; }"
            "QScrollArea QWidget { background-color: #111113; }"
            "QScrollBar:vertical { background-color: #111113; width: 8px; border: none; }"
            "QScrollBar::handle:vertical { background-color: #333; border-radius: 4px; min-height: 30px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #111113;")
        self.versions_layout = QVBoxLayout(self.scroll_content)
        self.versions_layout.setContentsMargins(10, 8, 10, 8)
        self.versions_layout.setSpacing(6)
        self.versions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_content)
        root.addWidget(scroll, 1)

    def _on_mode_changed(self, new_mode):
        if new_mode == self.current_mode:
            return
        self.current_mode = new_mode
        if new_mode == "exe":
            self.btn_mode_exe.setStyleSheet(TAB_ACTIVE_STYLE)
            self.btn_mode_git.setStyleSheet(TAB_INACTIVE_STYLE)
        else:
            self.btn_mode_git.setStyleSheet(TAB_ACTIVE_STYLE)
            self.btn_mode_exe.setStyleSheet(TAB_INACTIVE_STYLE)
        self._load_versions(force=True, auto_remote=False)

    # ───────────────────────── 详情 / 列表 视图模式 ─────────────────────────
    def _build_view_toggle(self):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #111113; border: 1px solid #333333; border-radius: 6px; }")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        self.btn_detail_mode = QPushButton("详情")
        self.btn_list_mode = QPushButton("列表")
        for b in (self.btn_detail_mode, self.btn_list_mode):
            b.setFixedSize(48, 28)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(self._on_view_mode_changed)
            layout.addWidget(b)
        self._apply_view_toggle_style()
        return frame

    def _apply_view_toggle_style(self):
        if self._detail_mode:
            active, inactive = self.btn_detail_mode, self.btn_list_mode
        else:
            active, inactive = self.btn_list_mode, self.btn_detail_mode
        active.setStyleSheet(
            "QPushButton { background-color: #CC0000; color: #FFFFFF; border: none; border-radius: 4px;"
            " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold; }"
            " QPushButton:hover { background-color: #FF0000; }")
        inactive.setStyleSheet(
            "QPushButton { background-color: transparent; color: #AAAAAA; border: none; border-radius: 4px;"
            " font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; font-size: 9pt; font-weight: bold; }"
            " QPushButton:hover { background-color: #222222; color: #DDDDDD; }")

    def _on_view_mode_changed(self):
        sender = self.sender()
        new_detail = (sender is self.btn_detail_mode)
        if new_detail == self._detail_mode:
            return
        self._detail_mode = new_detail
        self._apply_view_toggle_style()
        # 重新渲染当前 Tab（保留已加载数据，仅按新模式分页）
        self._load_versions(force=True, auto_remote=False)

    def _on_remote_fetch_clicked(self):
        self._load_versions(force=True, auto_remote=True)

    # ───────────────────────── 加载入口 ─────────────────────────
    def _load_versions(self, force=False, auto_remote=False):
        if self._versions_loaded and not force:
            return
        self._versions_loaded = True
        self._clear_layout()
        if auto_remote:
            self._start_remote_fetch()
            return
        if self.current_mode == "exe":
            self._render_exe_local()
        else:
            self._render_git_local()

    def _clear_layout(self):
        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_exe_local(self):
        current = self._get_current_exe_version()
        self._current_exe_version = (current or {}).get('version')
        versions = self._get_builtin_versions()
        self._status_label.setText("")
        self._clear_layout()
        self._load_more_btn = None
        if not versions:
            self._empty_label("暂无本地版本列表（versions.json 为空）")
            self._data_cache = []
            return
        self._data_cache = versions
        self._render_is_exe = True
        self._rendered_count = 0
        self._render_batch()
        self.current_info_label.setText(
            f"当前版本: v{self._current_exe_version} ｜ 共 {len(versions)} 个版本（本地静态列表，未联网）")

    def _render_git_local(self):
        commits = self._get_builtin_commits()
        self._status_label.setText("")
        self._clear_layout()
        self._load_more_btn = None
        if not commits:
            self._empty_label("暂无本地提交历史（git_commits.json 为空）")
            self._data_cache = []
            return
        self._data_cache = commits
        self._render_is_exe = False
        self._rendered_count = 0
        self._render_batch()
        self.current_info_label.setText(f"共 {len(commits)} 条提交（本地快照，未联网）")

    def _render_batch(self):
        if not self._data_cache:
            return
        page_size = self._detail_page_size if self._detail_mode else self._list_page_size
        end = min(self._rendered_count + page_size, len(self._data_cache))
        for idx in range(self._rendered_count, end):
            item = self._data_cache[idx]
            if self._render_is_exe:
                is_current = (item.get('version') == self._current_exe_version)
                if self._detail_mode:
                    self._create_exe_card(item, is_current)
                else:
                    self._create_exe_card_compact(item, is_current)
            else:
                if self._detail_mode:
                    self._create_commit_card(item)
                else:
                    self._create_commit_card_compact(item)
        self._rendered_count = end
        if self._load_more_btn is not None:
            self.versions_layout.removeWidget(self._load_more_btn)
            self._load_more_btn.setParent(None)
            self._load_more_btn.deleteLater()
            self._load_more_btn = None
        if end < len(self._data_cache):
            remaining = len(self._data_cache) - end
            btn = QPushButton(f"加载更多（{remaining} 条剩余）")
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(LOAD_MORE_STYLE)
            btn.clicked.connect(self._load_more)
            self._load_more_btn = btn
            self.versions_layout.addWidget(btn)

    def _load_more(self):
        if self._load_more_btn is not None:
            self.versions_layout.removeWidget(self._load_more_btn)
            self._load_more_btn.setParent(None)
            self._load_more_btn.deleteLater()
            self._load_more_btn = None
        self._render_batch()

    def _empty_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{C_TEXT_3}; padding:24px; font-size:12px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versions_layout.addWidget(lbl)

    def _create_exe_card(self, v, is_current):
        ver = v.get('version', '')
        local_path = v.get('path') or v.get('local_path')
        has_local = bool(local_path) and os.path.exists(local_path or '')
        has_url = bool(v.get('download_url'))
        is_new = (not is_current) and has_url and self._is_newer(ver, (self._get_current_exe_version() or {}).get('version'))

        # 状态着色（对齐视频创意站）
        if is_current:
            row_bg, border_color = "#1A1A1A", "#333333"
        elif has_local or has_url:
            row_bg, border_color = "#141414", "#222222"
        else:
            row_bg, border_color = "#111113", "#1A1A1A"

        card = VersionCard(is_current=is_current)
        card.setStyleSheet(
            f"QFrame{{ background-color: {row_bg}; border: 1px solid {border_color}; border-radius: 8px; }}")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # 左：版本号 + 摘要 + 日期
        info = QVBoxLayout()
        info.setSpacing(3)
        ver_color = "#FFFFFF" if is_current else ("#DDDDDD" if (has_url or has_local) else "#666666")
        name = QLabel(f"v{ver}")
        name.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {ver_color}; border: none;")
        info.addWidget(name)
        msg = v.get('message', '') or v.get('name', '')
        if msg:
            ml = QLabel(msg)
            ml.setStyleSheet("color: #999999; font-size: 11px; border: none;")
            ml.setWordWrap(True)
            info.addWidget(ml)
        sub = v.get('date', '')
        if sub:
            sl = QLabel(sub)
            sl.setStyleSheet("color: #666666; font-size: 10px; border: none;")
            info.addWidget(sl)
        layout.addLayout(info, 1)

        # 右：状态标签 + 按钮
        right = QVBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignRight)

        if is_current:
            s_text, s_color = "● 当前版本", "#4CAF50"
        elif is_new:
            s_text, s_color = "🆕 新版本", "#42A5F5"
        elif has_local:
            s_text, s_color = "📦 已下载", "#FF9800"
        elif has_url:
            s_text, s_color = "可下载", "#888888"
        else:
            s_text, s_color = "—", "#555555"
        status = QLabel(s_text)
        status.setStyleSheet(f"color: {s_color}; font-size: 9pt; font-weight: bold; border: none;")
        status.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(status)

        btns = QHBoxLayout()
        btns.setSpacing(6)
        btns.setAlignment(Qt.AlignmentFlag.AlignRight)
        if has_local and not is_current:
            run = QPushButton("运行")
            run.setFixedSize(64, 32)
            run.setCursor(Qt.CursorShape.PointingHandCursor)
            run.setStyleSheet(BTN_RED_STYLE)
            run.clicked.connect(lambda checked, p=local_path: self._launch_exe_version(p))
            btns.addWidget(run)
        if has_url:
            dl = QPushButton("下载")
            dl.setFixedSize(64, 32)
            dl.setCursor(Qt.CursorShape.PointingHandCursor)
            dl.setStyleSheet(BTN_GREEN_STYLE)
            dl.clicked.connect(lambda checked, ver=ver, url=v.get('download_url'):
                               self._download_version(ver, url))
            btns.addWidget(dl)
        if btns.count():
            right.addLayout(btns)
        layout.addLayout(right)
        self.versions_layout.addWidget(card)

    def _create_commit_card(self, c):
        card = VersionCard(is_current=False)
        card.setStyleSheet(
            "QFrame { background-color: #141414; border: 1px solid #222222; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(14, 10, 14, 10)

        head = QHBoxLayout()
        head.setSpacing(10)
        h = QLabel(c.get('short_hash', ''))
        h.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        h.setStyleSheet("color: #DDDDDD; border: none;")
        head.addWidget(h)
        head.addStretch(1)
        d = QLabel(c.get('date', ''))
        d.setStyleSheet("color: #888888; font-size: 11px; border: none;")
        head.addWidget(d)
        layout.addLayout(head)

        m = QLabel(c.get('message', ''))
        m.setStyleSheet("color: #EEEEEE; font-size: 12px; border: none;")
        m.setWordWrap(True)
        layout.addWidget(m)

        a = QLabel(c.get('author', ''))
        a.setStyleSheet("color: #888888; font-size: 11px; border: none;")
        layout.addWidget(a)
        self.versions_layout.addWidget(card)

    # ───────────────────────── 列表模式（紧凑行）─────────────────────────
    def _create_exe_card_compact(self, v, is_current):
        ver = v.get('version', '')
        local_path = v.get('path') or v.get('local_path')
        has_local = bool(local_path) and os.path.exists(local_path or '')
        has_url = bool(v.get('download_url'))
        is_new = (not is_current) and has_url and self._is_newer(ver, self._current_exe_version)

        if is_current:
            row_bg, border_color = "#1A1A1A", "#333333"
        elif has_local or has_url:
            row_bg, border_color = "#141414", "#222222"
        else:
            row_bg, border_color = "#111113", "#1A1A1A"

        card = QFrame()
        card.setStyleSheet(
            f"QFrame{{ background-color: {row_bg}; border: 1px solid {border_color}; border-radius: 6px; }}")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        name = QLabel(f"v{ver}")
        name.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {'#FFFFFF' if is_current else '#DDDDDD'}; border: none;")
        layout.addWidget(name)

        msg = v.get('message', '') or v.get('name', '')
        if msg and len(msg) > 46:
            msg = msg[:46] + '…'
        ml = QLabel(msg)
        ml.setStyleSheet("color: #999999; font-size: 10px; border: none;")
        layout.addWidget(ml, 1)

        right = QHBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignRight)
        if is_current:
            s_text, s_color = "当前", "#4CAF50"
        elif is_new:
            s_text, s_color = "新版本", "#42A5F5"
        elif has_local:
            s_text, s_color = "已下载", "#FF9800"
        elif has_url:
            s_text, s_color = "可下载", "#888888"
        else:
            s_text, s_color = "—", "#555555"
        status = QLabel(s_text)
        status.setStyleSheet(f"color: {s_color}; font-size: 9pt; font-weight: bold; border: none;")
        right.addWidget(status)

        if has_local and not is_current:
            run = QPushButton("运行")
            run.setFixedSize(56, 28)
            run.setCursor(Qt.CursorShape.PointingHandCursor)
            run.setStyleSheet(BTN_RED_STYLE)
            run.clicked.connect(lambda checked, p=local_path: self._launch_exe_version(p))
            right.addWidget(run)
        if has_url:
            dl = QPushButton("下载")
            dl.setFixedSize(56, 28)
            dl.setCursor(Qt.CursorShape.PointingHandCursor)
            dl.setStyleSheet(BTN_GREEN_STYLE)
            dl.clicked.connect(lambda checked, ver=ver, url=v.get('download_url'):
                               self._download_version(ver, url))
            right.addWidget(dl)
        layout.addLayout(right)
        self.versions_layout.addWidget(card)

    def _create_commit_card_compact(self, c):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #141414; border: 1px solid #222222; border-radius: 6px; }")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        h = c.get('short_hash', '') or c.get('hash', '')
        if len(h) > 8:
            h = h[:8]
        hl = QLabel(h)
        hl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        hl.setStyleSheet("color: #DDDDDD; border: none;")
        layout.addWidget(hl)

        m = c.get('message', '')
        first = m.split('\n')[0] if m else ''
        if len(first) > 50:
            first = first[:50] + '…'
        ml = QLabel(first)
        ml.setStyleSheet("color: #CCCCCC; font-size: 11px; border: none;")
        layout.addWidget(ml, 1)

        d = c.get('date', '')
        if d and 'T' in d:
            d = d.split('T')[0]
        elif d and len(d) > 10:
            d = d[:10]
        dl = QLabel(d)
        dl.setStyleSheet("color: #888888; font-size: 10px; border: none;")
        layout.addWidget(dl)

        a = c.get('author', '')
        if a:
            al = QLabel(a)
            al.setStyleSheet("color: #888888; font-size: 10px; border: none;")
            layout.addWidget(al)
        self.versions_layout.addWidget(card)

    # ───────────────────────── 远程获取 ─────────────────────────
    def _start_remote_fetch(self):
        self._clear_layout()
        lbl = QLabel("⏳ 正在远程获取版本列表...")
        lbl.setStyleSheet("color: #AAAAAA; padding:24px; font-size:12px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versions_layout.addWidget(lbl)
        self.current_info_label.setText("正在联网获取（仅本次，不自动）...")
        self._status_label.setText("加载中...")
        self._remote_worker = _RemoteFetchThread(self, self.current_mode, auto_remote=True)
        self._remote_worker.data_ready.connect(self._on_remote_data_ready)
        self._remote_worker.start()

    def _on_remote_data_ready(self, mode, current, versions, local, winner):
        self._clear_layout()
        self._load_more_btn = None
        self._status_label.setText("")
        self._render_is_exe = (mode == "exe")
        if mode == "exe":
            cur = (current or {}).get('version')
            self._current_exe_version = cur
            self._data_cache = versions or []
            self._rendered_count = 0
            if not self._data_cache:
                self._empty_label("远程暂无可用版本")
                self.current_info_label.setText("远程列表为空")
                return
            self._render_batch()
            self.current_info_label.setText(
                f"当前 v{cur} ｜ 远程共 {len(self._data_cache)} 个版本（来源: {winner}）")
        else:
            self._data_cache = versions or []
            self._rendered_count = 0
            if not self._data_cache:
                self._empty_label("远程暂无提交记录")
                self.current_info_label.setText("远程提交为空")
                return
            self._render_batch()
            self.current_info_label.setText(
                f"远程共 {len(self._data_cache)} 条提交（来源: {winner}）")

    def _launch_exe_version(self, path):
        """仅用户点击「运行」时触发；CREATE_NO_WINDOW 隐藏控制台。"""
        if not path or not os.path.exists(path):
            return
        try:
            import subprocess as _sp
            _sp.Popen([path], creationflags=_sp.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"启动版本失败: {e}")

    def _download_version(self, version, download_url):
        """仅用户点击「下载」时触发；走浏览器，无窗口、无子进程。"""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        if download_url:
            url = download_url
        else:
            url = f"https://github.com/yunjii-cn/music/releases"
        QDesktopServices.openUrl(QUrl(url))

class ModelManagerDialog(QWidget):
    """模型管理器 - 作为普通 QWidget 内嵌到主窗口（对齐视频创意站模型页）。

    基类已由 QDialog 改为 QWidget，确保内嵌时绝不会成为独立悬浮窗口 / 弹窗。
    """

    def __init__(self, parent=None, main_window=None, as_widget=False):
        super().__init__(parent)
        self.main_window = main_window
        self.as_widget = as_widget
        self.setObjectName("modelManagerPage")
        self.setWindowTitle("模型管理器")
        if not as_widget:
            self.setMinimumSize(1000, 700)
            self.resize(1200, 800)
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("""
            QWidget#modelManagerPage {
                background-color: #0D0D0D;
            }
        """)

        self.last_verify_time = ""
        self.last_verify_result = None

        self._setup_ui()
        self._update_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        top_bar = QHBoxLayout()

        title_label = QLabel("模型管理器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        self.verify_result_label = QLabel("未验证")
        self.verify_result_label.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        top_bar.addWidget(self.verify_result_label)

        self.verify_time_label = QLabel("")
        self.verify_time_label.setStyleSheet("font-size: 11px; color: #666666; margin-left: 10px;")
        self.verify_time_label.setVisible(False)  # 验证前隐藏时间占位，避免空槽残留
        top_bar.addWidget(self.verify_time_label)

        download_source_label = QLabel("下载源:")
        download_source_label.setStyleSheet("font-size: 12px; color: #AAAAAA; margin-left: 15px;")
        top_bar.addWidget(download_source_label)

        self.download_source_combo = QComboBox()
        self.download_source_combo.setStyleSheet("""
            QComboBox {
                background-color: #252525;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 30px 6px 10px;
                font-size: 12px;
                min-width: 130px;
            }
            QComboBox:hover {
                border-color: #444444;
            }
            QComboBox:focus {
                border-color: #1976D2;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #888888;
                width: 0;
                height: 0;
                right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 4px;
                outline: none;
                selection-background-color: #1976D2;
                selection-color: #FFFFFF;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
            }
        """)

        download_sources = {
            "auto": "自动检测",
            "huggingface": "HuggingFace",
            "modelscope": "ModelScope",
            "huggingface-cn": "HuggingFace (国内镜像)"
        }
        for source_key, source_name in download_sources.items():
            self.download_source_combo.addItem(source_name, source_key)

        if hasattr(self.main_window, 'selected_download_source'):
            for i in range(self.download_source_combo.count()):
                if self.download_source_combo.itemData(i) == self.main_window.selected_download_source:
                    self.download_source_combo.setCurrentIndex(i)
                    break

        self.download_source_combo.currentIndexChanged.connect(self._on_download_source_changed)
        top_bar.addWidget(self.download_source_combo)

        self.btn_verify_all = QPushButton("验证安装")
        self.btn_verify_all.setStyleSheet(DARK_BTN_SUCCESS)
        self.btn_verify_all.clicked.connect(self._verify_all_models)
        top_bar.addWidget(self.btn_verify_all)

        self.btn_open_model_dir = QPushButton("📁 打开模型目录")
        self.btn_open_model_dir.setStyleSheet(DARK_BTN_STYLE)
        self.btn_open_model_dir.setToolTip("在文件管理器中打开模型存储目录 (data/models)")
        self.btn_open_model_dir.clicked.connect(self._open_model_dir)
        top_bar.addWidget(self.btn_open_model_dir)

        if not self.as_widget:
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(self.accept)
            close_btn.setMinimumWidth(80)
            close_btn.setStyleSheet(DARK_BTN_STYLE)
            top_bar.addWidget(close_btn)

        layout.addLayout(top_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        self.models_container = QWidget()
        self.models_layout = QVBoxLayout(self.models_container)
        self.models_layout.setSpacing(10)
        self.models_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area.setWidget(self.models_container)
        layout.addWidget(scroll_area, stretch=1)

    def _on_download_source_changed(self, index):
        if self.main_window:
            source_key = self.download_source_combo.itemData(index)
            self.main_window.selected_download_source = source_key
            if hasattr(self.main_window, '_on_download_source_changed'):
                self.main_window._on_download_source_changed(index)

    def _verify_all_models(self):
        if self.main_window and hasattr(self.main_window, '_verify_all_models'):
            self.main_window._verify_all_models()
            QTimer.singleShot(100, self._update_ui)

    def _update_ui(self):
        if not self.main_window:
            return

        while self.models_layout.count() > 0:
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 清空进度条字典：旧 widget 已被 deleteLater，但字典仍持有引用。
        # 若不清空，重建期间 update_progress 可能命中已销毁的 widget，
        # bar.setValue 抛 RuntimeError，导致进度条固定不动。
        if hasattr(self, '_model_progress_bars'):
            self._model_progress_bars.clear()

        categories = {
            "main": {"name": "📦 主模型", "models": []},
            "lm": {"name": "📝 LM 语言模型", "models": []},
            "dit": {"name": "🎨 DiT 扩散模型", "models": []}
        }

        for model in self.main_window.model_list:
            cat = model.get("category", "dit")
            if cat in categories:
                categories[cat]["models"].append(model)

        for cat_id, cat_info in categories.items():
            if not cat_info["models"]:
                continue

            cat_label = QLabel(cat_info["name"])
            cat_label.setStyleSheet("font-weight: bold; color: #E53935; font-size: 13px; padding: 8px 0;")
            self.models_layout.addWidget(cat_label)

            header_frame = QFrame()
            header_frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border: none;
                    padding: 8px;
                }
            """)
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(8, 4, 8, 4)
            header_layout.setSpacing(10)

            name_header = QLabel("短名称")
            name_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 80px;")
            header_layout.addWidget(name_header)

            id_header = QLabel("模型ID")
            id_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 160px;")
            header_layout.addWidget(id_header)

            status_header = QLabel("状态")
            status_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 80px;")
            header_layout.addWidget(status_header)

            size_header = QLabel("大小")
            size_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 55px;")
            header_layout.addWidget(size_header)

            desc_header = QLabel("描述")
            desc_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")
            header_layout.addWidget(desc_header, 1)

            action_header = QLabel("操作")
            action_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 100px;")
            header_layout.addWidget(action_header)

            self.models_layout.addWidget(header_frame)

            for idx, model in enumerate(cat_info["models"]):
                model_item = QFrame()
                model_item.setStyleSheet("""
                    QFrame {
                        background-color: #1E1E1E;
                        border: none;
                        padding: 8px;
                    }
                    QFrame:hover {
                        background-color: #252525;
                    }
                """)

                model_item_layout = QVBoxLayout(model_item)
                model_item_layout.setContentsMargins(8, 6, 8, 6)
                model_item_layout.setSpacing(4)

                row_layout = QHBoxLayout()
                row_layout.setSpacing(10)

                short_name = model.get("short_name", model["display_name"])
                name_label = QLabel(f"{short_name}")
                name_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold; min-width: 80px;")
                row_layout.addWidget(name_label)

                model_id_label = QLabel(model["display_name"])
                model_id_label.setStyleSheet("color: #888888; font-size: 10px; min-width: 160px;")
                row_layout.addWidget(model_id_label)

                integrity_status = model.get("integrity_status", "missing")
                integrity_details = model.get("integrity_details")

                if model["exists"] and integrity_status == "complete":
                    status_text = "● 已安装"
                    status_color = "#4CAF50"
                elif integrity_status == "incomplete":
                    status_text = "● 不完整"
                    status_color = "#FF9800"
                else:
                    status_text = "● 未安装"
                    status_color = "#F44336"

                status_label = QLabel(status_text)
                status_label.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: bold; min-width: 80px;")
                row_layout.addWidget(status_label)

                # 下载总大小列（从 main_window 的 _FS_MODEL_DOWNLOAD_SIZE 查询）
                # 让用户在下载前就知道模型有多大，也作为进度条百分比的参照。
                # 主模型组件现已独立下载，显示其自身大小（而非整包总和）。
                size_text = ""
                try:
                    if self.main_window:
                        from main import _FS_MODEL_DOWNLOAD_SIZE
                        _model_name = model["name"]
                        _total = _FS_MODEL_DOWNLOAD_SIZE.get(_model_name, 0)
                        if _total > 0:
                            if _total >= 1e9:
                                size_text = f"{_total/1e9:.1f}GB"
                            elif _total >= 1e6:
                                size_text = f"{_total/1e6:.0f}MB"
                except Exception:
                    pass
                size_label = QLabel(size_text or "-")
                size_label.setStyleSheet("color: #BBBBBB; font-size: 11px; min-width: 55px;")
                size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row_layout.addWidget(size_label)

                desc_label = QLabel(model["description"])
                desc_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
                desc_label.setWordWrap(True)
                row_layout.addWidget(desc_label, 1)

                btn_layout = QHBoxLayout()
                btn_layout.setSpacing(4)

                # 下载中判定需同时匹配模型名与下载目标 dl_target。
                # 主模型组件现已独立下载，dl_target 即组件自身名（不再路由到 "main"），
                # 进度条/暂停/取消均独立显示，不再与主包同步。
                _dl_target = model["name"]
                # 批量下载：本模型正在下载判定（下载中的卡片只显示暂停/取消+进度条，
                # 不显示下载类按钮；而其它模型按钮保持可用，支持同时发起多个下载）。
                is_downloading = _dl_target in getattr(self.main_window, 'downloading_models', set())

                if is_downloading:
                    # 下载中：新增「暂停」+「取消」两个按钮（不是替换）。
                    # 下载/重新下载按钮仍保留但会被 _set_model_buttons_enabled(False) 禁用变灰。
                    # 暂停：橙色，停止下载但保留已下载的文件
                    # 取消：红色，停止下载并清理（当前两者行为相同，语义区分预留）
                    pause_btn = QPushButton("暂停")
                    pause_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #FF8F00;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #FF6F00;
                            filter: brightness(1.15);
                        }
                        QPushButton:disabled {
                            background-color: #4A3A2A;
                            color: #888888;
                        }
                    """)
                    pause_btn.clicked.connect(lambda checked=False, m=_dl_target: self.main_window._pause_download(m))
                    btn_layout.addWidget(pause_btn)

                    cancel_btn = QPushButton("取消")
                    cancel_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #C62828;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #D32F32;
                            filter: brightness(1.15);
                        }
                        QPushButton:disabled {
                            background-color: #4A2A2A;
                            color: #888888;
                        }
                    """)
                    cancel_btn.clicked.connect(lambda checked=False, m=_dl_target: self.main_window._pause_download(m))
                    btn_layout.addWidget(cancel_btn)
                # 主模型组件现已支持独立下载，dl_target 直接用模型自身名（不再路由到 "main"），
                # 进度条/暂停/取消/下载均独立显示。
                is_main_component = model["name"] in ("acestep-v15-turbo", "acestep-5Hz-lm-1.7B")
                dl_target = model["name"]

                if integrity_status == "missing":
                    # 未安装（含完全未下载的模型）：显示下载按钮。
                    # 正在下载本模型时不显示下载按钮（已有暂停/取消+进度条）；
                    # 其它模型按钮保持可用（支持批量下载，不再整体变灰）。
                    if not is_downloading:
                        download_btn = QPushButton("下载")
                        download_btn.setStyleSheet(DARK_BTN_PRIMARY)
                        download_btn.clicked.connect(lambda checked, t=dl_target: self._download_model(t))
                        btn_layout.addWidget(download_btn)
                elif integrity_status == "incomplete":
                    # 不完整/损坏：只提供「删除」。删除后状态变为 missing，再点「下载」即可重装。
                    # 不再提供「重新下载」——它与「删除+下载」等价（子模型），或对主模型仅做
                    # 增量修复（会残留过不了弱校验的损坏文件，见 model_downloader 的 force 逻辑），
                    # 属于冗余且有清理不干净隐患的设计，已移除。
                    # 正在下载本模型时不显示删除（已有暂停/取消+进度条）。
                    if not is_downloading:
                        delete_btn = QPushButton("删除")
                        delete_btn.setStyleSheet(DARK_BTN_DANGER)
                        delete_btn.setToolTip("删除不完整/损坏的模型文件，删除后可重新下载")
                        delete_btn.clicked.connect(lambda checked, m=model["name"]: self._delete_model(m))
                        btn_layout.addWidget(delete_btn)
                elif model["exists"]:
                    # 已安装：只提供「删除」。主模型组件也允许删除（内部路由到整包主模型删除），
                    # 不再禁用——之前禁用是逼用户用「重新下载」修复坏主模型，现已去掉该按钮，
                    # 故放开删除作为唯一修复出口（删后重新下载即可）。
                    # 正在下载本模型时不显示删除（已有暂停/取消+进度条）。
                    if not is_downloading:
                        delete_btn = QPushButton("删除")
                        delete_btn.setStyleSheet(DARK_BTN_DANGER)
                        _del_tip = "删除模型文件"
                        if model["name"] == "main":
                            _del_tip += "（将删除整个主模型）"
                        elif is_main_component:
                            _del_tip += "（仅删除该组件）"
                        delete_btn.setToolTip(_del_tip)
                        delete_btn.clicked.connect(lambda checked, m=model["name"]: self._delete_model(m))
                        btn_layout.addWidget(delete_btn)

                row_layout.addLayout(btn_layout)
                model_item_layout.addLayout(row_layout)

                if integrity_status == "incomplete" and integrity_details:
                    missing_files = integrity_details.get("files_missing", [])
                    total_size_mb = integrity_details.get("total_size_mb", 0)
                    expected_size_mb = integrity_details.get("expected_size_mb", 0)
                    size_ok = integrity_details.get("size_ok", False)
                    
                    warn_parts = []
                    if missing_files:
                        warn_parts.append(f"缺少文件: {', '.join(missing_files)}")
                    if not size_ok and expected_size_mb > 0:
                        warn_parts.append(f"大小不足: {total_size_mb}MB / 预期 {expected_size_mb}MB")
                    
                    if warn_parts:
                        warn_text = "⚠ " + "，".join(warn_parts) + "，建议删除后重新下载"
                        warn_label = QLabel(warn_text)
                        warn_label.setStyleSheet("font-size: 10px; color: #FF9800; font-weight: bold;")
                        warn_label.setWordWrap(True)
                        model_item_layout.addWidget(warn_label)

                if is_downloading:
                    progress_row = QHBoxLayout()
                    progress_bar = QProgressBar()
                    progress_bar.setMinimum(0)
                    progress_bar.setMaximum(100)
                    # 重建进度条时恢复当前下载线程的进度值，避免 _update_ui 重建后
                    # 进度条被重置为 0%（点击下载后 100ms 会触发 _update_ui 重建，
                    # 此时下载线程可能已推进到 15%+，重置为 0 会导致进度条回退）。
                    _cur_progress = 0
                    if self.main_window and hasattr(self.main_window, 'model_download_threads'):
                        _dt = self.main_window.model_download_threads.get(_dl_target)
                        if _dt is not None:
                            _cur_progress = getattr(_dt, 'current_progress', 0)
                    progress_bar.setValue(_cur_progress)
                    progress_bar.setFixedHeight(16)
                    progress_bar.setStyleSheet("""
                        QProgressBar {
                            background-color: #1A1A1A;
                            border: 1px solid #333333;
                            border-radius: 3px;
                            text-align: center;
                            color: #FFFFFF;
                            font-size: 10px;
                        }
                        QProgressBar::chunk {
                            background-color: #1976D2;
                            border-radius: 2px;
                        }
                    """)
                    progress_row.addWidget(progress_bar, 1)
                    progress_label = QLabel("下载中..." if _cur_progress > 0 else "准备下载...")
                    progress_label.setStyleSheet("color: #AAAAAA; font-size: 10px; min-width: 80px;")
                    progress_row.addWidget(progress_label)
                    model_item_layout.addLayout(progress_row)

                    if not hasattr(self, '_model_progress_bars'):
                        self._model_progress_bars = {}
                    # 进度条以下载目标 _dl_target 为键，与 main._download_model 中
                    # current_operation_model 的取值保持一致（主组件为 "main"）。
                    self._model_progress_bars[_dl_target] = (progress_bar, progress_label)

                self.models_layout.addWidget(model_item)

            if cat_id != list(categories.keys())[-1]:
                spacer = QWidget()
                spacer.setMinimumHeight(10)
                self.models_layout.addWidget(spacer)

    def _download_model(self, model_name, force: bool = False):
        if self.main_window and hasattr(self.main_window, '_download_model'):
            self.main_window._download_model(model_name, force=force)
            QTimer.singleShot(100, self._update_ui)

    def _delete_model(self, model_name):
        if self.main_window and hasattr(self.main_window, '_delete_model'):
            self.main_window._delete_model(model_name)
            QTimer.singleShot(100, self._update_ui)

    def _open_model_dir(self):
        """在系统文件管理器中打开模型存储目录（data/models）。

        checkpoints 目录解析规则与 main._fs_get_checkpoints_dir 保持一致：
        project_root = dirname(base_dir)，checkpoints = project_root/data/models。
        """
        try:
            base_dir = getattr(self.main_window, 'base_dir', None)
            if not base_dir:
                return
            ckpt = os.path.join(os.path.dirname(os.path.abspath(base_dir)), "data", "models")
            os.makedirs(ckpt, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(ckpt))
        except Exception as e:
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "打开失败", f"无法打开模型目录:\n{str(e)}")
            except Exception:
                pass

    def _dl_key(self, name: str) -> str:
        """将模型名解析为下载目标键，与 _update_ui 中进度条字典的键保持一致。
        主模型组件现已独立下载，键即模型自身名（不再路由到 'main'）。"""
        return name

    def show_progress(self, model_name: str, text: str = ""):
        """显示指定模型的下载进度条。

        点击下载后 _update_ui 会重建模型列表、重新创建该卡片的进度条，
        此时 _model_progress_bars 已含对应 key（以下载目标 _dl_key 为键，
        主模型组件统一为 "main"），直接定位设置即可。
        """
        key = self._dl_key(model_name)
        if key and hasattr(self, '_model_progress_bars') and key in self._model_progress_bars:
            bar, label = self._model_progress_bars[key]
            bar.setValue(0)
            label.setText(text or "准备下载...")

    def update_progress(self, model_name: str, value: int, desc: str = ""):
        """更新指定模型的下载进度条（批量下载：按 model_name 路由到对应卡片）。"""
        key = self._dl_key(model_name)
        target = None
        if key and hasattr(self, '_model_progress_bars') and key in self._model_progress_bars:
            target = self._model_progress_bars[key]
        elif model_name and hasattr(self, '_model_progress_bars') and model_name in self._model_progress_bars:
            target = self._model_progress_bars[model_name]
        if target is not None:
            bar, label = target
            bar.setValue(value)
            if desc:
                label.setText(desc)

    def hide_progress(self, model_name=None):
        """隐藏进度条。指定 model_name 时只清除该模型条目（批量下载不误伤其它）；
        未指定则清空全部（兜底）。"""
        if not hasattr(self, '_model_progress_bars'):
            return
        if model_name is not None:
            self._model_progress_bars.pop(self._dl_key(model_name), None)
        else:
            self._model_progress_bars.clear()


VersionManagerDialog = HybridVersionManagerDialog
