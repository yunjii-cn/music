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
    QComboBox, QTabWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QDesktopServices


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


class _ExeFetchWorker(QThread):
    data_ready = pyqtSignal(object, object, dict, str)

    def __init__(self, dialog, auto_remote=False):
        super().__init__()
        self.dialog = dialog
        self._cancelled = False
        self._result_versions = None
        self._result_winner = None
        # 是否允许后台自动拉取远程版本列表。
        # 打开页面时为 False（仅用内置静态文件秒开，零网络零弹窗）；
        # 用户点「刷新/远程获取」时传 True。
        self.auto_remote = auto_remote

    def cancel(self):
        self._cancelled = True

    def _fetch_url(self, url, is_api=False, timeout=10):
        """Single URL fetch, returns (data_dict, error)"""
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
            else:
                return json.loads(raw), None
        except Exception as e:
            return None, str(e)

    def run(self):
        try:
            current = self.dialog._get_current_exe_version()
            if self._cancelled:
                return

            # 秒开：先用 exe 内置的 versions.json 立即渲染历史列表，不依赖任何网络。
            # 内置列表优先秒开；winner 默认用 "github_mirror"（国内走 ghproxy 镜像），
            # 下载地址按 GitHub Releases 模板确定性生成，导入 GitHub 后下载即自动可用。
            builtin = self.dialog._get_builtin_versions()
            if builtin and not self._cancelled:
                local = self.dialog._get_local_exe_versions()
                self.data_ready.emit(current, builtin, local, "github_mirror")

            if self._cancelled:
                return

            # 后台再尝试远程拉取（多源竞速），拿到后再次 emit 覆盖（补充可能新增的版本）
            # 仅当用户显式点「刷新/远程获取」时才拉取（auto_remote=True），
            # 避免打开页面即联网/弹窗。
            if not self.auto_remote:
                return
            sources = UPDATE_SOURCES
            result = None
            winner = None
            results_lock = threading.Lock()
            done_event = threading.Event()

            def try_source(key):
                nonlocal result, winner
                if done_event.is_set() or self._cancelled:
                    return
                source = sources[key]
                data, error = self._fetch_url(source["version_url"], source.get("is_api", False))
                if data is not None and not done_event.is_set() and not self._cancelled:
                    with results_lock:
                        if not done_event.is_set():
                            result = data
                            winner = key
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
            if not remote:
                # 所有远程源都不可达：保持内置列表（上面已 emit），不再二次兜底
                return

            if self._cancelled:
                return

            local = self.dialog._get_local_exe_versions()
            if self._cancelled:
                return

            self.data_ready.emit(current, remote, local, winner or "github_mirror")
        except Exception as e:
            print(f"EXE版本数据获取失败: {e}")
            if not self._cancelled:
                # 出错也尽量用内置兜底显示
                builtin = self.dialog._get_builtin_versions()
                if builtin:
                    self.data_ready.emit(None, builtin, {}, "gitee")
                else:
                    self.data_ready.emit(None, [], {}, "")


# ── 远程提交历史源（仅用户手动点「远程获取」时拉取）──
GITEE_COMMITS_URL = f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/commits?per_page=60&sha=main{_GITEE_TOKEN_PARAM}"
GITHUB_COMMITS_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=60"
GITHUB_COMMITS_MIRROR = f"https://ghproxy.net/https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=60"


class _GitCommitsFetchWorker(QThread):
    """开发动态（git 提交历史）获取 worker。

    - 秒开：emit exe 内置的 git_commits.json（离线、零网络、零弹窗）；
    - 仅当用户显式点「远程获取」(auto_remote=True) 时才去仓库 commits API 拉最新提交。
    全程 urlopen，零 subprocess、零弹窗。
    """
    data_ready = pyqtSignal(object, list, str)

    def __init__(self, dialog, auto_remote=False):
        super().__init__()
        self.dialog = dialog
        self._cancelled = False
        self.auto_remote = auto_remote

    def cancel(self):
        self._cancelled = True

    def _fetch_one(self, url):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urlopen(req, timeout=12)
            raw = json.loads(resp.read().decode("utf-8"))
            if not isinstance(raw, list):
                return []
            return [self.dialog._normalize_commit(c) for c in raw if c]
        except Exception as e:
            print(f"远程提交获取失败 ({url}): {e}")
            return None

    def run(self):
        try:
            current = self.dialog._get_current_exe_version()
            if self._cancelled:
                return
            # 秒开：内置 git_commits.json
            builtin = self.dialog._get_builtin_commits()
            if builtin and not self._cancelled:
                self.data_ready.emit(current, builtin, "builtin")
            # 未要求远程拉取则到此为止（打开页面即此分支，零网络零弹窗）
            if not self.auto_remote or self._cancelled:
                return
            # 远程多源拉取最新提交（仅手动触发）
            for url in (GITHUB_COMMITS_MIRROR, GITHUB_COMMITS_URL, GITEE_COMMITS_URL):
                if self._cancelled:
                    return
                commits = self._fetch_one(url)
                if commits:  # 非空即采用（None=出错，重试下一源）
                    self.data_ready.emit(current, commits, url)
                    return
            # 全部失败：保持内置快照（上面已 emit）
        except Exception as e:
            print(f"Git提交获取失败: {e}")
            if not self._cancelled:
                builtin = self.dialog._get_builtin_commits()
                if builtin:
                    self.data_ready.emit(None, builtin, "builtin")




