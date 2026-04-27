"""
版本管理器模块 - 混合模式版本管理器
支持远程版本管理（Gitee API）和EXE文件版本管理
"""

import sys
import os
import re
from datetime import datetime
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QWidget, QMessageBox, QFrame, QApplication,
    QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont


REMOTE_REPO_OWNER = "yunjii"
REMOTE_REPO_NAME = "ace"
REMOTE_VERSIONS_URL = f"https://gitee.com/{REMOTE_REPO_OWNER}/{REMOTE_REPO_NAME}/raw/master/dev/versions.json"


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
        
        # 仅使用EXE模式
        self.current_mode = "exe"
        self._versions_loaded = False
        self._git_repo_checked = False
        self.has_git_repo = False
        
        self._setup_ui()
        self._load_version_history()
        
        QTimer.singleShot(800, self._delayed_init)
    
    def _delayed_init(self):
        """延迟初始化：仅检查git仓库，不加载版本列表"""
        if self.as_widget and not self.isVisible():
            QTimer.singleShot(500, self._delayed_init)
            return
        
        if self._git_repo_checked:
            return
        self._git_repo_checked = True
        
        self.has_git_repo = self._check_git_repo()
        
        if self.has_git_repo and hasattr(self, 'mode_buttons_widget'):
            self.mode_buttons_widget.setVisible(True)
            self.btn_mode_exe.setChecked(True)
            self.btn_mode_git.setChecked(False)
    
    def _load_version_history(self):
        """加载版本历史"""
        self.version_history = {}
        
        # 尝试从多个位置加载版本历史
        possible_paths = [
            Path(self.base_dir) / 'version_history.json',
            Path(self.base_dir) / 'dist' / 'version_history.json',
        ]
        
        for history_path in possible_paths:
            if history_path.exists():
                try:
                    with open(history_path, 'r', encoding='utf-8') as f:
                        self.version_history = json.load(f)
                    print(f"加载版本历史：{history_path}")
                    break
                except Exception as e:
                    print(f"加载版本历史失败：{e}")
    
    def _get_version_changes(self, version_name):
        """获取版本的修改内容"""
        if version_name in self.version_history:
            return self.version_history[version_name].get('changes', [])
        name_without_ext = version_name.replace('.exe', '')
        if name_without_ext in self.version_history:
            return self.version_history[name_without_ext].get('changes', [])
        return []
    
    def _check_git_repo(self):
        """检查是否是Git仓库（不使用gitpython避免弹窗）"""
        try:
            # 直接检查 .git 文件夹，不使用 gitpython
            current_dir = Path(self.base_dir)
            while current_dir.parent != current_dir:  # 直到根目录
                git_dir = current_dir / ".git"
                if git_dir.exists() and git_dir.is_dir():
                    return True
                current_dir = current_dir.parent
            return False
        except Exception:
            return False
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部标题栏
        top_bar = QHBoxLayout()
        
        title_label = QLabel("版本管理器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        top_bar.addWidget(title_label)
        
        # 模式选择 - 横向按钮组
        self.mode_btn_group = QHBoxLayout()
        self.mode_btn_group.setSpacing(0)
        self.mode_btn_group.setContentsMargins(0, 0, 0, 0)
        
        self.btn_mode_exe = QPushButton("EXE 版本")
        self.btn_mode_exe.setCheckable(True)
        self.btn_mode_exe.setChecked(True)
        self.btn_mode_exe.setFixedHeight(32)
        self.btn_mode_exe.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
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
                background-color: #1565C0;
                border-color: #1565C0;
            }
            QPushButton:!checked {
                background-color: #252525;
                color: #AAAAAA;
                border: 1px solid #333333;
                font-weight: normal;
            }
            QPushButton:!checked:hover {
                background-color: #333333;
                border-color: #444444;
                color: #FFFFFF;
            }
        """)
        self.btn_mode_exe.clicked.connect(lambda: self._on_mode_changed("exe"))
        self.mode_btn_group.addWidget(self.btn_mode_exe)
        
        self.btn_mode_git = QPushButton("远程版本")
        self.btn_mode_git.setCheckable(True)
        self.btn_mode_git.setChecked(False)
        self.btn_mode_git.setFixedHeight(32)
        self.btn_mode_git.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
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
                background-color: #1565C0;
                border-color: #1565C0;
            }
            QPushButton:!checked {
                background-color: #252525;
                color: #AAAAAA;
                border: 1px solid #333333;
                font-weight: normal;
            }
            QPushButton:!checked:hover {
                background-color: #333333;
                border-color: #444444;
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
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                color: #F0F0F0;
            }
            QPushButton:hover {
                background-color: #424242;
                border-color: #E53935;
            }
        """)
        top_bar.addWidget(refresh_btn)
        
        if not self.as_widget:
            close_btn = QPushButton("✕ 关闭")
            close_btn.clicked.connect(self.accept)
            close_btn.setMinimumWidth(70)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    border: 1px solid #424242;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 12px;
                    color: #F0F0F0;
                }
                QPushButton:hover {
                    background-color: #424242;
                    border-color: #E53935;
                }
            """)
            top_bar.addWidget(close_btn)
        
        layout.addLayout(top_bar)
        
        # 当前版本信息
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
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #333333;")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)
        
        # 版本列表标题
        list_label = QLabel("版本历史")
        list_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        list_label.setStyleSheet("color: #888888;")
        layout.addWidget(list_label)
        
        # 版本列表滚动区域
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
        """模式切换"""
        try:
            if new_mode == self.current_mode:
                return
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
    
    def _get_current_exe_version(self):
        """获取当前EXE版本信息"""
        try:
            # 首先检查是否是打包的EXE模式
            if hasattr(sys, 'frozen'):
                exe_path = sys.executable
                exe_name = os.path.basename(exe_path)
            else:
                # 如果不是打包模式（开发模式），尝试从文件名或其他方式获取
                # 尝试从version_history.json获取最新版本
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
            
            # 从文件名中提取版本号，支持多种格式
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
            import traceback
            traceback.print_exc()
            return None
    
    def _get_available_exe_versions(self):
        """获取可用EXE版本列表（检查ver文件夹）"""
        try:
            version_dir = Path(self.base_dir) / "ver"
            dev_dir = Path(self.base_dir).parent
            ver_dir = dev_dir / "ver" if dev_dir.exists() else None
            
            # 使用字典来存储所有版本，避免重复
            version_dict = {}
            
            # 首先从版本历史中获取所有版本
            for version_name in self.version_history:
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', version_name)
                if match:
                    version = match.group(1)
                    version_dict[version] = {
                        'version': version,
                        'name': version_name,
                        'available': False,
                        'path': None,
                        'size': None,
                        'date': None
                    }
            
            # 检查ver文件夹中哪些版本可用，并添加所有找到的exe
            if ver_dir and ver_dir.exists():
                for exe_file in ver_dir.glob("*.exe"):
                    match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_file.name)
                    if match:
                        version = match.group(1)
                        file_size = exe_file.stat().st_size / (1024 * 1024)
                        mtime = datetime.fromtimestamp(exe_file.stat().st_mtime)
                        
                        # 更新或添加版本信息
                        if version in version_dict:
                            version_dict[version]['available'] = True
                            version_dict[version]['path'] = str(exe_file)
                            version_dict[version]['size'] = f"{file_size:.2f} MB"
                            version_dict[version]['date'] = mtime.strftime("%Y-%m-%d %H:%M")
                            version_dict[version]['name'] = exe_file.name
                        else:
                            # 如果不在版本历史中，添加新条目
                            version_dict[version] = {
                                'version': version,
                                'name': exe_file.name,
                                'available': True,
                                'path': str(exe_file),
                                'size': f"{file_size:.2f} MB",
                                'date': mtime.strftime("%Y-%m-%d %H:%M")
                            }
            
            # 检查当前目录的exe（兼容开发模式）
            if Path(self.base_dir).exists():
                for exe_file in Path(self.base_dir).glob("*.exe"):
                    match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_file.name)
                    if match:
                        version = match.group(1)
                        file_size = exe_file.stat().st_size / (1024 * 1024)
                        mtime = datetime.fromtimestamp(exe_file.stat().st_mtime)
                        
                        # 更新版本信息（如果还没有）
                        if version in version_dict and not version_dict[version]['available']:
                            version_dict[version]['available'] = True
                            version_dict[version]['path'] = str(exe_file)
                            version_dict[version]['size'] = f"{file_size:.2f} MB"
                            version_dict[version]['date'] = mtime.strftime("%Y-%m-%d %H:%M")
                            version_dict[version]['name'] = exe_file.name
                        elif version not in version_dict:
                            # 如果不在版本历史中，添加新条目
                            version_dict[version] = {
                                'version': version,
                                'name': exe_file.name,
                                'available': True,
                                'path': str(exe_file),
                                'size': f"{file_size:.2f} MB",
                                'date': mtime.strftime("%Y-%m-%d %H:%M")
                            }
            
            # 转换为列表并按版本号排序
            all_versions = list(version_dict.values())
            all_versions.sort(key=lambda x: x['version'], reverse=True)
            return all_versions
        except Exception as e:
            print(f"获取EXE版本列表失败：{e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _fetch_remote_versions(self):
        """通过 Gitee Raw URL 获取远程版本列表（零 subprocess，零弹窗）"""
        try:
            req = Request(REMOTE_VERSIONS_URL)
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urlopen(req, timeout=10)
            versions = json.loads(resp.read().decode('utf-8'))
            return versions
        except HTTPError as e:
            print(f"远程版本获取失败 (HTTP {e.code}): {e.reason}")
            return []
        except URLError as e:
            print(f"远程版本获取失败 (网络错误): {e.reason}")
            return []
        except Exception as e:
            print(f"远程版本获取失败: {e}")
            return []

    def _get_current_remote_version(self):
        """获取当前版本对应的远程版本信息"""
        try:
            current_version = self._get_local_version_string()
            if not current_version:
                return None
            versions = self._fetch_remote_versions()
            for v in versions:
                if v.get('version') == current_version or v.get('name', '').replace('.exe', '') == f"云集智能音乐创意台-v{current_version}":
                    return v
            return None
        except Exception:
            return None

    def _get_local_version_string(self):
        """从 EXE 文件名获取当前版本号"""
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
        """加载版本列表"""
        if self._versions_loaded and not force:
            return
        self._versions_loaded = True
        
        scroll_area = self.versions_container.parent()
        if scroll_area:
            scroll_area.setVisible(False)
        
        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.current_mode == "exe":
            self._load_exe_versions()
        else:
            self._load_remote_versions()
        
        if scroll_area:
            scroll_area.setVisible(True)
    
    def _show_git_not_available(self):
        """显示Git未安装提示"""
        self.current_mode_label.setText("远程版本")
        
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.setSpacing(15)
        
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(icon_label)
        
        title_label = QLabel("Git 未安装")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FF9800;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Git模式需要安装Git才能查看源代码版本历史。\n\n"
            "Git是一个免费的开源版本控制系统。"
        )
        desc_label.setStyleSheet("color: #AAAAAA; font-size: 13px; line-height: 1.6;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        download_btn = QPushButton("📥 下载Git")
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        download_btn.clicked.connect(self._open_git_download)
        info_layout.addWidget(download_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.versions_layout.addWidget(info_widget)
    
    def _show_no_git_repo(self):
        """显示无法获取远程版本提示"""
        self.current_mode_label.setText("远程版本")
        
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.setSpacing(15)
        
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(icon_label)
        
        title_label = QLabel("不是Git仓库")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FF9800;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(title_label)
        
        desc_label = QLabel(
            "当前目录不是Git仓库，无法查看源代码版本历史。\n\n"
            "请切换到包含 .git 文件夹的目录，或克隆项目仓库。"
        )
        desc_label.setStyleSheet("color: #AAAAAA; font-size: 13px; line-height: 1.6;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        self.versions_layout.addWidget(info_widget)
    
    def _open_git_download(self):
        """打开Git下载页面"""
        from git_detector import GitDetector
        GitDetector.open_git_download()
    
    def _load_exe_versions(self):
        """加载EXE版本列表"""
        self.current_mode_label.setText("EXE 模式")
        
        current = self._get_current_exe_version()
        if current:
            self.current_info_label.setText(
                f"版本: v{current['version']} | 文件: {current['name']} | 大小: {current['size']}"
            )
        else:
            self.current_info_label.setText("⚠️ 无法获取当前版本信息")
        
        versions = self._get_available_exe_versions()
        
        if not versions:
            no_version_label = QLabel("未找到EXE版本文件")
            no_version_label.setStyleSheet("color: #666666; padding: 20px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return
        
        current_version = current['version'] if current else None
        
        # 初始化列表
        self.exe_version_items = []
        
        for version in versions:
            is_current = version['version'] == current_version
            self._create_exe_version_item(version, is_current)
    
    def _create_exe_version_item(self, version, is_current):
        """创建EXE版本项-卡片式设计"""
        changes = self._get_version_changes(version['name'])
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
        
        if is_available and version.get('size'):
            size_label = QLabel(version['size'])
            size_label.setFont(QFont("Consolas", 9))
            size_label.setStyleSheet("color: #555555; border: none; background: transparent;")
            header.addWidget(size_label)
        elif not is_available:
            status_label = QLabel("未提供")
            status_label.setFont(QFont("Microsoft YaHei", 9))
            status_label.setStyleSheet("color: #444444; border: none; background: transparent;")
            header.addWidget(status_label)
        
        if is_current:
            current_tag = QLabel("● 当前版本")
            current_tag.setFont(QFont("Microsoft YaHei", 9))
            current_tag.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
            header.addWidget(current_tag)
        else:
            toggle_btn = QPushButton("详情" if not is_expanded else "收起")
            toggle_btn.setFixedWidth(50)
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #666666;
                    border: none;
                    padding: 2px 6px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: #AAAAAA;
                }
            """)
            header.addWidget(toggle_btn)
            
            if is_available:
                switch_btn = QPushButton("切换")
                switch_btn.setFixedWidth(55)
                switch_btn.clicked.connect(lambda checked, v=version: self._launch_exe_version(v))
                switch_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1e1e1e;
                        border: 1px solid #2a2a2a;
                        border-radius: 4px;
                        padding: 3px 10px;
                        font-size: 11px;
                        color: #AAAAAA;
                    }
                    QPushButton:hover {
                        background-color: #2a2a2a;
                        border-color: #3a3a3a;
                        color: #FFFFFF;
                    }
                """)
                header.addWidget(switch_btn)
        
        layout.addLayout(header)
        
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
        layout.addWidget(detail_widget)
        
        if not is_current:
            def toggle_detail(checked=False):
                is_visible = not detail_widget.isVisible()
                detail_widget.setVisible(is_visible)
                toggle_btn.setText("收起" if is_visible else "详情")
            toggle_btn.clicked.connect(toggle_detail)
        
        if not hasattr(self, 'exe_version_items'):
            self.exe_version_items = []
        self.exe_version_items.append({
            'expanded': is_expanded,
            'detail_widget': detail_widget,
            'toggle_btn': toggle_btn if not is_current else None
        })
        
        self.versions_layout.addWidget(card)
    
    def _launch_exe_version(self, version):
        """启动EXE版本"""
        reply = QMessageBox.question(
            self,
            "确认启动",
            f"确定要启动版本 v{version['version']} 吗？\n\n"
            f"文件: {version['name']}\n"
            f"大小: {version['size']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import subprocess
                import os
                
                # 启动新的EXE（彻底隐藏窗口，使用DETACHED_PROCESS避免任何窗口闪烁）
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                creation_flags = subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, 'DETACHED_PROCESS'):
                    creation_flags |= subprocess.DETACHED_PROCESS
                if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP'):
                    creation_flags |= subprocess.CREATE_NEW_PROCESS_GROUP
                subprocess.Popen(
                    [version['path']],
                    cwd=os.path.dirname(version['path']),
                    startupinfo=si,
                    creationflags=creation_flags,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True
                )
                
                # 关闭当前程序
                QMessageBox.information(
                    self,
                    "启动成功",
                    f"已启动版本 v{version['version']}\n\n当前程序将退出。",
                    QMessageBox.StandardButton.Ok
                )
                
                QApplication.quit()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动版本失败:\n{str(e)}")
    
    def _load_remote_versions(self):
        """加载远程版本列表（Gitee API，零 subprocess）"""
        self.current_mode_label.setText("远程版本")
        
        current = self._get_current_remote_version()
        if current:
            self.current_info_label.setText(
                f"版本: v{current.get('version', '?')} | {current.get('message', '')} | {current.get('date', '')}"
            )
        else:
            local_ver = self._get_local_version_string()
            if local_ver:
                self.current_info_label.setText(f"当前版本: v{local_ver}")
            else:
                self.current_info_label.setText("⚠️ 无法获取当前版本信息")
        
        versions = self._fetch_remote_versions()
        
        if not versions:
            no_version_label = QLabel("未找到远程版本信息\n\n请检查网络连接")
            no_version_label.setStyleSheet("color: #666666; padding: 20px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return
        
        current_version = current.get('version') if current else None
        
        self.git_version_items = []
        
        for version in versions:
            is_current = version.get('version') == current_version
            self._create_remote_version_item(version, is_current)
    
    def _toggle_expand_all(self, checked):
        """全部展开/收起"""
        self.expand_all_btn.setText("全部收起" if checked else "全部展开")
        
        if hasattr(self, 'exe_version_items'):
            for item in self.exe_version_items:
                try:
                    item['expanded'] = checked
                    if item.get('detail_widget'):
                        item['detail_widget'].setVisible(checked)
                    if item.get('toggle_btn'):
                        item['toggle_btn'].setText("收起" if checked else "详情")
                except Exception as e:
                    print(f"更新EXE版本项状态失败: {e}")
        
        if hasattr(self, 'git_version_items'):
            for item in self.git_version_items:
                try:
                    item['expanded'] = checked
                    if item.get('detail_widget'):
                        item['detail_widget'].setVisible(checked)
                    if item.get('toggle_btn'):
                        item['toggle_btn'].setText("收起" if checked else "详情")
                except Exception as e:
                    print(f"更新Git版本项状态失败: {e}")
    
    def _create_remote_version_item(self, version, is_current):
        """创建远程版本项-卡片式设计"""
        card = QFrame()
        card.setObjectName("remoteVersionCard")
        if is_current:
            card.setStyleSheet("""
                #remoteVersionCard {
                    background-color: #162016;
                    border: 1px solid #1f3a1f;
                    border-radius: 8px;
                }
                #remoteVersionCard:hover {
                    background-color: #1a2a1a;
                    border-color: #2a4a2a;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)
        else:
            card.setStyleSheet("""
                #remoteVersionCard {
                    background-color: #161616;
                    border: 1px solid #222222;
                    border-radius: 8px;
                }
                #remoteVersionCard:hover {
                    background-color: #1c1c1c;
                    border-color: #333333;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)
        
        main_layout = QVBoxLayout(card)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(16, 12, 16, 12)
        
        changes = version.get('changes', [])
        version_str = version.get('version', '?')
        date_str = version.get('date', '')
        
        header = QHBoxLayout()
        header.setSpacing(10)
        
        ver_label = QLabel(f"v{version_str}")
        ver_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        if is_current:
            ver_label.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
        else:
            ver_label.setStyleSheet("color: #888888; border: none; background: transparent;")
        header.addWidget(ver_label)
        
        if date_str:
            date_label = QLabel(date_str)
            date_label.setFont(QFont("Consolas", 9))
            date_label.setStyleSheet("color: #555555; border: none; background: transparent;")
            header.addWidget(date_label)
        
        header.addStretch()
        
        if changes:
            toggle_btn = QPushButton("详情")
            toggle_btn.setFixedWidth(50)
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #666666;
                    border: none;
                    padding: 2px 6px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: #AAAAAA;
                }
            """)
            header.addWidget(toggle_btn)
        
        if is_current:
            current_tag = QLabel("● 当前版本")
            current_tag.setFont(QFont("Microsoft YaHei", 9))
            current_tag.setStyleSheet("color: #4CAF50; border: none; background: transparent;")
            header.addWidget(current_tag)
        else:
            download_url = version.get('download_url', '')
            if download_url:
                download_btn = QPushButton("下载")
                download_btn.setFixedWidth(55)
                download_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1e1e1e;
                        border: 1px solid #2a2a2a;
                        border-radius: 4px;
                        padding: 3px 10px;
                        font-size: 11px;
                        color: #AAAAAA;
                    }
                    QPushButton:hover {
                        background-color: #2a2a2a;
                        border-color: #3a3a3a;
                        color: #FFFFFF;
                    }
                """)
                download_btn.clicked.connect(lambda checked, url=download_url: self._download_version(url))
                header.addWidget(download_btn)
        
        main_layout.addLayout(header)
        
        message = version.get('message', '')
        if message:
            message_label = QLabel(message)
            message_label.setFont(QFont("Microsoft YaHei", 9))
            message_label.setStyleSheet("color: #AAAAAA; border: none; background: transparent;")
            message_label.setWordWrap(True)
            main_layout.addWidget(message_label)
        
        if changes:
            detail_widget = QWidget()
            detail_widget.setStyleSheet("border: none; background: transparent;")
            detail_layout = QVBoxLayout(detail_widget)
            detail_layout.setSpacing(2)
            detail_layout.setContentsMargins(0, 4, 0, 0)
            
            for change in changes:
                line_label = QLabel(f"· {change}")
                line_label.setFont(QFont("Microsoft YaHei", 9))
                line_label.setStyleSheet("color: #777777; border: none; background: transparent;")
                line_label.setWordWrap(True)
                detail_layout.addWidget(line_label)
            
            detail_widget.setVisible(False)
            main_layout.addWidget(detail_widget)
            
            def toggle_detail(checked=False, dw=detail_widget, tb=toggle_btn):
                is_visible = not dw.isVisible()
                dw.setVisible(is_visible)
                tb.setText("收起" if is_visible else "详情")
            toggle_btn.clicked.connect(toggle_detail)
        
        if not hasattr(self, 'git_version_items'):
            self.git_version_items = []
        self.git_version_items.append({
            'expanded': False,
            'detail_widget': detail_widget if changes else None,
            'toggle_btn': toggle_btn if changes else None
        })
        
        self.versions_layout.addWidget(card)
    
    def _download_version(self, url):
        """下载指定版本"""
        import webbrowser
        webbrowser.open(url)
    

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
        
        # 初始化验证相关的属性
        self.last_verify_time = ""
        self.last_verify_result = None
        
        self._setup_ui()
        self._update_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 顶部标题栏
        top_bar = QHBoxLayout()
        
        title_label = QLabel("模型管理器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        # 验证结果标签
        self.verify_result_label = QLabel("")
        self.verify_result_label.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        top_bar.addWidget(self.verify_result_label)
        
        # 验证时间标签
        self.verify_time_label = QLabel("")
        self.verify_time_label.setStyleSheet("font-size: 11px; color: #666666; margin-left: 10px;")
        top_bar.addWidget(self.verify_time_label)
        
        # 下载源设置
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
        
        # 添加下载源选项
        download_sources = {
            "auto": "自动检测",
            "huggingface": "HuggingFace",
            "modelscope": "ModelScope",
            "huggingface-cn": "HuggingFace (国内镜像)"
        }
        for source_key, source_name in download_sources.items():
            self.download_source_combo.addItem(source_name, source_key)
        
        # 设置当前选中的下载源
        if hasattr(self.main_window, 'selected_download_source'):
            for i in range(self.download_source_combo.count()):
                if self.download_source_combo.itemData(i) == self.main_window.selected_download_source:
                    self.download_source_combo.setCurrentIndex(i)
                    break
        
        self.download_source_combo.currentIndexChanged.connect(self._on_download_source_changed)
        top_bar.addWidget(self.download_source_combo)
        
        # 验证按钮
        self.btn_verify_all = QPushButton("验证安装")
        self.btn_verify_all.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
        """)
        self.btn_verify_all.clicked.connect(self._verify_all_models)
        top_bar.addWidget(self.btn_verify_all)
        
        if not self.as_widget:
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(self.accept)
            close_btn.setMinimumWidth(80)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    color: #F0F0F0;
                }
                QPushButton:hover {
                    background-color: #424242;
                }
            """)
            top_bar.addWidget(close_btn)
        
        layout.addLayout(top_bar)
        
        # 模型列表滚动区域
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
        """下载源改变"""
        if self.main_window:
            source_key = self.download_source_combo.itemData(index)
            self.main_window.selected_download_source = source_key
            if hasattr(self.main_window, '_on_download_source_changed'):
                self.main_window._on_download_source_changed(index)
    
    def _verify_all_models(self):
        """验证所有模型"""
        if self.main_window and hasattr(self.main_window, '_verify_all_models'):
            self.main_window._verify_all_models()
            # 使用定时器更新UI
            QTimer.singleShot(100, self._update_ui)
    
    def _update_ui(self):
        """更新UI - 表格样式"""
        if not self.main_window:
            return
        
        # 清空现有内容
        while self.models_layout.count() > 0:
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 按分类分组模型
        categories = {
            "main": {"name": "📦 主模型", "models": []},
            "lm": {"name": "📝 LM 语言模型", "models": []},
            "dit": {"name": "🎨 DiT 扩散模型", "models": []}
        }
        
        for model in self.main_window.model_list:
            cat = model.get("category", "dit")
            if cat in categories:
                categories[cat]["models"].append(model)
        
        # 添加各分类
        for cat_id, cat_info in categories.items():
            if not cat_info["models"]:
                continue
            
            # 分类标题 - 简约设计（无边框）
            cat_label = QLabel(cat_info["name"])
            cat_label.setStyleSheet("font-weight: bold; color: #E53935; font-size: 13px; padding: 8px 0;")
            self.models_layout.addWidget(cat_label)
            
            # 表格标题行
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
            
            # 名称列
            name_header = QLabel("模型名称")
            name_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 200px;")
            header_layout.addWidget(name_header)
            
            # 状态列
            status_header = QLabel("状态")
            status_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 80px;")
            header_layout.addWidget(status_header)
            
            # 描述列
            desc_header = QLabel("描述")
            desc_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")
            header_layout.addWidget(desc_header, 1)
            
            # 操作列
            action_header = QLabel("操作")
            action_header.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; min-width: 100px;")
            header_layout.addWidget(action_header)
            
            self.models_layout.addWidget(header_frame)
            
            # 模型行
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
                
                model_item_layout = QHBoxLayout(model_item)
                model_item_layout.setContentsMargins(8, 6, 8, 6)
                model_item_layout.setSpacing(10)
                
                # 名称列
                name_label = QLabel(model["display_name"])
                name_label.setStyleSheet("color: #FFFFFF; font-size: 12px; min-width: 200px;")
                model_item_layout.addWidget(name_label)
                
                # 状态列
                status_label = QLabel("✓ 已安装" if model["exists"] else "✗ 未安装")
                status_label.setStyleSheet(f"color: {'#4CAF50' if model['exists'] else '#F44336'}; font-size: 11px; min-width: 80px;")
                model_item_layout.addWidget(status_label)
                
                # 描述列
                desc_label = QLabel(model["description"])
                desc_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
                model_item_layout.addWidget(desc_label, 1)
                
                # 操作按钮
                btn_layout = QHBoxLayout()
                btn_layout.setSpacing(4)
                
                # 检查是否是当前正在下载的模型
                is_downloading = self.main_window.is_downloading and self.main_window.current_operation_model == model["name"]
                
                if is_downloading:
                    # 正在下载的模型：暂停按钮
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
                    # 已安装的模型：删除按钮
                    delete_btn = QPushButton("删除")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #C62828;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 11px;
                        }
                        QPushButton:hover {
                            background-color: #B71C1C;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, m=model["name"]: self._delete_model(m))
                    btn_layout.addWidget(delete_btn)
                else:
                    # 未安装的模型：下载按钮
                    download_btn = QPushButton("下载")
                    download_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #1565C0;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 11px;
                        }
                        QPushButton:hover {
                            background-color: #1976D2;
                        }
                    """)
                    download_btn.clicked.connect(lambda checked, m=model["name"]: self._download_model(m))
                    btn_layout.addWidget(download_btn)
                
                model_item_layout.addLayout(btn_layout)
                self.models_layout.addWidget(model_item)
            
            # 分类间距
            if cat_id != list(categories.keys())[-1]:
                spacer = QWidget()
                spacer.setMinimumHeight(10)
                self.models_layout.addWidget(spacer)
    
    def _download_model(self, model_name):
        """下载模型"""
        if self.main_window and hasattr(self.main_window, '_download_model'):
            self.main_window._download_model(model_name)
            # 使用定时器更新UI
            QTimer.singleShot(100, self._update_ui)
    
    def _delete_model(self, model_name):
        """删除模型"""
        if self.main_window and hasattr(self.main_window, '_delete_model'):
            self.main_window._delete_model(model_name)
            # 使用定时器更新UI
            QTimer.singleShot(100, self._update_ui)


# 保持向后兼容的别名
VersionManagerDialog = HybridVersionManagerDialog
