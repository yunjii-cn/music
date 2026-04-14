"""
初始化向导模块
第一次运行时引导用户完成环境配置
"""

import os
import sys
import platform
import psutil
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QWidget,
    QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from git_detector import GitDetector, GitInstallDialog
from git_downloader import ensure_git_available_silent
from python_downloader import ensure_python_312_silent, is_python_312


class InitStep:
    """初始化步骤"""
    ENV_CHECK = "环境检测"
    GIT_CHECK = "Git检测"
    CREATE_DIRS = "创建目录"
    INIT_CONFIG = "初始化配置"
    COMPLETE = "完成"


class InitWorker(QThread):
    """初始化工作线程"""
    
    progress_updated = pyqtSignal(str, int, str)  # 步骤名, 进度, 消息
    step_completed = pyqtSignal(str, bool, str)  # 步骤名, 是否成功, 消息
    finished = pyqtSignal(bool, str)  # 是否成功, 消息
    
    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.config = {}
    
    def run(self):
        """执行初始化"""
        steps = [
            (InitStep.ENV_CHECK, self._check_environment),
            (InitStep.GIT_CHECK, self._check_git),
            (InitStep.CREATE_DIRS, self._create_directories),
            (InitStep.INIT_CONFIG, self._init_config),
        ]
        
        total_steps = len(steps)
        success = True
        message = ""
        
        for i, (step_name, step_func) in enumerate(steps):
            progress = int((i / total_steps) * 100)
            self.progress_updated.emit(step_name, progress, f"正在执行：{step_name}...")
            
            try:
                step_success, step_msg = step_func()
                self.step_completed.emit(step_name, step_success, step_msg)
                
                if not step_success:
                    success = False
                    message = f"{step_name}失败：{step_msg}"
                    break
                
                QThread.msleep(300)  # 模拟工作时间
                
            except Exception as e:
                success = False
                message = f"{step_name}异常：{str(e)}"
                self.step_completed.emit(step_name, False, str(e))
                break
        
        self.progress_updated.emit(InitStep.COMPLETE, 100, "初始化完成！" if success else "初始化失败")
        self.finished.emit(success, message)
    
    def _check_environment(self):
        """检查环境"""
        self.config['system'] = platform.system()
        self.config['system_version'] = platform.version()
        self.config['python_version'] = platform.python_version()
        self.config['cpu_count'] = psutil.cpu_count()
        self.config['memory_total'] = psutil.virtual_memory().total // (1024 ** 3)  # GB
        self.config['memory_available'] = psutil.virtual_memory().available // (1024 ** 3)  # GB
        
        # 检查Python版本是否符合官方要求（3.12.x）
        python_version = self.config['python_version']
        python_major_minor = '.'.join(python_version.split('.')[:2])
        python_ok = python_major_minor == '3.12'
        self.config['python_version_ok'] = python_ok
        
        if python_ok:
            python_status = "✅ 符合官方要求"
        else:
            python_status = f"⚠️ 建议使用Python 3.12（当前：{python_version}）"
        
        msg = (
            f"系统：{self.config['system']} {self.config['system_version']}\n"
            f"Python：{self.config['python_version']} {python_status}\n"
            f"CPU：{self.config['cpu_count']} 核心\n"
            f"内存：{self.config['memory_available']}GB / {self.config['memory_total']}GB"
        )
        
        return True, msg
    
    def _check_git(self):
        """检查Git"""
        if GitDetector.is_git_available():
            version = GitDetector.get_git_version()
            self.config['git_available'] = True
            self.config['git_version'] = version
            return True, f"Git已安装：{version}"
        else:
            self.config['git_available'] = False
            return True, "Git未安装（可选，用于版本管理）"
    
    def _create_directories(self):
        """创建目录结构"""
        dirs = [
            'config',
            'models',
            'output',
            'logs',
            'temp',
        ]
        
        created = []
        for dir_name in dirs:
            dir_path = self.base_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(dir_name)
        
        if created:
            return True, f"创建目录：{', '.join(created)}"
        else:
            return True, "目录已存在"
    
    def _init_config(self):
        """初始化配置"""
        import json
        from datetime import datetime
        
        self.config['initialized'] = True
        self.config['init_time'] = datetime.now().isoformat()
        self.config['version'] = "1.0.0"
        
        config_file = self.base_dir / 'config' / 'init_config.json'
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        return True, f"配置已保存到：{config_file}"


