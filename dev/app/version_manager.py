"""
版本管理器模块 - 混合模式版本管理器
支持Git源代码版本管理和EXE文件版本管理
"""

import subprocess
import sys
import os
import re
from datetime import datetime
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QWidget, QMessageBox, QFrame, QApplication,
    QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from subprocess import SW_HIDE, CREATE_NO_WINDOW
from git_detector import GitDetector, GitInstallDialog


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
        
        # 检测运行模式
        self.is_exe_mode = hasattr(sys, 'frozen')
        self.has_git_repo = self._check_git_repo()
        self.current_mode = "exe" if self.is_exe_mode else "git"
        
        self._setup_ui()
        self._load_version_history()
        self._load_versions()
    
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
        return []
    
    def _check_git_repo(self):
        """检查是否是Git仓库"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                capture_output=True, text=True,
                cwd=self.base_dir, timeout=3,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            return result.returncode == 0 and result.stdout.strip() == 'true'
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
        
        # 模式选择（只在有Git仓库时显示）
        if self.has_git_repo:
            mode_label = QLabel("模式:")
            mode_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
            top_bar.addWidget(mode_label)
            
            self.mode_combo = QComboBox()
            self.mode_combo.addItem("📦 EXE 版本", "exe")
            self.mode_combo.addItem("🔧 Git 源代码", "git")
            self.mode_combo.setStyleSheet("""
                QComboBox {
                    background-color: #1A1A1A;
                    color: #F0F0F0;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    min-width: 120px;
                }
                QComboBox:hover {
                    border-color: #444444;
                }
            """)
            self.mode_combo.setCurrentIndex(0 if self.current_mode == "exe" else 1)
            self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
            top_bar.addWidget(self.mode_combo)
        
        top_bar.addStretch()
        
        # 全部展开/收起开关（只在Git模式时显示）
        self.expand_all_btn = QPushButton("📖 全部展开")
        self.expand_all_btn.setCheckable(True)
        self.expand_all_btn.setChecked(True)
        self.expand_all_btn.clicked.connect(self._toggle_expand_all)
        self.expand_all_btn.setMinimumWidth(90)
        self.expand_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11px;
                color: #F0F0F0;
            }
            QPushButton:checked {
                background-color: #1565C0;
                border-color: #1976D2;
            }
            QPushButton:hover {
                border-color: #555555;
            }
        """)
        top_bar.addWidget(self.expand_all_btn)
        
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
                background-color: #1565C0;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
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
        self.versions_layout = QVBoxLayout(self.versions_container)
        self.versions_layout.setSpacing(6)
        self.versions_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(self.versions_container)
        layout.addWidget(scroll_area, stretch=1)
    
    def _on_mode_changed(self, index):
        """模式切换"""
        self.current_mode = self.mode_combo.itemData(index)
        self._load_versions()
    
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
    
    def _get_current_git_version(self):
        """获取当前Git版本信息"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%h|%s|%ai'],
                capture_output=True, text=True,
                cwd=self.base_dir, timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.split('|')
                if len(parts) >= 3:
                    return {
                        'hash': parts[0],
                        'message': parts[1],
                        'date': parts[2][:16]
                    }
            
            return None
        except Exception as e:
            print(f"获取当前Git版本失败：{e}")
            return None
    
    def _get_available_git_versions(self, limit=30):
        """获取可用Git版本列表"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'log', f'-n {limit}', '--pretty=format:%h|%s|%ai'],
                capture_output=True, text=True,
                cwd=self.base_dir, timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            versions = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            versions.append({
                                'hash': parts[0],
                                'message': parts[1],
                                'date': parts[2][:16]
                            })
            
            return versions
        except Exception as e:
            print(f"获取Git版本列表失败：{e}")
            return []
    
    def _load_versions(self):
        """加载版本列表"""
        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 检查Git是否可用
        git_available = GitDetector.is_git_available()
        
        # 根据当前模式直接加载，不强制切换
        if self.current_mode == "exe":
            self._load_exe_versions()
        else:
            # 检查Git仓库和Git是否可用
            if not self.has_git_repo or not git_available:
                # Git模式但没有Git，引导安装
                reply = QMessageBox.question(
                    self,
                    "需要Git",
                    "Git模式需要安装Git才能使用。\n\n"
                    "是否打开Git安装引导？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    dialog = GitInstallDialog(self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 用户安装了Git，重新加载
                        self.has_git_repo = self._check_git_repo()
                        self._load_versions()
                        return
                # 切换回EXE模式
                self.current_mode = "exe"
                if hasattr(self, 'mode_combo'):
                    self.mode_combo.blockSignals(True)
                    self.mode_combo.setCurrentIndex(0)
                    self.mode_combo.blockSignals(False)
                self._load_exe_versions()
            else:
                self._load_git_versions()
    
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
        
        for version in versions:
            is_current = version['version'] == current_version
            self._create_exe_version_item(version, is_current)
    
    def _create_exe_version_item(self, version, is_current):
        """创建EXE版本项"""
        # 获取版本修改内容
        changes = self._get_version_changes(version['name'])
        is_available = version.get('available', False)
        
        frame = QFrame()
        if is_current:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #1B5E20;
                    border: 1px solid #4CAF50;
                    border-radius: 5px;
                    padding: 10px;
                }
                QFrame:hover {
                    background-color: #2E7D32;
                }
            """)
        elif not is_available:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-radius: 5px;
                    padding: 10px;
                }
                QFrame:hover {
                    border: 1px solid #555555;
                    background-color: #252525;
                }
            """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # 顶部：版本信息行
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        # 版本号
        version_label = QLabel(f"v{version['version']}")
        version_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        if is_current:
            version_label.setStyleSheet("color: #4CAF50; min-width: 120px;")
        elif not is_available:
            version_label.setStyleSheet("color: #666666; min-width: 120px;")
        else:
            version_label.setStyleSheet("color: #E53935; min-width: 120px;")
        top_layout.addWidget(version_label)
        
        # 日期
        if version.get('date'):
            date_label = QLabel(version['date'])
            date_label.setFont(QFont("Consolas", 9))
            date_label.setStyleSheet("color: #666666; min-width: 130px;")
            top_layout.addWidget(date_label)
        else:
            # 如果没有日期，占位
            spacer = QLabel("")
            spacer.setStyleSheet("min-width: 130px;")
            top_layout.addWidget(spacer)
        
        # 文件名
        name_label = QLabel(version['name'])
        name_label.setFont(QFont("Microsoft YaHei", 9))
        if not is_available:
            name_label.setStyleSheet("color: #666666;")
        else:
            name_label.setStyleSheet("color: #F0F0F0;")
        name_label.setWordWrap(True)
        top_layout.addWidget(name_label, 1)
        
        # 大小或状态标签
        if is_available and version.get('size'):
            size_label = QLabel(version['size'])
            size_label.setFont(QFont("Consolas", 9))
            size_label.setStyleSheet("color: #888888; min-width: 70px;")
            top_layout.addWidget(size_label)
        elif not is_available:
            status_label = QLabel("未提供")
            status_label.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
            status_label.setStyleSheet("""
                QLabel {
                    background-color: #424242;
                    color: #9E9E9E;
                    padding: 3px 8px;
                    border-radius: 3px;
                }
            """)
            top_layout.addWidget(status_label)
        else:
            # 占位
            spacer = QLabel("")
            spacer.setStyleSheet("min-width: 70px;")
            top_layout.addWidget(spacer)
        
        # 当前标记或切换按钮
        if is_current:
            current_tag = QLabel("当前")
            current_tag.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
            current_tag.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                }
            """)
            top_layout.addWidget(current_tag)
        elif is_available:
            # 切换版本按钮
            switch_btn = QPushButton("切换版本")
            switch_btn.setMinimumWidth(75)
            switch_btn.clicked.connect(lambda checked, v=version: self._launch_exe_version(v))
            switch_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    padding: 4px 12px;
                    font-size: 11px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #43A047;
                    border-color: #43A047;
                }
            """)
            top_layout.addWidget(switch_btn)
        
        layout.addLayout(top_layout)
        
        # 底部：版本修改内容（所有版本都显示，如果有）
        if changes:
            changes_layout = QVBoxLayout()
            changes_layout.setSpacing(4)
            changes_layout.setContentsMargins(10, 0, 0, 0)
            
            changes_label = QLabel("📋 修改内容：")
            changes_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            changes_label.setStyleSheet("color: #FF9800;")
            changes_layout.addWidget(changes_label)
            
            for change in changes:
                change_label = QLabel(f"  • {change}")
                change_label.setFont(QFont("Microsoft YaHei", 9))
                change_label.setStyleSheet("color: #AAAAAA;")
                change_label.setWordWrap(True)
                changes_layout.addWidget(change_label)
            
            layout.addLayout(changes_layout)
        
        self.versions_layout.addWidget(frame)
    
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
                
                # 启动新的EXE
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen(
                    [version['path']],
                    cwd=os.path.dirname(version['path']),
                    startupinfo=startupinfo
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
    
    def _load_git_versions(self):
        """加载Git版本列表"""
        self.current_mode_label.setText("Git 模式")
        
        current = self._get_current_git_version()
        if current:
            self.current_info_label.setText(
                f"提交: {current['hash']} | {current['message']} | {current['date']}"
            )
        else:
            self.current_info_label.setText("⚠️ 无法获取当前版本信息")
        
        versions = self._get_available_git_versions()
        
        if not versions:
            no_version_label = QLabel("未找到Git版本信息")
            no_version_label.setStyleSheet("color: #666666; padding: 20px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return
        
        current_hash = current['hash'] if current else None
        
        # 存储所有版本项，用于全部展开/收起
        self.git_version_items = []
        
        for version in versions:
            is_current = version['hash'] == current_hash
            self._create_git_version_item(version, is_current)
    
    def _toggle_expand_all(self, checked):
        """全部展开/收起"""
        if hasattr(self, 'git_version_items'):
            for item in self.git_version_items:
                item['expanded'] = checked
                item['detail_widget'].setVisible(checked)
                item['toggle_btn'].setText("📕 收起" if checked else "📖 展开")
    
    def _create_git_version_item(self, version, is_current):
        """创建Git版本项"""
        # 获取版本详情（提前获取，用于默认展开）
        detail_content = ""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'show', '-s', '--pretty=format:%B', version['hash']],
                capture_output=True, text=True,
                cwd=self.base_dir, timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            detail_content = result.stdout.strip() if result.stdout else ""
        except Exception:
            pass
        
        frame = QFrame()
        if is_current:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #1B5E20;
                    border: 1px solid #4CAF50;
                    border-radius: 5px;
                    padding: 10px;
                }
                QFrame:hover {
                    background-color: #2E7D32;
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-radius: 5px;
                    padding: 10px;
                }
                QFrame:hover {
                    border: 1px solid #555555;
                    background-color: #252525;
                }
            """)
        
        main_layout = QVBoxLayout(frame)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 8, 10, 8)
        
        # 顶部：版本信息行
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        # 提交哈希
        hash_label = QLabel(version['hash'])
        hash_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        if is_current:
            hash_label.setStyleSheet("color: #4CAF50; min-width: 60px;")
        else:
            hash_label.setStyleSheet("color: #E53935; min-width: 60px;")
        top_layout.addWidget(hash_label)
        
        # 日期
        date_label = QLabel(version['date'])
        date_label.setFont(QFont("Consolas", 9))
        date_label.setStyleSheet("color: #666666; min-width: 130px;")
        top_layout.addWidget(date_label)
        
        # 消息
        message_label = QLabel(version['message'])
        message_label.setFont(QFont("Microsoft YaHei", 9))
        message_label.setStyleSheet("color: #F0F0F0;")
        message_label.setWordWrap(True)
        top_layout.addWidget(message_label, 1)
        
        # 当前标记
        if is_current:
            current_tag = QLabel("当前")
            current_tag.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
            current_tag.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                }
            """)
            top_layout.addWidget(current_tag)
        else:
            # 展开/收起按钮 - 使用安全检查
            is_expanded = True
            if hasattr(self, 'expand_all_btn'):
                try:
                    is_expanded = self.expand_all_btn.isChecked()
                except:
                    is_expanded = True
            
            toggle_btn = QPushButton("📕 收起" if is_expanded else "📖 展开")
            toggle_btn.setMinimumWidth(65)
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #424242;
                    border-radius: 3px;
                    padding: 4px 10px;
                    font-size: 11px;
                    color: #AAAAAA;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                    border-color: #1976D2;
                    color: white;
                }
            """)
            top_layout.addWidget(toggle_btn)
            
            # 切换按钮
            switch_btn = QPushButton("切换")
            switch_btn.setMinimumWidth(55)
            switch_btn.clicked.connect(lambda checked, v=version: self._switch_git_version(v['hash']))
            switch_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    padding: 4px 10px;
                    font-size: 11px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #43A047;
                    border-color: #43A047;
                }
            """)
            top_layout.addWidget(switch_btn)
        
        main_layout.addLayout(top_layout)
        
        # 详情区域（默认展开）
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setSpacing(4)
        detail_layout.setContentsMargins(10, 4, 0, 0)
        
        if detail_content:
            changes_label = QLabel("📋 提交详情：")
            changes_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            changes_label.setStyleSheet("color: #FF9800;")
            detail_layout.addWidget(changes_label)
            
            detail_text = QTextEdit()
            detail_text.setReadOnly(True)
            detail_text.setMaximumHeight(150)
            detail_text.setStyleSheet("""
                QTextEdit {
                    background-color: #121212;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Consolas', monospace;
                    font-size: 11px;
                    color: #F0F0F0;
                }
            """)
            detail_text.setPlainText(detail_content)
            detail_layout.addWidget(detail_text)
        
        detail_widget.setVisible(is_expanded)
        main_layout.addWidget(detail_widget)
        
        # 保存引用，用于全部展开/收起
        if not is_current:
            item_ref = {
                'toggle_btn': toggle_btn,
                'detail_widget': detail_widget,
                'expanded': is_expanded
            }
            self.git_version_items.append(item_ref)
            
            # 点击展开/收起按钮的事件
            def toggle_this(checked, item=item_ref):
                item['expanded'] = not item['expanded']
                item['detail_widget'].setVisible(item['expanded'])
                item['toggle_btn'].setText("📕 收起" if item['expanded'] else "📖 展开")
            
            toggle_btn.clicked.connect(toggle_this)
        
        self.versions_layout.addWidget(frame)
    
    def _preview_git_version(self, version):
        """预览Git版本详情"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'show', '-s', '--pretty=format:%B', version['hash']],
                capture_output=True, text=True,
                cwd=self.base_dir, timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            detail_dialog = QDialog(self)
            detail_dialog.setWindowTitle(f"版本详情 - {version['hash']}")
            detail_dialog.setMinimumSize(500, 350)
            detail_dialog.setStyleSheet("QDialog { background-color: #0D0D0D; }")
            
            layout = QVBoxLayout(detail_dialog)
            
            header = QHBoxLayout()
            title = QLabel(f"{version['hash']}")
            title.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            title.setStyleSheet("color: #E53935;")
            header.addWidget(title)
            
            header.addStretch()
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(detail_dialog.accept)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    border: 1px solid #424242;
                    border-radius: 4px;
                    padding: 6px 14px;
                    font-size: 11px;
                    color: #F0F0F0;
                }
                QPushButton:hover {
                    background-color: #424242;
                }
            """)
            header.addWidget(close_btn)
            
            layout.addLayout(header)
            
            date = QLabel(f"{version['date']}")
            date.setStyleSheet("color: #666666; padding: 4px 0;")
            layout.addWidget(date)
            
            desc_text = QTextEdit()
            desc_text.setReadOnly(True)
            desc_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 10px;
                    font-family: 'Consolas', monospace;
                    font-size: 11px;
                    color: #F0F0F0;
                }
            """)
            desc_text.setPlainText(result.stdout.strip() if result.stdout else "无详细说明")
            layout.addWidget(desc_text, stretch=1)
            
            detail_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取版本详情失败:\n{str(e)}")
    
    def _switch_git_version(self, commit_hash):
        """切换Git版本"""
        reply = QMessageBox.question(
            self,
            "确认切换",
            f"确定要切换到版本 {commit_hash} 吗？\n\n"
            f"程序将会自动保存配置并重启。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.switch_thread = GitVersionSwitchThread(self.base_dir, commit_hash, self)
                self.switch_thread.finished.connect(self._on_git_switch_finished)
                self.switch_thread.error_occurred.connect(self._on_git_switch_error)
                
                # 显示切换中提示
                self.switching_dialog = QDialog(self)
                self.switching_dialog.setWindowTitle("正在切换版本")
                self.switching_dialog.setMinimumSize(320, 100)
                self.switching_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
                self.switching_dialog.setStyleSheet("QDialog { background-color: #0D0D0D; }")
                
                dialog_layout = QVBoxLayout(self.switching_dialog)
                
                label = QLabel(f"正在切换到 {commit_hash}...")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("color: #F0F0F0; font-size: 12px; padding: 15px;")
                dialog_layout.addWidget(label)
                
                self.switching_dialog.show()
                QApplication.processEvents()
                
                # 启动线程
                self.switch_thread.start()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动版本切换失败:\n{str(e)}")
    
    def _on_git_switch_finished(self, commit_hash):
        """Git版本切换完成"""
        if hasattr(self, 'switching_dialog'):
            self.switching_dialog.accept()
        
        self.accept()
        
        # 提示重启
        QMessageBox.information(
            self,
            "切换成功",
            f"已成功切换到版本 {commit_hash}\n\n请重新启动程序。",
            QMessageBox.StandardButton.Ok
        )
        
        # 退出当前程序
        QApplication.quit()
    
    def _on_git_switch_error(self, error_message):
        """Git版本切换错误"""
        if hasattr(self, 'switching_dialog'):
            self.switching_dialog.accept()
        
        QMessageBox.critical(self, "错误", f"切换版本失败:\n{error_message}")


class GitVersionSwitchThread(QThread):
    """Git版本切换线程 - 避免UI假死"""
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, base_dir, commit_hash, parent=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.commit_hash = commit_hash
    
    def run(self):
        """执行版本切换"""
        import os
        import shutil
        try:
            # 1. 备份用户数据
            user_dirs = ['config', 'models', 'output', '.env']
            backup_dir = os.path.join(self.base_dir, '.git_backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            for dir_name in user_dirs:
                src = os.path.join(self.base_dir, dir_name)
                dst = os.path.join(backup_dir, dir_name)
                
                if os.path.exists(src):
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # 2. 切换 Git 分支
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'checkout', self.commit_hash],
                capture_output=True, text=True,
                cwd=self.base_dir,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                raise Exception(f"Git checkout 失败:\n{result.stderr}")
            
            # 3. 恢复用户数据
            for dir_name in user_dirs:
                src = os.path.join(backup_dir, dir_name)
                dst = os.path.join(self.base_dir, dir_name)
                
                if os.path.exists(src):
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # 4. 清理备份目录
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            
            self.finished.emit(self.commit_hash)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


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
        
        # 下载源设置
        download_source_label = QLabel("下载源:")
        download_source_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        top_bar.addWidget(download_source_label)
        
        self.download_source_combo = QComboBox()
        self.download_source_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                color: #F0F0F0;
                border: 1px solid #333333;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #444444;
            }
            QComboBox::drop-down {
                border: none;
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
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #333333;
                border-color: #333333;
                color: #666666;
            }
        """)
        self.btn_verify_all.clicked.connect(self._verify_all_models)
        top_bar.addWidget(self.btn_verify_all)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._update_ui)
        refresh_btn.setMinimumWidth(80)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 13px;
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
            close_btn.setMinimumWidth(80)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    border: 1px solid #424242;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-size: 13px;
                    color: #F0F0F0;
                }
                QPushButton:hover {
                    background-color: #424242;
                    border-color: #E53935;
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
        """更新UI - 调用main_window的更新方法"""
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
            
            # 分类标题 - 更简约的设计
            cat_header = QFrame()
            cat_header.setStyleSheet("""
                QFrame {
                    background-color: #252525;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 8px;
                }
            """)
            cat_layout = QHBoxLayout(cat_header)
            cat_layout.setContentsMargins(6, 4, 6, 4)
            
            cat_label = QLabel(cat_info["name"])
            cat_label.setStyleSheet("font-weight: bold; color: #E53935; font-size: 12px;")
            cat_layout.addWidget(cat_label)
            cat_layout.addStretch()
            
            self.models_layout.addWidget(cat_header)
            
            # 模型表格 - 更简约的设计
            for idx, model in enumerate(cat_info["models"]):
                model_item = QFrame()
                is_last = idx == len(cat_info["models"]) - 1
                model_item.setStyleSheet("""
                    QFrame {
                        background-color: #1E1E1E;
                        border: none;
                        border-bottom: 1px solid #2A2A2A;
                        padding: 6px 8px;
                    }
                    QFrame:last {
                        border-bottom: none;
                    }
                """)
                
                model_item_layout = QVBoxLayout(model_item)
                model_item_layout.setSpacing(4)
                model_item_layout.setContentsMargins(8, 6, 8, 6)
                
                # 第一行：名称 + 状态 + 按钮
                row1 = QHBoxLayout()
                
                name_label = QLabel(model["display_name"])
                name_label.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 12px;")
                row1.addWidget(name_label)
                
                row1.addStretch()
                
                # 状态
                status_label = QLabel("✓ 已安装" if model["exists"] else "✗ 未安装")
                status_label.setStyleSheet(f"font-size: 11px; color: {'#4CAF50' if model['exists'] else '#F44336'};")
                row1.addWidget(status_label)
                
                # 按钮区域
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
                            border-radius: 3px;
                            padding: 3px 8px;
                            font-size: 11px;
                            font-weight: normal;
                        }
                        QPushButton:hover {
                            background-color: #FF6F00;
                        }
                        QPushButton:disabled {
                            background-color: #333333;
                            color: #666666;
                        }
                    """)
                    pause_btn.clicked.connect(self.main_window._pause_download)
                    btn_layout.addWidget(pause_btn)
                elif model["exists"]:
                    # 已安装的模型：只保留删除按钮
                    delete_btn = QPushButton("删除")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #C62828;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            padding: 3px 8px;
                            font-size: 11px;
                            font-weight: normal;
                        }
                        QPushButton:hover {
                            background-color: #B71C1C;
                        }
                        QPushButton:disabled {
                            background-color: #333333;
                            color: #666666;
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
                            border-radius: 3px;
                            padding: 3px 10px;
                            font-size: 11px;
                            font-weight: normal;
                        }
                        QPushButton:hover {
                            background-color: #1976D2;
                        }
                        QPushButton:disabled {
                            background-color: #333333;
                            color: #666666;
                        }
                    """)
                    download_btn.clicked.connect(lambda checked, m=model["name"]: self._download_model(m))
                    btn_layout.addWidget(download_btn)
                
                row1.addLayout(btn_layout)
                
                model_item_layout.addLayout(row1)
                
                # 第二行：描述
                desc_label = QLabel(model["description"])
                desc_label.setStyleSheet("font-size: 11px; color: #AAAAAA;")
                model_item_layout.addWidget(desc_label)
                
                # 第三行：详细介绍
                if "info" in model:
                    info_label = QLabel(model["info"])
                    info_label.setStyleSheet("font-size: 10px; color: #888888;")
                    info_label.setWordWrap(True)
                    model_item_layout.addWidget(info_label)
                
                self.models_layout.addWidget(model_item)
            
            # 分类间距
            if cat_id != list(categories.keys())[-1]:
                spacer = QWidget()
                spacer.setMinimumHeight(8)
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
