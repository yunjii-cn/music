#!/usr/bin/env python3
"""
文件用途: PyQt6 GUI启动器主程序
项目名称: 云集智能音乐创意台 (ACE-Step)
版本: v2.8.3+

核心功能:
- 环境维护与检测
- 模型管理界面
- 项目服务启动（青龙训练器、官方音乐演练场等）
- 版本管理器集成
- 日志显示和UI更新

关键类:
- MainWindow: 主窗口类
- ServiceManager: 服务管理器
- EnvironmentMaintenance: 环境维护线程

修改注意事项:
- 使用信号槽机制进行线程安全的UI更新
- 不要直接修改UI元素，必须通过信号
- 保持代码模块化

依赖文件:
- launcher/version_manager.py (版本管理器)
- 1、install-uv-qinglong.ps1 (环境安装)
- 2、run_gradio.ps1 (Gradio界面启动)
- 3、run_server.ps1 (API服务启动)
- 4、run_npmgui.ps1 (青龙前端启动)

被调用: 用户直接运行，或被EXE打包后运行

更多信息请参考:
- .ai-context/FILE_INDEX.md
- .ai-context/KNOWLEDGE_GRAPH.md
"""

import sys
import os
import json
import time
import subprocess
import threading
import socket
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import psutil

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFrame, QGridLayout, QScrollArea,
    QGroupBox, QMessageBox, QProgressBar, QSplitter, QSystemTrayIcon,
    QMenu, QStyle, QComboBox, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction, QKeySequence

# Version manager
from version_manager import VersionManagerDialog

# Version based on executable filename
def get_version_from_filename():
    """从可执行文件名称中提取版本号"""
    try:
        if hasattr(sys, 'frozen'):
            exe_path = sys.executable
            exe_name = os.path.basename(exe_path)
            import re
            match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_name)
            if match:
                return match.group(1)
        return datetime.now().strftime("%Y.%m.%d.%H%M")
    except:
        return datetime.now().strftime("%Y.%m.%d.%H%M")

VERSION = get_version_from_filename()

# 项目定义
PROJECTS = {
    "music": {
        "name": "官方音乐演练场",
        "services": {
            "gradio": {
                "name": "官方音乐演练场",
                "port": 7860,
                "script": "2、run_gradio.ps1",
                "url": "http://127.0.0.1:7860",
                "color": "#E53935",
                "icon": "🎵"
            },
            "api": {
                "name": "API 服务",
                "port": 8001,
                "script": "3、run_server.ps1",
                "url": "http://127.0.0.1:8001/docs",
                "color": "#E53935",
                "icon": "🔌",
                "is_core": True
            }
        }
    },
    "qinglong": {
        "name": "青龙 LoRA 训练器",
        "services": {
            "frontend": {
                "name": "青龙前端",
                "port": 3000,
                "script": "4、run_npmgui.ps1",
                "url": "http://localhost:3000",
                "color": "#E53935",
                "icon": "🎨"
            },
            "backend": {
                "name": "青龙后端",
                "port": 3001,
                "script": "",
                "url": "http://localhost:3001",
                "color": "#E53935",
                "icon": "⚙️"
            }
        }
    }
}

# 扁平化服务定义（用于监控）
SERVICES = {}
for project_id, project in PROJECTS.items():
    for service_id, service in project["services"].items():
        full_service_id = f"{project_id}_{service_id}"
        SERVICES[full_service_id] = service
        SERVICES[full_service_id]["project"] = project_id
        SERVICES[full_service_id]["project_name"] = project["name"]


