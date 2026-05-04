"""
版本管理器模块 - 混合模式版本管理器
支持Git开发版（Gitee API）和EXE稳定版管理
所有远程数据获取均通过 urlopen，零 subprocess，零弹窗
"""

import sys
import os
import re
import base64
from datetime import datetime
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QWidget, QMessageBox, QFrame, QApplication,
    QComboBox, QTabWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont


REMOTE_REPO_OWNER = "yunjii"
REMOTE_REPO_NAME = "ace"
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
"""

def _get_gitee_token():
    if hasattr(sys, '_MEIPASS'):
        token_file = Path(sys._MEIPASS) / ".gitee_token"
    else:
        token_file = Path(__file__).parent / ".gitee_token"
    if token_file.exists():
        return token_file.read_text(encoding='utf-8').strip()
    return ""


def _build_api_url(base_url):
    token = _get_gitee_token()
    if token:
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}access_token={token}"
    return base_url


class _ExeFetchWorker(QThread):
    data_ready = pyqtSignal(object, list, dict)

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            current = self.dialog._get_current_exe_version()
            if self._cancelled:
                return
            remote = self.dialog._fetch_remote_versions()
            if self._cancelled:
                return
            local = self.dialog._get_local_exe_versions()
            if self._cancelled:
                return
            self.data_ready.emit(current, remote, local)
        except Exception as e:
            print(f"EXE版本数据获取失败: {e}")
            if not self._cancelled:
                self.data_ready.emit(None, [], {})


class _GitFetchWorker(QThread):
    data_ready = pyqtSignal(str, list)

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            local_ver = self.dialog._get_local_version_string()
            if self._cancelled:
                return
            commits = self.dialog._fetch_git_commits()
            if self._cancelled:
                return
            self.data_ready.emit(local_ver or '', commits)
        except Exception as e:
            print(f"Git版本数据获取失败: {e}")
            if not self._cancelled:
                self.data_ready.emit('', [])


class HybridVersionManagerDialog(QDialog):
    """混合模式版本管理器 - 支持Git和EXE两种模式"""

    def __init__(self, parent=None, base_dir=None, as_widget=False):
        super().__init__(parent)
        self.base_dir = base_dir
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

        self.current_mode = "git"
        self._versions_loaded = False
        self._git_repo_checked = False
        self.has_git_repo = False
        self._remote_versions_cache = None
        self._detail_widgets = []
        self._all_expanded = True
        self._exe_worker = None
        self._git_worker = None

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
        self.has_git_repo = self._check_git_repo()
        if hasattr(self, 'mode_buttons_widget'):
            self.mode_buttons_widget.setVisible(True)
            self.btn_mode_exe.setChecked(False)
            self.btn_mode_git.setChecked(True)

    def _load_local_version_history(self):
        self.version_history = {}
        possible_paths = [
            Path(self.base_dir) / 'version_history.json',
            Path(self.base_dir) / 'dist' / 'version_history.json',
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
            current_dir = Path(self.base_dir)
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

        self.btn_mode_exe = QPushButton("EXE 稳定版")
        self.btn_mode_exe.setCheckable(True)
        self.btn_mode_exe.setChecked(False)
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

        self.btn_mode_git = QPushButton("Git 开发版")
        self.btn_mode_git.setCheckable(True)
        self.btn_mode_git.setChecked(True)
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

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_versions)
        refresh_btn.setMinimumWidth(70)
        refresh_btn.setStyleSheet(DARK_BTN_STYLE)
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

    def _fetch_remote_versions(self):
        if self._remote_versions_cache is not None:
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

    def _get_local_exe_versions(self):
        local_versions = {}
        ver_dirs = []
        ver_dir = Path(self.base_dir) / "ver"
        if ver_dir.exists():
            ver_dirs.append(ver_dir)
        dev_dir = Path(self.base_dir).parent
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

        if Path(self.base_dir).exists():
            for exe_file in Path(self.base_dir).glob("*.exe"):
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

    def _fetch_git_commits(self):
        try:
            url = _build_api_url(f"{REMOTE_COMMITS_URL}?per_page=30")
            req = Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urlopen(req, timeout=10)
            commits = json.loads(resp.read().decode('utf-8'))
            return commits
        except HTTPError as e:
            print(f"远程版本获取失败 (HTTP {e.code}): {e.reason}")
            return []
        except URLError as e:
            print(f"远程版本获取失败 (网络错误): {e.reason}")
            return []
        except Exception as e:
            print(f"远程版本获取失败: {e}")
            return []

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

    def _load_versions(self, force=False):
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
            self._load_exe_versions()
        else:
            self._load_git_versions()

    def _load_exe_versions(self):
        self.current_mode_label.setText("EXE 稳定版")
        self.current_info_label.setText("⏳ 正在加载版本信息...")

        loading_label = QLabel("⏳ 正在获取版本信息...")
        loading_label.setStyleSheet("color: #888888; padding: 20px;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versions_layout.addWidget(loading_label)

        self._exe_worker = _ExeFetchWorker(self)
        self._exe_worker.data_ready.connect(self._on_exe_data_ready)
        self._exe_worker.start()

    def _on_exe_data_ready(self, current, remote_versions, local_versions):
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

        if not remote_versions and not local_versions:
            no_version_label = QLabel("未找到稳定版信息\n\n请检查网络连接")
            no_version_label.setStyleSheet("color: #666666; padding: 20px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return

        merged = {}
        for rv in remote_versions:
            ver = rv.get('version', '')
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
                'download_url': rv.get('download_url', ''),
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

    def _create_exe_version_item(self, version, is_current):
        changes = version.get('changes', [])
        is_available = version.get('available', False)
        is_expanded = True

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

        version_label = QLabel(f"v{version['version']}")
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

        self.versions_layout.addWidget(card)

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

    def _load_git_versions(self):
        self.current_mode_label.setText("Git 开发版")
        self.current_info_label.setText("⏳ 正在加载版本信息...")

        loading_label = QLabel("⏳ 正在获取Git提交历史...")
        loading_label.setStyleSheet("color: #888888; padding: 20px;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versions_layout.addWidget(loading_label)

        self._git_worker = _GitFetchWorker(self)
        self._git_worker.data_ready.connect(self._on_git_data_ready)
        self._git_worker.start()

    def _on_git_data_ready(self, local_ver, commits):
        if self.current_mode != "git":
            return

        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if local_ver:
            self.current_info_label.setText(f"当前版本: v{local_ver}")
        else:
            self.current_info_label.setText("⚠️ 无法获取当前版本信息")

        if not commits:
            no_version_label = QLabel("未获取到远程提交历史\n\n请检查网络连接")
            no_version_label.setStyleSheet("color: #666666; padding: 20px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return

        current_version = local_ver

        for commit_data in commits:
            commit = commit_data.get('commit', {})
            sha = commit_data.get('sha', '?')[:7]
            message = commit.get('message', '').split('\n')[0]
            body = '\n'.join(commit.get('message', '').split('\n')[1:]).strip()
            date_str = commit.get('committer', {}).get('date', '')[:16].replace('T', ' ')
            author = commit.get('author', {}).get('name', '')

            is_current = current_version and f"v{current_version}" in commit.get('message', '')

            version = {
                'hash': sha,
                'full_sha': commit_data.get('sha', ''),
                'message': message,
                'body': body,
                'date': date_str,
                'author': author
            }

            self._create_git_version_item(version, is_current)

    def _create_git_version_item(self, version, is_current):
        card = QFrame()
        card.setObjectName("gitVersionCard")
        if is_current:
            card.setStyleSheet("""
                #gitVersionCard {
                    background-color: #162016;
                    border: 1px solid #1f3a1f;
                    border-radius: 8px;
                }
                #gitVersionCard:hover {
                    background-color: #1a2a1a;
                    border-color: #2a4a2a;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)
        else:
            card.setStyleSheet("""
                #gitVersionCard {
                    background-color: #161616;
                    border: 1px solid #222222;
                    border-radius: 8px;
                }
                #gitVersionCard:hover {
                    background-color: #1c1c1c;
                    border-color: #333333;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)

        main_layout = QVBoxLayout(card)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(16, 12, 16, 12)

        body = version.get('body', '')

        header = QHBoxLayout()
        header.setSpacing(10)

        hash_label = QLabel(version['hash'])
        hash_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        if is_current:
            hash_label.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
        else:
            hash_label.setStyleSheet("color: #888888; border: none; background: transparent;")
        header.addWidget(hash_label)

        date_label = QLabel(version['date'])
        date_label.setFont(QFont("Consolas", 9))
        date_label.setStyleSheet("color: #555555; border: none; background: transparent;")
        header.addWidget(date_label)

        if version.get('author'):
            author_label = QLabel(version['author'])
            author_label.setFont(QFont("Microsoft YaHei", 9))
            author_label.setStyleSheet("color: #555555; border: none; background: transparent;")
            header.addWidget(author_label)

        header.addStretch()

        if is_current:
            current_tag = QLabel("● 当前版本")
            current_tag.setFont(QFont("Microsoft YaHei", 9))
            current_tag.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
            header.addWidget(current_tag)
        else:
            switch_btn = QPushButton("切换")
            switch_btn.setFixedWidth(60)
            switch_btn.setStyleSheet(DARK_BTN_SUCCESS)
            switch_btn.clicked.connect(
                lambda checked, sha=version['full_sha']: self._switch_git_commit(sha)
            )
            header.addWidget(switch_btn)

        toggle_btn = QPushButton("详情")
        toggle_btn.setFixedWidth(60)
        toggle_btn.setStyleSheet(DARK_BTN_STYLE)
        header.addWidget(toggle_btn)

        main_layout.addLayout(header)

        message_label = QLabel(version['message'])
        message_label.setFont(QFont("Microsoft YaHei", 9))
        message_label.setStyleSheet("color: #AAAAAA; border: none; background: transparent;")
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)

        detail_widget = QWidget()
        detail_widget.setStyleSheet("border: none; background: transparent;")
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setSpacing(2)
        detail_layout.setContentsMargins(0, 4, 0, 0)

        if body:
            for line in body.split('\n'):
                if line.strip():
                    line_label = QLabel(f"· {line.strip()}")
                    line_label.setFont(QFont("Microsoft YaHei", 9))
                    line_label.setStyleSheet("color: #777777; border: none; background: transparent;")
                    line_label.setWordWrap(True)
                    detail_layout.addWidget(line_label)
        else:
            no_detail_label = QLabel("暂无详细说明")
            no_detail_label.setFont(QFont("Microsoft YaHei", 9))
            no_detail_label.setStyleSheet("color: #3a3a3a; border: none; background: transparent;")
            detail_layout.addWidget(no_detail_label)

        detail_widget.setVisible(False)
        self._detail_widgets.append(detail_widget)
        main_layout.addWidget(detail_widget)

        def toggle_detail(checked=False, dw=detail_widget, tb=toggle_btn):
            is_visible = not dw.isVisible()
            dw.setVisible(is_visible)
            tb.setText("收起" if is_visible else "详情")
        toggle_btn.clicked.connect(toggle_detail)

        self.versions_layout.addWidget(card)

    def _switch_git_commit(self, full_sha):
        if not self.has_git_repo:
            QMessageBox.warning(self, "无法切换", "当前不是Git仓库，无法切换版本。")
            return

        reply = QMessageBox.question(
            self,
            "确认切换",
            f"确定要切换到提交 {full_sha[:7]} 吗？\n\n"
            "这将执行 git checkout 操作，切换到指定的开发版本。\n"
            "切换后需要重新启动应用程序。",
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

                result = subprocess.run(
                    ["git", "checkout", full_sha],
                    cwd=self.base_dir,
                    startupinfo=si,
                    creationflags=creation_flags,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    QMessageBox.information(
                        self,
                        "切换成功",
                        f"已切换到提交 {full_sha[:7]}\n\n请重新启动应用程序。",
                        QMessageBox.StandardButton.Ok
                    )
                    QApplication.quit()
                else:
                    QMessageBox.critical(
                        self,
                        "切换失败",
                        f"Git checkout 失败:\n{result.stderr}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换版本失败:\n{str(e)}")


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

        self.verify_result_label = QLabel("")
        self.verify_result_label.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        top_bar.addWidget(self.verify_result_label)

        self.verify_time_label = QLabel("")
        self.verify_time_label.setStyleSheet("font-size: 11px; color: #666666; margin-left: 10px;")
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

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 4px;
                height: 20px;
                text-align: center;
                color: #FFFFFF;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #1976D2;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

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

            name_header = QLabel("模型名称")
            name_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 200px;")
            header_layout.addWidget(name_header)

            status_header = QLabel("状态")
            status_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 80px;")
            header_layout.addWidget(status_header)

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

                name_label = QLabel(model["display_name"])
                name_label.setStyleSheet("color: #FFFFFF; font-size: 12px; min-width: 200px;")
                row_layout.addWidget(name_label)

                status_label = QLabel("✓ 已安装" if model["exists"] else "✗ 未安装")
                status_label.setStyleSheet(f"color: {'#4CAF50' if model['exists'] else '#F44336'}; font-size: 11px; min-width: 80px;")
                row_layout.addWidget(status_label)

                desc_label = QLabel(model["description"])
                desc_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
                row_layout.addWidget(desc_label, 1)

                btn_layout = QHBoxLayout()
                btn_layout.setSpacing(4)

                is_downloading = self.main_window.is_downloading and self.main_window.current_operation_model == model["name"]

                if is_downloading:
                    pause_btn = QPushButton("暂停")
                    pause_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #FF8F00;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 11px;
                        }
                        QPushButton:hover {
                            background-color: #FF6F00;
                        }
                    """)
                    pause_btn.clicked.connect(self.main_window._pause_download)
                    btn_layout.addWidget(pause_btn)
                elif model["exists"]:
                    delete_btn = QPushButton("删除")
                    delete_btn.setStyleSheet(DARK_BTN_DANGER)
                    delete_btn.clicked.connect(lambda checked, m=model["name"]: self._delete_model(m))
                    btn_layout.addWidget(delete_btn)
                else:
                    download_btn = QPushButton("下载")
                    download_btn.setStyleSheet(DARK_BTN_PRIMARY)
                    download_btn.clicked.connect(lambda checked, m=model["name"]: self._download_model(m))
                    btn_layout.addWidget(download_btn)

                row_layout.addLayout(btn_layout)
                model_item_layout.addLayout(row_layout)

                if is_downloading:
                    progress_row = QHBoxLayout()
                    progress_bar = QProgressBar()
                    progress_bar.setMinimum(0)
                    progress_bar.setMaximum(100)
                    progress_bar.setValue(0)
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
                    progress_label = QLabel("准备下载...")
                    progress_label.setStyleSheet("color: #AAAAAA; font-size: 10px; min-width: 80px;")
                    progress_row.addWidget(progress_label)
                    model_item_layout.addLayout(progress_row)

                    if not hasattr(self, '_model_progress_bars'):
                        self._model_progress_bars = {}
                    self._model_progress_bars[model["name"]] = (progress_bar, progress_label)

                self.models_layout.addWidget(model_item)

            if cat_id != list(categories.keys())[-1]:
                spacer = QWidget()
                spacer.setMinimumHeight(10)
                self.models_layout.addWidget(spacer)

    def _download_model(self, model_name):
        if self.main_window and hasattr(self.main_window, '_download_model'):
            self.main_window._download_model(model_name)
            QTimer.singleShot(100, self._update_ui)

    def _delete_model(self, model_name):
        if self.main_window and hasattr(self.main_window, '_delete_model'):
            self.main_window._delete_model(model_name)
            QTimer.singleShot(100, self._update_ui)

    def show_progress(self, text: str = ""):
        model_name = ""
        if self.main_window and hasattr(self.main_window, 'current_operation_model'):
            model_name = self.main_window.current_operation_model or ""
        if model_name and hasattr(self, '_model_progress_bars') and model_name in self._model_progress_bars:
            bar, label = self._model_progress_bars[model_name]
            bar.setValue(0)
            label.setText(text or "准备下载...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText(text)

    def update_progress(self, value: int, desc: str = ""):
        model_name = ""
        if self.main_window and hasattr(self.main_window, 'current_operation_model'):
            model_name = self.main_window.current_operation_model or ""
        if model_name and hasattr(self, '_model_progress_bars') and model_name in self._model_progress_bars:
            bar, label = self._model_progress_bars[model_name]
            bar.setValue(value)
            if desc:
                label.setText(desc)
        self.progress_bar.setValue(value)
        if desc:
            self.progress_label.setText(desc)

    def hide_progress(self):
        if hasattr(self, '_model_progress_bars'):
            for bar, label in self._model_progress_bars.values():
                bar.setValue(0)
                label.setText("")
            self._model_progress_bars.clear()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(False)


VersionManagerDialog = HybridVersionManagerDialog