class HybridVersionManagerDialog(QDialog):
    """混合模式版本管理器 - 支持Git和EXE两种模式"""

    def __init__(self, parent=None, project_root=None, as_widget=False):
        super().__init__(parent)
        self.project_root = project_root
        self.as_widget = as_widget
        self.setWindowTitle("版本管理器")
        self.setMinimumSize(950, 650)
        self.resize(1050, 750)

        if not as_widget:
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0D0D;
            }
        """)

        self.current_mode = "exe"
        self._versions_loaded = False
        self._git_repo_checked = False
        self.has_git_repo = False
        self._remote_versions_cache = None
        self._detail_widgets = []
        self._all_expanded = True
        self._exe_worker = None
        self._git_worker = None

        # 多源竞速 / 下载相关
        self._ver_race_winner = ""
        self._ver_stable_data = []
        self._ver_current_version = ""
        self._ver_source_combo = None
        self._ver_active_source = "auto"

        self._setup_ui()
        self._load_local_version_history()

        QTimer.singleShot(800, self._delayed_init)

    def _delayed_init(self):
        if self.as_widget and not self.isVisible():
            QTimer.singleShot(500, self._delayed_init)
            return
        if self._git_repo_checked:
            return
        self._git_repo_checked = True
        # has_git_repo 仅用于「开发动态」里的 git checkout 切换能力判断，
        # 不再据此自动切到 git 模式（避免打开页面即触发远程拉取/弹窗）。
        self.has_git_repo = self._check_git_repo()
        if hasattr(self, 'mode_buttons_widget'):
            self.mode_buttons_widget.setVisible(True)

    def _load_local_version_history(self):
        self.version_history = {}
        possible_paths = [
            Path(self.project_root) / 'app' / 'version_history.json',
            Path(self.project_root).parent / 'dist' / 'version_history.json',
        ]
        if hasattr(sys, '_MEIPASS'):
            possible_paths.append(Path(sys._MEIPASS) / 'version_history.json')
        for history_path in possible_paths:
            if history_path.exists():
                try:
                    with open(history_path, 'r', encoding='utf-8') as f:
                        self.version_history = json.load(f)
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

    def _check_git_repo(self):
        try:
            current_dir = Path(self.project_root)
            while current_dir.parent != current_dir:
                git_dir = current_dir / ".git"
                if git_dir.exists() and git_dir.is_dir():
                    return True
                current_dir = current_dir.parent
            return False
        except Exception:
            return False

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        top_bar = QHBoxLayout()

        title_label = QLabel("版本管理器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        top_bar.addWidget(title_label)

        self.mode_btn_group = QHBoxLayout()
        self.mode_btn_group.setSpacing(0)
        self.mode_btn_group.setContentsMargins(0, 0, 0, 0)

        self.btn_mode_exe = QPushButton("软件版本")
        self.btn_mode_exe.setCheckable(True)
        self.btn_mode_exe.setChecked(True)
        self.btn_mode_exe.setFixedHeight(32)
        self.btn_mode_exe.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #FFFFFF;
                border: 1px solid #1976D2;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:!checked {
                background-color: #252525;
                color: #AAAAAA;
                border: 1px solid #333333;
                font-weight: normal;
            }
            QPushButton:!checked:hover {
                background-color: #333333;
                color: #FFFFFF;
            }
        """)
        self.btn_mode_exe.clicked.connect(lambda: self._on_mode_changed("exe"))
        self.mode_btn_group.addWidget(self.btn_mode_exe)

        self.btn_mode_git = QPushButton("开发动态")
        self.btn_mode_git.setCheckable(True)
        self.btn_mode_git.setChecked(False)
        self.btn_mode_git.setFixedHeight(32)
        self.btn_mode_git.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #FFFFFF;
                border: 1px solid #1976D2;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:!checked {
                background-color: #252525;
                color: #AAAAAA;
                border: 1px solid #333333;
                font-weight: normal;
            }
            QPushButton:!checked:hover {
                background-color: #333333;
                color: #FFFFFF;
            }
        """)
        self.btn_mode_git.clicked.connect(lambda: self._on_mode_changed("git"))
        self.mode_btn_group.addWidget(self.btn_mode_git)

        self.mode_buttons_widget = QWidget()
        self.mode_buttons_widget.setLayout(self.mode_btn_group)
        self.mode_buttons_widget.setVisible(False)
        top_bar.addWidget(self.mode_buttons_widget)

        top_bar.addStretch()

        src_label = QLabel("下载源:")
        src_label.setStyleSheet("font-size: 11px; color: #AAAAAA; margin-left: 8px;")
        top_bar.addWidget(src_label)

        self._ver_source_combo = QComboBox()
        self._ver_source_combo.setStyleSheet("""
            QComboBox {
                background-color: #252525; color: #FFFFFF;
                border: 1px solid #333333; border-radius: 4px;
                padding: 4px 24px 4px 8px; font-size: 11px;
                min-width: 110px;
            }
            QComboBox:hover { border-color: #444444; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow {
                image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #888888; width: 0; height: 0; right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525; border: 1px solid #333333;
                border-radius: 4px; outline: none;
                selection-background-color: #1976D2; selection-color: #FFFFFF;
            }
            QComboBox QAbstractItemView::item { padding: 4px 8px; }
        """)
        self._ver_source_combo.addItem("⚡ 自动竞速", "auto")
        for key, src in UPDATE_SOURCES.items():
            self._ver_source_combo.addItem(src["name"], key)
        self._ver_source_combo.currentIndexChanged.connect(self._on_ver_source_changed)
        top_bar.addWidget(self._ver_source_combo)

        refresh_btn = QPushButton("🌐 远程获取")
        refresh_btn.clicked.connect(lambda: self._load_versions(force=True, auto_remote=True))
        refresh_btn.setMinimumWidth(90)
        refresh_btn.setStyleSheet(DARK_BTN_STYLE)
        refresh_btn.setToolTip("手动从仓库拉取最新数据：软件版本列表 / 开发动态提交历史（git），不弹窗")
        top_bar.addWidget(refresh_btn)

        if not self.as_widget:
            close_btn = QPushButton("✕ 关闭")
            close_btn.clicked.connect(self.accept)
            close_btn.setMinimumWidth(70)
            close_btn.setStyleSheet(DARK_BTN_DANGER)
            top_bar.addWidget(close_btn)

        layout.addLayout(top_bar)

        current_frame = QFrame()
        current_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        current_layout = QVBoxLayout(current_frame)
        current_layout.setSpacing(8)

        current_header = QHBoxLayout()
        current_label = QLabel("当前版本:")
        current_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        current_label.setStyleSheet("color: #888888;")
        current_header.addWidget(current_label)

        self.current_mode_label = QLabel("")
        self.current_mode_label.setStyleSheet("""
            QLabel {
                color: #1565C0;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        current_header.addWidget(self.current_mode_label)
        current_header.addStretch()
        current_layout.addLayout(current_header)

        self.current_info_label = QLabel("")
        self.current_info_label.setStyleSheet("color: #F0F0F0; font-size: 13px;")
        self.current_info_label.setWordWrap(True)
        current_layout.addWidget(self.current_info_label)

        layout.addWidget(current_frame)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #333333;")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)

        list_header = QHBoxLayout()
        list_label = QLabel("版本历史")
        list_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        list_label.setStyleSheet("color: #888888;")
        list_header.addWidget(list_label)
        list_header.addStretch()

        self.toggle_all_btn = QPushButton("全部收起")
        self.toggle_all_btn.setFixedWidth(90)
        self.toggle_all_btn.setStyleSheet(DARK_BTN_STYLE)
        self.toggle_all_btn.clicked.connect(self._toggle_all_details)
        list_header.addWidget(self.toggle_all_btn)
        layout.addLayout(list_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        self.versions_container = QWidget()
        self.versions_container.setStyleSheet("background-color: transparent; border: none;")
        self.versions_layout = QVBoxLayout(self.versions_container)
        self.versions_layout.setSpacing(8)
        self.versions_layout.setContentsMargins(4, 4, 4, 4)

        scroll_area.setWidget(self.versions_container)
        layout.addWidget(scroll_area, stretch=1)

    def _on_mode_changed(self, new_mode):
        try:
            if new_mode == self.current_mode:
                return
            if self._exe_worker and self._exe_worker.isRunning():
                self._exe_worker.cancel()
                self._exe_worker.wait(2000)
                self._exe_worker = None
            if self._git_worker and self._git_worker.isRunning():
                self._git_worker.cancel()
                self._git_worker.wait(2000)
                self._git_worker = None
            self.current_mode = new_mode
            if new_mode == "exe":
                self.btn_mode_exe.setChecked(True)
                self.btn_mode_git.setChecked(False)
            else:
                self.btn_mode_exe.setChecked(False)
                self.btn_mode_git.setChecked(True)
            self._load_versions(force=True)
        except Exception as e:
            print(f"模式切换失败：{e}")

    def _toggle_all_details(self):
        self._all_expanded = not self._all_expanded
        for dw in self._detail_widgets:
            dw.setVisible(self._all_expanded)
        self.toggle_all_btn.setText("全部收起" if self._all_expanded else "全部展开")

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
        """从 exe 内置的 versions.json 读取版本历史（离线兜底）。

        构建时通过 --add-data 把 dev/app/versions.json 打进 exe，
        运行时位于 sys._MEIPASS/versions.json（或 exe 同目录）。
        当所有远程源都不可达时，用它显示本地已知的完整历史版本列表，
        避免离线时版本页一片空白。
        """
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
        """从 exe 内置的 git_commits.json 读取提交历史（离线兜底）。

        构建时通过 --add-data 把 dev/app/git_commits.json 打进 exe，
        运行时位于 sys._MEIPASS/git_commits.json（或 exe 同目录）。
        """
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
        """把 Gitee/GitHub commits API 的响应归一化为统一结构。"""
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
        local_versions = {}
        ver_dirs = []
        ver_dir = Path(self.project_root) / "ver"
        if ver_dir.exists():
            ver_dirs.append(ver_dir)
        dev_dir = Path(self.project_root)
        alt_ver = dev_dir / "ver"
        if alt_ver.exists() and alt_ver not in ver_dirs:
            ver_dirs.append(alt_ver)
        if hasattr(sys, '_MEIPASS'):
            meipass_ver = Path(sys._MEIPASS) / "ver"
            if meipass_ver.exists() and meipass_ver not in ver_dirs:
                ver_dirs.append(meipass_ver)
        exe_dir_ver = Path(os.path.dirname(sys.executable)) / "ver"
        if exe_dir_ver.exists() and exe_dir_ver not in ver_dirs:
            ver_dirs.append(exe_dir_ver)

        for vd in ver_dirs:
            for exe_file in vd.glob("*.exe"):
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_file.name)
                if match:
                    version = match.group(1)
                    if version not in local_versions:
                        file_size = exe_file.stat().st_size / (1024 * 1024)
                        mtime = datetime.fromtimestamp(exe_file.stat().st_mtime)
                        local_versions[version] = {
                            'path': str(exe_file),
                            'size': f"{file_size:.2f} MB",
                            'date': mtime.strftime("%Y-%m-%d %H:%M"),
                            'name': exe_file.name,
                        }

        if Path(self.project_root).exists():
            for exe_file in Path(self.project_root).glob("*.exe"):
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_file.name)
                if match:
                    version = match.group(1)
                    if version not in local_versions:
                        file_size = exe_file.stat().st_size / (1024 * 1024)
                        mtime = datetime.fromtimestamp(exe_file.stat().st_mtime)
                        local_versions[version] = {
                            'path': str(exe_file),
                            'size': f"{file_size:.2f} MB",
                            'date': mtime.strftime("%Y-%m-%d %H:%M"),
                            'name': exe_file.name,
                        }

        return local_versions


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

    def _load_versions(self, force=False, auto_remote=False):
        if self._versions_loaded and not force:
            return
        if self._exe_worker and self._exe_worker.isRunning():
            self._exe_worker.cancel()
            self._exe_worker.wait(2000)
            self._exe_worker = None
        if self._git_worker and self._git_worker.isRunning():
            self._git_worker.cancel()
            self._git_worker.wait(2000)
            self._git_worker = None
        self._versions_loaded = True
        self._remote_versions_cache = None
        self._detail_widgets = []
        self._all_expanded = True
        self.toggle_all_btn.setText("全部收起")

        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.current_mode == "exe":
            self._load_exe_versions(auto_remote=auto_remote)
        else:
            self._load_git_versions(auto_remote=auto_remote)

    def _load_exe_versions(self, auto_remote=False):
        self.current_mode_label.setText("软件版本")
        self.current_info_label.setText("⏳ 正在加载版本信息...")

        loading_label = QLabel("⏳ 正在读取内置版本列表...")
        loading_label.setStyleSheet("color: #888888; padding: 20px;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versions_layout.addWidget(loading_label)

        # auto_remote=False：仅用 exe 内置静态 versions.json 秒开，不联网、不弹窗。
        # 用户点「🌐 远程获取」时传 True 才会去仓库拉最新列表。
        self._exe_worker = _ExeFetchWorker(self, auto_remote=auto_remote)
        self._exe_worker.data_ready.connect(self._on_exe_data_ready)
        self._exe_worker.start()

    def _on_ver_source_changed(self, index):
        key = self._ver_source_combo.itemData(index)
        self._ver_active_source = key

    def _on_exe_data_ready(self, current, remote_versions, local_versions, winner_source):
        if self.current_mode != "exe":
            return

        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if current:
            self.current_info_label.setText(
                f"版本: v{current['version']} | 文件: {current['name']} | 大小: {current['size']}"
            )
        else:
            self.current_info_label.setText("⚠️ 无法获取当前版本信息")

        current_version = current['version'] if current else None
        self._ver_current_version = current_version or ""
        self._ver_race_winner = winner_source or "github_mirror"

        if not remote_versions and not local_versions:
            no_version_label = QLabel("未找到稳定版信息\n\n请检查网络连接")
            no_version_label.setStyleSheet("color: #666666; padding: 20px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return

        # Determine download URL template from winning source
        source = UPDATE_SOURCES.get(winner_source, {})
        download_tpl = source.get("download_url_tpl", "")

        merged = {}
        for rv in remote_versions:
            ver = rv.get('version', '')
            dl_url = rv.get('download_url', '')
            if not dl_url and download_tpl:
                fn = self._asset_filename_for_source(winner_source, ver, rv.get('name', ''))
                # 文件名含中文，拼进 URL 前必须做 percent-encoding，否则请求会失败
                dl_url = download_tpl.format(filename=quote(fn), version=ver)
            merged[ver] = {
                'version': ver,
                'name': rv.get('name', f"v{ver}"),
                'date': rv.get('date', ''),
                'message': rv.get('message', ''),
                'changes': rv.get('changes', []),
                'available': ver in local_versions,
                'local_path': local_versions.get(ver, {}).get('path'),
                'local_size': local_versions.get(ver, {}).get('size'),
                'local_date': local_versions.get(ver, {}).get('date'),
                'download_url': dl_url,
            }

        for ver, lv in local_versions.items():
            if ver not in merged:
                changes = self._get_version_changes(lv['name'])
                merged[ver] = {
                    'version': ver,
                    'name': lv['name'],
                    'date': lv.get('date', ''),
                    'message': '',
                    'changes': changes,
                    'available': True,
                    'local_path': lv.get('path'),
                    'local_size': lv.get('size'),
                    'local_date': lv.get('date'),
                    'download_url': '',
                }

        all_versions = list(merged.values())
        all_versions.sort(key=lambda x: x['version'], reverse=True)

        for version in all_versions:
            is_current = version['version'] == current_version
            self._create_exe_version_item(version, is_current)

        # Async fetch release assets for real download URLs
        if winner_source:
            self._fetch_release_assets(winner_source, all_versions)

    def _on_git_data_ready(self, current, commits, source):
        if self.current_mode != "git":
            return

        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ver_str = current.get('version') if isinstance(current, dict) else "未知"
        src_name = "内置快照" if source == "builtin" else "远程最新"
        if not commits:
            no_label = QLabel("暂无提交历史")
            no_label.setStyleSheet("color: #666666; padding: 20px;")
            no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_label)
            self.current_info_label.setText(f"版本: v{ver_str}")
            return

        self.current_info_label.setText(
            f"版本: v{ver_str} | 共 {len(commits)} 条提交（来源: {src_name}）"
        )

        for c in commits:
            self._create_git_commit_item(c)

    def _create_git_commit_item(self, commit):
        card = QFrame()
        card.setObjectName("commitCard")
        card.setStyleSheet("""
            #commitCard {
                background-color: #111111;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }
            #commitCard:hover {
                background-color: #161616;
                border-color: #222222;
            }
            QLabel { border: none; background: transparent; }
            QWidget { border: none; background: transparent; }
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 10, 16, 10)

        header = QHBoxLayout()
        header.setSpacing(10)

        hash_label = QLabel(commit.get("short_hash", "") or "")
        hash_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        hash_label.setStyleSheet("color: #4FC3F7; border: none; background: transparent;")
        header.addWidget(hash_label)

        author_label = QLabel(commit.get("author", "") or "")
        author_label.setStyleSheet("color: #AAAAAA; font-size: 11px; border: none; background: transparent;")
        header.addWidget(author_label)

        header.addStretch()

        date_label = QLabel(commit.get("date", "") or "")
        date_label.setStyleSheet("color: #777777; font-size: 11px; border: none; background: transparent;")
        header.addWidget(date_label)

        layout.addLayout(header)

        msg_label = QLabel(commit.get("message", "") or "")
        msg_label.setStyleSheet("color: #E0E0E0; font-size: 12px; border: none; background: transparent;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        self.versions_layout.addWidget(card)


    def _create_exe_version_item(self, version, is_current):
        changes = version.get('changes', [])
        is_available = version.get('available', False)
        is_expanded = True
        ver_str = version['version']
        dl_url = version.get('download_url', '')

        card = QFrame()
        card.setObjectName("versionCard")
        if is_current:
            card.setStyleSheet("""
                #versionCard {
                    background-color: #162016;
                    border: 1px solid #1f3a1f;
                    border-radius: 8px;
                }
                #versionCard:hover {
                    background-color: #1a2a1a;
                    border-color: #2a4a2a;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)
        elif is_available:
            card.setStyleSheet("""
                #versionCard {
                    background-color: #161616;
                    border: 1px solid #222222;
                    border-radius: 8px;
                }
                #versionCard:hover {
                    background-color: #1c1c1c;
                    border-color: #333333;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)
        else:
            card.setStyleSheet("""
                #versionCard {
                    background-color: #111111;
                    border: 1px solid #1a1a1a;
                    border-radius: 8px;
                }
                #versionCard:hover {
                    background-color: #161616;
                    border-color: #222222;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 12, 16, 12)

        header = QHBoxLayout()
        header.setSpacing(10)

        version_label = QLabel(f"v{ver_str}")
        version_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        if is_current:
            version_label.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
        elif not is_available:
            version_label.setStyleSheet("color: #555555; border: none; background: transparent;")
        else:
            version_label.setStyleSheet("color: #E0E0E0; border: none; background: transparent;")
        header.addWidget(version_label)

        if version.get('date'):
            date_label = QLabel(version['date'])
            date_label.setFont(QFont("Consolas", 9))
            date_label.setStyleSheet("color: #555555; border: none; background: transparent;")
            header.addWidget(date_label)

        header.addStretch()

        if is_available and version.get('local_size'):
            size_label = QLabel(version['local_size'])
            size_label.setFont(QFont("Consolas", 9))
            size_label.setStyleSheet("color: #555555; border: none; background: transparent;")
            header.addWidget(size_label)

        if is_current:
            current_tag = QLabel("● 当前版本")
            current_tag.setFont(QFont("Microsoft YaHei", 9))
            current_tag.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
            header.addWidget(current_tag)
        else:
            if is_available:
                switch_btn = QPushButton("切换")
                switch_btn.setFixedWidth(60)
                switch_btn.clicked.connect(lambda checked, v=version: self._launch_exe_version(v))
                switch_btn.setStyleSheet(DARK_BTN_PRIMARY)
                header.addWidget(switch_btn)
            elif dl_url:
                dl_btn = QPushButton("下载")
                dl_btn.setFixedWidth(60)
                dl_btn.setStyleSheet(DARK_BTN_PRIMARY)
                header.addWidget(dl_btn)
            else:
                status_label = QLabel("未提供")
                status_label.setFont(QFont("Microsoft YaHei", 9))
                status_label.setStyleSheet("color: #666666; border: none; background: transparent;")
                header.addWidget(status_label)

            toggle_btn = QPushButton("详情" if not is_expanded else "收起")
            toggle_btn.setFixedWidth(60)
            toggle_btn.setStyleSheet(DARK_BTN_STYLE)
            header.addWidget(toggle_btn)

        layout.addLayout(header)

        # Progress row (hidden by default)
        progress_row = QFrame()
        progress_row.setObjectName(f"_dl_progress_{ver_str}")
        progress_row.setVisible(False)
        progress_row.setStyleSheet("border: none; background: transparent;")
        progress_layout = QHBoxLayout(progress_row)
        progress_layout.setContentsMargins(0, 4, 0, 0)
        progress_layout.setSpacing(6)

        dl_progress = QProgressBar()
        dl_progress.setRange(0, 100)
        dl_progress.setValue(0)
        dl_progress.setFixedHeight(16)
        dl_progress.setStyleSheet("""
            QProgressBar { background-color: #1A1A1A; border: 1px solid #333333;
                border-radius: 3px; text-align: center; color: #FFFFFF; font-size: 10px; }
            QProgressBar::chunk { background-color: #CC0000; border-radius: 2px; }
        """)
        progress_layout.addWidget(dl_progress, 1)

        dl_status_label = QLabel("0.0/0.0MB")
        dl_status_label.setStyleSheet("color: #AAAAAA; font-size: 10px; min-width: 80px; border: none; background: transparent;")
        progress_layout.addWidget(dl_status_label)

        pause_btn = QPushButton("暂停")
        pause_btn.setFixedWidth(50)
        pause_btn.setStyleSheet("QPushButton { background-color: #FF8F00; color: white; border: none; border-radius: 3px; padding: 3px 8px; font-size: 10px; } QPushButton:hover { background-color: #FF6F00; }")
        progress_layout.addWidget(pause_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(50)
        cancel_btn.setStyleSheet("QPushButton { background-color: #C62828; color: white; border: none; border-radius: 3px; padding: 3px 8px; font-size: 10px; } QPushButton:hover { background-color: #D32F2F; }")
        progress_layout.addWidget(cancel_btn)

        layout.addWidget(progress_row)

        if version.get('message'):
            msg_label = QLabel(version['message'])
            msg_label.setFont(QFont("Microsoft YaHei", 9))
            msg_label.setStyleSheet("color: #777777; border: none; background: transparent;")
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

        name_label = QLabel(version['name'])
        name_label.setFont(QFont("Microsoft YaHei", 9))
        if not is_available:
            name_label.setStyleSheet("color: #444444; border: none; background: transparent;")
        else:
            name_label.setStyleSheet("color: #777777; border: none; background: transparent;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        detail_widget = QWidget()
        detail_widget.setStyleSheet("border: none; background: transparent;")
        changes_layout = QVBoxLayout(detail_widget)
        changes_layout.setSpacing(2)
        changes_layout.setContentsMargins(0, 4, 0, 0)

        if changes:
            for change in changes:
                change_label = QLabel(f"· {change}")
                change_label.setFont(QFont("Microsoft YaHei", 9))
                change_label.setStyleSheet("color: #777777; border: none; background: transparent;")
                change_label.setWordWrap(True)
                changes_layout.addWidget(change_label)
        else:
            no_changes_label = QLabel("暂无修改记录")
            no_changes_label.setFont(QFont("Microsoft YaHei", 9))
            no_changes_label.setStyleSheet("color: #3a3a3a; border: none; background: transparent;")
            changes_layout.addWidget(no_changes_label)

        detail_widget.setVisible(is_expanded)
        self._detail_widgets.append(detail_widget)
        layout.addWidget(detail_widget)

        if not is_current:
            def toggle_detail(checked=False, dw=detail_widget, tb=toggle_btn):
                is_visible = not dw.isVisible()
                dw.setVisible(is_visible)
                tb.setText("收起" if is_visible else "详情")
            toggle_btn.clicked.connect(toggle_detail)

        # Connect download button if present
        if not is_current and not is_available and dl_url:
            remote_info = {
                "version": ver_str,
                "filename": version.get('name', f"{APP_NAME}-v{ver_str}.exe"),
                "download_url": dl_url,
                "changes": changes,
            }
            dl_btn.clicked.connect(lambda checked, ri=remote_info: self._start_inline_download(ri, progress_row, dl_progress, dl_status_label, pause_btn, cancel_btn))

        self.versions_layout.addWidget(card)

    def _effective_source_key(self):
        """Return the effective source key to use for download URLs"""
        key = self._ver_active_source if hasattr(self, '_ver_active_source') else "auto"
        if key == "auto":
            return self._ver_race_winner or "github_mirror"
        return key

    def _asset_filename_for_source(self, source_key, version, chinese_name=""):
        """按下载源决定 release 资产文件名。

        GitHub release 资产名不支持中文（会被静默丢弃前缀），故 GitHub 系源
        统一用 ASCII 名 ``yunji-music-v{version}.exe``；Gitee 源保留中文原名。
        """
        if source_key in ("github_mirror", "github"):
            return f"yunji-music-v{version}.exe"
        return chinese_name or f"{APP_NAME}-v{version}.exe"

    def _fetch_release_assets(self, source_key, current_versions):
        """Async fetch real download URLs from Releases API"""
        source = UPDATE_SOURCES.get(source_key, {})
        releases_url = source.get("releases_url", "")
        if not releases_url:
            return

        def on_done():
            try:
                req = Request(releases_url, headers={"User-Agent": "Mozilla/5.0"})
                resp = urlopen(req, timeout=15)
                raw = resp.read().decode("utf-8")
                releases = json.loads(raw)
                if not isinstance(releases, list):
                    return

                release_downloads = {}
                for rel in releases:
                    tag = rel.get("tag_name", "")
                    tag_ver = tag.lstrip("v")
                    if not re.match(r"\d+\.\d+\.\d+\.\d+", tag_ver):
                        continue
                    assets = rel.get("assets", [])
                    if source.get("is_api"):
                        for asset in assets:
                            fname = asset.get("name", "")
                            if fname.endswith(".exe"):
                                url = asset.get("browser_download_url", "")
                                if url:
                                    asset_ver = tag_ver
                                    release_downloads[asset_ver] = {
                                        "download_url": url,
                                        "filename": fname,
                                    }
                                    break
                    else:
                        for asset in assets:
                            fname = asset.get("name", "")
                            if fname.endswith(".exe"):
                                url = asset.get("browser_download_url", "")
                                if url:
                                    asset_ver = tag_ver
                                    release_downloads[asset_ver] = {
                                        "download_url": url,
                                        "filename": fname,
                                    }
                                    break
                if release_downloads:
                    QTimer.singleShot(0, lambda rd=release_downloads: self._apply_release_assets(rd))
            except Exception:
                pass

        t = threading.Thread(target=on_done, daemon=True)
        t.start()

    def _apply_release_assets(self, release_downloads):
        """Update version card UIs with real download URLs (must run on main thread)."""
        if not release_downloads:
            return
        for i in range(self.versions_layout.count()):
            item = self.versions_layout.itemAt(i)
            if not item or not item.widget():
                continue
            card = item.widget()
            version_labels = card.findChildren(QLabel, Qt.FindChildOption.FindChildrenRecursively)
            for vl in version_labels:
                font = vl.font()
                if font and "Consolas" in font.family() and font.bold():
                    raw_ver = vl.text().lstrip("v")
                    if raw_ver in release_downloads:
                        rd = release_downloads[raw_ver]
                        btns = card.findChildren(QPushButton)
                        for btn in btns:
                            if btn.text() == "下载":
                                ri = {
                                    "version": raw_ver,
                                    "filename": rd["filename"],
                                    "download_url": rd["download_url"],
                                    "changes": [],
                                }
                                try:
                                    btn.clicked.disconnect()
                                except TypeError:
                                    pass
                                progress_row = card.findChild(QFrame, f"_dl_progress_{raw_ver}")
                                dl_progress = progress_row.findChild(QProgressBar) if progress_row else None
                                dl_status = progress_row.findChildren(QLabel) if progress_row else []
                                pause_btn_widgets = progress_row.findChildren(QPushButton) if progress_row else []
                                cancel_btn = None
                                status_label = None
                                for pw in (pause_btn_widgets or []):
                                    if pw.text() in ("暂停", "继续"):
                                        pause_btn_widgets = pw
                                    elif pw.text() == "取消":
                                        cancel_btn = pw
                                for sl in (dl_status or []):
                                    if "MB" in sl.text() or sl.text() == "0.0/0.0MB":
                                        status_label = sl
                                btn.clicked.connect(lambda checked, ri=ri, pr=progress_row, dp=dl_progress, ds=status_label, pb=pause_btn_widgets, cb=cancel_btn: self._start_inline_download(ri, pr, dp, ds, pb, cb) if pr else None)
                                break
                        break

    def _start_inline_download(self, remote_info, progress_row, dl_progress, dl_status_label, pause_btn, cancel_btn):
        """Inline download with progress bar in the version card"""
        if not remote_info:
            return
        filename = remote_info.get("filename", "")
        download_url = remote_info.get("download_url", "")
        version = remote_info.get("version", "")

        if not download_url:
            source_key = self._effective_source_key()
            source = UPDATE_SOURCES.get(source_key, list(UPDATE_SOURCES.values())[0] if UPDATE_SOURCES else {})
            if filename and version:
                download_url = source.get("download_url_tpl", "").format(filename=quote(filename), version=version)
        if not download_url:
            return

        ver_dir = Path(self.project_root) / "ver" if self.project_root else Path("ver")
        ver_dir.mkdir(parents=True, exist_ok=True)
        target_filename = filename if filename else f"{APP_NAME}-v{version}.exe"
        target_path = ver_dir / target_filename

        # If already exists, switch directly
        if target_path.exists():
            self._switch_to_exe(str(target_path))
            return

        # Show progress row
        progress_row.setVisible(True)
        dl_progress.setValue(0)
        dl_status_label.setText("0.0/0.0MB")

        dl_state = {"paused": False, "cancelled": False, "done": False, "pause_event": threading.Event()}
        dl_state["pause_event"].set()

        def on_pause():
            if dl_state["paused"]:
                dl_state["paused"] = False
                dl_state["pause_event"].set()
                if pause_btn:
                    pause_btn.setText("暂停")
            else:
                dl_state["paused"] = True
                dl_state["pause_event"].clear()
                if pause_btn:
                    pause_btn.setText("继续")

        def on_cancel():
            dl_state["cancelled"] = True
            dl_state["pause_event"].set()

        if pause_btn:
            try:
                pause_btn.clicked.disconnect()
            except Exception:
                pass
            pause_btn.clicked.connect(on_pause)
        if cancel_btn:
            try:
                cancel_btn.clicked.disconnect()
            except Exception:
                pass
            cancel_btn.clicked.connect(on_cancel)

        tmp_path = str(target_path) + ".downloading"

        def do_download():
            # 候选下载地址：传入的 primary 优先，再按 github_mirror → github → gitee 顺序回退，
            # 任一源失败（404/超时/文件异常）自动尝试下一源，确保国内用户也能稳定下载。
            candidates = []
            if download_url:
                candidates.append(download_url)
            for _key in ("github_mirror", "github", "gitee"):
                _src = UPDATE_SOURCES.get(_key, {})
                _tpl = _src.get("download_url_tpl", "")
                if _tpl and version:
                    # GitHub 系源用 ASCII 资产名，Gitee 用中文原名
                    _fname = self._asset_filename_for_source(_key, version, filename)
                    try:
                        candidates.append(_tpl.format(filename=quote(_fname), version=version))
                    except Exception:
                        pass
            _seen, candidates = set(), [u for u in candidates if u and not (u in _seen or _seen.add(u))]
            _n = len(candidates)

            for _idx, _cand in enumerate(candidates, 1):
                if dl_state["cancelled"]:
                    break
                try:
                    _pu = urlparse(_cand)
                    _enc_path = quote(_pu.path, safe="/")
                    _enc_url = urlunparse((_pu.scheme, _pu.netloc, _enc_path, _pu.params, _pu.query, _pu.fragment))
                    req = Request(_enc_url, headers={"User-Agent": "Mozilla/5.0"})
                    resp = urlopen(req, timeout=60)
                    total = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    block_size = 65536
                    with open(tmp_path, "wb") as f:
                        while True:
                            if dl_state["cancelled"]:
                                break
                            dl_state["pause_event"].wait()
                            if dl_state["cancelled"]:
                                break
                            chunk = resp.read(block_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                pct = int(downloaded * 100 / total)
                                mb = downloaded / (1024 * 1024)
                                total_mb = total / (1024 * 1024)
                                QTimer.singleShot(0, lambda p=pct, m=mb, t=total_mb: (
                                    dl_progress.setValue(p),
                                    dl_status_label.setText(f"{m:.1f}/{t:.1f}MB")
                                ))

                    if dl_state["cancelled"]:
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        QTimer.singleShot(0, lambda: progress_row.setVisible(False))
                        return

                    if os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 1024 * 1024:
                        os.replace(tmp_path, str(target_path))
                        dl_state["done"] = True
                        QTimer.singleShot(0, lambda: (
                            dl_progress.setValue(100),
                            dl_status_label.setText("下载完成"),
                        ))
                        time_module.sleep(0.5)
                        QTimer.singleShot(800, lambda: self._switch_to_exe(str(target_path)))
                        return
                    else:
                        # 该源文件异常（过小），清理并尝试下一源
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        QTimer.singleShot(0, lambda i=_idx, n=_n: (
                            dl_status_label.setText(f"源 {i}/{n} 文件异常，尝试下一源...")
                        ))
                        continue
                except Exception:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                    if _idx < _n and not dl_state["cancelled"]:
                        QTimer.singleShot(0, lambda i=_idx, n=_n: (
                            dl_status_label.setText(f"源 {i}/{n} 失败，切换中...")
                        ))
                    continue

            # 所有源均失败
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            QTimer.singleShot(0, lambda: (
                progress_row.setVisible(False),
                dl_status_label.setText("下载失败：所有源均不可用")
            ))

        t = threading.Thread(target=do_download, daemon=True)
        t.start()

    def _switch_to_exe(self, exe_path):
        """Verify EXE, create hardlink to entry point, stop services, launch new version"""
        if not os.path.exists(exe_path):
            return

        try:
            exe_size = os.path.getsize(exe_path)
            if exe_size < 1024 * 1024:
                return
        except Exception:
            return

        # Find deployment directory
        dev_dir = Path(self.project_root).parent
        entry_exe = dev_dir / f"{BRAND_NAME}.exe"

        # Backup current entry
        backup_exe = str(entry_exe) + ".bak"
        if entry_exe.exists():
            try:
                import shutil
                shutil.copy2(str(entry_exe), backup_exe)
            except Exception:
                backup_exe = ""

        # Copy new EXE as entry point (hardlink may fail on different drives)
        import shutil
        try:
            os.link(exe_path, str(entry_exe))
        except Exception:
            try:
                shutil.copy2(exe_path, str(entry_exe))
            except Exception:
                # Try removing first then copy
                removed = False
                try:
                    entry_exe.unlink()
                    removed = True
                except Exception:
                    pass
                try:
                    shutil.copy2(exe_path, str(entry_exe))
                except Exception as exc:
                    # Restore from backup if available
                    if removed and backup_exe and os.path.exists(backup_exe):
                        try:
                            shutil.copy2(backup_exe, str(entry_exe))
                        except Exception:
                            pass
                    return

        # Stop current app (signal main window if available)
        import subprocess
        # Launch new version with delay
        cmd = f'ping -n 2 127.0.0.1 >nul & start "" "{entry_exe}"'
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

        QApplication.quit()

    def _launch_exe_version(self, version):
        if not version.get('local_path'):
            QMessageBox.warning(self, "无法切换", "该版本不在本地，无法切换。")
            return

        reply = QMessageBox.question(
            self,
            "确认启动",
            f"确定要启动版本 v{version['version']} 吗？\n\n"
            f"文件: {version['name']}\n"
            f"大小: {version.get('local_size', '未知')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                import subprocess
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                creation_flags = subprocess.CREATE_NO_WINDOW
                subprocess.Popen(
                    [version['local_path']],
                    cwd=os.path.dirname(version['local_path']),
                    startupinfo=si,
                    creationflags=creation_flags,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True
                )

                QMessageBox.information(
                    self,
                    "启动成功",
                    f"已启动版本 v{version['version']}\n\n当前程序将退出。",
                    QMessageBox.StandardButton.Ok
                )

                QApplication.quit()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动版本失败:\n{str(e)}")

    def _load_git_versions(self, auto_remote=False):
        self.current_mode_label.setText("开发动态")
        self.current_info_label.setText("⏳ 正在读取内置提交历史...")

        loading_label = QLabel("⏳ 正在读取内置提交历史...")
        loading_label.setStyleSheet("color: #888888; padding: 20px;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versions_layout.addWidget(loading_label)

        # auto_remote=False：仅用 exe 内置静态 git_commits.json 秒开，
        # 不联网、不弹窗（开发动态与软件版本对称，都是静态页面内置）。
        # 用户点「🌐 远程获取」时传 True 才会去仓库 commits API 拉最新提交。
        if self._git_worker and self._git_worker.isRunning():
            self._git_worker.cancel()
            self._git_worker.wait(2000)
        self._git_worker = _GitCommitsFetchWorker(self, auto_remote=auto_remote)
        self._git_worker.data_ready.connect(self._on_git_data_ready)
        self._git_worker.start()



class ModelManagerDialog(QDialog):
    """模型管理器对话框 - 可以作为对话框或widget使用"""

    def __init__(self, parent=None, main_window=None, as_widget=False):
        super().__init__(parent)
        self.main_window = main_window
        self.as_widget = as_widget
        self.setWindowTitle("模型管理器")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        if not as_widget:
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("""
            QDialog {
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
                # 让用户在下载前就知道模型有多大，也作为进度条百分比的参照
                size_text = ""
                try:
                    if self.main_window:
                        from main import _FS_MODEL_DOWNLOAD_SIZE, _FS_MAIN_MODEL_COMPONENTS
                        _model_name = model["name"]
                        if _model_name in ("acestep-v15-turbo", "acestep-5Hz-lm-1.7B"):
                            # 主模型组件：显示各组件总和
                            _total = sum(_FS_MODEL_DOWNLOAD_SIZE.get(c, 0) for c in _FS_MAIN_MODEL_COMPONENTS)
                        else:
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

                # 下载中判定需同时匹配模型名与下载目标 dl_target：主模型组件实际以
                # 下载目标 "main" 进行，main.current_operation_model 会是 "main" 而非组件名，
                # 仅按 model["name"] 比对会让主组件的进度条/暂停按钮永远不显示。
                _dl_target = "main" if model["name"] in ("acestep-v15-turbo", "acestep-5Hz-lm-1.7B") else model["name"]
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
                # 主模型组件无法单独下载，统一路由到主模型下载
                is_main_component = model["name"] in ("acestep-v15-turbo", "acestep-5Hz-lm-1.7B")
                dl_target = "main" if is_main_component else model["name"]

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
                        delete_btn.setToolTip("删除模型文件" + ("（将删除整个主模型）" if is_main_component else ""))
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
        特殊主模型组件(acestep-v15-turbo / ace-step-5Hz-lm-1.7B)统一路由到主模型下载，键为 'main'。"""
        if name in ("acestep-v15-turbo", "acestep-5Hz-lm-1.7B"):
            return "main"
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