class ServiceMonitor(QThread):
    """服务状态监控线程"""
    status_changed = pyqtSignal(str, bool)
    
    def __init__(self, check_interval: int = 3):
        super().__init__()
        self.check_interval = check_interval
        self.running = True
        self._status_cache = {}
    
    def run(self):
        while self.running:
            for service_id, service in SERVICES.items():
                is_running = self._check_port(service["port"])
                if self._status_cache.get(service_id) != is_running:
                    self._status_cache[service_id] = is_running
                    self.status_changed.emit(service_id, is_running)
            time.sleep(self.check_interval)
    
    def _check_port(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def stop(self):
        self.running = False


class ServiceProcess(QThread):
    """服务进程包装类 - 使用subprocess实时捕获输出"""
    output_received = pyqtSignal(str, str)
    finished = pyqtSignal(int, int)
    
    def __init__(self, service_id: str, parent=None):
        super().__init__(parent)
        self.service_id = service_id
        self.service_info = SERVICES[service_id]
        self.ready = False
        self.process = None
        self.working_dir = None
        self.script_path = None
    
    def start_service(self, working_dir: str):
        """启动服务"""
        try:
            script_path = os.path.join(working_dir, self.service_info["script"])
            
            if not os.path.exists(script_path) and hasattr(sys, '_MEIPASS'):
                script_path = os.path.join(sys._MEIPASS, self.service_info["script"])
            
            if not os.path.exists(script_path):
                error_msg = f"[错误] 脚本不存在: {script_path}"
                self.output_received.emit(self.service_id, error_msg)
                return False
            
            self.working_dir = working_dir
            self.script_path = script_path
            self.start()
            return True
        except Exception as e:
            error_msg = f"[错误] 启动服务失败: {str(e)}"
            self.output_received.emit(self.service_id, error_msg)
            return False
    
    def run(self):
        """线程运行方法"""
        try:
            if not self.working_dir or not self.script_path:
                error_msg = "[错误] 服务未正确初始化"
                self.output_received.emit(self.service_id, error_msg)
                self.finished.emit(1, 0)
                return
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            cmd = [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-Command", f"& '{self.script_path}' 2>&1"
            ]
            
            creationflags = subprocess.CREATE_NO_WINDOW
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_received.emit(self.service_id, line.strip())
            
            exit_code = self.process.wait()
            self.finished.emit(exit_code, 0)
            
        except Exception as e:
            error_msg = f"[错误] 进程执行失败: {str(e)}"
            self.output_received.emit(self.service_id, error_msg)
            self.finished.emit(1, 0)
    
    def terminate(self):
        """终止进程"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                try:
                    self.process.kill()
                except Exception as e:
                    pass
    
    def state(self):
        """获取进程状态"""
        try:
            if not self.process:
                return 0
            try:
                self.process.wait(timeout=0.1)
                return 0
            except subprocess.TimeoutExpired:
                return 2
        except Exception as e:
            return 0


class ModelDownloadThread(QThread):
    """模型下载线程 - 异步下载模型，避免UI阻塞"""
    log_received = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, model_name: str, base_dir: str, download_source: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.base_dir = base_dir
        self.download_source = download_source
        self.process = None
        self._should_stop = False
    
    def run(self):
        """执行模型下载"""
        try:
            self.log_received.emit(f"开始下载模型: {self.model_name}")
            
            # 构建下载命令 - 使用虚拟环境中的Python
            venv_python = os.path.join(self.base_dir, ".venv", "Scripts", "python.exe")
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_python):
                self.log_received.emit("[错误] 虚拟环境不存在，请先运行环境检测")
                self.download_finished.emit(False, "虚拟环境不存在")
                return
            
            cmd_args = [venv_python, "-m", "acestep.model_downloader"]
            if self.model_name != "main":
                cmd_args.extend(["--model", self.model_name])
            if self.download_source != "auto":
                cmd_args.extend(["--source", self.download_source])
            
            # 构建完整命令字符串
            cmd_str = " ".join(cmd_args)
            
            # 使用虚拟环境中的Python
            cmd = [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-Command", f"cd '{self.base_dir}'; {cmd_str}"
            ]
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            # 读取输出
            while self.process.poll() is None and not self._should_stop:
                line = self.process.stdout.readline()
                if line:
                    self.log_received.emit(f"[模型下载] {line.strip()}")
                else:
                    time.sleep(0.05)
            
            # 读取剩余的输出
            if not self._should_stop:
                for line in self.process.stdout:
                    if line:
                        self.log_received.emit(f"[模型下载] {line.strip()}")
            
            exit_code = self.process.poll()
            if exit_code == 0 and not self._should_stop:
                self.log_received.emit(f"✓ 模型 {self.model_name} 下载成功")
                self.download_finished.emit(True, self.model_name)
            elif not self._should_stop:
                self.log_received.emit(f"❌ 模型 {self.model_name} 下载失败 (退出码: {exit_code})")
                self.download_finished.emit(False, f"模型 {self.model_name} 下载失败")
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.log_received.emit(f"❌ 下载模型时出错: {str(e)}")
            self.log_received.emit(f"错误详情: {error_detail}")
            self.download_finished.emit(False, str(e))
    
    def stop(self):
        """停止下载"""
        self._should_stop = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass


class ModelDeleteThread(QThread):
    """模型删除线程"""
    log_received = pyqtSignal(str)
    delete_finished = pyqtSignal(bool, str)
    
    def __init__(self, model_name: str, base_dir: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.base_dir = base_dir
        self.process = None
    
    def run(self):
        """执行模型删除"""
        try:
            self.log_received.emit(f"开始删除模型: {self.model_name}")
            
            venv_python = os.path.join(self.base_dir, ".venv", "Scripts", "python.exe")
            
            if not os.path.exists(venv_python):
                self.log_received.emit("[错误] 虚拟环境不存在")
                self.delete_finished.emit(False, "虚拟环境不存在")
                return
            
            cmd_args = [venv_python, "-m", "acestep.model_downloader", "--delete", self.model_name]
            cmd_str = " ".join(cmd_args)
            
            cmd = [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-Command", f"cd '{self.base_dir}'; {cmd_str}"
            ]
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_received.emit(f"[模型删除] {line.strip()}")
            
            exit_code = self.process.wait()
            if exit_code == 0:
                self.log_received.emit(f"✓ 模型 {self.model_name} 删除成功")
                self.delete_finished.emit(True, self.model_name)
            else:
                self.log_received.emit(f"❌ 模型 {self.model_name} 删除失败")
                self.delete_finished.emit(False, f"模型 {self.model_name} 删除失败")
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.log_received.emit(f"❌ 删除模型时出错: {str(e)}")
            self.log_received.emit(f"错误详情: {error_detail}")
            self.delete_finished.emit(False, str(e))


class ModelVerifyThread(QThread):
    """模型验证线程"""
    log_received = pyqtSignal(str)
    verify_finished = pyqtSignal(bool, str)
    
    def __init__(self, model_name: str, base_dir: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.base_dir = base_dir
    
    def run(self):
        """执行模型验证"""
        try:
            self.log_received.emit(f"开始验证模型: {self.model_name}")
            
            # 直接调用verify_model函数获取详细结果
            import sys
            sys.path.insert(0, os.path.join(self.base_dir))
            from acestep.model_downloader import verify_model, get_checkpoints_dir
            
            checkpoints_dir = get_checkpoints_dir()
            success, message, details = verify_model(self.model_name, checkpoints_dir)
            
            # 生成详细的验证报告
            self.log_received.emit(f"[模型验证] Verifying model: {self.model_name}")
            self.log_received.emit("[模型验证] 详细分析报告：")
            
            if self.model_name == "main":
                # 主模型验证报告
                total_size = 0
                valid_components = 0
                total_components = 0
                
                for component, comp_details in details.items():
                    if component in ["model_name", "files_found", "files_missing", "size_ok", "total_size", "expected_size"]:
                        continue
                    
                    total_components += 1
                    comp_success = "✓" if comp_details.get("size_ok", True) and len(comp_details.get("files_missing", [])) == 0 else "✗"
                    if comp_success == "✓":
                        valid_components += 1
                    
                    comp_size = comp_details.get("total_size", 0) / 1e6
                    expected_size = comp_details.get("expected_size", 0) / 1e6
                    files_found = len(comp_details.get("files_found", []))
                    files_missing = len(comp_details.get("files_missing", []))
                    
                    self.log_received.emit(f"[模型验证]   {comp_success} {component}:")
                    self.log_received.emit(f"[模型验证]     状态: {'验证通过' if comp_success == '✓' else '验证失败'}")
                    self.log_received.emit(f"[模型验证]     文件: {files_found} 个找到, {files_missing} 个缺失")
                    self.log_received.emit(f"[模型验证]     大小: {comp_size:.2f}MB")
                    if expected_size > 0:
                        self.log_received.emit(f"[模型验证]     期望: {expected_size:.2f}MB")
                    
                    # 显示找到的文件清单
                    if files_found > 0:
                        found_files = comp_details.get("files_found", [])
                        self.log_received.emit(f"[模型验证]     找到文件: {', '.join(found_files)}")
                    
                    if files_missing > 0:
                        missing_files = comp_details.get("files_missing", [])
                        self.log_received.emit(f"[模型验证]     缺失文件: {', '.join(missing_files)}")
                    total_size += comp_details.get("total_size", 0)
                
                self.log_received.emit("[模型验证] 验证总结：")
                self.log_received.emit(f"[模型验证]   总组件数: {total_components}")
                self.log_received.emit(f"[模型验证]   验证通过: {valid_components}")
                self.log_received.emit(f"[模型验证]   验证失败: {total_components - valid_components}")
                self.log_received.emit(f"[模型验证]   总大小: {total_size/1e6:.2f}MB")
            else:
                # 单个模型验证报告
                files_found = len(details.get('files_found', []))
                files_missing = len(details.get('files_missing', []))
                
                self.log_received.emit(f"[模型验证]   状态: {'验证通过' if success else '验证失败'}")
                self.log_received.emit(f"[模型验证]   文件: {files_found} 个找到, {files_missing} 个缺失")
                self.log_received.emit(f"[模型验证]   大小: {details.get('total_size', 0)/1e6:.2f}MB")
                if details.get('expected_size', 0) > 0:
                    self.log_received.emit(f"[模型验证]   期望: {details.get('expected_size', 0)/1e6:.2f}MB")
                
                # 显示找到的文件清单
                if files_found > 0:
                    found_files = details.get('files_found', [])
                    self.log_received.emit(f"[模型验证]   找到文件: {', '.join(found_files)}")
                
                if files_missing > 0:
                    missing_files = details.get('files_missing', [])
                    self.log_received.emit(f"[模型验证]   缺失文件: {', '.join(missing_files)}")
            
            self.log_received.emit(f"[模型验证] {message}")
            self.verify_finished.emit(success, self.model_name)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.log_received.emit(f"❌ 验证模型时出错: {str(e)}")
            self.log_received.emit(f"错误详情: {error_detail}")
            self.verify_finished.emit(False, str(e))


class CollapsiblePanel(QWidget):
    """可展开/折叠的面板组件 - 支持覆盖模式"""
    expanded_changed = pyqtSignal(bool)
    
    def __init__(self, title: str, parent=None, overlay_mode: bool = False):
        super().__init__(parent)
        self.title = title
        self.is_expanded = False
        self.content_widget = None
        self.overlay_mode = overlay_mode
        self.overlay_widget = None
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题按钮
        self.toggle_btn = QPushButton(f"{self.title} ▼")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border-color: #444444;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_btn)
        
        if not self.overlay_mode:
            # 普通模式 - 内容区域在下方
            self.content_frame = QFrame()
            self.content_frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border: 1px solid #333333;
                    border-top: none;
                    border-radius: 0 0 8px 8px;
                }
            """)
            self.content_layout = QVBoxLayout(self.content_frame)
            self.content_layout.setSpacing(10)
            self.content_layout.setContentsMargins(15, 10, 15, 15)
            self.content_frame.hide()
            layout.addWidget(self.content_frame)
    
    def set_content(self, content_widget: QWidget):
        """设置内容组件"""
        self.content_widget = content_widget
        if self.overlay_mode:
            # 覆盖模式 - 不立即添加到布局
            pass
        else:
            self.content_layout.addWidget(content_widget)
    
    def _toggle(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        
        if self.overlay_mode:
            self._toggle_overlay()
        else:
            self._toggle_normal()
        
        self.expanded_changed.emit(self.is_expanded)
    
    def _toggle_normal(self):
        """普通模式切换"""
        if self.is_expanded:
            self.toggle_btn.setText(f"{self.title} ▲")
            self.content_frame.show()
        else:
            self.toggle_btn.setText(f"{self.title} ▼")
            self.content_frame.hide()
    
    def _toggle_overlay(self):
        """覆盖模式切换"""
        if self.is_expanded:
            self.toggle_btn.setText(f"{self.title} ▲")
            self._show_overlay()
        else:
            self.toggle_btn.setText(f"{self.title} ▼")
            self._hide_overlay()
    
    def _show_overlay(self):
        """显示覆盖层"""
        if not self.content_widget:
            return
        
        # 创建覆盖层
        self.overlay_widget = QFrame(self.parent())
        self.overlay_widget.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 2px solid #E53935;
                border-radius: 8px;
            }
        """)
        
        # 设置位置和大小
        btn_rect = self.toggle_btn.geometry()
        global_pos = self.toggle_btn.mapToGlobal(btn_rect.bottomLeft())
        parent_pos = self.parent().mapFromGlobal(global_pos)
        
        # 计算覆盖层大小 - 至少覆盖下方300px高度
        overlay_height = 400
        overlay_width = self.parent().width() - 30
        
        self.overlay_widget.setGeometry(
            parent_pos.x(),
            parent_pos.y() + 5,
            overlay_width,
            overlay_height
        )
        
        # 添加内容
        overlay_layout = QVBoxLayout(self.overlay_widget)
        overlay_layout.setSpacing(10)
        overlay_layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加关闭按钮
        close_btn = QPushButton("✕ 关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        close_btn.clicked.connect(self._toggle)
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        close_btn_layout.addWidget(close_btn)
        overlay_layout.addLayout(close_btn_layout)
        
        # 将内容widget重新parent到覆盖层
        self.content_widget.setParent(self.overlay_widget)
        overlay_layout.addWidget(self.content_widget)
        
        self.overlay_widget.show()
        self.overlay_widget.raise_()
    
    def _hide_overlay(self):
        """隐藏覆盖层"""
        if self.overlay_widget and self.content_widget:
            # 将内容widget重新parent回来
            self.content_widget.setParent(None)
            self.overlay_widget.deleteLater()
            self.overlay_widget = None


class ConfigManager:
    """配置管理器"""
    CONFIG_FILE = "launcher_config.json"
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, self.CONFIG_FILE)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置"""
        default_config = {
            "version": VERSION,
            "services": {
                "auto_start": False,
                "start_sequence": ["music", "api", "frontend", "backend"]
            },
            "ui": {
                "window_size": {"width": 1200, "height": 850},
                "last_tab": 0
            },
            "service_settings": {
                "music": {"auto_open": True},
                "api": {"auto_open": False},
                "frontend": {"auto_open": True},
                "backend": {"auto_open": False}
            },
            "browser": {
                "default": "system",
                "custom_path": ""
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    for key, value in loaded.items():
                        if key in default_config:
                            if isinstance(value, dict) and isinstance(default_config[key], dict):
                                default_config[key].update(value)
                            else:
                                default_config[key] = value
            except Exception as e:
                pass
        
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass
    
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value):
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()


class ServiceCard(QFrame):
    """服务状态卡片"""
    restart_clicked = pyqtSignal(str)
    open_clicked = pyqtSignal(str)
    
    def __init__(self, service_id: str, parent=None):
        super().__init__(parent)
        self.service_id = service_id
        self.service_info = SERVICES[service_id]
        self.is_running = False
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet(f"""
            ServiceCard {{
                background-color: #1E1E1E;
                border-radius: 10px;
                border: 2px solid #333333;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_layout = QHBoxLayout()
        self.icon_label = QLabel(self.service_info["icon"])
        self.icon_label.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(self.icon_label)
        
        self.name_label = QLabel(self.service_info["name"])
        self.name_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: #FFFFFF;
        """)
        title_layout.addWidget(self.name_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        self.status_label = QLabel("○ 未启动")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #1976D2;
        """)
        layout.addWidget(self.status_label)
        
        self.port_label = QLabel(f"端口: {self.service_info['port']}")
        self.port_label.setStyleSheet("font-size: 11px; color: #FFFFFF;")
        layout.addWidget(self.port_label)
        
        btn_layout = QHBoxLayout()
        
        self.restart_btn = QPushButton("重启")
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #E0E0E0;
                border: 1px solid #1976D2;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 11px;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """)
        self.restart_btn.clicked.connect(lambda: self.restart_clicked.emit(self.service_id))
        btn_layout.addWidget(self.restart_btn)
        
        self.open_btn = QPushButton("打开")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #C62828;
            }
        """)
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(self.service_id))
        btn_layout.addWidget(self.open_btn)
        
        layout.addLayout(btn_layout)
    
    def update_status(self, is_running: bool):
        """更新状态显示"""
        self.is_running = is_running
        if is_running:
            self.status_label.setText("● 运行中")
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #E53935;
                font-weight: bold;
            """)
            self.setStyleSheet(f"""
                ServiceCard {{
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    border: 2px solid {self.service_info["color"]};
                }}
            """)
        else:
            self.status_label.setText("○ 未启动")
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #1976D2;
            """)
            self.setStyleSheet(f"""
                ServiceCard {{
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    border: 2px solid #333333;
                }}
            """)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        # 恢复系统顶栏
        self.setWindowTitle("云集智能音乐创意台")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D0D0D;
            }
        """)
        
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'ico.png')
            else:
                icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ico.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            pass
        
        if hasattr(sys, '_MEIPASS'):
            self.base_dir = os.path.abspath(os.path.dirname(sys.executable))
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        print(f"Initial base_dir: {self.base_dir}")
        while not os.path.exists(os.path.join(self.base_dir, 'acestep')) and not os.path.exists(os.path.join(self.base_dir, '2、run_gradio.ps1')):
            parent_dir = os.path.dirname(self.base_dir)
            if parent_dir == self.base_dir:
                break
            self.base_dir = parent_dir
            print(f"Updated base_dir: {self.base_dir}")
        
        self.config = ConfigManager(self.base_dir)
        
        self.service_processes: Dict[str, ServiceProcess] = {}
        self.service_cards: Dict[str, ServiceCard] = {}
        
        self.is_starting = False
        
        self.current_project = "qinglong"
        
        # 浏览器设置
        self.browsers = self._detect_browsers()
        self.selected_browser = self.config.get("browser.default", "system")
        self.custom_browser_path = self.config.get("browser.custom_path", "")
        
        # 如果有自定义浏览器路径，添加到浏览器列表
        if self.custom_browser_path and os.path.exists(self.custom_browser_path):
            self.browsers["自定义浏览器"] = self.custom_browser_path
        
        # 模型下载源设置
        self.download_sources = {
            "auto": "自动检测",
            "huggingface": "HuggingFace",
            "modelscope": "ModelScope",
            "huggingface-cn": "HuggingFace (国内镜像)"
        }
        self.selected_download_source = self.config.get("download.source", "auto")
        
        # 模型管理相关
        self.model_list = []
        self._load_model_list()
        
        # 模型下载线程
        self.model_download_thread = None
        self.is_downloading = False
        
        # 模型删除线程
        self.model_delete_thread = None
        self.is_deleting = False
        
        # 模型验证线程
        self.model_verify_thread = None
        self.is_verifying = False
        
        # 当前正在操作的模型
        self.current_operation_model = None
        
        self._setup_ui()
        self._setup_monitor()
        self._setup_tray()
        
        size = self.config.get("ui.window_size", {"width": 1200, "height": 1100})
        self.resize(size["width"], size["height"])
    
    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D0D0D;
            }
            QWidget {
                background-color: #0D0D0D;
                color: #F0F0F0;
            }
            
            QPushButton {
                background-color: #E53935;
                color: white;
                border: 1px solid #E53935;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', sans-serif;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 2px 4px rgba(229, 57, 53, 0.2);
            }
            QPushButton:hover {
                background-color: #C62828;
                border-color: #C62828;
                box-shadow: 0 4px 8px rgba(229, 57, 53, 0.3);
                transform: translateY(-2px);
            }
            QPushButton:disabled {
                background-color: #333333;
                border-color: #333333;
                color: #757575;
                box-shadow: none;
                transform: none;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
                border-color: #B71C1C;
                transform: translateY(0);
            }
            
            QTextEdit {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
                selection-background-color: #E53935;
                selection-color: white;
            }
            QTextEdit:focus {
                border-color: #E53935;
                outline: none;
                box-shadow: 0 0 0 2px rgba(229, 57, 53, 0.2);
            }
            
            QGroupBox {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 15px;
                padding: 15px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #F0F0F0;
                font-size: 14px;
                font-weight: bold;
            }
            
            QLabel {
                color: #F0F0F0;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            
            QScrollArea {
                border: none;
                background-color: #0D0D0D;
            }
            QScrollBar:vertical {
                background-color: #1A1A1A;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #E53935;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background-color: #1A1A1A;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background-color: #424242;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #E53935;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部区域 - 包含标题、版本号和版本更新按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # 标题（使用原有样式）
        title_label = QLabel("🎵 云集智能音乐创意台")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #E53935;
            font-family: 'Microsoft YaHei', sans-serif;
        """)
        header_layout.addWidget(title_label)
        
        # 版本信息标签
        version_info_label = QLabel("v2026.03.19")
        version_info_label.setStyleSheet("""
            font-size: 12px;
            color: #888888;
            font-family: 'Consolas', monospace;
            padding: 4px 8px;
            background-color: #2D2D2D;
            border-radius: 4px;
        """)
        header_layout.addWidget(version_info_label)
        
        header_layout.addStretch()
        
        # 版本更新按钮已移动到底部
        
        layout.addLayout(header_layout)
        
        # 底部按钮栏（移到启动按钮之前）
        bottom_btn_layout = QVBoxLayout()
        
        env_stop_layout = QHBoxLayout()
        env_stop_layout.setSpacing(20)
        
        # 版本更新按钮
        self.version_btn = QPushButton("🔄 版本更新")
        self.version_btn.setToolTip("切换到版本管理器界面")
        self.version_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #1565C0;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(25, 118, 210, 0.3);
            }
        """)
        self.version_btn.clicked.connect(self._show_version_manager)
        env_stop_layout.addWidget(self.version_btn)
        
        # 部署维护按钮（合并环境检测和智能修复）
        self.btn_deploy_maintain = QPushButton("🚀 部署维护")
        self.btn_deploy_maintain.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #E0E0E0;
                border: 2px solid #1976D2;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(25, 118, 210, 0.3);
            }
        """)
        self.btn_deploy_maintain.clicked.connect(self._deploy_maintenance)
        env_stop_layout.addWidget(self.btn_deploy_maintain)
        
        self.btn_stop_all = QPushButton("⏹ 退出服务")
        self.btn_stop_all.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #E0E0E0;
                border: 2px solid #1976D2;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(25, 118, 210, 0.3);
            }
        """)
        self.btn_stop_all.clicked.connect(self._stop_all_services)
        env_stop_layout.addWidget(self.btn_stop_all)
        
        bottom_btn_layout.addLayout(env_stop_layout)
        
        layout.addLayout(bottom_btn_layout)
        
        # 启动按钮区域
        start_btn_layout = QVBoxLayout()
        
        start_buttons = QHBoxLayout()
        start_buttons.setSpacing(20)
        
        self.btn_start_music = QPushButton("🎵 启动官方音乐演练场")
        self.btn_start_music.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: 2px solid #E53935;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #C62828;
                border-color: #C62828;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(229, 57, 53, 0.3);
            }
        """)
        self.btn_start_music.clicked.connect(lambda: self._start_project("music"))
        start_buttons.addWidget(self.btn_start_music)
        
        self.btn_start_qinglong = QPushButton("🎨 启动青龙 LoRA 训练器")
        self.btn_start_qinglong.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: 2px solid #E53935;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #C62828;
                border-color: #C62828;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(229, 57, 53, 0.3);
            }
        """)
        self.btn_start_qinglong.clicked.connect(lambda: self._start_project("qinglong"))
        start_buttons.addWidget(self.btn_start_qinglong)
        
        start_btn_layout.addLayout(start_buttons)
        layout.addLayout(start_btn_layout)
        
        log_group = QFrame()
        log_group.setFrameShape(QFrame.Shape.StyledPanel)
        log_layout = QVBoxLayout(log_group)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)
        log_layout.addWidget(self.log_output)
        
        layout.addWidget(log_group, 1)
        
        # 创建设置面板容器
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. 浏览器设置面板
        browser_panel = CollapsiblePanel("🌐 浏览器设置")
        browser_content = QWidget()
        browser_content_layout = QVBoxLayout(browser_content)
        browser_content_layout.setSpacing(10)
        browser_content_layout.setContentsMargins(0, 0, 0, 0)
        
        browser_header_layout = QHBoxLayout()
        browser_label = QLabel("启动后打开的浏览器:")
        browser_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        browser_header_layout.addWidget(browser_label)
        browser_header_layout.addStretch()
        
        self.browser_combo = QComboBox()
        self.browser_combo.setStyleSheet("""
            QComboBox {
                background-color: #1A1A1A;
                color: #F0F0F0;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #1976D2;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        
        # 添加浏览器选项
        for browser_name, browser_path in self.browsers.items():
            self.browser_combo.addItem(browser_name, browser_path)
        
        # 设置当前选中的浏览器
        for i in range(self.browser_combo.count()):
            if self.browser_combo.itemText(i) == self.selected_browser:
                self.browser_combo.setCurrentIndex(i)
                break
        
        # 保存浏览器选择
        self.browser_combo.currentIndexChanged.connect(self._on_browser_changed)
        
        browser_header_layout.addWidget(self.browser_combo)
        browser_content_layout.addLayout(browser_header_layout)
        
        # 添加手动选择浏览器按钮
        browser_custom_layout = QHBoxLayout()
        self.browser_custom_label = QLabel("自定义浏览器:")
        self.browser_custom_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        browser_custom_layout.addWidget(self.browser_custom_label)
        
        self.browser_path_edit = QLineEdit()
        self.browser_path_edit.setReadOnly(True)
        self.browser_path_edit.setPlaceholderText("点击右侧按钮选择浏览器...")
        self.browser_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1A1A1A;
                color: #F0F0F0;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:hover {
                border-color: #1976D2;
            }
        """)
        self.browser_path_edit.setText(self.custom_browser_path)
        browser_custom_layout.addWidget(self.browser_path_edit, 1)
        
        self.btn_select_browser = QPushButton("📁 选择...")
        self.btn_select_browser.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #E0E0E0;
                border: 2px solid #1976D2;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """)
        self.btn_select_browser.clicked.connect(self._select_custom_browser)
        browser_custom_layout.addWidget(self.btn_select_browser)
        
        browser_content_layout.addLayout(browser_custom_layout)
        browser_panel.set_content(browser_content)
        settings_layout.addWidget(browser_panel)
        
        # 2. 模型管理面板（包含下载源设置）
        self.model_panel = CollapsiblePanel("📦 模型管理")
        model_content = QWidget()
        model_content_layout = QVBoxLayout(model_content)
        model_content_layout.setSpacing(8)
        model_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 下载源设置
        download_source_header = QHBoxLayout()
        download_source_header.setSpacing(8)
        download_source_label = QLabel("下载源:")
        download_source_label.setStyleSheet("font-size: 13px; color: #AAAAAA;")
        download_source_header.addWidget(download_source_label)
        
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
        for source_key, source_name in self.download_sources.items():
            self.download_source_combo.addItem(source_name, source_key)
        
        # 设置当前选中的下载源
        for i in range(self.download_source_combo.count()):
            if self.download_source_combo.itemData(i) == self.selected_download_source:
                self.download_source_combo.setCurrentIndex(i)
                break
        
        # 保存下载源选择
        self.download_source_combo.currentIndexChanged.connect(self._on_download_source_changed)
        
        download_source_header.addWidget(self.download_source_combo)
        
        # 验证安装按钮
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
        download_source_header.addWidget(self.btn_verify_all)
        
        download_source_header.addStretch()
        model_content_layout.addLayout(download_source_header)
        
        # 模型列表
        self.model_list_widget = QScrollArea()
        self.model_list_widget.setWidgetResizable(True)
        
        model_list_content = QWidget()
        self.model_list_layout = QVBoxLayout(model_list_content)
        self.model_list_layout.setSpacing(10)
        
        # 更新模型列表UI
        self._update_model_management_ui()
        
        self.model_list_widget.setWidget(model_list_content)
        model_content_layout.addWidget(self.model_list_widget, 1)
        
        self.model_panel.set_content(model_content)
        settings_layout.addWidget(self.model_panel)
        
        # 连接模型管理面板展开/折叠信号
        self.model_panel.expanded_changed.connect(self._on_model_panel_expanded_changed)
        
        layout.addWidget(settings_container)
        
        music_project = PROJECTS["music"]
        self.music_group = QFrame()
        self.music_group.setFrameShape(QFrame.Shape.StyledPanel)
        music_layout = QGridLayout(self.music_group)
        
        col = 0
        for service_id, service in music_project["services"].items():
            full_service_id = f"music_{service_id}"
            card = ServiceCard(full_service_id)
            card.restart_clicked.connect(self._restart_service)
            card.open_clicked.connect(self._open_service)
            music_layout.addWidget(card, 0, col)
            self.service_cards[full_service_id] = card
            col += 1
        
        layout.addWidget(self.music_group)
        
        qinglong_project = PROJECTS["qinglong"]
        self.qinglong_group = QFrame()
        self.qinglong_group.setFrameShape(QFrame.Shape.StyledPanel)
        qinglong_layout = QGridLayout(self.qinglong_group)
        
        col = 0
        for service_id, service in qinglong_project["services"].items():
            full_service_id = f"qinglong_{service_id}"
            card = ServiceCard(full_service_id)
            card.restart_clicked.connect(self._restart_service)
            card.open_clicked.connect(self._open_service)
            qinglong_layout.addWidget(card, 0, col)
            self.service_cards[full_service_id] = card
            col += 1
        
        layout.addWidget(self.qinglong_group)
    
    def _setup_monitor(self):
        """设置监控"""
        self.monitor = ServiceMonitor(check_interval=3)
        self.monitor.status_changed.connect(self._on_status_changed)
        self.monitor.start()
    
    def _setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip(f"ACE-Step 启动器 v{VERSION}")
        
        tray_menu = QMenu()
        
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self._exit_all)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()
    
    def _tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
    
    def _on_status_changed(self, service_id: str, is_running: bool):
        """状态变化处理"""
        if service_id in self.service_cards:
            self.service_cards[service_id].update_status(is_running)
    
    def _log(self, message: str, color: str = "#00FF00"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_output.append(html)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _start_project(self, project_id: str):
        """启动单个项目"""
        if self.is_starting:
            self._log("正在启动中，请稍候...", "#616161")
            return
        
        self.is_starting = True
        self.btn_check_env.setEnabled(False)
        self.btn_start_music.setEnabled(False)
        self.btn_start_qinglong.setEnabled(False)
        self.btn_stop_all.setEnabled(False)
        
        self.start_thread = threading.Thread(target=self._start_project_services, args=(project_id,))
        self.start_thread.start()
    
    def _show_version_manager(self):
        """显示版本选择下拉菜单（混合式版本管理器）"""
        try:
            # 创建下拉菜单
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2D2D2D;
                    color: #F0F0F0;
                    border: 1px solid #424242;
                    border-radius: 6px;
                    padding: 8px;
                }
                QMenu::item {
                    padding: 8px 12px;
                    border-radius: 4px;
                    margin: 2px 0;
                }
                QMenu::item:selected {
                    background-color: #E53935;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #424242;
                    margin: 4px 0;
                }
            """)
            
            # 获取最近版本
            versions = self._get_recent_versions(limit=5)
            
            if not versions:
                # 如果无法获取版本，直接打开完整弹窗
                self._open_full_version_dialog()
                return
            
            # 添加快速切换版本选项
            for version in versions:
                action = QAction(f"{version['hash']} - {version['message'][:40]}", self)
                action.setToolTip(f"{version['message']}\n日期：{version['date']}")
                action.triggered.connect(lambda checked, v=version: self._quick_switch_version(v['hash']))
                menu.addAction(action)
            
            menu.addSeparator()
            
            # 添加"查看更多版本"选项
            more_action = QAction("📋 查看更多版本...", self)
            more_action.setToolTip("打开完整的版本管理器对话框")
            more_action.triggered.connect(self._on_show_more_versions)
            menu.addAction(more_action)
            
            # 在按钮下方显示菜单（PyQt6 使用 exec() 而不是 exec_()）
            menu.exec(self.version_btn.mapToGlobal(self.version_btn.rect().bottomLeft()))
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"版本管理器错误：{error_detail}")
            QMessageBox.critical(self, "错误", f"打开版本管理器失败:\n{str(e)}")
    
    def _on_show_more_versions(self):
        """处理"查看更多版本"点击事件 - 延迟打开对话框以避免闪烁"""
        from PyQt6.QtCore import QTimer
        # 使用单次定时器延迟打开对话框，确保菜单已经完全关闭
        QTimer.singleShot(100, self._open_full_version_dialog)
    
    def _get_recent_versions(self, limit=5):
        """获取最近的 Git 版本列表"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', f'-n {limit}', '--pretty=format:%h|%s|%ai'],
                capture_output=True, text=True,
                cwd=self.base_dir, timeout=5
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
    
    def _quick_switch_version(self, commit_hash):
        """快速切换版本"""
        # 获取版本详情用于确认提示
        versions = self._get_recent_versions(limit=5)
        version_info = next((v for v in versions if v['hash'] == commit_hash), None)
        
        if not version_info:
            return
        
        reply = QMessageBox.question(
            self,
            "确认切换版本",
            f"确定要切换到版本 {commit_hash} 吗？\n\n"
            f"说明：{version_info['message']}\n"
            f"日期：{version_info['date']}\n\n"
            f"程序将会自动保存配置并重启。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 显示切换中提示
                switching_dialog = QDialog(self)
                switching_dialog.setWindowTitle("正在切换版本")
                switching_dialog.setMinimumSize(300, 150)
                switching_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
                switching_dialog.setStyleSheet("""
                    QDialog {
                        background-color: #1A1A1A;
                        color: #F0F0F0;
                    }
                    QLabel {
                        padding: 20px;
                        font-size: 14px;
                    }
                """)
                
                dialog_layout = QVBoxLayout(switching_dialog)
                label = QLabel(f"正在切换到 {commit_hash}...")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dialog_layout.addWidget(label)
                
                switching_dialog.show()
                QApplication.processEvents()
                
                # 执行版本切换
                self._do_switch_version(commit_hash)
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换版本失败:\n{str(e)}")
    
    def _do_switch_version(self, commit_hash):
        """执行版本切换操作"""
        import os
        import shutil
        from PyQt6.QtWidgets import QApplication
        
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
        import subprocess
        result = subprocess.run(
            ['git', 'checkout', commit_hash],
            capture_output=True, text=True,
            cwd=self.base_dir
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
        
        # 5. 提示重启
        QMessageBox.information(
            self,
            "切换成功",
            f"已成功切换到版本 {commit_hash}\n\n请重新启动程序。",
            QMessageBox.StandardButton.Ok
        )
        
        # 退出当前程序
        QApplication.quit()
    
    def _open_full_version_dialog(self):
        """打开完整的版本管理器对话框"""
        try:
            dialog = VersionManagerDialog(self, self.base_dir)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开版本管理器失败:\n{str(e)}")
    
    def _start_project_services(self, project_id: str):
        """启动项目服务"""
        project = PROJECTS[project_id]
        self._log("========================================")
        self._log(f"开始启动 {project['name']}...")
        self._log("========================================")
        
        all_success = True
        started_services = []
        
        uv_path = os.path.expanduser("~/.local/bin/uv.exe")
        if not os.path.exists(uv_path):
            self._log("[错误] uv 未安装，请先运行环境检测", "#F44336")
            self.is_starting = False
            self._enable_buttons()
            return
        
        if project_id == "qinglong":
            venv_path = os.path.join(self.base_dir, ".venv")
            if not os.path.exists(venv_path):
                self._log("[错误] 虚拟环境不存在，请先运行环境检测", "#F44336")
                self.is_starting = False
                self._enable_buttons()
                return
            
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            if os.path.exists(ace_step_ui_path):
                node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                if not os.path.exists(node_modules_path):
                    self._log("[错误] ace-step-ui 依赖未安装，请先运行环境检测", "#F44336")
                    self.is_starting = False
                    self._enable_buttons()
                    return
        
        if project_id in ["qinglong", "music"]:
            api_port = 8001
            api_running = self.monitor._check_port(api_port)
            
            if not api_running:
                self._log("核心 API 服务未运行，正在启动...")
                api_success = False
                music_api_service_id = "music_api"
                if music_api_service_id in SERVICES:
                    api_success = self._start_single_service(project_id, music_api_service_id, "API 服务")
                
                if not api_success:
                    self._log("[错误] 核心 API 服务启动失败", "#F44336")
                    self.is_starting = False
                    self._enable_buttons()
                    return
                
                self._log("等待核心 API 服务就绪...")
                api_ready = False
                max_wait = 30
                waited = 0
                while waited < max_wait and not api_ready:
                    if self.monitor._check_port(api_port):
                        api_ready = True
                    else:
                        time.sleep(2)
                        waited += 2
                        self._log(f"等待 API 服务就绪... ({waited}/{max_wait} 秒)", "#888888")
                if not api_ready:
                    self._log("[错误] 核心 API 服务启动超时", "#F44336")
                    self.is_starting = False
                    self._enable_buttons()
                    return
                self._log("✓ 核心 API 服务已就绪")
            else:
                self._log("✓ 核心 API 服务已运行，跳过启动步骤")
        
        service_threads = []
        service_results = {}
            
        def start_service_thread(service_id, service):
            full_service_id = f"{project_id}_{service_id}"
            success = self._start_single_service(project_id, full_service_id, service["name"])
            service_results[full_service_id] = success
            if success:
                started_services.append(full_service_id)
            
        for service_id, service in project["services"].items():
            thread = threading.Thread(
                target=start_service_thread,
                args=(service_id, service)
            )
            service_threads.append(thread)
            thread.start()
            
        for thread in service_threads:
            thread.join()
            
        for full_service_id, success in service_results.items():
            if not success:
                all_success = False
                break
        
        if all_success and started_services:
            self._log("等待所有服务就绪...")
            all_ready = False
            max_wait = 60
            waited = 0
            
            while waited < max_wait and not all_ready:
                all_ready = True
                for service_id in started_services:
                    if not self.monitor._check_port(SERVICES[service_id]["port"]):
                        all_ready = False
                        break
                
                if not all_ready:
                    time.sleep(2)
                    waited += 2
                    self._log(f"等待服务就绪... ({waited}/{max_wait} 秒)", "#888888")
            
            if all_ready:
                self._log("✓ 所有服务已就绪，正在打开浏览器...")
                for service_id in started_services:
                    if "_" in service_id:
                        base_service_id = service_id.split("_", 1)[1]
                    else:
                        base_service_id = service_id
                    
                    if self.config.get(f"service_settings.{base_service_id}.auto_open", False):
                        self._open_service(service_id)
        
        self._log("")
        self._log("========================================")
        if all_success:
            self._log(f"✓ {project['name']} 启动完成！", "#E53935")
        else:
            self._log(f"⚠ {project['name']} 启动失败，请检查日志", "#616161")
        self._log("========================================")
        
        self._generate_startup_diagnosis(project_id, started_services, all_success)
        
        self.is_starting = False
        self._enable_buttons()
    
    def _enable_buttons(self):
        """启用所有按钮"""
        self.btn_check_env.setEnabled(True)
        self.btn_smart_fix.setEnabled(True)
        self.btn_start_music.setEnabled(True)
        self.btn_start_qinglong.setEnabled(True)
        self.btn_stop_all.setEnabled(True)
    
    def _check_environment(self):
        """环境检测"""
        self._log("========================================")
        self._log("开始环境检测...")
        self._log("========================================")
        
        self._log("0. 检查 PowerShell 安装...")
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            powershell_paths = [
                "powershell.exe",
                "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                "C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
            ]
            
            found = False
            for powershell_exe in powershell_paths:
                try:
                    process = subprocess.Popen(
                        [powershell_exe, "-Version"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                    stdout, stderr = process.communicate(timeout=5)
                    if process.returncode == 0:
                        version = stdout.strip() if stdout.strip() else "PowerShell"
                        self._log(f"✓ PowerShell 已安装: {version}")
                        found = True
                        break
                except:
                    continue
            
            if not found:
                try:
                    process = subprocess.Popen(
                        ["where", "powershell"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                    stdout, stderr = process.communicate(timeout=5)
                    if process.returncode == 0 and stdout.strip():
                        self._log(f"✓ PowerShell 已安装: {stdout.strip()}")
                        found = True
                except:
                    pass
            
            if not found:
                self._log("[错误] PowerShell 未安装或无法访问", "#F44336")
                return
        except Exception as e:
            self._log(f"[错误] 检查 PowerShell 失败: {e}", "#F44336")
            return
        
        self._log("1. 检查环境...")
        
        uv_path = os.path.expanduser("~/.local/bin/uv.exe")
        if not os.path.exists(uv_path):
            self._log("[错误] uv 未安装，请先安装环境", "#F44336")
            return
        
        self._log("✓ 环境检查通过")
        
        self._log("2. 检查并安装依赖...")
        
        skip_install = False
        
        uv_path = os.path.expanduser("~/.local/bin/uv.exe")
        if os.path.exists(uv_path):
            venv_path = os.path.join(self.base_dir, ".venv")
            if os.path.exists(venv_path):
                ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
                if os.path.exists(ace_step_ui_path):
                    package_json_path = os.path.join(ace_step_ui_path, "package.json")
                    if os.path.exists(package_json_path):
                        node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                        if os.path.exists(node_modules_path):
                            skip_install = True
                            self._log("✓ 依赖已安装，跳过安装步骤")
        
        if not skip_install:
            install_script = os.path.join(self.base_dir, "1、install-uv-qinglong.ps1")
            if os.path.exists(install_script):
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    process = subprocess.Popen(
                        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", install_script],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                    
                    while process.poll() is None:
                        line = process.stdout.readline()
                        if line:
                            self._log(f"[安装] {line.strip()}")
                        line_err = process.stderr.readline()
                        if line_err:
                            self._log(f"[安装错误] {line_err.strip()}", "#F44336")
                    
                    if process.returncode == 0:
                        self._log("✓ 依赖安装完成")
                    else:
                        self._log("[错误] 依赖安装失败", "#F44336")
                except Exception as e:
                    self._log(f"[错误] 运行安装脚本失败: {e}", "#F44336")
            else:
                self._log("[错误] 安装脚本不存在", "#F44336")
        
        self._log("3. 检查启动脚本...")
        scripts = [
            "2、run_gradio.ps1",
            "3、run_server.ps1",
            "4、run_npmgui.ps1"
        ]
        for script in scripts:
            script_path = os.path.join(self.base_dir, script)
            if os.path.exists(script_path):
                self._log(f"✓ {script} 存在")
            else:
                self._log(f"[错误] {script} 不存在", "#F44336")
        
        self._log("4. 检查git子模块...")
        ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
        git_dir = os.path.join(ace_step_ui_path, ".git")
        
        if os.path.exists(ace_step_ui_path):
            if os.path.exists(git_dir):
                self._log("✓ ace-step-ui git子模块已初始化")
            else:
                self._log("[信息] ace-step-ui 是git子模块，当前未初始化", "#FF9800")
                self._log("[提示] 请运行智能修复来初始化git子模块", "#FF9800")
        else:
            self._log("[警告] ace-step-ui 目录不存在", "#FF9800")
        
        self._log("5. 检查前端依赖...")
        if os.path.exists(ace_step_ui_path):
            package_json_path = os.path.join(ace_step_ui_path, "package.json")
            if os.path.exists(package_json_path):
                node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                if os.path.exists(node_modules_path):
                    self._log("✓ 前端依赖已安装")
                else:
                    self._log("[信息] 未检测到前端依赖", "#FF9800")
                    self._log("[提示] 请运行智能修复来安装前端依赖", "#FF9800")
            else:
                self._log("[警告] package.json 不存在，跳过前端依赖检查", "#FF9800")
        else:
            self._log("[警告] ace-step-ui 目录不存在，跳过前端依赖检查", "#FF9800")
        
        self._log("")
        self._log("========================================")
        self._log("环境检测完成！", "#E53935")
        self._log("========================================")
    
    def _smart_fix_environment(self):
        """智能修复环境 - 自动检测并修复所有环境问题"""
        self._log("========================================")
        self._log("开始智能环境修复...")
        self._log("=======================================")
        
        # 禁用按钮以防止重复操作
        self.btn_deploy_maintain.setEnabled(False)
        self.btn_start_music.setEnabled(False)
        self.btn_start_qinglong.setEnabled(False)
        self.btn_stop_all.setEnabled(False)
        
        try:
            # 1. 检查并修复 PowerShell
            self._log("1. 检查 PowerShell...")
            powershell_available = False
            
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                powershell_paths = [
                    "powershell.exe",
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
                ]
                
                for powershell_exe in powershell_paths:
                    try:
                        process = subprocess.Popen(
                            [powershell_exe, "-Version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0:
                            version = stdout.strip() if stdout.strip() else "PowerShell"
                            self._log(f"✓ PowerShell 已安装: {version}")
                            powershell_available = True
                            break
                    except:
                        continue
                
                if not powershell_available:
                    try:
                        process = subprocess.Popen(
                            ["where", "powershell"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0 and stdout.strip():
                            self._log(f"✓ PowerShell 已安装: {stdout.strip()}")
                            powershell_available = True
                    except:
                        pass
                
                if not powershell_available:
                    self._log("[错误] PowerShell 未安装或无法访问", "#F44336")
                    self._log("请手动安装 PowerShell 或确保其在系统路径中", "#F44336")
                    return
            except Exception as e:
                self._log(f"[错误] 检查 PowerShell 失败: {e}", "#F44336")
                return
            
            # 2. 检查并安装 uv
            self._log("2. 检查并安装 uv...")
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            
            if not os.path.exists(uv_path):
                self._log("[信息] uv 未安装，正在安装...")
                try:
                    # 下载并安装 uv
                    install_uv_script = os.path.join(self.base_dir, "install_uv.bat")
                    if os.path.exists(install_uv_script):
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                        process = subprocess.Popen(
                            ["cmd.exe", "/c", install_uv_script],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        
                        while process.poll() is None:
                            line = process.stdout.readline()
                            if line:
                                self._log(f"[安装 uv] {line.strip()}")
                            line_err = process.stderr.readline()
                            if line_err:
                                self._log(f"[安装 uv 错误] {line_err.strip()}", "#F44336")
                        
                        if process.returncode == 0:
                            self._log("✓ uv 安装完成")
                        else:
                            self._log("[错误] uv 安装失败", "#F44336")
                            return
                    else:
                        # 如果没有 install_uv.bat，使用 PowerShell 安装
                        self._log("[信息] 正在使用 PowerShell 安装 uv...")
                        powershell_script = """\
                            $ProgressPreference = 'SilentlyContinue'
                            Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -OutFile install-uv.ps1
                            powershell -ExecutionPolicy Bypass -File install-uv.ps1
                            Remove-Item install-uv.ps1
                        """
                        
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                        process = subprocess.Popen(
                            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        
                        while process.poll() is None:
                            line = process.stdout.readline()
                            if line:
                                self._log(f"[安装 uv] {line.strip()}")
                            line_err = process.stderr.readline()
                            if line_err:
                                self._log(f"[安装 uv 错误] {line_err.strip()}", "#F44336")
                        
                        if process.returncode == 0:
                            self._log("✓ uv 安装完成")
                        else:
                            self._log("[错误] uv 安装失败", "#F44336")
                            return
                except Exception as e:
                    self._log(f"[错误] 安装 uv 失败: {e}", "#F44336")
                    return
            else:
                self._log("✓ uv 已安装")
            
            # 3. 检查并创建虚拟环境
            self._log("3. 检查并创建虚拟环境...")
            venv_path = os.path.join(self.base_dir, ".venv")
            
            if not os.path.exists(venv_path):
                self._log("[信息] 虚拟环境不存在，正在创建...")
                try:
                    # 使用 uv 创建虚拟环境
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    process = subprocess.Popen(
                        [uv_path, "venv"],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                    
                    while process.poll() is None:
                        line = process.stdout.readline()
                        if line:
                            self._log(f"[创建虚拟环境] {line.strip()}")
                        line_err = process.stderr.readline()
                        if line_err:
                            self._log(f"[创建虚拟环境错误] {line_err.strip()}", "#F44336")
                    
                    if process.returncode == 0:
                        self._log("✓ 虚拟环境创建完成")
                    else:
                        self._log("[错误] 虚拟环境创建失败", "#F44336")
                        return
                except Exception as e:
                    self._log(f"[错误] 创建虚拟环境失败: {e}", "#F44336")
                    return
            else:
                self._log("✓ 虚拟环境已存在")
            
            # 4. 安装项目依赖
            self._log("4. 安装项目依赖...")
            try:
                # 检查 requirements.txt 是否存在
                requirements_path = os.path.join(self.base_dir, "requirements.txt")
                if not os.path.exists(requirements_path):
                    # 尝试从 pyproject.toml 安装
                    self._log("[信息] 使用 pyproject.toml 安装依赖...")
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    process = subprocess.Popen(
                        [uv_path, "pip", "install", "."],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                else:
                    # 使用 requirements.txt 安装
                    self._log("[信息] 使用 requirements.txt 安装依赖...")
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    process = subprocess.Popen(
                        [uv_path, "pip", "install", "-r", "requirements.txt"],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                
                while process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        self._log(f"[安装依赖] {line.strip()}")
                    line_err = process.stderr.readline()
                    if line_err:
                        self._log(f"[安装依赖错误] {line_err.strip()}", "#F44336")
                
                if process.returncode == 0:
                    self._log("✓ 项目依赖安装完成")
                else:
                    self._log("[错误] 项目依赖安装失败", "#F44336")
                    return
            except Exception as e:
                self._log(f"[错误] 安装项目依赖失败: {e}", "#F44336")
                return
            
            # 5. 检查并初始化git子模块
            self._log("5. 检查git子模块...")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            git_dir = os.path.join(ace_step_ui_path, ".git")
            
            if os.path.exists(ace_step_ui_path):
                # 检查是否是未初始化的git子模块
                if not os.path.exists(git_dir):
                    self._log("[信息] ace-step-ui 是git子模块，当前未初始化，正在初始化...")
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                        # 初始化并更新子模块
                        process = subprocess.Popen(
                            ["git", "submodule", "update", "--init", "--recursive"],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        
                        while process.poll() is None:
                            line = process.stdout.readline()
                            if line:
                                self._log(f"[初始化子模块] {line.strip()}")
                            line_err = process.stderr.readline()
                            if line_err:
                                self._log(f"[初始化子模块错误] {line_err.strip()}", "#FF9800")
                        
                        if process.returncode == 0:
                            self._log("✓ git子模块初始化完成")
                        else:
                            self._log("[警告] git子模块初始化失败，可能影响UI功能", "#FF9800")
                    except Exception as e:
                        self._log(f"[警告] 初始化git子模块失败: {e}", "#FF9800")
                else:
                    self._log("✓ git子模块已初始化")
            else:
                self._log("[警告] ace-step-ui 目录不存在，跳过子模块检查", "#FF9800")
            
            # 6. 安装前端依赖
            self._log("6. 安装前端依赖...")
            if os.path.exists(ace_step_ui_path):
                package_json_path = os.path.join(ace_step_ui_path, "package.json")
                if os.path.exists(package_json_path):
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    if not os.path.exists(node_modules_path):
                        self._log("[信息] 前端依赖未安装，正在安装...")
                        try:
                            # 检查 npm 是否可用
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            
                            # 先检查 npm 是否存在
                            npm_check = subprocess.Popen(
                                ["npm", "--version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                startupinfo=startupinfo
                            )
                            npm_check.wait()
                            
                            if npm_check.returncode == 0:
                                # 安装前端依赖
                                process = subprocess.Popen(
                                    ["npm", "install"],
                                    cwd=ace_step_ui_path,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    startupinfo=startupinfo
                                )
                                
                                while process.poll() is None:
                                    line = process.stdout.readline()
                                    if line:
                                        self._log(f"[安装前端依赖] {line.strip()}")
                                    line_err = process.stderr.readline()
                                    if line_err:
                                        self._log(f"[安装前端依赖错误] {line_err.strip()}", "#F44336")
                                
                                if process.returncode == 0:
                                    self._log("✓ 前端依赖安装完成")
                                else:
                                    self._log("[警告] 前端依赖安装失败，可能影响UI功能", "#FF9800")
                            else:
                                self._log("[警告] npm 未安装，跳过前端依赖安装", "#FF9800")
                        except Exception as e:
                            self._log(f"[警告] 安装前端依赖失败: {e}", "#FF9800")
                    else:
                        self._log("✓ 前端依赖已安装")
                else:
                    self._log("[警告] package.json 不存在，跳过前端依赖安装", "#FF9800")
            else:
                self._log("[警告] ace-step-ui 目录不存在，跳过前端依赖安装", "#FF9800")
            
            # 7. 检查启动脚本
            self._log("7. 检查启动脚本...")
            scripts = [
                "2、run_gradio.ps1",
                "3、run_server.ps1",
                "4、run_npmgui.ps1"
            ]
            missing_scripts = []
            for script in scripts:
                script_path = os.path.join(self.base_dir, script)
                if os.path.exists(script_path):
                    self._log(f"✓ {script} 存在")
                else:
                    self._log(f"[错误] {script} 不存在", "#F44336")
                    missing_scripts.append(script)
            
            if missing_scripts:
                self._log(f"[警告] 缺少启动脚本: {', '.join(missing_scripts)}", "#FF9800")
                self._log("请确保这些脚本存在或从原始项目中复制", "#FF9800")
            
            # 8. 检查环境变量
            self._log("8. 检查环境变量...")
            try:
                # 检查 PATH 环境变量是否包含 uv 的路径
                path_env = os.environ.get("PATH", "")
                uv_dir = os.path.dirname(uv_path)
                if uv_dir not in path_env:
                    self._log("[信息] uv 路径未在环境变量中，正在添加...")
                    # 这里可以添加代码来修改环境变量，但需要管理员权限
                    # 为了安全，我们只是提示用户
                    self._log(f"[提示] 请将 {uv_dir} 添加到系统环境变量 PATH 中", "#FF9800")
                else:
                    self._log("✓ uv 路径已在环境变量中")
            except Exception as e:
                self._log(f"[错误] 检查环境变量失败: {e}", "#F44336")
            
            # 9. 检查模型目录
            self._log("9. 检查模型目录...")
            models_dir = os.path.join(self.base_dir, "models")
            if not os.path.exists(models_dir):
                self._log("[信息] 模型目录不存在，正在创建...")
                try:
                    os.makedirs(models_dir, exist_ok=True)
                    self._log("✓ 模型目录创建完成")
                except Exception as e:
                    self._log(f"[错误] 创建模型目录失败: {e}", "#F44336")
            else:
                self._log("✓ 模型目录已存在")
            
            # 10. 检查配置文件
            self._log("10. 检查配置文件...")
            env_example_path = os.path.join(self.base_dir, ".env.example")
            env_path = os.path.join(self.base_dir, ".env")
            if not os.path.exists(env_path) and os.path.exists(env_example_path):
                self._log("[信息] .env 文件不存在，正在从 .env.example 创建...")
                try:
                    import shutil
                    shutil.copy2(env_example_path, env_path)
                    self._log("✓ .env 文件创建完成")
                except Exception as e:
                    self._log(f"[错误] 创建 .env 文件失败: {e}", "#F44336")
            elif os.path.exists(env_path):
                self._log("✓ .env 文件已存在")
            else:
                self._log("[警告] .env.example 文件不存在，无法创建 .env 文件", "#FF9800")
            
            # 11. 最终检查
            self._log("11. 最终环境检查...")
            
            # 检查 uv 是否可用
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    [uv_path, "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo
                )
                stdout, stderr = process.communicate(timeout=5)
                if process.returncode == 0:
                    self._log(f"✓ uv 版本: {stdout.strip()}")
                else:
                    self._log("[错误] uv 不可用", "#F44336")
            except Exception as e:
                self._log(f"[错误] 检查 uv 失败: {e}", "#F44336")
            
            # 检查 Python 版本
            try:
                venv_python = os.path.join(venv_path, "Scripts", "python.exe")
                if os.path.exists(venv_python):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    process = subprocess.Popen(
                        [venv_python, "--version"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo
                    )
                    stdout, stderr = process.communicate(timeout=5)
                    if process.returncode == 0:
                        self._log(f"✓ Python 版本: {stdout.strip()}")
                    else:
                        self._log("[错误] Python 不可用", "#F44336")
                else:
                    self._log("[错误] 虚拟环境 Python 不存在", "#F44336")
            except Exception as e:
                self._log(f"[错误] 检查 Python 失败: {e}", "#F44336")
            
            self._log("")
            self._log("========================================")
            self._log("智能环境修复完成！", "#E53935")
            self._log("=======================================")
            self._log("环境已准备就绪，您可以开始使用云集智能音乐创意台了！", "#E53935")
            self._log("")
            self._log("[提示] 模型管理面板已自动展开，您可以查看和下载模型", "#4CAF50")
            
            # 自动展开模型管理面板
            if hasattr(self, 'model_panel') and not self.model_panel.is_expanded:
                from PyQt6.QtCore import QTimer
                # 使用延迟执行，确保UI已完全准备好
                QTimer.singleShot(100, lambda: self._expand_model_panel())
            
        except Exception as e:
            self._log(f"[错误] 智能修复失败: {e}", "#F44336")
            import traceback
            self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
        finally:
            # 重新启用按钮
            self.btn_deploy_maintain.setEnabled(True)
            self.btn_start_music.setEnabled(True)
            self.btn_start_qinglong.setEnabled(True)
            self.btn_stop_all.setEnabled(True)
    
    def _deploy_maintenance(self):
        """部署维护 - 合并环境检测和智能修复功能
        - 自动检测环境是否安装
        - 未安装则自动安装部署
        - 已安装则检测问题并自动修复
        - 解决不了的提供手动解决建议
        """
        self._log("========================================")
        self._log("开始部署维护...")
        self._log("=======================================")
        
        # 禁用按钮以防止重复操作
        self.btn_deploy_maintain.setEnabled(False)
        self.btn_start_music.setEnabled(False)
        self.btn_start_qinglong.setEnabled(False)
        self.btn_stop_all.setEnabled(False)
        
        try:
            # 1. 首先检查PowerShell
            self._log("1. 检查 PowerShell...")
            powershell_available = False
            
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                powershell_paths = [
                    "powershell.exe",
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
                ]
                
                for powershell_exe in powershell_paths:
                    try:
                        process = subprocess.Popen(
                            [powershell_exe, "-Version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0:
                            version = stdout.strip() if stdout.strip() else "PowerShell"
                            self._log(f"✓ PowerShell 已安装: {version}")
                            powershell_available = True
                            break
                    except:
                        continue
                
                if not powershell_available:
                    try:
                        process = subprocess.Popen(
                            ["where", "powershell"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0 and stdout.strip():
                            self._log(f"✓ PowerShell 已安装: {stdout.strip()}")
                            powershell_available = True
                    except:
                        pass
                
                if not powershell_available:
                    self._log("[错误] PowerShell 未安装或无法访问", "#F44336")
                    self._log("[建议] 请确保PowerShell已安装并添加到系统PATH", "#FF9800")
                    return
            except Exception as e:
                self._log(f"[错误] 检查 PowerShell 失败: {e}", "#F44336")
                return
            
            # 2. 检查环境是否已安装
            self._log("2. 检查环境安装状态...")
            
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            venv_path = os.path.join(self.base_dir, ".venv")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            
            environment_installed = False
            if os.path.exists(uv_path) and os.path.exists(venv_path):
                if os.path.exists(ace_step_ui_path):
                    package_json_path = os.path.join(ace_step_ui_path, "package.json")
                    if os.path.exists(package_json_path):
                        node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                        if os.path.exists(node_modules_path):
                            environment_installed = True
                            self._log("✓ 环境已完全安装")
            
            if not environment_installed:
                # 环境未安装，执行完整安装
                self._log("[信息] 环境未完全安装，开始自动部署...", "#FF9800")
                
                install_script = os.path.join(self.base_dir, "1、install-uv-qinglong.ps1")
                if os.path.exists(install_script):
                    try:
                        self._log("3. 执行环境安装脚本...")
                        
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                        process = subprocess.Popen(
                            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", install_script],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            startupinfo=startupinfo
                        )
                        
                        while process.poll() is None:
                            line = process.stdout.readline()
                            if line:
                                self._log(f"[安装] {line.strip()}")
                            line_err = process.stderr.readline()
                            if line_err:
                                self._log(f"[安装错误] {line_err.strip()}", "#F44336")
                        
                        if process.returncode == 0:
                            self._log("✓ 环境部署完成")
                        else:
                            self._log("[错误] 环境部署失败", "#F44336")
                            self._log("[建议] 请手动运行 1、install-uv-qinglong.ps1 脚本", "#FF9800")
                            return
                    except Exception as e:
                        self._log(f"[错误] 运行安装脚本失败: {e}", "#F44336")
                        self._log("[建议] 请手动运行 1、install-uv-qinglong.ps1 脚本", "#FF9800")
                        return
                else:
                    self._log("[错误] 安装脚本不存在", "#F44336")
                    self._log("[建议] 请确保 1、install-uv-qinglong.ps1 脚本存在", "#FF9800")
                    return
            else:
                # 环境已安装，执行智能修复
                self._log("3. 环境已安装，执行智能修复...")
                self._smart_fix_environment()
            
            # 4. 最终检查
            self._log("4. 最终检查...")
            
            # 检查启动脚本
            scripts = [
                "2、run_gradio.ps1",
                "3、run_server.ps1",
                "4、run_npmgui.ps1"
            ]
            script_missing = False
            for script in scripts:
                script_path = os.path.join(self.base_dir, script)
                if os.path.exists(script_path):
                    self._log(f"✓ {script} 存在")
                else:
                    self._log(f"[错误] {script} 不存在", "#F44336")
                    script_missing = True
            
            if script_missing:
                self._log("[建议] 请确保所有启动脚本都存在", "#FF9800")
            
            self._log("")
            self._log("=======================================")
            self._log("部署维护完成！", "#E53935")
            self._log("=======================================")
            self._log("环境已准备就绪，您可以开始使用云集智能音乐创意台了！", "#E53935")
            
        except Exception as e:
            self._log(f"[错误] 部署维护失败: {e}", "#F44336")
            import traceback
            self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
        finally:
            # 重新启用按钮
            self.btn_deploy_maintain.setEnabled(True)
            self.btn_start_music.setEnabled(True)
            self.btn_start_qinglong.setEnabled(True)
            self.btn_stop_all.setEnabled(True)
    
    def _generate_startup_diagnosis(self, project_id: str, started_services: List[str], all_success: bool):
        """生成启动诊断分析报告"""
        project = PROJECTS[project_id]
        
        self._log("")
        self._log("========================================")
        self._log("启动诊断分析报告")
        self._log("========================================")
        
        all_ok = True
        
        self._log("1. 服务启动状态检查...")
        for service_id, service in project["services"].items():
            full_service_id = f"{project_id}_{service_id}"
            is_running = self.monitor._check_port(service["port"])
            
            if is_running:
                self._log(f"✓ {service['name']} - 运行正常 (端口: {service['port']})")
            elif full_service_id in started_services:
                self._log(f"⚠ {service['name']} - 已尝试启动但未检测到运行", "#FF9800")
                self._log(f"  建议：检查服务日志，查看是否有报错信息", "#FF9800")
                all_ok = False
            else:
                self._log(f"○ {service['name']} - 未启动", "#616161")
        
        if project_id == "qinglong":
            self._log("2. 核心API服务检查...")
            api_port = 8001
            api_running = self.monitor._check_port(api_port)
            if api_running:
                self._log("✓ API服务 - 运行正常 (端口: 8001)")
            else:
                self._log("⚠ API服务 - 未运行", "#FF9800")
                self._log("  建议：先启动官方音乐演练场来启动API服务", "#FF9800")
                all_ok = False
        
        self._log("3. 常见问题排查...")
        
        port_conflicts = []
        for service_id, service in SERVICES.items():
            port = service["port"]
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name()
                            if "python" not in proc_name.lower() and "node" not in proc_name.lower():
                                port_conflicts.append((port, service["name"], proc_name))
                        except:
                            pass
            except:
                pass
        
        if port_conflicts:
            for port, service_name, proc_name in port_conflicts:
                self._log(f"⚠ 端口冲突: 端口 {port} ({service_name}) 被 {proc_name} 占用", "#FF9800")
                self._log(f"  解决方案：关闭占用端口的程序，或修改服务配置使用其他端口", "#FF9800")
                all_ok = False
        else:
            self._log("✓ 无端口冲突")
        
        self._log("")
        self._log("========================================")
        if all_success and all_ok:
            self._log("✓ 启动诊断完成 - 全部正常！", "#E53935")
            self._log("所有服务已成功启动并正常运行", "#E53935")
        elif all_success:
            self._log("⚠ 启动完成但有警告 - 请检查上述建议", "#FF9800")
        else:
            self._log("❌ 启动失败 - 请根据上述建议解决问题", "#F44336")
        self._log("========================================")
    
    def _start_single_service(self, project_id: str, service_id: str, service_name: str) -> bool:
        """启动单个服务"""
        self._log("========================================")
        self._log(f"正在启动 {service_name}...")
        self._log(f"服务ID: {service_id}")
        self._log(f"端口: {SERVICES[service_id]['port']}")
        self._log(f"脚本: {SERVICES[service_id]['script']}")
        self._log("========================================")
        
        if self.monitor._check_port(SERVICES[service_id]["port"]):
            self._log(f"✓ {service_name} 已在运行")
            return True
        
        script = SERVICES[service_id].get("script", "")
        if not script:
            self._log(f"⚠ {service_name} 没有脚本，跳过启动")
            return True
        
        process = ServiceProcess(service_id)
        process.output_received.connect(self._on_service_output)
        self.service_processes[service_id] = process
        
        self._log(f"开始启动 {service_name} 进程...")
        if not process.start_service(self.base_dir):
            self._log(f"[错误] {service_name} 启动失败", "#F44336")
            return False
        
        self._log(f"✓ {service_name} 进程已启动")
        
        max_wait = 60
        waited = 0
        while waited < max_wait:
            time.sleep(2)
            waited += 2
            
            if self.monitor._check_port(SERVICES[service_id]["port"]):
                self._log(f"✓ {service_name} 已就绪", "#E53935")
                return True
            
            if process.state() == 0:
                self._log(f"[错误] {service_name} 进程已退出", "#F44336")
                return False
                
            self._log(f"等待 {service_name} 就绪... ({waited}/{max_wait} 秒)", "#888888")
        
        self._log(f"[错误] {service_name} 启动超时", "#F44336")
        return False
    
    def _on_service_output(self, service_id: str, output: str):
        """服务输出处理"""
        service_name = SERVICES[service_id]["name"]
        self._log(f"[{service_name}] {output}", "#AAAAAA")
    
    def _stop_all_services(self):
        """停止所有服务"""
        self._log("========================================")
        self._log("正在停止所有服务...")
        self._log("========================================")
        
        for project_id, project in PROJECTS.items():
            for service_id in project["services"]:
                full_service_id = f"{project_id}_{service_id}"
                self._stop_service(full_service_id)
        
        self._log("")
        self._log("========================================")
        self._log("所有服务已停止")
        self._log("========================================")
    
    def _stop_service(self, service_id: str):
        """停止单个服务"""
        service = SERVICES[service_id]
        self._log(f"正在停止 {service['name']}...")
        
        if service_id in self.service_processes:
            process = self.service_processes[service_id]
            if process.state() != 0:
                process.terminate()
                self._log(f"✓ {service['name']} 进程已终止")
        
        port = service["port"]
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        p = psutil.Process(conn.pid)
                        p.terminate()
                        p.wait(timeout=3)
                        self._log(f"已终止占用端口 {port} 的进程")
                    except:
                        pass
        except:
            pass
    
    def _restart_service(self, service_id: str):
        """重启服务"""
        self._stop_service(service_id)
        time.sleep(2)
        
        if "_" in service_id:
            project_id, service_short_id = service_id.split("_", 1)
            service = SERVICES[service_id]
            service_name = service["name"]
            
            threading.Thread(
                target=self._start_single_service,
                args=(project_id, service_id, service_name)
            ).start()
    
    def _open_service(self, service_id: str):
        """在浏览器中打开服务"""
        url = SERVICES[service_id]["url"]
        self._open_url_in_browser(url)
    
    def _detect_browsers(self) -> Dict[str, str]:
        """检测本地已安装的浏览器"""
        browsers = {
            "系统默认": "system"
        }
        
        # 检测常见浏览器
        browser_paths = [
            # Chrome
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            # Edge
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            # Firefox
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            # Opera
            r"C:\Program Files\Opera\launcher.exe",
            r"C:\Program Files (x86)\Opera\launcher.exe",
            # Brave
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        ]
        
        browser_names = {
            "chrome.exe": "Chrome",
            "msedge.exe": "Edge",
            "firefox.exe": "Firefox",
            "launcher.exe": "Opera",
            "brave.exe": "Brave"
        }
        
        for path in browser_paths:
            if os.path.exists(path):
                exe_name = os.path.basename(path)
                if exe_name in browser_names:
                    browsers[browser_names[exe_name]] = path
        
        return browsers
    
    def _on_browser_changed(self, index):
        """处理浏览器选择变化"""
        selected_browser = self.browser_combo.itemText(index)
        self.selected_browser = selected_browser
        self.config.set("browser.default", selected_browser)
        self._log(f"已设置默认浏览器为: {selected_browser}")
    
    def _open_url_in_browser(self, url: str):
        """使用选择的浏览器打开URL"""
        selected_browser = self.selected_browser
        
        if selected_browser == "系统默认":
            import webbrowser
            webbrowser.open(url)
        else:
            browser_path = self.browsers.get(selected_browser)
            if browser_path:
                try:
                    subprocess.Popen([browser_path, url])
                    self._log(f"使用 {selected_browser} 打开: {url}")
                except Exception as e:
                    self._log(f"打开浏览器失败: {e}", "#F44336")
                    # 回退到系统默认
                    import webbrowser
                    webbrowser.open(url)
            else:
                # 浏览器路径不存在，回退到系统默认
                import webbrowser
                webbrowser.open(url)
    
    def _select_custom_browser(self):
        """手动选择浏览器"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("可执行文件 (*.exe)")
        file_dialog.setWindowTitle("选择浏览器可执行文件")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                browser_path = selected_files[0]
                self.browser_path_edit.setText(browser_path)
                self.custom_browser_path = browser_path
                self.config.set("browser.custom_path", browser_path)
                
                # 更新浏览器列表
                if "自定义浏览器" in self.browsers:
                    del self.browsers["自定义浏览器"]
                self.browsers["自定义浏览器"] = browser_path
                
                # 更新下拉框
                self.browser_combo.clear()
                for browser_name, browser_path in self.browsers.items():
                    self.browser_combo.addItem(browser_name, browser_path)
                
                # 选择自定义浏览器
                for i in range(self.browser_combo.count()):
                    if self.browser_combo.itemText(i) == "自定义浏览器":
                        self.browser_combo.setCurrentIndex(i)
                        break
                
                self._log(f"已选择自定义浏览器: {browser_path}")
    
    def _on_download_source_changed(self, index):
        """处理下载源选择变化"""
        selected_source = self.download_source_combo.itemData(index)
        self.selected_download_source = selected_source
        self.config.set("download.source", selected_source)
        self._log(f"已设置默认下载源为: {self.download_sources[selected_source]}")
    
    def _expand_model_panel(self):
        """展开模型管理面板"""
        if hasattr(self, 'model_panel') and not self.model_panel.is_expanded:
            # 直接调用toggle方法
            self.model_panel._toggle()
    
    def _on_model_panel_expanded_changed(self, is_expanded: bool):
        """处理模型管理面板展开/折叠变化"""
        if is_expanded:
            # 展开时隐藏服务管理区域
            if hasattr(self, 'music_group'):
                self.music_group.hide()
            if hasattr(self, 'qinglong_group'):
                self.qinglong_group.hide()
        else:
            # 折叠时显示服务管理区域
            if hasattr(self, 'music_group'):
                self.music_group.show()
            if hasattr(self, 'qinglong_group'):
                self.qinglong_group.show()
    
    def _load_model_list(self):
        """加载模型列表"""
        # 主模型
        self.model_list.append({
            "name": "main",
            "display_name": "Main Model",
            "repo": "ACE-Step/Ace-Step1.5",
            "category": "main",
            "description": "包含：VAE、Qwen3-Embedding-0.6B、acestep-v15-turbo、acestep-5Hz-lm-1.7B",
            "info": "完整的基础模型包，包含所有必需组件，适合初次使用",
            "exists": self._check_main_model_exists()
        })
        
        # LM 模型
        lm_models = {
            "acestep-5Hz-lm-0.6B": {
                "repo": "ACE-Step/acestep-5Hz-lm-0.6B",
                "description": "轻量级语言模型",
                "info": "0.6B参数，速度快，适合资源有限的环境"
            },
            "acestep-5Hz-lm-4B": {
                "repo": "ACE-Step/acestep-5Hz-lm-4B",
                "description": "大型语言模型",
                "info": "4B参数，质量更高，生成效果更好"
            }
        }
        
        for model_name, model_info in lm_models.items():
            self.model_list.append({
                "name": model_name,
                "display_name": model_name,
                "repo": model_info["repo"],
                "category": "lm",
                "description": model_info["description"],
                "info": model_info["info"],
                "exists": self._check_model_exists(model_name)
            })
        
        # DiT 模型
        dit_models = {
            "acestep-v15-base": {
                "repo": "ACE-Step/acestep-v15-base",
                "description": "基础DiT模型",
                "info": "v1.5版本的基础模型，平衡质量和速度"
            },
            "acestep-v15-sft": {
                "repo": "ACE-Step/acestep-v15-sft",
                "description": "监督微调模型",
                "info": "经过监督微调，生成更加稳定可控"
            },
            "acestep-v15-turbo-shift1": {
                "repo": "ACE-Step/acestep-v15-turbo-shift1",
                "description": "Turbo加速模型 (Shift 1)",
                "info": "Turbo系列，Shift 1采样，生成速度快"
            },
            "acestep-v15-turbo-shift3": {
                "repo": "ACE-Step/acestep-v15-turbo-shift3",
                "description": "Turbo加速模型 (Shift 3)",
                "info": "Turbo系列，Shift 3采样，平衡质量和速度"
            },
            "acestep-v15-turbo-continuous": {
                "repo": "ACE-Step/acestep-v15-turbo-continuous",
                "description": "Turbo连续生成模型",
                "info": "支持连续生成，适合长音频创作"
            }
        }
        
        for model_name, model_info in dit_models.items():
            self.model_list.append({
                "name": model_name,
                "display_name": model_name,
                "repo": model_info["repo"],
                "category": "dit",
                "description": model_info["description"],
                "info": model_info["info"],
                "exists": self._check_model_exists(model_name)
            })
    
    def _check_main_model_exists(self):
        """检查主模型是否存在"""
        checkpoints_dir = os.path.join(self.base_dir, "models")
        components = ["acestep-v15-turbo", "vae", "Qwen3-Embedding-0.6B", "acestep-5Hz-lm-1.7B"]
        for component in components:
            component_path = os.path.join(checkpoints_dir, component)
            if not os.path.exists(component_path):
                return False
            # 检查目录是否有文件
            if not os.listdir(component_path):
                return False
        return True
    
    def _check_model_exists(self, model_name):
        """检查模型是否存在"""
        checkpoints_dir = os.path.join(self.base_dir, "models")
        model_path = os.path.join(checkpoints_dir, model_name)
        if not os.path.exists(model_path):
            return False
        # 检查目录是否有文件
        if not os.listdir(model_path):
            return False
        return True
    
    def _download_model(self, model_name):
        """下载模型 - 使用异步线程避免UI阻塞"""
        if self.is_downloading or self.is_deleting or self.is_verifying:
            self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
            return
        
        self.is_downloading = True
        self.current_operation_model = model_name
        
        # 刷新UI以显示暂停按钮
        self._update_model_management_ui()
        
        # 创建下载线程
        self.model_download_thread = ModelDownloadThread(
            model_name, 
            self.base_dir, 
            self.selected_download_source
        )
        
        # 连接信号
        self.model_download_thread.log_received.connect(self._log)
        self.model_download_thread.download_finished.connect(self._on_download_finished)
        
        # 禁用所有模型按钮
        self._set_model_buttons_enabled(False)
        
        # 启动下载线程
        self.model_download_thread.start()
    
    def _on_download_finished(self, success: bool, model_name: str):
        """下载完成回调"""
        self.is_downloading = False
        self.current_operation_model = None
        
        if success:
            # 更新模型状态
            self.model_list = []
            self._load_model_list()
        self._update_model_management_ui()
        
        # 重新启用所有按钮
        self._set_model_buttons_enabled(True)
    
    def _delete_model(self, model_name):
        """删除模型"""
        if self.is_deleting or self.is_downloading or self.is_verifying:
            self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
            return
        
        self.is_deleting = True
        self.current_operation_model = model_name
        
        # 创建删除线程
        self.model_delete_thread = ModelDeleteThread(
            model_name,
            self.base_dir
        )
        
        # 连接信号
        self.model_delete_thread.log_received.connect(self._log)
        self.model_delete_thread.delete_finished.connect(self._on_delete_finished)
        
        # 禁用所有模型按钮
        self._set_model_buttons_enabled(False)
        
        # 启动删除线程
        self.model_delete_thread.start()
    
    def _on_delete_finished(self, success: bool, model_name: str):
        """删除完成回调"""
        self.is_deleting = False
        self.current_operation_model = None
        
        if success:
            # 更新模型状态
            self.model_list = []
            self._load_model_list()
            self._update_model_management_ui()
        
        # 重新启用所有按钮
        self._set_model_buttons_enabled(True)
    
    def _verify_model(self, model_name):
        """验证模型"""
        if self.is_deleting or self.is_downloading or self.is_verifying:
            self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
            return
        
        self.is_verifying = True
        self.current_operation_model = model_name
        
        # 创建验证线程
        self.model_verify_thread = ModelVerifyThread(
            model_name,
            self.base_dir
        )
        
        # 连接信号
        self.model_verify_thread.log_received.connect(self._log)
        self.model_verify_thread.verify_finished.connect(self._on_verify_finished)
        
        # 禁用所有模型按钮
        self._set_model_buttons_enabled(False)
        
        # 启动验证线程
        self.model_verify_thread.start()
    
    def _on_verify_finished(self, success: bool, model_name: str):
        """验证完成回调"""
        self.is_verifying = False
        self.current_operation_model = None
        
        # 重新启用所有按钮
        self._set_model_buttons_enabled(True)
    
    def _pause_download(self):
        """暂停下载"""
        if self.model_download_thread and self.is_downloading:
            self._log("正在停止下载...", "#FF9800")
            self.model_download_thread.stop()
            self.is_downloading = False
            self.current_operation_model = None
            self._update_model_management_ui()
            self._set_model_buttons_enabled(True)
    
    def _verify_all_models(self):
        """一键验证所有模型安装"""
        if self.is_deleting or self.is_downloading or self.is_verifying:
            self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
            return
        
        self.is_verifying = True
        
        # 禁用验证按钮
        self.btn_verify_all.setEnabled(False)
        
        # 启动验证线程
        self.model_verify_thread = ModelVerifyThread(
            "main",
            self.base_dir
        )
        
        # 连接信号
        self.model_verify_thread.log_received.connect(self._log)
        self.model_verify_thread.verify_finished.connect(self._on_verify_all_finished)
        
        # 禁用所有模型按钮
        self._set_model_buttons_enabled(False)
        
        # 启动验证线程
        self.model_verify_thread.start()
    
    def _on_verify_all_finished(self, success: bool, model_name: str):
        """验证完成回调"""
        self.is_verifying = False
        
        # 重新启用验证按钮
        self.btn_verify_all.setEnabled(True)
        
        # 重新启用所有按钮
        self._set_model_buttons_enabled(True)
    
    def _redownload_model(self, model_name):
        """重新下载模型（先删除再下载）"""
        if self.is_deleting or self.is_downloading or self.is_verifying:
            self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
            return
        
        # 先删除
        self._delete_model(model_name)
        # 等待删除完成后会自动刷新UI，用户可以重新点击下载
    
    def _set_model_buttons_enabled(self, enabled: bool):
        """设置所有模型按钮的启用状态"""
        if hasattr(self, 'model_list_layout'):
            for i in range(self.model_list_layout.count()):
                item = self.model_list_layout.itemAt(i)
                if item and item.widget():
                    model_widget = item.widget()
                    # 查找所有按钮并设置状态
                    for child in model_widget.findChildren(QPushButton):
                        child.setEnabled(enabled)
    
    def _update_model_management_ui(self):
        """更新模型管理UI - 分类表格形式"""
        # 清空现有内容
        if hasattr(self, 'model_list_layout'):
            while self.model_list_layout.count() > 0:
                item = self.model_list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # 按分类分组模型
        categories = {
            "main": {"name": "📦 主模型", "models": []},
            "lm": {"name": "📝 LM 语言模型", "models": []},
            "dit": {"name": "🎨 DiT 扩散模型", "models": []}
        }
        
        for model in self.model_list:
            cat = model.get("category", "dit")
            if cat in categories:
                categories[cat]["models"].append(model)
        
        # 添加各分类
        for cat_id, cat_info in categories.items():
            if not cat_info["models"]:
                continue
            
            # 分类标题
            cat_header = QFrame()
            cat_header.setStyleSheet("""
                QFrame {
                    background-color: #2A2A2A;
                    border-radius: 4px;
                    border: 1px solid #444444;
                    padding: 6px 10px;
                }
            """)
            cat_layout = QHBoxLayout(cat_header)
            cat_layout.setContentsMargins(8, 5, 8, 5)
            
            cat_label = QLabel(cat_info["name"])
            cat_label.setStyleSheet("font-weight: bold; color: #E53935; font-size: 13px;")
            cat_layout.addWidget(cat_label)
            cat_layout.addStretch()
            
            if hasattr(self, 'model_list_layout'):
                self.model_list_layout.addWidget(cat_header)
            
            # 模型表格
            for idx, model in enumerate(cat_info["models"]):
                model_item = QFrame()
                is_last = idx == len(cat_info["models"]) - 1
                if is_last:
                    border_style = "border-radius: 0 0 4px 4px;"
                else:
                    border_style = "border-radius: 0px;"
                model_item.setStyleSheet(f"""
                    QFrame {{
                        background-color: #1E1E1E;
                        {border_style}
                        border: 1px solid #333333;
                        border-top: none;
                        padding: 8px 10px;
                    }}
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
                is_downloading = self.is_downloading and self.current_operation_model == model["name"]
                
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
                    pause_btn.clicked.connect(self._pause_download)
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
                
                if hasattr(self, 'model_list_layout'):
                    self.model_list_layout.addWidget(model_item)
            
            # 分类间距
            if cat_id != list(categories.keys())[-1]:
                spacer = QWidget()
                spacer.setMinimumHeight(8)
                if hasattr(self, 'model_list_layout'):
                    self.model_list_layout.addWidget(spacer)

    def _exit_all(self):
        """退出所有进程"""
        self._log("========================================")
        self._log("正在退出所有进程...")
        self._log("========================================")
        
        self._stop_all_services()
        
        process_names = ["python.exe", "python", "node.exe", "node", "powershell.exe", "pwsh.exe"]
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in process_names:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'acestep' in cmdline.lower() or 'qinglong' in cmdline.lower():
                        self._log(f"终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=3)
            except:
                pass
        
        self._log("✓ 所有进程已退出")
        
        self.config.set("ui.window_size", {
            "width": self.width(),
            "height": self.height()
        })
        
        self.close()
    
    def closeEvent(self, event):
        """关闭事件"""
        self.config.set("ui.window_size", {
            "width": self.width(),
            "height": self.height()
        })
        
        self.monitor.stop()
        self.monitor.wait()
        
        self.tray_icon.hide()
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