class InitWizardDialog(QDialog):
    """初始化向导对话框"""
    
    def __init__(self, base_dir=None, parent=None):
        super().__init__(parent)
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.worker = None
        
        self.setWindowTitle("初始化向导")
        self.setMinimumSize(700, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0D0D;
            }
        """)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self._setup_ui()
        self._start_init()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("🚀 欢迎使用云集智能音乐创意台")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("首次运行，正在完成初始化配置...")
        subtitle_label.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # 当前步骤
        self.current_step_label = QLabel("准备开始...")
        self.current_step_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.current_step_label.setStyleSheet("color: #4CAF50;")
        self.current_step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_step_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 5px;
                height: 25px;
                text-align: center;
                color: #FFFFFF;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addSpacing(15)
        
        # 步骤列表
        steps_label = QLabel("初始化步骤：")
        steps_label.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: bold;")
        layout.addWidget(steps_label)
        
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setSpacing(8)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        
        self.step_items = {}
        steps = [
            InitStep.ENV_CHECK,
            InitStep.GIT_CHECK,
            InitStep.CREATE_DIRS,
            InitStep.INIT_CONFIG,
            InitStep.COMPLETE,
        ]
        
        for step in steps:
            step_widget = self._create_step_item(step)
            self.step_items[step] = step_widget
            self.steps_layout.addWidget(step_widget)
        
        scroll = QScrollArea()
        scroll.setWidget(self.steps_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #333333;
                border-radius: 5px;
                background-color: #121212;
            }
        """)
        scroll.setMinimumHeight(200)
        layout.addWidget(scroll)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("完成")
        self.close_btn.setMinimumWidth(140)
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #424242;
                color: #888888;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _create_step_item(self, step_name):
        """创建步骤项"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # 状态图标
        status_label = QLabel("⏳")
        status_label.setFont(QFont("Segoe UI Emoji", 14))
        layout.addWidget(status_label)
        
        # 步骤名
        name_label = QLabel(step_name)
        name_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # 消息
        msg_label = QLabel("")
        msg_label.setStyleSheet("color: #666666; font-size: 11px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(msg_label)
        
        widget.status_label = status_label
        widget.name_label = name_label
        widget.msg_label = msg_label
        
        return widget
    
    def _start_init(self):
        """开始初始化"""
        self.worker = InitWorker(self.base_dir)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress_updated(self, step_name, progress, message):
        """进度更新"""
        self.current_step_label.setText(message)
        self.progress_bar.setValue(progress)
        
        if step_name in self.step_items:
            widget = self.step_items[step_name]
            widget.name_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
    
    def _on_step_completed(self, step_name, success, message):
        """步骤完成"""
        if step_name in self.step_items:
            widget = self.step_items[step_name]
            if success:
                widget.status_label.setText("✅")
                widget.name_label.setStyleSheet("color: #4CAF50;")
            else:
                widget.status_label.setText("❌")
                widget.name_label.setStyleSheet("color: #F44336;")
            widget.msg_label.setText(message)
    
    def _on_finished(self, success, message):
        """初始化完成"""
        self.close_btn.setEnabled(True)
        
        if success:
            # 静默检查Python 3.12是否可用（不弹对话框）
            python_cmd = None
            try:
                python_cmd, python_ok = ensure_python_312_silent(self.base_dir)
                if python_ok and python_cmd:
                    # 更新配置，记录Python路径
                    import json
                    config_file = self.base_dir / 'config' / 'init_config.json'
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        config['python_312_available'] = True
                        config['python_312_path'] = python_cmd
                        with open(config_file, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Python配置失败：{e}")
            
            # 静默检查Git是否可用（不弹对话框）
            git_cmd = None
            try:
                git_cmd, git_ok = ensure_git_available_silent(self.base_dir)
                if git_ok and git_cmd:
                    # 更新配置，记录Git路径
                    import json
                    config_file = self.base_dir / 'config' / 'init_config.json'
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        config['git_available'] = True
                        config['git_path'] = git_cmd
                        with open(config_file, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Git配置失败：{e}")
            
            self.current_step_label.setText("🎉 初始化完成！")
            self.current_step_label.setStyleSheet("color: #4CAF50;")
            
            if InitStep.COMPLETE in self.step_items:
                widget = self.step_items[InitStep.COMPLETE]
                widget.status_label.setText("✅")
                widget.name_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                widget.msg_label.setText("可以开始使用了！")
        else:
            self.current_step_label.setText(f"❌ 初始化失败：{message}")
            self.current_step_label.setStyleSheet("color: #F44336;")
            
            if InitStep.COMPLETE in self.step_items:
                widget = self.step_items[InitStep.COMPLETE]
                widget.status_label.setText("❌")
                widget.name_label.setStyleSheet("color: #F44336;")


def is_initialized(base_dir):
    """检查是否已初始化"""
    config_file = Path(base_dir) / 'config' / 'init_config.json'
    return config_file.exists()


def auto_check_and_update_config(base_dir):
    """自动检测并更新配置信息"""
    import json
    import platform
    import psutil
    from datetime import datetime
    
    config_file = Path(base_dir) / 'config' / 'init_config.json'
    
    config = {}
    
    # 加载现有配置
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}
    
    # 检查并补充系统信息
    needs_update = False
    
    if 'system' not in config:
        config['system'] = platform.system()
        needs_update = True
    
    if 'system_version' not in config:
        config['system_version'] = platform.version()
        needs_update = True
    
    if 'python_version' not in config:
        config['python_version'] = platform.python_version()
        needs_update = True
    
    # 检查Python版本是否符合官方要求（3.12.x）
    if 'python_version_ok' not in config:
        python_version = config.get('python_version', platform.python_version())
        python_major_minor = '.'.join(python_version.split('.')[:2])
        config['python_version_ok'] = python_major_minor == '3.12'
        needs_update = True
    
    if 'cpu_count' not in config:
        config['cpu_count'] = psutil.cpu_count()
        needs_update = True
    
    if 'memory_total' not in config:
        config['memory_total'] = psutil.virtual_memory().total // (1024 ** 3)
        needs_update = True
    
    if 'memory_available' not in config:
        config['memory_available'] = psutil.virtual_memory().available // (1024 ** 3)
        needs_update = True
    
    # 检查Git状态
    from git_detector import GitDetector
    if 'git_available' not in config:
        config['git_available'] = GitDetector.is_git_available()
        if config['git_available']:
            config['git_version'] = GitDetector.get_git_version()
        needs_update = True
    
    # 确保初始化标记
    if 'initialized' not in config:
        config['initialized'] = True
        needs_update = True
    
    if 'init_time' not in config:
        config['init_time'] = datetime.now().isoformat()
        needs_update = True
    
    if 'version' not in config:
        config['version'] = "1.0.0"
        needs_update = True
    
    # 保存更新后的配置
    if needs_update:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"配置已更新：{config_file}")
        except Exception as e:
            print(f"保存配置失败：{e}")
    
    return True
