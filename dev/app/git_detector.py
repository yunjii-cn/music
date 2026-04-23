"""
Git检测和安装引导模块
检测系统是否安装Git，如果没有则提供安装引导
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

if sys.platform == 'win32':
    _HIDDEN_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    _HIDDEN_FLAGS = 0

def _hidden_startupinfo():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si

def hidden_run(*args, **kwargs):
    kwargs.setdefault('startupinfo', _hidden_startupinfo())
    kwargs.setdefault('creationflags', _HIDDEN_FLAGS)
    return subprocess.run(*args, **kwargs)

def hidden_popen(*args, **kwargs):
    kwargs.setdefault('startupinfo', _hidden_startupinfo())
    kwargs.setdefault('creationflags', _HIDDEN_FLAGS)
    return subprocess.Popen(*args, **kwargs)


class GitDetector:
    """Git检测器"""
    
    GIT_DOWNLOAD_URL = "https://git-scm.com/download/win"
    
    @staticmethod
    def is_git_available():
        """检查Git是否可用"""
        try:
            result = hidden_run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def get_git_version():
        """获取Git版本"""
        try:
            result = hidden_run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    @staticmethod
    def open_git_download():
        """打开Git下载页面"""
        try:
            webbrowser.open(GitDetector.GIT_DOWNLOAD_URL)
            return True
        except Exception as e:
            print(f"打开Git下载页面失败：{e}")
            return False


class GitInstallDialog(QDialog):
    """Git安装引导对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("需要安装Git")
        self.setMinimumSize(500, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0D0D;
            }
        """)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 图标/标题
        title_label = QLabel("⚠️ 需要安装Git")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF9800;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel(
            "要使用版本管理功能，需要先安装Git。\n\n"
            "Git是一个免费的开源版本控制系统，可以帮助您：\n"
            "  • 轻松切换到不同的软件版本\n"
            "  • 回滚到之前的版本\n"
            "  • 自动获取最新更新"
        )
        desc_label.setStyleSheet("color: #CCCCCC; font-size: 13px; line-height: 1.6;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Git下载链接
        link_label = QLabel(
            f'<a href="{GitDetector.GIT_DOWNLOAD_URL}" style="color: #1976D2; font-size: 12px;">'
            f'点击这里打开Git官方下载页面 →'
            f'</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(link_label)
        
        layout.addSpacing(20)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        download_btn = QPushButton("📥 下载Git")
        download_btn.setMinimumWidth(140)
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
        download_btn.clicked.connect(self._download_git)
        btn_layout.addWidget(download_btn)
        
        check_btn = QPushButton("🔄 已安装，检测")
        check_btn.setMinimumWidth(140)
        check_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        check_btn.clicked.connect(self._check_git)
        btn_layout.addWidget(check_btn)
        
        skip_btn = QPushButton("暂时跳过")
        skip_btn.setMinimumWidth(100)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: #CCCCCC;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _download_git(self):
        """下载Git"""
        GitDetector.open_git_download()
        QMessageBox.information(
            self,
            "提示",
            "Git下载页面已在浏览器中打开。\n\n"
            "请下载并安装Git后，点击「已安装，检测」按钮。"
        )
    
    def _check_git(self):
        """检测Git"""
        if GitDetector.is_git_available():
            version = GitDetector.get_git_version()
            QMessageBox.information(
                self,
                "检测成功",
                f"✓ Git已安装！\n\n{version}\n\n现在可以使用版本管理功能了。"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "未检测到Git",
                "未检测到Git安装。\n\n"
                "请先安装Git，或点击「暂时跳过」稍后再试。"
            )
