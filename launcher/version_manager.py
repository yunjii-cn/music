"""
版本管理器模块 - 简约风格的全屏版本管理器
提供基于 Git 的版本选择功能
"""

import subprocess
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QWidget, QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from subprocess import SW_HIDE, CREATE_NO_WINDOW


class VersionManagerDialog(QDialog):
    """简约风格的版本管理器 - 全屏显示"""
    
    def __init__(self, parent=None, base_dir=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.setWindowTitle("版本管理器")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0D0D;
            }
        """)
        
        self._setup_ui()
        self._load_versions()
    
    def _setup_ui(self):
        """设置简约的 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部标题栏
        top_bar = QHBoxLayout()
        
        title_label = QLabel("版本管理器")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_versions)
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
        
        log_btn = QPushButton("📝 日志")
        log_btn.clicked.connect(self._view_full_log)
        log_btn.setMinimumWidth(80)
        log_btn.setStyleSheet("""
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
                border-color: #1976D2;
            }
        """)
        top_bar.addWidget(log_btn)
        
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
        current_layout = QHBoxLayout(current_frame)
        current_layout.setSpacing(15)
        
        current_label = QLabel("当前:")
        current_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        current_label.setStyleSheet("color: #888888;")
        current_layout.addWidget(current_label)
        
        self.current_hash_label = QLabel("")
        self.current_hash_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.current_hash_label.setStyleSheet("color: #E53935;")
        current_layout.addWidget(self.current_hash_label)
        
        self.current_message_label = QLabel("")
        self.current_message_label.setFont(QFont("Microsoft YaHei", 11))
        self.current_message_label.setStyleSheet("color: #F0F0F0;")
        current_layout.addWidget(self.current_message_label, 1)
        
        self.current_date_label = QLabel("")
        self.current_date_label.setFont(QFont("Consolas", 10))
        self.current_date_label.setStyleSheet("color: #666666;")
        current_layout.addWidget(self.current_date_label)
        
        layout.addWidget(current_frame)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #333333;")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)
        
        # 版本列表标题
        list_label = QLabel("历史版本")
        list_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
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
    
    def _get_current_version(self):
        """获取当前版本信息"""
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
            print(f"获取当前版本失败：{e}")
            return None
    
    def _get_available_versions(self, limit=30):
        """获取可用版本列表"""
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
            print(f"获取版本列表失败：{e}")
            return []
    
    def _load_versions(self):
        """加载版本列表"""
        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        current = self._get_current_version()
        if current:
            self.current_hash_label.setText(current['hash'])
            self.current_message_label.setText(current['message'])
            self.current_date_label.setText(current['date'])
        else:
            self.current_hash_label.setText("")
            self.current_message_label.setText("⚠️ 无法获取当前版本")
            self.current_date_label.setText("")
        
        versions = self._get_available_versions()
        
        if not versions:
            no_version_label = QLabel("未找到版本信息")
            no_version_label.setStyleSheet("color: #666666; padding: 30px;")
            no_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.versions_layout.addWidget(no_version_label)
            return
        
        current_hash = current['hash'] if current else None
        
        for i, version in enumerate(versions):
            is_current = version['hash'] == current_hash
            self._create_version_item(version, is_current)
    
    def _create_version_item(self, version, is_current):
        """创建单个版本项 - 简约样式"""
        frame = QFrame()
        if is_current:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #1B5E20;
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
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
                    border-radius: 4px;
                    padding: 10px;
                }
                QFrame:hover {
                    border: 1px solid #555555;
                    background-color: #252525;
                }
            """)
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # 版本号
        hash_label = QLabel(version['hash'])
        hash_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        if is_current:
            hash_label.setStyleSheet("color: #4CAF50; min-width: 60px;")
        else:
            hash_label.setStyleSheet("color: #E53935; min-width: 60px;")
        layout.addWidget(hash_label)
        
        # 日期
        date_label = QLabel(version['date'])
        date_label.setFont(QFont("Consolas", 9))
        date_label.setStyleSheet("color: #666666; min-width: 120px;")
        layout.addWidget(date_label)
        
        # 消息
        message_label = QLabel(version['message'])
        message_label.setFont(QFont("Microsoft YaHei", 10))
        message_label.setStyleSheet("color: #F0F0F0;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label, 1)
        
        # 当前标记
        if is_current:
            current_tag = QLabel("当前")
            current_tag.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
            current_tag.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(current_tag)
        else:
            # 预览按钮
            preview_btn = QPushButton("预览")
            preview_btn.setMinimumWidth(70)
            preview_btn.clicked.connect(lambda checked, v=version: self._preview_version(v))
            preview_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #424242;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: #AAAAAA;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                    border-color: #1976D2;
                    color: white;
                }
            """)
            layout.addWidget(preview_btn)
            
            # 切换按钮
            switch_btn = QPushButton("切换")
            switch_btn.setMinimumWidth(70)
            switch_btn.clicked.connect(lambda checked, v=version: self._switch_version(v['hash']))
            switch_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #43A047;
                    border-color: #43A047;
                }
            """)
            layout.addWidget(switch_btn)
        
        self.versions_layout.addWidget(frame)
    
    def _preview_version(self, version):
        """预览版本详情"""
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
            detail_dialog.setMinimumSize(600, 400)
            detail_dialog.setStyleSheet("QDialog { background-color: #0D0D0D; }")
            
            layout = QVBoxLayout(detail_dialog)
            
            header = QHBoxLayout()
            title = QLabel(f"{version['hash']}")
            title.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
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
                    padding: 8px 16px;
                    font-size: 12px;
                    color: #F0F0F0;
                }
                QPushButton:hover {
                    background-color: #424242;
                }
            """)
            header.addWidget(close_btn)
            
            layout.addLayout(header)
            
            date = QLabel(f"{version['date']}")
            date.setStyleSheet("color: #666666; padding: 5px 0;")
            layout.addWidget(date)
            
            desc_text = QTextEdit()
            desc_text.setReadOnly(True)
            desc_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 12px;
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                    color: #F0F0F0;
                }
            """)
            desc_text.setPlainText(result.stdout.strip() if result.stdout else "无详细说明")
            layout.addWidget(desc_text, stretch=1)
            
            detail_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取版本详情失败:\n{str(e)}")
    
    def _switch_version(self, commit_hash):
        """切换版本"""
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
                from PyQt6.QtWidgets import QApplication
                import os
                import shutil
                
                # 显示切换中提示
                switching_dialog = QDialog(self)
                switching_dialog.setWindowTitle("正在切换版本")
                switching_dialog.setMinimumSize(350, 120)
                switching_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
                switching_dialog.setStyleSheet("QDialog { background-color: #0D0D0D; }")
                
                dialog_layout = QVBoxLayout(switching_dialog)
                
                label = QLabel(f"正在切换到 {commit_hash}...")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("color: #F0F0F0; font-size: 13px; padding: 20px;")
                dialog_layout.addWidget(label)
                
                switching_dialog.show()
                QApplication.processEvents()
                
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
                    ['git', 'checkout', commit_hash],
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
                
                switching_dialog.accept()
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
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换版本失败:\n{str(e)}")
    
    def _view_full_log(self):
        """查看完整日志"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            result = subprocess.run(
                ['git', 'log', '--oneline', '-100'],
                capture_output=True, text=True,
                cwd=self.base_dir,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            log_dialog = QDialog(self)
            log_dialog.setWindowTitle("版本历史")
            log_dialog.setMinimumSize(900, 700)
            log_dialog.setStyleSheet("QDialog { background-color: #0D0D0D; }")
            
            layout = QVBoxLayout(log_dialog)
            
            header = QHBoxLayout()
            title = QLabel("版本历史 (最近 100 条)")
            title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            title.setStyleSheet("color: #E53935;")
            header.addWidget(title)
            
            header.addStretch()
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(log_dialog.accept)
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
                }
            """)
            header.addWidget(close_btn)
            
            layout.addLayout(header)
            
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 12px;
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                    color: #F0F0F0;
                }
            """)
            log_text.setPlainText(result.stdout)
            layout.addWidget(log_text, stretch=1)
            
            log_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取日志失败:\n{str(e)}")
