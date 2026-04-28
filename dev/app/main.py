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
import subprocess as _subprocess

if sys.platform == 'win32':
    def _ensure_hidden(kwargs):
        si = kwargs.get('startupinfo', _subprocess.STARTUPINFO())
        si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs['startupinfo'] = si
        flags = _subprocess.CREATE_NO_WINDOW
        if hasattr(_subprocess, 'DETACHED_PROCESS'):
            flags |= _subprocess.DETACHED_PROCESS
        if hasattr(_subprocess, 'CREATE_NEW_PROCESS_GROUP'):
            flags |= _subprocess.CREATE_NEW_PROCESS_GROUP
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | flags
        else:
            kwargs['creationflags'] = flags
        return kwargs

    _orig_popen_init = _subprocess.Popen.__init__
    def _patched_popen_init(self, *args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        _orig_popen_init(self, *args, **kwargs)
    _subprocess.Popen.__init__ = _patched_popen_init

    _orig_run = _subprocess.run
    def _patched_run(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_run(*args, **kwargs)
    _subprocess.run = _patched_run

    _orig_call = _subprocess.call
    def _patched_call(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_call(*args, **kwargs)
    _subprocess.call = _patched_call

    _orig_check_call = _subprocess.check_call
    def _patched_check_call(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_call(*args, **kwargs)
    _subprocess.check_call = _patched_check_call

    _orig_check_output = _subprocess.check_output
    def _patched_check_output(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_output(*args, **kwargs)
    _subprocess.check_output = _patched_check_output

import subprocess
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

if sys.platform == 'win32':
    _HIDDEN_FLAGS = subprocess.CREATE_NO_WINDOW | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
else:
    _HIDDEN_FLAGS = 0

def _hidden_startupinfo():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si

def hidden_run(*args, **kwargs):
    si = kwargs.get('startupinfo', subprocess.STARTUPINFO())
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    kwargs['startupinfo'] = si
    if sys.platform == 'win32':
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | _HIDDEN_FLAGS
        else:
            kwargs['creationflags'] = _HIDDEN_FLAGS
    return subprocess.run(*args, **kwargs)

def hidden_popen(*args, **kwargs):
    si = kwargs.get('startupinfo', subprocess.STARTUPINFO())
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    kwargs['startupinfo'] = si
    if sys.platform == 'win32':
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | _HIDDEN_FLAGS
        else:
            kwargs['creationflags'] = _HIDDEN_FLAGS
    return subprocess.Popen(*args, **kwargs)

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFrame, QGridLayout, QScrollArea,
    QGroupBox, QMessageBox, QProgressBar, QSplitter, QSystemTrayIcon,
    QMenu, QStyle, QComboBox, QFileDialog, QLineEdit, QStackedWidget, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction, QKeySequence

# Version manager - lazy imported

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
                "script": "scripts/2、run_gradio.ps1",
                "url": "http://127.0.0.1:7860",
                "color": "#E53935",
                "icon": "🎵"
            },
            "api": {
                "name": "API 服务",
                "port": 8001,
                "script": "scripts/3、run_server.ps1",
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
            "backend": {
                "name": "青龙后端",
                "port": 3001,
                "script": "scripts/5、run_qinglong_backend.ps1",
                "url": "http://localhost:3001",
                "color": "#E53935",
                "icon": "⚙️"
            },
            "frontend": {
                "name": "青龙前端",
                "port": 3000,
                "script": "scripts/6、run_qinglong_frontend.ps1",
                "url": "http://localhost:3000",
                "color": "#E53935",
                "icon": "🎨"
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
            

            
            cmd = [
                "powershell.exe",
                "-WindowStyle", "Hidden",
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-Command", f"& '{self.script_path}' 2>&1"
            ]
            
            self.process = hidden_popen(
                cmd,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
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
    progress_updated = pyqtSignal(int, str)
    
    def __init__(self, model_name: str, base_dir: str, download_source: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.base_dir = base_dir
        self.download_source = download_source
        self.process = None
        self._should_stop = False
        self.current_progress = 0
    
    def run(self):
        """执行模型下载"""
        try:
            self.log_received.emit(f"开始下载模型: {self.model_name}")
            
            # 初始化进度
            self.current_progress = 5
            self.progress_updated.emit(self.current_progress, "准备下载...")
            
            # 构建下载命令 - 使用虚拟环境中的Python
            venv_python = os.path.join(self.base_dir, "scripts", ".venv", "Scripts", "python.exe")
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_python):
                self.log_received.emit("[错误] 虚拟环境不存在，请先运行环境检测")
                self.download_finished.emit(False, "虚拟环境不存在")
                return
            
            self.current_progress = 10
            self.progress_updated.emit(self.current_progress, "检查环境...")
            
            cmd_args = [venv_python, "-m", "acestep.model_downloader"]
            if self.model_name != "main":
                cmd_args.extend(["--model", self.model_name])
            if self.download_source != "auto":
                cmd_args.extend(["--source", self.download_source])
            
            cmd_str = " ".join(f'"{arg}"' if ' ' in arg else arg for arg in cmd_args)
            
            cmd = [
                "powershell.exe",
                "-WindowStyle", "Hidden",
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-Command", f"cd '{self.base_dir}'; {cmd_str}"
            ]
            
            self.current_progress = 15
            self.progress_updated.emit(self.current_progress, "连接下载源...")
            

            self.process = hidden_popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            # 模拟下载进度
            import random
            start_time = time.time()
            last_progress = self.current_progress
            
            # 读取输出
            while self.process.poll() is None and not self._should_stop:
                line = self.process.stdout.readline()
                if line:
                    self.log_received.emit(f"[模型下载] {line.strip()}")
                    # 根据时间模拟进度
                    elapsed = time.time() - start_time
                    if elapsed > 0.5:
                        # 随机增加进度
                        if self.current_progress < 95:
                            increment = random.uniform(0.5, 3.0)
                            self.current_progress = min(95, self.current_progress + increment)
                            self.progress_updated.emit(int(self.current_progress), "下载中...")
                        start_time = time.time()
                else:
                    time.sleep(0.05)
                    # 即使没有输出也缓慢增加进度
                    elapsed = time.time() - start_time
                    if elapsed > 1.0:
                        if self.current_progress < 95:
                            increment = random.uniform(0.3, 1.0)
                            self.current_progress = min(95, self.current_progress + increment)
                            self.progress_updated.emit(int(self.current_progress), "下载中...")
                        start_time = time.time()
            
            # 读取剩余的输出
            if not self._should_stop:
                for line in self.process.stdout:
                    if line:
                        self.log_received.emit(f"[模型下载] {line.strip()}")
            
            exit_code = self.process.poll()
            if exit_code == 0 and not self._should_stop:
                self.current_progress = 100
                self.progress_updated.emit(100, "下载完成!")
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
            
            venv_python = os.path.join(self.base_dir, "scripts", ".venv", "Scripts", "python.exe")
            
            if not os.path.exists(venv_python):
                self.log_received.emit("[错误] 虚拟环境不存在")
                self.delete_finished.emit(False, "虚拟环境不存在")
                return
            
            cmd_args = [venv_python, "-m", "acestep.model_downloader", "--delete", self.model_name]
            cmd_str = " ".join(f'"{arg}"' if ' ' in arg else arg for arg in cmd_args)
            
            cmd = [
                "powershell.exe",
                "-WindowStyle", "Hidden",
                "-ExecutionPolicy", "Bypass",
                "-NoProfile",
                "-Command", f"cd '{self.base_dir}'; {cmd_str}"
            ]
            

            self.process = hidden_popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
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
    """严格模型验证线程 - 使用与前端API相同的 verify_model 逻辑"""
    log_received = pyqtSignal(str)
    verify_finished = pyqtSignal(bool, str)
    verify_details = pyqtSignal(dict)  # 发送详细验证结果
    
    def __init__(self, model_name: str, base_dir: str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.base_dir = base_dir
    
    def run(self):
        """使用官方严格验证逻辑 - 与 API 端点 /api/generate/models/verify 一致"""
        try:
            import sys
            sys.path.insert(0, os.path.join(self.base_dir))
            
            try:
                from acestep.model_downloader import verify_model, get_checkpoints_dir
            except Exception as e:
                self.log_received.emit(f"[错误] 无法加载验证模块: {e}")
                self.verify_finished.emit(False, self.model_name)
                return
            
            try:
                checkpoints_dir = get_checkpoints_dir()
                self.log_received.emit(f"[验证] 检查目录: {checkpoints_dir}")
            except Exception as e:
                self.log_received.emit(f"[错误] 无法获取模型目录: {e}")
                self.verify_finished.emit(False, self.model_name)
                return
            
            # 使用官方 verify_model 进行严格验证
            success, message, details = verify_model(self.model_name, checkpoints_dir)
            
            # 输出详细日志
            if success:
                self.log_received.emit(f"[验证通过] {message}")
            else:
                self.log_received.emit(f"[验证失败] {message}")
                if details.get("files_missing"):
                    self.log_received.emit(f"  缺少文件: {', '.join(details['files_missing'])}")
                if not details.get("size_ok", True):
                    actual = round(details.get("total_size", 0) / 1e6, 2)
                    expected = round(details.get("expected_size", 0) / 1e6, 2)
                    self.log_received.emit(f"  大小不足: {actual}MB < 预期 {expected}MB")
                self.log_received.emit(f"  建议: 请重新下载模型以修复不完整的文件")
            
            # 发送详细结果
            self.verify_details.emit({
                "model_name": self.model_name,
                "is_valid": success,
                "message": message,
                "files_found": details.get("files_found", []),
                "files_missing": details.get("files_missing", []),
                "total_size_mb": round(details.get("total_size", 0) / 1e6, 2),
                "expected_size_mb": round(details.get("expected_size", 0) / 1e6, 2),
                "size_ok": details.get("size_ok", False),
            })
            
            self.verify_finished.emit(success, self.model_name)
            
        except Exception as e:
            try:
                self.log_received.emit(f"[错误] 验证异常: {e}")
                self.verify_finished.emit(False, str(e))
            except:
                pass


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
        self.scripts_dir = os.path.join(base_dir, "scripts")
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir, exist_ok=True)
        self.config_path = os.path.join(self.scripts_dir, self.CONFIG_FILE)
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
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 第一行：图标、名称、端口、状态都在同一排
        top_row_layout = QHBoxLayout()
        
        self.icon_label = QLabel(self.service_info["icon"])
        self.icon_label.setStyleSheet("font-size: 24px;")
        top_row_layout.addWidget(self.icon_label)
        
        self.name_label = QLabel(self.service_info["name"])
        self.name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #FFFFFF;
        """)
        top_row_layout.addWidget(self.name_label)
        
        self.port_label = QLabel(f"端口:{self.service_info['port']}")
        self.port_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        top_row_layout.addWidget(self.port_label)
        
        top_row_layout.addStretch()
        
        # 状态指示灯+文字
        status_container = QHBoxLayout()
        status_container.setSpacing(6)
        
        self.status_label = QLabel()
        self.status_label.setFixedSize(16, 16)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #424242;
                border: 2px solid #616161;
                border-radius: 8px;
            }
        """)
        status_container.addWidget(self.status_label)
        
        self.status_text_label = QLabel("未启动")
        self.status_text_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        status_container.addWidget(self.status_text_label)
        
        top_row_layout.addLayout(status_container)
        
        layout.addLayout(top_row_layout)
        
        # 第二行：操作按钮
        btn_layout = QHBoxLayout()
        
        self.restart_btn = QPushButton("重启")
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #FFFFFF;
                border: 1px solid #1976D2;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
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
                color: #FFFFFF;
                border: 1px solid #C62828;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C62828;
                border-color: #C62828;
            }
        """)
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(self.service_id))
        btn_layout.addWidget(self.open_btn)
        
        layout.addLayout(btn_layout)
    
    def update_status(self, is_running: bool):
        """更新状态显示"""
        self.is_running = is_running
        if is_running:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    border: 2px solid #388E3C;
                    border-radius: 8px;
                }
            """)
            self.status_text_label.setText("运行中")
            self.status_text_label.setStyleSheet("font-size: 12px; color: #4CAF50; font-weight: bold;")
            self.setStyleSheet(f"""
                ServiceCard {{
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    border: 2px solid {self.service_info["color"]};
                }}
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #424242;
                    border: 2px solid #616161;
                    border-radius: 8px;
                }
            """)
            self.status_text_label.setText("未启动")
            self.status_text_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
            self.setStyleSheet(f"""
                ServiceCard {{
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    border: 2px solid #333333;
                }}
            """)


class NativeSplash:
    _hwnd = None
    _progress = 0.0
    _bar_x = 60
    _bar_y = 240
    _bar_w = 400
    _bar_h = 10

    @classmethod
    def find_splash_hwnd(cls):
        if cls._hwnd:
            return cls._hwnd
        try:
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            found = []
            @WNDENUMPROC
            def _enum(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    cls_buf = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, cls_buf, 256)
                    if 'Tk' in cls_buf.value or 'Splash' in cls_buf.value:
                        found.append(hwnd)
                return True
            user32.EnumWindows(_enum, 0)
            if found:
                cls._hwnd = found[0]
        except Exception:
            pass
        return cls._hwnd

    @classmethod
    def draw_progress(cls, progress, message=""):
        hwnd = cls.find_splash_hwnd()
        if not hwnd:
            try:
                import pyi_splash
                if message:
                    pyi_splash.update_text(message)
            except Exception:
                pass
            return
        try:
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32

            if message:
                try:
                    import pyi_splash
                    pyi_splash.update_text(message)
                except Exception:
                    pass

            rect = ctypes.wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            cw = rect.right - rect.left
            ch = rect.bottom - rect.top

            hdc = user32.GetDC(hwnd)
            if not hdc:
                return

            bar_x = int(cw * cls._bar_x / 520)
            bar_y = int(ch * cls._bar_y / 360)
            bar_w = int(cw * cls._bar_w / 520)
            bar_h = int(ch * cls._bar_h / 360)

            bg_rect = ctypes.wintypes.RECT()
            bg_rect.left = bar_x
            bg_rect.top = bar_y
            bg_rect.right = bar_x + bar_w
            bg_rect.bottom = bar_y + bar_h
            bg_brush = gdi32.CreateSolidBrush(0x00222222)
            gdi32.SelectObject(hdc, bg_brush)
            gdi32.RoundRect(hdc, bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, 5, 5)

            fill_w = int(bar_w * min(progress, 1.0))
            if fill_w > 0:
                fill_rect = ctypes.wintypes.RECT()
                fill_rect.left = bar_x
                fill_rect.top = bar_y
                fill_rect.right = bar_x + fill_w
                fill_rect.bottom = bar_y + bar_h
                fill_brush = gdi32.CreateSolidBrush(0x00A54215)
                gdi32.SelectObject(hdc, fill_brush)
                gdi32.RoundRect(hdc, bar_x, bar_y, bar_x + fill_w, bar_y + bar_h, 5, 5)
                gdi32.DeleteObject(fill_brush)

            gdi32.DeleteObject(bg_brush)

            if progress > 0.01:
                pct_text = f"{int(min(progress, 1.0) * 100)}%"
                font = gdi32.CreateFontW(14, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, "Microsoft YaHei")
                old_font = gdi32.SelectObject(hdc, font)
                gdi32.SetTextColor(hdc, 0x00F5A542)
                gdi32.SetBkMode(hdc, 1)
                pct_w = 50
                pct_x = bar_x + (bar_w - pct_w) // 2
                pct_y = bar_y + bar_h + 6
                gdi32.TextOutW(hdc, pct_x, pct_y, pct_text, len(pct_text))
                gdi32.SelectObject(hdc, old_font)
                gdi32.DeleteObject(font)

            user32.ReleaseDC(hwnd, hdc)
            cls._progress = progress
        except Exception:
            pass

    @classmethod
    def close(cls):
        try:
            import pyi_splash
            pyi_splash.close()
        except Exception:
            pass
        if cls._hwnd:
            try:
                import ctypes
                ctypes.windll.user32.PostMessageW(cls._hwnd, 0x0010, 0, 0)
            except Exception:
                pass
            cls._hwnd = None


class MainWindow(QMainWindow):
    """主窗口"""
    log_signal = pyqtSignal(str, str)
    enable_buttons_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"云集智能音乐创意台 v{VERSION}")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D0D0D;
            }
        """)
        
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        
        if hasattr(sys, '_MEIPASS'):
            self.base_dir = os.path.abspath(os.path.dirname(sys.executable))
            app_dir = os.path.join(self.base_dir, 'app')
            if os.path.exists(app_dir):
                self.base_dir = app_dir
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            while not os.path.exists(os.path.join(self.base_dir, 'acestep')) and not os.path.exists(os.path.join(self.base_dir, '2、run_gradio.ps1')):
                parent_dir = os.path.dirname(self.base_dir)
                if parent_dir == self.base_dir:
                    break
                self.base_dir = parent_dir
        
        self.service_processes: Dict[str, ServiceProcess] = {}
        self.service_cards: Dict[str, ServiceCard] = {}
        self.is_starting = False
        self.current_project = "qinglong"
        self.browsers = {"系统默认": "system"}
        self.selected_browser = "system"
        self.custom_browser_path = ""
        self.download_sources = {
            "auto": "自动检测",
            "huggingface": "HuggingFace",
            "modelscope": "ModelScope",
            "huggingface-cn": "HuggingFace (国内镜像)"
        }
        self.selected_download_source = "auto"
        self.model_list = []
        self._model_list_loaded = False
        self.model_download_thread = None
        self.is_downloading = False
        self.model_delete_thread = None
        self.is_deleting = False
        self.model_verify_thread = None
        self.is_verifying = False
        self.current_operation_model = None
        self.model_page = None
        self.model_manager_widget = None
        self.version_page = None
        self.version_manager_widget = None
        self._home_loaded = False
        
        self._setup_ui_skeleton()
        
        self.log_signal.connect(self._append_log_to_ui)
        self.enable_buttons_signal.connect(self._enable_buttons)
        
        self.resize(1200, 1100)
        
        QTimer.singleShot(0, self._deferred_init)
    
    def _setup_ui_skeleton(self):
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
            }
            QPushButton:disabled {
                background-color: #333333;
                border-color: #333333;
                color: #757575;
            }
            QLabel {
                color: #F0F0F0;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: #0D0D0D;
            }
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        nav_bar = QFrame()
        nav_bar.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: none;
                border-bottom: 2px solid #333333;
                border-radius: 0px;
            }
        """)
        nav_bar_layout = QHBoxLayout(nav_bar)
        nav_bar_layout.setSpacing(15)
        nav_bar_layout.setContentsMargins(15, 12, 15, 12)
        
        menu_button_style = """
            QPushButton {
                background-color: #252525;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #444444;
            }
            QPushButton:checked {
                background-color: #1565C0;
                border-color: #1976D2;
                color: #FFFFFF;
            }
            QPushButton:checked:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """
        
        self.btn_home = QPushButton("🚀 运行服务")
        self.btn_home.setCheckable(True)
        self.btn_home.setChecked(True)
        self.btn_home.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_home.setStyleSheet(menu_button_style)
        self.btn_home.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_home.clicked.connect(lambda: self._switch_page(0))
        nav_bar_layout.addWidget(self.btn_home)
        
        self.btn_version_nav = QPushButton("🔄 软件更新")
        self.btn_version_nav.setCheckable(True)
        self.btn_version_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_version_nav.setStyleSheet(menu_button_style)
        self.btn_version_nav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_version_nav.clicked.connect(lambda: self._switch_page(2))
        nav_bar_layout.addWidget(self.btn_version_nav)
        
        self.btn_model_nav = QPushButton("📦 模型管理")
        self.btn_model_nav.setCheckable(True)
        self.btn_model_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_model_nav.setStyleSheet(menu_button_style)
        self.btn_model_nav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_model_nav.clicked.connect(lambda: self._switch_page(1))
        nav_bar_layout.addWidget(self.btn_model_nav)
        
        main_layout.addWidget(nav_bar)
        
        self.page_stack = QStackedWidget()
        
        self.home_page = QWidget()
        self.home_layout = QVBoxLayout(self.home_page)
        self.home_layout.setSpacing(8)
        self.home_layout.setContentsMargins(12, 12, 12, 12)
        loading_label = QLabel("⏳ 正在加载...")
        loading_label.setStyleSheet("color: #888888; font-size: 16px; padding: 40px;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.home_layout.addWidget(loading_label)
        self.page_stack.addWidget(self.home_page)
        
        self.page_stack.addWidget(QWidget())
        self.page_stack.addWidget(QWidget())
        
        main_layout.addWidget(self.page_stack, 1)
        
        NativeSplash.draw_progress(0.2, "正在初始化框架...")
    
    def _deferred_init(self):
        NativeSplash.draw_progress(0.3, "正在加载配置...")
        
        self.config = ConfigManager(self.base_dir)
        
        NativeSplash.draw_progress(0.4, "正在检测浏览器...")
        
        self.browsers = self._detect_browsers()
        self.selected_browser = self.config.get("browser.default", "system")
        self.custom_browser_path = self.config.get("browser.custom_path", "")
        if self.custom_browser_path and os.path.exists(self.custom_browser_path):
            self.browsers["自定义浏览器"] = self.custom_browser_path
        self.selected_download_source = self.config.get("download.source", "auto")
        
        NativeSplash.draw_progress(0.5, "正在构建主界面...")
        
        while self.home_layout.count():
            item = self.home_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._populate_home_page()
        
        NativeSplash.draw_progress(0.75, "正在启动监控...")
        
        self._setup_monitor()
        self._setup_tray()
        
        size = self.config.get("ui.window_size", {"width": 1200, "height": 1100})
        self.resize(size["width"], size["height"])
        
        self._home_loaded = True
        
        NativeSplash.draw_progress(1.0, "加载完成！")
    
    def _populate_home_page(self):
        """填充首页内容到已有的home_layout"""
        
        # 日志区域（高度紧凑结构：系统信息+日志融合）
        self.log_group = QFrame()
        self.log_group.setFrameShape(QFrame.Shape.StyledPanel)
        self.log_group.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 6px;
            }
        """)
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setSpacing(6)
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题+系统信息（紧凑的一行）
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        log_title = QLabel("📋 运行日志")
        log_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        log_title.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(log_title)
        
        self.system_info_label = QLabel()
        self.system_info_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #999999;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        self.system_info_label.setWordWrap(False)
        header_layout.addWidget(self.system_info_label, 1)
        
        # 自动滚动开关
        self.auto_scroll_switch = QPushButton("🔄 自动滚动")
        self.auto_scroll_switch.setCheckable(True)
        self.auto_scroll_switch.setChecked(True)
        self.auto_scroll_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_scroll_switch.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: 1px solid #388E3C;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2E7D32;
            }
            QPushButton:!checked {
                background-color: #424242;
                border-color: #616161;
            }
        """)
        self.auto_scroll_switch.clicked.connect(self._on_auto_scroll_toggled)
        header_layout.addWidget(self.auto_scroll_switch)
        
        # 展开窗口开关
        self.expand_switch = QPushButton("📐 展开窗口")
        self.expand_switch.setCheckable(True)
        self.expand_switch.setChecked(False)
        self.expand_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_switch.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: 1px solid #616161;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #1565C0;
                border-color: #1976D2;
            }
        """)
        self.expand_switch.clicked.connect(self._on_expand_toggled)
        header_layout.addWidget(self.expand_switch)
        
        log_layout.addWidget(header_container)
        
        # 分隔线（更细）
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #2A2A2A;")
        separator.setFixedHeight(1)
        log_layout.addWidget(separator)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(180)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                border: 1px solid #2A2A2A;
                border-radius: 4px;
                padding: 8px;
                color: #CCCCCC;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_output)
        
        self.home_layout.addWidget(self.log_group, 1)
        
        # 服务区域容器（用于展开/收起）
        self.services_container = QWidget()
        self.services_layout = QVBoxLayout(self.services_container)
        self.services_layout.setSpacing(8)
        self.services_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建设置面板容器
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # 加载系统信息或显示初始化流程（延迟执行，避免启动时弹窗）
        QTimer.singleShot(500, self._check_and_load_system_info)
        
        # 1. 浏览器设置面板 - 一排横向布局
        browser_panel = QFrame()
        browser_panel.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        browser_layout = QHBoxLayout(browser_panel)
        browser_layout.setSpacing(12)
        browser_layout.setContentsMargins(12, 10, 12, 10)
        
        browser_label = QLabel("🌐 浏览器:")
        browser_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #FFFFFF;")
        browser_layout.addWidget(browser_label)
        
        self.browser_combo = QComboBox()
        self.browser_combo.setStyleSheet("""
            QComboBox {
                background-color: #252525;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 30px 6px 10px;
                font-size: 12px;
                min-width: 180px;
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
        
        # 添加浏览器选项，包括自定义选项
        for browser_name, browser_path in self.browsers.items():
            self.browser_combo.addItem(browser_name, browser_path)
        
        # 添加自定义浏览器选项
        self.browser_combo.addItem("📁 自定义浏览器...", "custom")
        
        # 设置当前选中的浏览器
        is_custom = self.selected_browser == "自定义浏览器" or self.selected_browser == "custom"
        if is_custom and self.custom_browser_path:
            # 如果是自定义模式，检查是否在列表中
            found = False
            for i in range(self.browser_combo.count()):
                if self.browser_combo.itemText(i) == self.selected_browser:
                    self.browser_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                # 选择自定义选项
                for i in range(self.browser_combo.count()):
                    if self.browser_combo.itemData(i) == "custom":
                        self.browser_combo.setCurrentIndex(i)
                        break
        else:
            # 选择系统浏览器
            for i in range(self.browser_combo.count()):
                if self.browser_combo.itemText(i) == self.selected_browser:
                    self.browser_combo.setCurrentIndex(i)
                    break
        
        # 保存浏览器选择
        self.browser_combo.currentIndexChanged.connect(self._on_browser_changed)
        
        browser_layout.addWidget(self.browser_combo)
        
        # 自定义浏览器路径（默认隐藏）
        self.browser_path_edit = QLineEdit()
        self.browser_path_edit.setReadOnly(False)
        self.browser_path_edit.setPlaceholderText("粘贴或输入浏览器路径...")
        self.browser_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #121212;
                color: #F0F0F0;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 12px;
            }
            QLineEdit:hover, QLineEdit:focus {
                border-color: #1976D2;
            }
        """)
        self.browser_path_edit.setText(self.custom_browser_path)
        self.browser_path_edit.setVisible(is_custom)
        self.browser_path_edit.textChanged.connect(self._on_custom_browser_path_changed)
        browser_layout.addWidget(self.browser_path_edit, 1)
        
        self.btn_select_browser = QPushButton("📂 选择")
        self.btn_select_browser.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #E0E0E0;
                border: 1px solid #1976D2;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """)
        self.btn_select_browser.clicked.connect(self._select_custom_browser)
        self.btn_select_browser.setVisible(is_custom)
        browser_layout.addWidget(self.btn_select_browser)
        
        settings_layout.addWidget(browser_panel)
        
        self.services_layout.addWidget(settings_container)
        
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
        
        self.services_layout.addWidget(self.music_group)
        
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
        
        self.services_layout.addWidget(self.qinglong_group)
        
        # 功能按钮区域
        start_btn_layout = QVBoxLayout()
        
        function_buttons = QHBoxLayout()
        function_buttons.setSpacing(15)
        
        self.btn_deploy_maintain = QPushButton("⚙️ 部署维护")
        self.btn_deploy_maintain.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: 2px solid #388E3C;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #388E3C;
                border-color: #388E3C;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(46, 125, 50, 0.3);
            }
        """)
        self.btn_deploy_maintain.clicked.connect(self._deploy_maintenance)
        function_buttons.addWidget(self.btn_deploy_maintain)
        
        self.btn_stop_all = QPushButton("⏹ 退出服务")
        self.btn_stop_all.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: 2px solid #1976D2;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
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
        function_buttons.addWidget(self.btn_stop_all)
        
        start_btn_layout.addLayout(function_buttons)
        
        # 启动按钮区域（放在最下面）
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
        self.services_layout.addLayout(start_btn_layout)
        
        self.home_layout.addWidget(self.services_container)
    
    def _on_auto_scroll_toggled(self, checked):
        """自动滚动开关切换"""
        if checked:
            self.auto_scroll_switch.setStyleSheet("""
                QPushButton {
                    background-color: #2E7D32;
                    color: white;
                    border: 1px solid #388E3C;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
        else:
            self.auto_scroll_switch.setStyleSheet("""
                QPushButton {
                    background-color: #424242;
                    color: white;
                    border: 1px solid #616161;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
    
    def _on_expand_toggled(self, checked):
        """展开窗口开关切换"""
        if checked:
            self.services_container.hide()
            self.expand_switch.setText("📐 收起窗口")
        else:
            self.services_container.show()
            self.expand_switch.setText("📐 展开窗口")
    
    def _create_version_page(self):
        """创建版本管理器页面"""
        from version_manager import HybridVersionManagerDialog
        
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建版本管理器容器
        self.version_manager_widget = HybridVersionManagerDialog(self, self.base_dir, as_widget=True)
        
        layout.addWidget(self.version_manager_widget)
        
        return page
    
    def _create_model_page(self):
        """创建模型管理器页面"""
        from version_manager import ModelManagerDialog
        
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建模型管理器容器
        self.model_manager_widget = ModelManagerDialog(self, self, as_widget=True)
        
        layout.addWidget(self.model_manager_widget)
        
        return page
    
    def _switch_page(self, index):
        """切换页面"""
        self.btn_home.setChecked(index == 0)
        self.btn_model_nav.setChecked(index == 1)
        self.btn_version_nav.setChecked(index == 2)
        
        if index == 1 and self.model_page is None:
            self.model_page = self._create_model_page()
            self.page_stack.removeWidget(self.page_stack.widget(1))
            self.page_stack.insertWidget(1, self.model_page)
        
        if index == 2 and self.version_page is None:
            self.version_page = self._create_version_page()
            self.page_stack.removeWidget(self.page_stack.widget(2))
            self.page_stack.insertWidget(2, self.version_page)
        
        self.page_stack.setCurrentIndex(index)
        
        if index == 1 and self.model_manager_widget is not None:
            if not self._model_list_loaded:
                self._model_list_loaded = True
                self._load_model_list()
            self.model_manager_widget._update_ui()
        
        if index == 2 and self.version_manager_widget is not None:
            if not self.version_manager_widget._versions_loaded:
                QTimer.singleShot(300, self._delayed_load_versions)
    
    def _delayed_load_versions(self):
        """延迟加载版本列表"""
        if self.version_manager_widget is not None:
            vm = self.version_manager_widget
            if not vm._git_repo_checked:
                vm._git_repo_checked = True
                if hasattr(vm, 'mode_buttons_widget'):
                    vm.mode_buttons_widget.setVisible(True)
                    vm.btn_mode_exe.setChecked(False)
                    vm.btn_mode_git.setChecked(True)
            vm._load_versions(force=True)
    
    def _setup_monitor(self):
        """设置监控"""
        self.monitor = ServiceMonitor(check_interval=3)
        self.monitor.status_changed.connect(self._on_status_changed)
        self.monitor.start()
    
    def _setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip(f"ACE-Step 启动器 v{VERSION}")
        
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
        except Exception as e:
            pass
        
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
    
    def _append_log_to_ui(self, message: str, color: str):
        """在主线程中添加日志到UI（由信号调用）"""
        if not hasattr(self, 'log_output') or self.log_output is None:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_output.append(html)
        # 只有在自动滚动开关打开时才滚动到底部
        if hasattr(self, 'auto_scroll_switch') and self.auto_scroll_switch.isChecked():
            scrollbar = self.log_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _log(self, message: str, color: str = "#00FF00"):
        """添加日志（线程安全）"""
        self.log_signal.emit(message, color)
    
    def _start_project(self, project_id: str):
        """启动单个项目"""
        if self.is_starting:
            self._log("正在启动中，请稍候...", "#616161")
            return
        
        self.is_starting = True
        self.btn_deploy_maintain.setEnabled(False)
        self.btn_start_music.setEnabled(False)
        self.btn_start_qinglong.setEnabled(False)
        self.btn_stop_all.setEnabled(False)
        
        self.start_thread = threading.Thread(target=self._start_project_services, args=(project_id,))
        self.start_thread.start()
    
    def _show_version_manager(self):
        """切换到版本管理器页面"""
        self._switch_page(1)
    
    def _on_show_more_versions(self):
        """处理"查看更多版本"点击事件 - 延迟打开对话框以避免闪烁"""
        from PyQt6.QtCore import QTimer
        # 使用单次定时器延迟打开对话框，确保菜单已经完全关闭
        QTimer.singleShot(100, self._open_full_version_dialog)
    
    def _open_full_version_dialog(self):
        """打开完整的版本管理器对话框"""
        try:
            from version_manager import VersionManagerDialog
            dialog = VersionManagerDialog(self, self.base_dir)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开版本管理器失败:\n{str(e)}")
    
    def _show_model_manager(self):
        """切换到模型管理器页面"""
        self._switch_page(2)
    
    def _start_project_services(self, project_id: str):
        """启动项目服务"""
        try:
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
                venv_path = os.path.join(self.base_dir, "scripts", ".venv")
                if not os.path.exists(venv_path):
                    self._log("[错误] 虚拟环境不存在，请先运行部署维护", "#F44336")
                    self.is_starting = False
                    self._enable_buttons()
                    return
                
                # 检查虚拟环境中是否有 loguru 模块，确保依赖已安装
                try:

                    
                    python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                    self._log(f"[信息] 检查虚拟环境 Python: {python_exe}")
                    
                    process = hidden_popen(
                        [python_exe, "-c", "import loguru"],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=10)
                    
                    if process.returncode != 0:
                        self._log(f"[警告] 虚拟环境依赖检查失败 (返回码: {process.returncode})", "#FF9800")
                        if stderr:
                            self._log(f"[调试] 错误信息: {stderr.strip()}", "#FF9800")
                        self._log("[信息] 尝试继续启动，依赖可能已安装...", "#FF9800")
                    else:
                        self._log("✓ 虚拟环境依赖检查通过")
                    
                    try:
                        process = hidden_popen(
                            [python_exe, "-c", "import transformers; v=transformers.__version__; major=int(v.split('.')[0]); print(v); exit(0 if major<5 else 1)"],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(timeout=10)
                        if process.returncode != 0:
                            installed_ver = stdout.strip() if stdout.strip() else "unknown"
                            self._log(f"[错误] transformers 版本不兼容: {installed_ver} (需要 <5.0)", "#F44336")
                            self._log("[信息] 正在自动修复: 降级 transformers 到兼容版本...", "#FF9800")
                            fix_process = hidden_popen(
                                [python_exe, "-m", "pip", "install", "transformers>=4.51.0,<4.58.0", "--quiet"],
                                cwd=self.base_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            fix_stdout, fix_stderr = fix_process.communicate(timeout=120)
                            if fix_process.returncode == 0:
                                self._log("✓ transformers 已降级到兼容版本", "#4CAF50")
                            else:
                                self._log(f"[错误] 自动修复失败: {fix_stderr.strip()}", "#F44336")
                                self._log("[建议] 请手动运行: pip install \"transformers>=4.51.0,<4.58.0\"", "#FF9800")
                        else:
                            self._log(f"✓ transformers 版本兼容: {stdout.strip()}")
                    except Exception as e:
                        self._log(f"[警告] 检查 transformers 版本失败: {e}", "#FF9800")
                except Exception as e:
                    self._log(f"[警告] 检查虚拟环境依赖失败: {e}，尝试继续启动...", "#FF9800")
                
                ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
                self._log(f"[调试] 启动时 ace-step-ui 路径: {ace_step_ui_path}")
                if os.path.exists(ace_step_ui_path):
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    self._log(f"[调试] 启动时 node_modules 路径: {node_modules_path}")
                    if not os.path.exists(node_modules_path):
                        self._log("[警告] ace-step-ui node_modules 不存在，尝试直接启动...", "#FF9800")
                        self._log("[提示] 如果启动失败，请先运行部署维护安装依赖", "#FF9800")
            
            if project_id in ["qinglong", "music"]:
                try:
                    api_port = 8001
                    api_running = self.monitor._check_port(api_port)
                    
                    if not api_running:
                        self._log("核心 API 服务未运行，正在启动...")
                        api_script = os.path.join(self.base_dir, "scripts", "3、run_server.ps1")
                        if not os.path.exists(api_script):
                            self._log(f"[错误] API 服务脚本不存在: {api_script}", "#F44336")
                            self.is_starting = False
                            self._enable_buttons()
                            return
                        

                        
                        process = hidden_popen(
                            ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", api_script],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        self.api_process = process
                        
                        def read_api_output():
                            while process.poll() is None:
                                line = process.stdout.readline()
                                if line:
                                    self._log(f"[API 服务] {line.strip()}")
                                line_err = process.stderr.readline()
                                if line_err:
                                    self._log(f"[API 服务] {line_err.strip()}", "#FF9800")
                        
                        threading.Thread(target=read_api_output, daemon=True).start()
                        
                        self._log("等待核心 API 服务就绪（模型加载可能需要较长时间）...")
                        api_ready = False
                        max_wait = 300
                        waited = 0
                        while waited < max_wait and not api_ready:
                            if self.monitor._check_port(api_port):
                                api_ready = True
                            else:
                                time.sleep(2)
                                waited += 2
                                if waited % 30 == 0 and waited > 0:
                                    self._log(f"[信息] 仍在等待 API 服务就绪... (已等待 {waited} 秒)", "#FF9800")
                        if not api_ready:
                            self._log("[错误] 核心 API 服务启动超时", "#F44336")
                            self.is_starting = False
                            self._enable_buttons()
                            return
                        self._log("✓ 核心 API 服务已就绪")
                    else:
                        self._log("✓ 核心 API 服务已运行，跳过启动步骤")
                except Exception as e:
                    self._log(f"[错误] 启动API服务失败: {e}", "#F44336")
                    import traceback
                    self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
                    self.is_starting = False
                    self._enable_buttons()
                    return
            
            if project_id == "qinglong":
                # 青龙训练器：先启动后端，等后端就绪后再启动前端
                self._log("青龙训练器：先后端，后前端")
                
                # 1. 启动后端
                backend_service_id = "qinglong_backend"
                backend_service = project["services"]["backend"]
                self._log(f"正在启动 {backend_service['name']}...")
                backend_success = self._start_single_service(project_id, backend_service_id, backend_service["name"])
                
                if not backend_success:
                    self._log(f"[错误] {backend_service['name']} 启动失败", "#F44336")
                    all_success = False
                else:
                    started_services.append(backend_service_id)
                    
                    # 等待后端就绪
                    self._log(f"等待 {backend_service['name']} 就绪...")
                    backend_ready = False
                    max_wait = 120
                    waited = 0
                    while waited < max_wait and not backend_ready:
                        if self.monitor._check_port(backend_service["port"]):
                            backend_ready = True
                        else:
                            time.sleep(2)
                            waited += 2
                    
                    if not backend_ready:
                        self._log(f"[错误] {backend_service['name']} 启动超时", "#F44336")
                        all_success = False
                    else:
                        self._log(f"✓ {backend_service['name']} 已就绪")
                        
                        # 2. 启动前端
                        frontend_service_id = "qinglong_frontend"
                        frontend_service = project["services"]["frontend"]
                        self._log(f"正在启动 {frontend_service['name']}...")
                        frontend_success = self._start_single_service(project_id, frontend_service_id, frontend_service["name"])
                        
                        if frontend_success:
                            started_services.append(frontend_service_id)
                        else:
                            all_success = False
            else:
                # 其他项目：并行启动所有服务
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
                try:
                    self._log("等待所有服务就绪...")
                    all_ready = False
                    max_wait = 60
                    start_time = time.time()
                    
                    while (time.time() - start_time) < max_wait and not all_ready:
                        all_ready = True
                        for service_id in started_services:
                            if not self.monitor._check_port(SERVICES[service_id]["port"]):
                                all_ready = False
                                break
                        
                        if not all_ready:
                            time.sleep(10)
                    
                    waited = int(time.time() - start_time)
                    if all_ready:
                        self._log(f"✓ 所有服务已就绪 (耗时 {waited} 秒)，正在打开浏览器...")
                        for service_id in started_services:
                            if "_" in service_id:
                                base_service_id = service_id.split("_", 1)[1]
                            else:
                                base_service_id = service_id
                            
                            auto_open = self.config.get(f"service_settings.{base_service_id}.auto_open", True)
                            if auto_open:
                                if project_id == "qinglong" and base_service_id == "frontend":
                                    self._open_service(service_id)
                                elif project_id != "qinglong":
                                    self._open_service(service_id)
                except Exception as e:
                    self._log(f"[警告] 等待服务就绪或打开浏览器失败: {e}", "#FF9800")
            
            self._log("")
            self._log("========================================")
            if all_success:
                self._log(f"✓ {project['name']} 启动完成！", "#E53935")
            else:
                self._log(f"⚠ {project['name']} 启动失败，请检查日志", "#616161")
            self._log("========================================")
            
            self._generate_startup_diagnosis(project_id, started_services, all_success)
        except Exception as e:
            self._log(f"[错误] 启动项目服务失败: {e}", "#F44336")
            import traceback
            self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
        finally:
            self.is_starting = False
            try:
                self._enable_buttons()
            except:
                pass
    
    def _enable_buttons(self):
        """启用所有按钮"""
        self.btn_deploy_maintain.setEnabled(True)
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

            
            powershell_paths = [
                "powershell.exe",
                "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                "C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
            ]
            
            found = False
            for powershell_exe in powershell_paths:
                try:
                    process = hidden_popen(
                        [powershell_exe, "-Version"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
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
                    process = hidden_popen(
                        ["where", "powershell"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
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
            venv_path = os.path.join(self.base_dir, "scripts", ".venv")
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
            install_script = os.path.join(self.base_dir, "scripts", "1、install-uv-qinglong.ps1")
            if os.path.exists(install_script):
                try:

                    
                    process = hidden_popen(
                        ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_script],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
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
            script_path = os.path.join(self.base_dir, "scripts", script)
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
    
    def _install_minimal_dependencies(self, venv_python, uv_path, scripts_dir, env):
        """安装最小化的关键依赖（备用方案）"""
        self._log("[信息] 正在安装关键依赖...")

        
        minimal_deps = [
            "loguru",
            "psutil",
            "fastapi",
            "uvicorn",
            "toml"
        ]
        
        for dep in minimal_deps:
            try:
                self._log(f"[信息] 正在安装: {dep}")
                process = hidden_popen(
                    [uv_path, "pip", "install", dep],
                    cwd=scripts_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                stdout, _ = process.communicate(timeout=120)
                if process.returncode == 0:
                    self._log(f"✓ {dep} 安装完成")
                else:
                    self._log(f"[警告] {dep} 安装返回码: {process.returncode}", "#FF9800")
            except Exception as e:
                self._log(f"[警告] 安装 {dep} 失败: {e}", "#FF9800")
    
    def _quick_check_dependencies(self, venv_python):
        """快速检查关键依赖是否已安装 - 返回True表示所有依赖都OK"""

        
        deps_to_check = ["loguru", "psutil", "torch", "torchaudio", "transformers", "diffusers", "gradio", "peft"]
        all_ok = True
        
        for dep in deps_to_check:
            try:
                process = hidden_popen(
                    [venv_python, "-c", f"import {dep}"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=10)
                if process.returncode != 0:
                    all_ok = False
                    break
            except Exception:
                all_ok = False
                break
        
        return all_ok
    
    def _verify_dependencies(self, venv_python):
        """验证关键依赖是否安装，区分必须依赖和可选加速项"""

        
        # 必须依赖 - 缺失则功能不可用
        required_deps = [
            ("loguru", "日志库"),
            ("psutil", "系统监控"),
            ("torch", "PyTorch 核心"),
            ("torchaudio", "音频处理"),
            ("transformers", "模型加载"),
            ("diffusers", "扩散模型"),
            ("peft", "LoRA/训练"),
            ("lycoris", "LoKr 训练"),
        ]
        # 可选加速 - 缺失只影响性能，不影响功能
        optional_deps = [
            ("flash_attn", "Flash Attention 加速推理"),
        ]
        
        all_ok = True
        
        self._log("[信息] 验证必须依赖...")
        for dep, desc in required_deps:
            try:
                process = hidden_popen(
                    [venv_python, "-c", f"import {dep}"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=10)
                if process.returncode == 0:
                    self._log(f"✓ {dep} ({desc}) 已安装")
                else:
                    self._log(f"✗ {dep} ({desc}) 未安装", "#FF9800")
                    all_ok = False
            except Exception as e:
                self._log(f"✗ 检查 {dep} 失败: {e}", "#FF9800")
                all_ok = False
        
        try:
            process = hidden_popen(
                [venv_python, "-c", "import transformers; v=transformers.__version__; major=int(v.split('.')[0]); print(v); exit(0 if major<5 else 1)"],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=10)
            if process.returncode != 0:
                installed_ver = stdout.strip() if stdout.strip() else "unknown"
                self._log(f"✗ transformers 版本不兼容: {installed_ver} (需要 <5.0，5.x 会导致模型加载失败)", "#F44336")
                all_ok = False
            else:
                self._log(f"✓ transformers 版本兼容: {stdout.strip()}")
        except Exception as e:
            self._log(f"⚠ 检查 transformers 版本失败: {e}", "#FF9800")
        
        self._log("[信息] 验证可选加速项...")
        for dep, desc in optional_deps:
            try:
                process = hidden_popen(
                    [venv_python, "-c", f"import {dep}; print({dep}.__version__)"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=10)
                if process.returncode == 0:
                    version = stdout.strip()
                    self._log(f"✓ {dep} ({desc}) 已安装 v{version}")
                else:
                    self._log(f"⚠ {dep} ({desc}) 未安装 - 不影响功能，但推理速度会较慢", "#FF9800")
            except Exception:
                self._log(f"⚠ {dep} ({desc}) 检测失败 - 不影响功能", "#FF9800")
        
        if all_ok:
            self._log("✓ 关键依赖验证通过")
        else:
            self._log("[警告] 部分必须依赖缺失", "#FF9800")
    
    def _quick_verify_environment(self):
        """快速验证环境 - 只做检查不做安装"""
        self._log("========================================")
        self._log("开始快速环境验证...")
        self._log("=======================================")
        
        try:
            # 1. 检查 PowerShell
            self._log("1. 检查 PowerShell...")
            try:

                process = hidden_popen(
                    ["powershell.exe", "-WindowStyle", "Hidden", "-Version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=5)
                if process.returncode == 0:
                    version = stdout.strip() if stdout.strip() else "PowerShell"
                    self._log(f"✓ PowerShell 已安装: {version}")
            except:
                pass
            
            # 2. 检查 Node.js
            self._log("2. 检查 Node.js...")
            try:

                portable_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
                portable_node22_dir = os.path.join(self.base_dir, "tools", "node-v22.22.2-win-x64", "node-v22.22.2-win-x64")
                node_paths = [
                    os.path.join(portable_node24_dir, "node.exe"),
                    os.path.join(portable_node22_dir, "node.exe"),
                    "node.exe",
                ]
                for node_exe in node_paths:
                    try:
                        process = hidden_popen(
                            [node_exe, "--version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0 and stdout.strip():
                            self._log(f"✓ Node.js 已安装: {stdout.strip()}")
                            break
                    except:
                        continue
            except:
                pass
            
            # 3. 检查 uv
            self._log("3. 检查 uv...")
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            if os.path.exists(uv_path):
                self._log("✓ uv 已安装")
            
            # 4. 检查虚拟环境
            self._log("4. 检查虚拟环境...")
            scripts_dir = os.path.join(self.base_dir, "scripts")
            venv_path = os.path.join(scripts_dir, ".venv")
            if os.path.exists(venv_path):
                self._log("✓ 虚拟环境已存在")
            
            # 5. 验证关键依赖
            self._log("5. 验证关键依赖...")
            venv_python = os.path.join(scripts_dir, ".venv", "Scripts", "python.exe")
            self._verify_dependencies(venv_python)
            
            # 6. 检查 git 子模块
            self._log("6. 检查 git 子模块...")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            if os.path.exists(ace_step_ui_path):
                git_dir = os.path.join(ace_step_ui_path, ".git")
                if os.path.exists(git_dir):
                    self._log("✓ ace-step-ui git 子模块已初始化")
                else:
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    if os.path.exists(node_modules_path):
                        self._log("✓ ace-step-ui node_modules 已存在")
            
            # 7. 检查前端依赖
            self._log("7. 检查前端依赖...")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            package_json_path = os.path.join(ace_step_ui_path, "package.json")
            if os.path.exists(package_json_path):
                node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                if os.path.exists(node_modules_path):
                    self._log("✓ 前端依赖已安装")
            
            self._log("✓ 快速环境验证完成")
            
        except Exception as e:
            self._log(f"[警告] 快速验证过程中出错: {e}", "#FF9800")
    
    def _smart_fix_environment(self):
        """智能修复环境 - 自动检测并修复所有环境问题"""
        self._log("========================================")
        self._log("开始智能环境修复...")
        self._log("=======================================")
        
        has_errors = False
        has_warnings = False
        
        try:
            # 1. 检查并修复 PowerShell
            self._log("1. 检查 PowerShell...")
            powershell_available = False
            
            try:

                
                powershell_paths = [
                    "powershell.exe",
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
                ]
                
                for powershell_exe in powershell_paths:
                    try:
                        process = hidden_popen(
                            [powershell_exe, "-Version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
                        process = hidden_popen(
                            ["where", "powershell"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
            
            # 2. 检查 Node.js
            self._log("2. 检查 Node.js...")
            node_available = False
            
            try:

                
                portable_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
                portable_node22_dir = os.path.join(self.base_dir, "tools", "node-v22.22.2-win-x64", "node-v22.22.2-win-x64")
                node_paths = [
                    os.path.join(portable_node24_dir, "node.exe"),
                    os.path.join(portable_node22_dir, "node.exe"),
                    "node.exe",
                    "C:/Program Files/nodejs/node.exe",
                    "C:/Program Files (x86)/nodejs/node.exe",
                ]
                
                for node_exe in node_paths:
                    try:
                        process = hidden_popen(
                            [node_exe, "--version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0 and stdout.strip():
                            self._log(f"✓ Node.js 已安装: {stdout.strip()}")
                            node_available = True
                            break
                    except:
                        continue
                
                if not node_available:
                    self._log("[信息] Node.js 未安装，请运行部署维护自动安装便携版", "#FF9800")
            except Exception as e:
                self._log(f"[错误] 检查 Node.js 失败: {e}", "#F44336")
                return
            
            # 3. 检查并安装 uv
            self._log("3. 检查并安装 uv...")
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            
            if not os.path.exists(uv_path):
                self._log("[信息] uv 未安装，正在安装...")
                try:
                    # 下载并安装 uv
                    install_uv_script = os.path.join(self.base_dir, "install_uv.bat")
                    if os.path.exists(install_uv_script):

                        
                        process = hidden_popen(
                            ["cmd.exe", "/c", install_uv_script],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
                        

                        
                        process = hidden_popen(
                            ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
            
            # 4. 检查并创建虚拟环境
            self._log("4. 检查并创建虚拟环境...")
            scripts_dir = os.path.join(self.base_dir, "scripts")
            venv_path = os.path.join(scripts_dir, ".venv")
            
            if not os.path.exists(venv_path):
                self._log("[信息] 虚拟环境不存在，正在创建...")
                try:
                    # 使用 uv 创建虚拟环境

                    
                    process = hidden_popen(
                        [uv_path, "venv"],
                        cwd=scripts_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
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
            
            # 5. 安装项目依赖
            self._log("5. 检查项目依赖...")
            try:
                venv_python = os.path.join(scripts_dir, ".venv", "Scripts", "python.exe")
                pyproject_toml_path = os.path.join(scripts_dir, "pyproject.toml")
                install_env_ps1 = os.path.join(scripts_dir, "install-env.ps1")
                
                # 先快速验证关键依赖是否已安装
                all_deps_ok = self._quick_check_dependencies(venv_python)
                
                if all_deps_ok:
                    self._log("✓ 关键依赖已完整安装，跳过依赖安装步骤")
                elif os.path.exists(pyproject_toml_path):
                    # 关键依赖缺失，需要安装
                    self._log("[信息] 检测到依赖缺失，开始安装...")
                    
                    # 方案1: 尝试使用 uv sync
                    self._log("[信息] 方案1: 使用 uv sync 安装完整依赖...")
                    self._log("[信息] 这可能需要较长时间，请耐心等待...")

                    
                    # 设置国内镜像源
                    env = os.environ.copy()
                    env["UV_INDEX_URL"] = "https://pypi.tuna.tsinghua.edu.cn/simple/"
                    env["UV_EXTRA_INDEX_URL"] = "https://download.pytorch.org/whl/cu128"
                    
                    success = False
                    
                    # 尝试 uv sync
                    process = hidden_popen(
                        [uv_path, "sync"],
                        cwd=scripts_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=env
                    )
                    
                    try:
                        stdout, _ = process.communicate(timeout=1200)
                        
                        if stdout:
                            for line in stdout.splitlines():
                                if line.strip():
                                    self._log(f"[安装依赖] {line.strip()}")
                        
                        if process.returncode == 0:
                            self._log("✓ 项目依赖安装完成")
                            success = True
                        else:
                            self._log(f"[警告] uv sync 返回码: {process.returncode}", "#FF9800")
                    except subprocess.TimeoutExpired:
                        process.kill()
                        self._log("[警告] uv sync 超时(20分钟)", "#FF9800")
                    
                    # 如果 uv sync 失败，尝试方案2: 使用 install-env.ps1
                    if not success and os.path.exists(install_env_ps1):
                        self._log("[信息] 方案2: 使用 install-env.ps1 安装依赖...")
                        try:

                            
                            # 使用 PowerShell 执行脚本
                            ps_process = hidden_popen(
                                ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_env_ps1],
                                cwd=scripts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True
                            )
                            
                            stdout_ps, _ = ps_process.communicate(timeout=1800)
                            
                            if stdout_ps:
                                for line in stdout_ps.splitlines():
                                    if line.strip():
                                        self._log(f"[install-env] {line.strip()}")
                            
                            if ps_process.returncode == 0:
                                self._log("✓ 使用 install-env.ps1 安装完成")
                                success = True
                            else:
                                self._log(f"[警告] install-env.ps1 返回码: {ps_process.returncode}", "#FF9800")
                        except subprocess.TimeoutExpired:
                            ps_process.kill()
                            self._log("[警告] install-env.ps1 超时(30分钟)", "#FF9800")
                        except Exception as e:
                            self._log(f"[警告] install-env.ps1 执行失败: {e}", "#FF9800")
                    
                    # 如果都失败了，使用方案3: 最小化依赖
                    if not success:
                        self._log("[信息] 方案3: 安装最小化关键依赖...", "#FF9800")
                        self._install_minimal_dependencies(venv_python, uv_path, scripts_dir, env)
                        self._log("[警告] 仅安装了最小化依赖，部分功能可能不可用", "#FF9800")
                else:
                    self._log("[警告] pyproject.toml 不存在，跳过依赖安装", "#FF9800")
            except Exception as e:
                self._log(f"[警告] 安装项目依赖失败: {e}", "#FF9800")
            
            # 验证关键依赖是否安装
            self._verify_dependencies(venv_python)
            
            # 6. 检查并初始化git子模块
            self._log("6. 检查git子模块...")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            git_dir = os.path.join(ace_step_ui_path, ".git")
            
            if os.path.exists(ace_step_ui_path):
                # 检查是否是未初始化的git子模块
                if not os.path.exists(git_dir):
                    self._log("[信息] ace-step-ui 是git子模块，当前未初始化，正在初始化...")
                    try:

                        
                        # 初始化并更新子模块
                        process = hidden_popen(
                            ["git", "submodule", "update", "--init", "--recursive"],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )
                        
                        try:
                            stdout, _ = process.communicate(timeout=300)
                            
                            if stdout:
                                for line in stdout.splitlines():
                                    if line.strip():
                                        self._log(f"[初始化子模块] {line.strip()}")
                            
                            if process.returncode == 0:
                                self._log("✓ git子模块初始化完成")
                            else:
                                self._log(f"[警告] git子模块初始化返回码: {process.returncode}", "#FF9800")
                        except subprocess.TimeoutExpired:
                            process.kill()
                            self._log("[警告] git子模块初始化超时(5分钟)，跳过继续", "#FF9800")
                    except Exception as e:
                        self._log(f"[警告] 初始化git子模块失败: {e}", "#FF9800")
                else:
                    self._log("✓ git子模块已初始化")
            else:
                self._log("[警告] ace-step-ui 目录不存在，跳过子模块检查", "#FF9800")
            
            # 7. 安装/修复前端依赖
            self._log("7. 安装/修复前端依赖...")
            self._log(f"[调试] ace-step-ui 路径: {ace_step_ui_path}")
            if os.path.exists(ace_step_ui_path):
                self._log(f"[调试] ace-step-ui 目录存在")
                package_json_path = os.path.join(ace_step_ui_path, "package.json")
                if os.path.exists(package_json_path):
                    self._log(f"[调试] package.json 存在")
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    server_node_modules_path = os.path.join(ace_step_ui_path, "server", "node_modules")
                    self._log(f"[调试] node_modules 路径: {node_modules_path}")
                    
                    # 检查是否需要重新安装
                    need_reinstall = False
                    if not os.path.exists(node_modules_path):
                        need_reinstall = True
                        self._log("[信息] 前端依赖未安装，需要安装...")
                    elif not os.path.exists(server_node_modules_path):
                        need_reinstall = True
                        self._log("[信息] server 依赖未安装，需要安装...")
                    else:
                        # 检查 better-sqlite3 模块是否存在且能正常加载
                        better_sqlite3_path = os.path.join(server_node_modules_path, "better-sqlite3")
                        if not os.path.exists(better_sqlite3_path):
                            need_reinstall = True
                            self._log("[信息] better-sqlite3 模块缺失，需要重新安装...")
                        else:
                            # 尝试用当前 Node.js 测试 better-sqlite3 是否能正常加载
                            self._log("[信息] 检测 better-sqlite3 是否与当前 Node.js 版本匹配...")
                            try:
                                # 查找 Node.js（优先使用 Node.js 22）
                                test_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
                                test_node22_dir = os.path.join(self.base_dir, "tools", "node-v22.22.2-win-x64", "node-v22.22.2-win-x64")
                                
                                test_node_exe = None
                                if os.path.exists(os.path.join(test_node22_dir, "node.exe")):
                                    test_node_exe = os.path.join(test_node22_dir, "node.exe")
                                elif os.path.exists(os.path.join(test_node24_dir, "node.exe")):
                                    test_node_exe = os.path.join(test_node24_dir, "node.exe")
                                
                                if test_node_exe:
                                    # 创建测试脚本
                                    test_script = os.path.join(server_node_modules_path, "..", "test_better_sqlite3.js")
                                    with open(test_script, "w", encoding="utf-8") as f:
                                        f.write("""
try {
    const Database = require('better-sqlite3');
    console.log('better-sqlite3 loaded successfully');
    process.exit(0);
} catch (e) {
    console.error('Error loading better-sqlite3:', e.message);
    process.exit(1);
}
""")
                                    
                                    # 运行测试

                                    
                                    test_process = hidden_popen(
                                        [test_node_exe, test_script],
                                        cwd=os.path.join(ace_step_ui_path, "server"),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True
                                    )
                                    
                                    test_stdout, test_stderr = test_process.communicate(timeout=10)
                                    
                                    # 清理测试文件
                                    if os.path.exists(test_script):
                                        os.remove(test_script)
                                    
                                    if test_process.returncode != 0:
                                        need_reinstall = True
                                        self._log("[信息] better-sqlite3 版本不匹配，需要重新安装...")
                                        if test_stderr:
                                            self._log(f"[调试] {test_stderr.strip()}")
                                    else:
                                        self._log("✓ better-sqlite3 版本匹配")
                            except Exception as e:
                                self._log(f"[警告] 检测 better-sqlite3 失败: {e}，尝试继续...", "#FF9800")
                    
                    if need_reinstall:
                        self._log("[信息] 正在清理旧的 node_modules...")
                        try:
                            import shutil
                            if os.path.exists(node_modules_path):
                                shutil.rmtree(node_modules_path, ignore_errors=True)
                            if os.path.exists(server_node_modules_path):
                                shutil.rmtree(server_node_modules_path, ignore_errors=True)
                            self._log("✓ 旧的 node_modules 已清理")
                        except Exception as e:
                            self._log(f"[警告] 清理 node_modules 失败: {e}", "#FF9800")
                        
                        self._log("[信息] 正在重新安装前端依赖...")
                        self._log("[信息] 这可能需要几分钟，请稍候...")
                        try:
                            # 查找 npm 命令路径
                            portable_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
                            portable_node22_dir = os.path.join(self.base_dir, "tools", "node-v22.22.2-win-x64", "node-v22.22.2-win-x64")
                            
                            npm_cmd = None
                            # 先尝试便携版 Node.js 24
                            if os.path.exists(os.path.join(portable_node24_dir, "node.exe")):
                                self._log(f"[信息] 使用便携版 Node.js 24: {portable_node24_dir}")
                                npm_cmd = os.path.join(portable_node24_dir, "npm.cmd")
                                # 更新环境变量 PATH
                                os.environ["PATH"] = f"{portable_node24_dir};{os.environ.get('PATH', '')}"
                            # 再尝试便携版 Node.js 22
                            elif os.path.exists(os.path.join(portable_node22_dir, "node.exe")):
                                self._log(f"[信息] 使用便携版 Node.js 22: {portable_node22_dir}")
                                npm_cmd = os.path.join(portable_node22_dir, "npm.cmd")
                                # 更新环境变量 PATH
                                os.environ["PATH"] = f"{portable_node22_dir};{os.environ.get('PATH', '')}"
                            # 最后尝试系统 npm
                            else:
                                try:
                                    import shutil
                                    npm_cmd = shutil.which("npm")
                                    if npm_cmd:
                                        self._log("[信息] 使用系统 npm")
                                except Exception:
                                    pass
                            
                            # 设置 Python 环境变量，使用 uv 虚拟环境中的 Python 用于编译 better-sqlite3
                            venv_python = os.path.join(self.base_dir, "scripts", ".venv", "Scripts", "python.exe")
                            if os.path.exists(venv_python):
                                self._log(f"[信息] 设置 Python 路径: {venv_python}")
                                os.environ["PYTHON"] = venv_python
                                os.environ["npm_config_python"] = venv_python
                            
                            if npm_cmd and os.path.exists(npm_cmd):

                                
                                # 先安装根目录依赖
                                self._log("[信息] 安装根目录依赖...")
                                process = hidden_popen(
                                    [npm_cmd, "install"],
                                    cwd=ace_step_ui_path,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True
                                )
                                
                                try:
                                    stdout, _ = process.communicate(timeout=600)
                                    
                                    if stdout:
                                        for line in stdout.splitlines():
                                            if line.strip():
                                                self._log(f"[安装根目录依赖] {line.strip()}")
                                    
                                    if process.returncode == 0:
                                        self._log("✓ 根目录依赖安装完成")
                                    else:
                                        self._log(f"[警告] 根目录依赖安装返回码: {process.returncode}", "#FF9800")
                                        has_warnings = True
                                except subprocess.TimeoutExpired:
                                    process.kill()
                                    self._log("[警告] 根目录依赖安装超时(10分钟)，跳过继续", "#FF9800")
                                    has_warnings = True
                                
                                # 再安装 server 目录依赖
                                server_path = os.path.join(ace_step_ui_path, "server")
                                if os.path.exists(server_path):
                                    self._log("[信息] 安装 server 目录依赖...")
                                    process2 = hidden_popen(
                                        [npm_cmd, "install"],
                                        cwd=server_path,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True
                                    )
                                    
                                    try:
                                        stdout2, _ = process2.communicate(timeout=600)
                                        
                                        if stdout2:
                                            for line in stdout2.splitlines():
                                                if line.strip():
                                                    self._log(f"[安装server依赖] {line.strip()}")
                                        
                                        if process2.returncode == 0:
                                            self._log("✓ server 目录依赖安装完成")
                                        else:
                                            self._log(f"[警告] server 目录依赖安装返回码: {process2.returncode}", "#FF9800")
                                            has_warnings = True
                                    except subprocess.TimeoutExpired:
                                        process2.kill()
                                        self._log("[警告] server 目录依赖安装超时(10分钟)，跳过继续", "#FF9800")
                                        has_warnings = True
                            else:
                                self._log("[警告] npm 未找到，跳过前端依赖安装", "#FF9800")
                        except Exception as e:
                            self._log(f"[警告] 安装前端依赖失败: {e}", "#FF9800")
                    else:
                        self._log("✓ 前端依赖已安装且无需修复")
                else:
                    self._log("[警告] package.json 不存在，跳过前端依赖安装", "#FF9800")
            else:
                self._log("[警告] ace-step-ui 目录不存在，跳过前端依赖安装", "#FF9800")
            
            # 8. 检查启动脚本
            self._log("8. 检查启动脚本...")
            scripts = [
                "2、run_gradio.ps1",
                "3、run_server.ps1",
                "5、run_qinglong_backend.ps1",
                "6、run_qinglong_frontend.ps1"
            ]
            missing_scripts = []
            for script in scripts:
                script_path = os.path.join(self.base_dir, "scripts", script)
                if os.path.exists(script_path):
                    self._log(f"✓ {script} 存在")
                else:
                    self._log(f"[错误] {script} 不存在", "#F44336")
                    missing_scripts.append(script)
            
            if missing_scripts:
                self._log(f"[警告] 缺少启动脚本: {', '.join(missing_scripts)}", "#FF9800")
                self._log("请确保这些脚本存在或从原始项目中复制", "#FF9800")
            
            # 9. 检查环境变量
            self._log("9. 检查环境变量...")
            try:
                # 检查 PATH 环境变量是否包含 uv 的路径
                path_env = os.environ.get("PATH", "")
                uv_dir = os.path.dirname(uv_path)
                if uv_dir not in path_env:
                    self._log("[信息] uv 路径未在环境变量中，正在添加...")
                    # 使用 setx 命令添加到用户环境变量
                    try:

                        
                        # 获取当前用户 PATH
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                        current_user_path, _ = winreg.QueryValueEx(key, "PATH")
                        winreg.CloseKey(key)
                        
                        # 如果用户 PATH 中还没有这个目录，就添加
                        if uv_dir not in current_user_path:
                            new_user_path = current_user_path + ";" + uv_dir
                            
                            # 使用 setx 设置
                            process = hidden_popen(
                                ["setx", "PATH", new_user_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            process.communicate(timeout=10)
                            
                            # 同时更新当前进程的环境变量
                            os.environ["PATH"] = os.environ["PATH"] + ";" + uv_dir
                            
                            self._log("✓ uv 路径已添加到用户环境变量")
                            self._log("[提示] 请重启应用或重新打开终端使环境变量生效", "#FF9800")
                        else:
                            self._log("✓ uv 路径已在用户环境变量中")
                    except Exception as e:
                        self._log(f"[警告] 自动添加环境变量失败: {e}", "#FF9800")
                        self._log(f"[提示] 请手动将 {uv_dir} 添加到系统环境变量 PATH 中", "#FF9800")
                else:
                    self._log("✓ uv 路径已在环境变量中")
            except Exception as e:
                self._log(f"[错误] 检查环境变量失败: {e}", "#F44336")
            
            # 10. 检查模型目录
            self._log("10. 检查模型目录...")
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
            
            # 11. 检查配置文件
            self._log("11. 检查配置文件...")
            env_example_path = os.path.join(self.base_dir, "scripts", ".env.example")
            env_path = os.path.join(self.base_dir, "scripts", ".env")
            if not os.path.exists(env_path) and os.path.exists(env_example_path):
                self._log("[信息] .env 文件不存在，正在从 scripts/.env.example 创建...")
                try:
                    import shutil
                    shutil.copy2(env_example_path, env_path)
                    self._log("✓ .env 文件创建完成")
                except Exception as e:
                    self._log(f"[错误] 创建 .env 文件失败: {e}", "#F44336")
            elif os.path.exists(env_path):
                self._log("✓ .env 文件已存在")
            else:
                self._log("[警告] scripts/.env.example 文件不存在，无法创建 .env 文件", "#FF9800")
            
            # 11. 最终检查
            self._log("11. 最终环境检查...")
            
            # 检查 uv 是否可用
            try:

                
                process = hidden_popen(
                    [uv_path, "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
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

                    
                    process = hidden_popen(
                        [venv_python, "--version"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
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
            if has_errors:
                self._log("智能环境修复完成，但存在错误！", "#F44336")
                self._log("=======================================")
                self._log("环境存在问题，请检查错误日志并手动解决！", "#F44336")
            elif has_warnings:
                self._log("智能环境修复完成，但存在警告！", "#FF9800")
                self._log("=======================================")
                self._log("环境基本可用，但建议检查警告信息！", "#FF9800")
            else:
                self._log("智能环境修复完成！", "#E53935")
                self._log("=======================================")
                self._log("环境已准备就绪，您可以开始使用云集智能音乐创意台了！", "#E53935")
            self._log("=======================================")
            self._log("")
            if not has_errors:
                self._log("[提示] 模型管理面板已自动展开，您可以查看和下载模型", "#4CAF50")
            
            # 自动展开模型管理面板
            try:
                if hasattr(self, 'model_panel') and not self.model_panel.is_expanded:
                    from PyQt6.QtCore import QTimer
                    # 使用延迟执行，确保UI已完全准备好
                    QTimer.singleShot(100, lambda: self._expand_model_panel())
            except Exception as e:
                self._log(f"[警告] 展开模型面板失败: {e}", "#FF9800")
            
        except Exception as e:
            self._log(f"[错误] 智能修复失败: {e}", "#F44336")
            import traceback
            self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
    
    def _ensure_scripts_available(self):
        """确保脚本文件在 scripts/ 目录可用"""
        import sys
        from pathlib import Path
        
        work_dir = Path(self.base_dir)
        scripts_dir = work_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        scripts_to_check = ["install-env.ps1", "start.ps1", "3、run_server.ps1"]
        
        for script_name in scripts_to_check:
            script_path = scripts_dir / script_name
            
            if script_path.exists():
                self._log(f"✓ 脚本已存在: {script_name}")
            else:
                self._log(f"⚠️ 脚本不存在: {script_name}", "#FF9800")
    
    def _deploy_maintenance(self):
        """部署维护 - 合并环境检测和智能修复功能
        - 自动检测环境是否安装
        - 未安装则自动安装部署
        - 已安装则检测问题并自动修复
        - 解决不了的提供手动解决建议
        """
        if self.is_starting:
            self._log("正在运行中，请稍候...", "#616161")
            return
        
        self.is_starting = True
        self.btn_deploy_maintain.setEnabled(False)
        self.btn_start_music.setEnabled(False)
        self.btn_start_qinglong.setEnabled(False)
        self.btn_stop_all.setEnabled(False)
        
        self.deploy_thread = threading.Thread(target=self._deploy_maintenance_thread)
        self.deploy_thread.daemon = True
        self.deploy_thread.start()
    
    def _deploy_maintenance_thread(self):
        """部署维护线程函数"""
        self._log("========================================")
        self._log("开始部署维护...")
        self._log("========================================")
        self._log(f"[调试] 当前工作目录: {self.base_dir}")
        
        # 确保脚本文件存在（再次尝试提取）
        self._ensure_scripts_available()
        
        try:
            # 1. 首先检查PowerShell
            self._log("1. 检查 PowerShell...")
            powershell_available = False
            
            try:

                
                powershell_paths = [
                    "powershell.exe",
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
                ]
                
                for powershell_exe in powershell_paths:
                    try:
                        process = hidden_popen(
                            [powershell_exe, "-Version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
                        process = hidden_popen(
                            ["where", "powershell"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
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
            
            # 2. 检查 Node.js
            self._log("2. 检查 Node.js...")
            node_available = False
            node_path = None
            
            try:

                
                portable_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
                portable_node22_dir = os.path.join(self.base_dir, "tools", "node-v22.22.2-win-x64", "node-v22.22.2-win-x64")
                node_paths = [
                    os.path.join(portable_node24_dir, "node.exe"),
                    os.path.join(portable_node22_dir, "node.exe"),
                    "node.exe",
                    "C:/Program Files/nodejs/node.exe",
                    "C:/Program Files (x86)/nodejs/node.exe",
                ]
                
                for node_exe in node_paths:
                    try:
                        process = hidden_popen(
                            [node_exe, "--version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0 and stdout.strip():
                            self._log(f"✓ Node.js 已安装: {stdout.strip()}")
                            node_available = True
                            node_path = node_exe
                            break
                    except:
                        continue
                
                if not node_available:
                    self._log("[信息] Node.js 未安装，正在下载便携版 Node.js 24...", "#FF9800")
                    
                    tools_dir = os.path.join(self.base_dir, "tools")
                    os.makedirs(tools_dir, exist_ok=True)
                    node24_zip = os.path.join(tools_dir, "node-v24.14.1-win-x64.zip")
                    node24_url = "https://nodejs.org/dist/v24.14.1/node-v24.14.1-win-x64.zip"
                    
                    downloaded = False
                    if os.path.exists(portable_node24_dir) and os.path.exists(os.path.join(portable_node24_dir, "node.exe")):
                        self._log("✓ 便携版 Node.js 24 已存在", "#4CAF50")
                        node_available = True
                        node_path = os.path.join(portable_node24_dir, "node.exe")
                    else:
                        try:
                            import urllib.request
                            self._log(f"[信息] 下载 Node.js 24 便携版...")
                            self._log(f"[信息] 下载地址: {node24_url}")
                            
                            def _download_progress(block_num, block_size, total_size):
                                downloaded_bytes = block_num * block_size
                                percent = min(downloaded_bytes * 100 / total_size, 100) if total_size > 0 else 0
                                if block_num % 500 == 0:
                                    self._log(f"[下载] Node.js 24: {percent:.1f}%")
                            
                            urllib.request.urlretrieve(node24_url, node24_zip, _download_progress)
                            self._log("✓ Node.js 24 下载完成", "#4CAF50")
                            downloaded = True
                        except Exception as e:
                            self._log(f"[警告] Node.js 24 下载失败: {e}", "#FF9800")
                            self._log("[信息] 尝试下载 Node.js 22 便携版作为备选...", "#FF9800")
                            
                            try:
                                node22_url = "https://nodejs.org/dist/v22.22.2/node-v22.22.2-win-x64.zip"
                                node22_zip = os.path.join(tools_dir, "node-v22.22.2-win-x64.zip")
                                urllib.request.urlretrieve(node22_url, node22_zip)
                                downloaded = True
                                node24_zip = node22_zip
                                portable_node24_dir = portable_node22_dir
                                self._log("✓ Node.js 22 下载完成", "#4CAF50")
                            except Exception as e2:
                                self._log(f"[错误] Node.js 22 下载也失败: {e2}", "#F44336")
                        
                        if downloaded:
                            self._log("[信息] 正在解压 Node.js 便携版...")
                            try:
                                import zipfile
                                with zipfile.ZipFile(node24_zip, 'r') as zf:
                                    zf.extractall(tools_dir)
                                self._log("✓ Node.js 便携版解压完成", "#4CAF50")
                                
                                try:
                                    os.remove(node24_zip)
                                except:
                                    pass
                                
                                if os.path.exists(os.path.join(portable_node24_dir, "node.exe")):
                                    node_available = True
                                    node_path = os.path.join(portable_node24_dir, "node.exe")
                                    ver_process = hidden_popen(
                                        [node_path, "--version"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True
                                    )
                                    v_stdout, _ = ver_process.communicate(timeout=5)
                                    self._log(f"✓ Node.js 便携版安装成功: {v_stdout.strip()}", "#4CAF50")
                                else:
                                    self._log("[错误] 解压后未找到 node.exe", "#F44336")
                            except Exception as e:
                                self._log(f"[错误] 解压失败: {e}", "#F44336")
                    
                    if not node_available:
                        self._log("[信息] 尝试使用 winget 安装 Node.js...", "#FF9800")
                        winget_available = False
                        try:
                            process = hidden_popen(
                                ["winget", "--version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            stdout, stderr = process.communicate(timeout=10)
                            if process.returncode == 0:
                                winget_available = True
                                self._log(f"✓ winget 可用: {stdout.strip()}")
                        except:
                            pass
                        
                        if winget_available:
                            self._log("正在使用 winget 安装 Node.js 22...")
                            self._log("这可能需要几分钟，请稍候...")
                            
                            try:
                                process = hidden_popen(
                                    ["winget", "install", "--id", "OpenJS.NodeJS.LTS.22", "--silent", "--accept-package-agreements", "--accept-source-agreements"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
                                
                                while process.poll() is None:
                                    line = process.stdout.readline()
                                    if line:
                                        self._log(f"[Node.js 安装] {line.strip()}")
                                    line_err = process.stderr.readline()
                                    if line_err:
                                        self._log(f"[Node.js 安装错误] {line_err.strip()}", "#F44336")
                                
                                if process.returncode == 0:
                                    self._log("✓ Node.js 22 安装成功！", "#4CAF50")
                                    self._log("[信息] 请重新运行部署维护以完成后续步骤", "#FF9800")
                                    return
                                else:
                                    self._log(f"[错误] Node.js 安装失败，返回码: {process.returncode}", "#F44336")
                            except Exception as e:
                                self._log(f"[错误] Node.js 安装失败: {e}", "#F44336")
                        else:
                            self._log("[错误] winget 不可用", "#F44336")
                            self._log("[建议] 请手动安装 Node.js 22+ 或使用 winget", "#FF9800")
                            return
            except Exception as e:
                self._log(f"[错误] 检查 Node.js 失败: {e}", "#F44336")
                return
            
            # 3. 检查环境是否已安装
            self._log("3. 检查环境安装状态...")
            
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            venv_path = os.path.join(self.base_dir, "scripts", ".venv")
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
                
                install_script = os.path.join(self.base_dir, "scripts", "install-env.ps1")
                if os.path.exists(install_script):
                    try:
                        self._log("4. 执行环境安装脚本...")
                        self._log("[信息] 这可能需要几分钟，请稍候...")
                        

                        
                        # 使用 subprocess.run 不捕获输出，避免阻塞
                        result = hidden_run(
                            ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_script],
                            cwd=self.base_dir,
                            capture_output=False,
                            text=True,
                            timeout=1800
                        )
                        
                        if result.returncode == 0:
                            self._log("✅ 环境安装完成", "#4CAF50")
                        else:
                            self._log(f"[错误] 环境安装失败，返回码: {result.returncode}", "#F44336")
                            return
                    except subprocess.TimeoutExpired:
                        self._log("[错误] 环境安装超时(30分钟)，请手动运行安装脚本", "#F44336")
                        self._log("[建议] 请手动运行 scripts/install-env.ps1 脚本", "#FF9800")
                        return
                    except Exception as e:
                        self._log(f"[错误] 运行安装脚本失败: {e}", "#F44336")
                        self._log("[建议] 请手动运行 scripts/install-env.ps1 脚本", "#FF9800")
                        return
                else:
                    self._log("[错误] 安装脚本不存在", "#F44336")
                    self._log("[建议] 请确保 scripts/install-env.ps1 脚本存在", "#FF9800")
                    return
            
            # 如果环境已完全安装，跳过智能修复的依赖安装步骤，只做快速检查
            if environment_installed:
                self._log("5. 环境已完全安装，执行快速验证...")
                self._quick_verify_environment()
            else:
                # 环境未完全安装，执行完整智能修复
                self._log("5. 执行智能修复（安装前端依赖等）...")
                self._smart_fix_environment()
            
            # 6. 最终检查
            self._log("6. 最终检查...")
            
            # 检查启动脚本
            scripts = [
                "2、run_gradio.ps1",
                "3、run_server.ps1",
                "4、run_npmgui.ps1"
            ]
            script_missing = False
            for script in scripts:
                script_path = os.path.join(self.base_dir, "scripts", script)
                if os.path.exists(script_path):
                    self._log(f"✓ {script} 存在")
                else:
                    self._log(f"[错误] {script} 不存在", "#F44336")
                    script_missing = True
            
            if script_missing:
                self._log("[建议] 请确保所有启动脚本都存在", "#FF9800")
            
        except Exception as e:
            self._log(f"[错误] 部署维护失败: {e}", "#F44336")
            import traceback
            self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
        finally:
            self.is_starting = False
            self.enable_buttons_signal.emit()
    
    def _generate_startup_diagnosis(self, project_id: str, started_services: List[str], all_success: bool):
        """生成启动诊断分析报告"""
        try:
            project = PROJECTS[project_id]
            
            self._log("")
            self._log("========================================")
            self._log("启动诊断分析报告")
            self._log("========================================")
            
            all_ok = True
            
            self._log("1. 服务启动状态检查...")
            for service_id, service in project["services"].items():
                try:
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
                except Exception as e:
                    self._log(f"[警告] 检查服务 {service_id} 失败: {e}", "#FF9800")
            
            if project_id == "qinglong":
                try:
                    self._log("2. 核心API服务检查...")
                    api_port = 8001
                    api_running = self.monitor._check_port(api_port)
                    if api_running:
                        self._log("✓ API服务 - 运行正常 (端口: 8001)")
                    else:
                        self._log("⚠ API服务 - 未运行", "#FF9800")
                        self._log("  建议：先启动官方音乐演练场来启动API服务", "#FF9800")
                        all_ok = False
                except Exception as e:
                    self._log(f"[警告] 检查API服务失败: {e}", "#FF9800")
            
            self._log("3. 常见问题排查...")
            
            try:
                port_conflicts = []
                for service_id, service in SERVICES.items():
                    port = service["port"]
                    try:
                        import psutil
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
            except Exception as e:
                self._log(f"[警告] 检查端口冲突失败: {e}", "#FF9800")
            
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
        except Exception as e:
            self._log(f"[错误] 生成启动诊断报告失败: {e}", "#F44336")
            import traceback
            self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
    
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
        
        max_wait = 120
        waited = 0
        start_time = time.time()
        while waited < max_wait:
            time.sleep(5)
            waited = int(time.time() - start_time)
            
            if self.monitor._check_port(SERVICES[service_id]["port"]):
                self._log(f"✓ {service_name} 已就绪 (耗时 {waited} 秒)", "#E53935")
                return True
            
            if process.state() == 0:
                self._log(f"[错误] {service_name} 进程已退出", "#F44336")
                return False
        
        self._log(f"[错误] {service_name} 启动超时 (已等待 {waited} 秒)", "#F44336")
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
                try:
                    process.terminate()
                    self._log(f"✓ {service['name']} 进程已终止")
                except:
                    pass
        
        port = service["port"]
        try:
            import subprocess

            
            result = hidden_run(
                ["netstat", "-ano", "-p", "TCP"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                hidden_run(
                                    ["taskkill", "/F", "/PID", pid],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    timeout=5
                                )
                                self._log(f"已终止占用端口 {port} 的进程 (PID: {pid})")
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
    
    def _check_and_load_system_info(self):
        """检查是否已初始化，加载系统信息或显示初始化流程"""
        from init_wizard import is_initialized, auto_check_and_update_config
        from pathlib import Path
        
        base_dir = Path(self.base_dir)
        
        if is_initialized(base_dir):
            # 已初始化，自动检测并补充系统信息
            auto_check_and_update_config(base_dir)
            self._load_system_info()
        else:
            # 未初始化，在日志区域显示初始化流程
            self._start_initialization_in_log()
    
    def _start_initialization_in_log(self):
        """在日志区域启动初始化流程"""
        from init_wizard import InitWorker
        from pathlib import Path
        
        self.log_output.append("🚀 欢迎使用云集智能音乐创意台！")
        self.log_output.append("=" * 60)
        self.log_output.append("")
        self.log_output.append("首次运行，正在完成初始化配置...")
        self.log_output.append("")
        
        # 创建初始化工作线程
        self.init_worker = InitWorker(self.base_dir)
        self.init_worker.progress_updated.connect(self._on_init_progress)
        self.init_worker.step_completed.connect(self._on_init_step_completed)
        self.init_worker.finished.connect(self._on_init_finished)
        
        self.init_worker.start()
    
    def _on_init_progress(self, step_name, progress, message):
        """初始化进度更新"""
        self.log_output.append(f"[{progress}%] {message}")
    
    def _on_init_step_completed(self, step_name, success, message):
        """初始化步骤完成"""
        status = "✅" if success else "❌"
        self.log_output.append(f"{status} {step_name}：{message}")
        self.log_output.append("")
    
    def _on_init_finished(self, success, message):
        """初始化完成"""
        self.log_output.append("=" * 60)
        if success:
            self.log_output.append("🎉 初始化完成！")
            self.log_output.append("")
            # 刷新系统信息显示
            self._load_system_info()
        else:
            self.log_output.append(f"❌ 初始化失败：{message}")
        self.log_output.append("=" * 60)
    
    def _load_system_info(self):
        """加载并显示系统信息（高度紧凑）"""
        import json
        from pathlib import Path
        
        config_file = Path(self.base_dir) / 'config' / 'init_config.json'
        
        compact_info = []
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'python_version' in config:
                    py_status = "✅" if config.get('python_version_ok', False) else "⚠️"
                    compact_info.append(f"Python:{config['python_version']}{py_status}")
                
                if 'python_312_available' in config:
                    py312 = "✅312" if config['python_312_available'] else "❌312"
                    compact_info.append(py312)
                
                if 'git_available' in config:
                    git = "✅Git" if config['git_available'] else "❌Git"
                    compact_info.append(git)
                
                if 'memory_available' in config and 'memory_total' in config:
                    compact_info.append(f"RAM:{config['memory_available']}/{config['memory_total']}GB")
                
                if 'cpu_count' in config:
                    compact_info.append(f"CPU:{config['cpu_count']}c")
                
            except Exception as e:
                compact_info = [f"⚠️读取失败"]
        else:
            compact_info = ["初始化中..."]
        
        self.system_info_label.setText(" | ".join(compact_info))
    
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
        selected_data = self.browser_combo.itemData(index)
        
        # 检查是否选择了自定义浏览器
        is_custom = selected_data == "custom" or selected_browser == "自定义浏览器"
        
        # 显示/隐藏自定义设置
        self.browser_path_edit.setVisible(is_custom)
        self.btn_select_browser.setVisible(is_custom)
        
        if is_custom:
            # 自定义浏览器模式
            self.selected_browser = "custom"
            self.config.set("browser.default", "custom")
            if self.custom_browser_path and os.path.exists(self.custom_browser_path):
                self._log(f"已启用自定义浏览器")
            else:
                self._log(f"请选择或输入自定义浏览器路径")
        else:
            # 系统浏览器模式
            self.selected_browser = selected_browser
            self.config.set("browser.default", selected_browser)
            self._log(f"已设置默认浏览器为: {selected_browser}")
    
    def _on_custom_browser_path_changed(self, path):
        """处理自定义浏览器路径变化"""
        self.custom_browser_path = path
        self.config.set("browser.custom_path", path)
        if path and os.path.exists(path):
            self.selected_browser = "custom"
            self.config.set("browser.default", "custom")
            self._log(f"已设置自定义浏览器: {path}")
    
    def _open_url_in_browser(self, url: str):
        """使用选择的浏览器打开URL"""
        if (self.selected_browser == "custom" or self.selected_browser == "自定义浏览器") and self.custom_browser_path and os.path.exists(self.custom_browser_path):
            try:
                hidden_popen([self.custom_browser_path, url]),
                self._log(f"使用自定义浏览器打开: {url}")
            except Exception as e:
                self._log(f"打开自定义浏览器失败: {e}", "#F44336")
                import webbrowser
                webbrowser.open(url)
        else:
            selected_browser = self.selected_browser
            if selected_browser == "系统默认" or selected_browser == "custom" or selected_browser == "自定义浏览器":
                import webbrowser
                webbrowser.open(url)
            else:
                browser_path = self.browsers.get(selected_browser)
                if browser_path:
                    try:
                        hidden_popen([browser_path, url]),
                        self._log(f"使用 {selected_browser} 打开: {url}")
                    except Exception as e:
                        self._log(f"打开浏览器失败: {e}", "#F44336")
                        import webbrowser
                        webbrowser.open(url)
                else:
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
                
                self.selected_browser = "custom"
                self.config.set("browser.default", "custom")
                
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
            "description": "完整基础模型包",
            "info": "包含VAE、Qwen3-Embedding-0.6B、acestep-v15-turbo、acestep-5Hz-lm-1.7B等核心组件。适合初次使用的用户，提供一站式完整解决方案。",
            "exists": self._check_main_model_exists()
        })
        
        # LM 模型
        lm_models = {
            "acestep-5Hz-lm-0.6B": {
                "repo": "ACE-Step/acestep-5Hz-lm-0.6B",
                "description": "轻量级语言模型",
                "info": "0.6B参数的语言模型，速度极快，资源占用低，适合快速原型开发和资源有限的环境。"
            },
            "acestep-5Hz-lm-4B": {
                "repo": "ACE-Step/acestep-5Hz-lm-4B",
                "description": "大型语言模型",
                "info": "4B参数的语言模型，生成质量更高，能理解更复杂的音乐结构和风格，适合专业音乐创作。"
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
                "info": "v1.5版本的基础模型，适合从零开始创作，能生成风格多样的音乐，是最灵活的选择。"
            },
            "acestep-v15-sft": {
                "repo": "ACE-Step/acestep-v15-sft",
                "description": "监督微调模型",
                "info": "经过监督微调的模型，更适合风格延续和参考创作，旋律还原度较高，生成更加稳定可控。"
            },
            "acestep-v15-turbo-shift1": {
                "repo": "ACE-Step/acestep-v15-turbo-shift1",
                "description": "Turbo加速模型 (Shift 1)",
                "info": "Turbo系列，Shift 1采样，生成速度快，质量也不错，适合快速迭代和测试想法。"
            },
            "acestep-v15-turbo-shift3": {
                "repo": "ACE-Step/acestep-v15-turbo-shift3",
                "description": "Turbo加速模型 (Shift 3)",
                "info": "Turbo系列，Shift 3采样，平衡质量和速度，质量更好的快速模型，推荐用于正式创作。"
            },
            "acestep-v15-turbo-continuous": {
                "repo": "ACE-Step/acestep-v15-turbo-continuous",
                "description": "Turbo连续生成模型",
                "info": "支持连续生成，适合长音频创作，稳定性极佳，能生成连贯的完整音乐作品。"
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
        """检查主模型是否存在 - 使用与model_downloader.py相同的逻辑"""
        try:
            import sys
            sys.path.insert(0, self.base_dir)
            from acestep.model_downloader import check_main_model_exists, get_checkpoints_dir
            return check_main_model_exists(get_checkpoints_dir())
        except Exception as e:
            print(f"[check_main_model_exists] Error: {e}")
            # Fallback: 简单检查
            try:
                checkpoints_dir = os.path.join(self.base_dir, "models")
                if not os.path.exists(checkpoints_dir):
                    checkpoints_dir = os.path.join(self.base_dir, "checkpoints")
                components = ["acestep-v15-turbo", "vae", "Qwen3-Embedding-0.6B", "acestep-5Hz-lm-1.7B"]
                for component in components:
                    component_path = os.path.join(checkpoints_dir, component)
                    if not os.path.exists(component_path):
                        return False
                    # 检查目录是否有文件
                    if not os.listdir(component_path):
                        return False
                return True
            except Exception:
                return False
    
    def _check_model_exists(self, model_name):
        """检查模型是否存在 - 使用与model_downloader.py相同的逻辑"""
        try:
            import sys
            sys.path.insert(0, self.base_dir)
            from acestep.model_downloader import check_model_exists, get_checkpoints_dir
            return check_model_exists(model_name, get_checkpoints_dir())
        except Exception as e:
            print(f"[check_model_exists] Error: {e}")
            # Fallback: 简单检查
            try:
                checkpoints_dir = os.path.join(self.base_dir, "models")
                if not os.path.exists(checkpoints_dir):
                    checkpoints_dir = os.path.join(self.base_dir, "checkpoints")
                model_path = os.path.join(checkpoints_dir, model_name)
                if not os.path.exists(model_path):
                    return False
                # 检查目录是否有文件
                if not os.listdir(model_path):
                    return False
                return True
            except Exception:
                return False
    
    def _download_model(self, model_name):
        """下载模型 - 使用异步线程避免UI阻塞"""
        if self.is_downloading or self.is_deleting or self.is_verifying:
            self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
            return
        
        self.is_downloading = True
        self.current_operation_model = model_name
        
        # 刷新UI以显示暂停按钮
        self._update_model_management_ui()
        
        # 显示进度条
        if self.model_manager_widget is not None:
            self.model_manager_widget.show_progress(f"正在下载: {model_name}")
        
        # 创建下载线程
        self.model_download_thread = ModelDownloadThread(
            model_name, 
            self.base_dir, 
            self.selected_download_source
        )
        
        # 连接信号
        self.model_download_thread.log_received.connect(self._log)
        self.model_download_thread.download_finished.connect(self._on_download_finished)
        self.model_download_thread.progress_updated.connect(self._on_download_progress_updated)
        
        # 禁用所有模型按钮
        self._set_model_buttons_enabled(False)
        
        # 启动下载线程
        self.model_download_thread.start()
    
    def _on_download_progress_updated(self, value: int, desc: str):
        """下载进度更新回调"""
        if self.model_manager_widget is not None:
            self.model_manager_widget.update_progress(value, desc)
    
    def _on_download_finished(self, success: bool, model_name: str):
        """下载完成回调"""
        self.is_downloading = False
        self.current_operation_model = None
        
        # 隐藏进度条
        if self.model_manager_widget is not None:
            self.model_manager_widget.hide_progress()
        
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
        self.model_verify_thread.verify_details.connect(self._on_verify_details)
        
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
    
    def _on_verify_details(self, details: dict):
        """验证详情回调 - 显示详细的完整性信息"""
        if not details.get("is_valid", False):
            msg = f"[验证详情] 模型 {details.get('model_name', '')} 不完整"
            if details.get("files_missing"):
                msg += f"\n  缺少文件: {', '.join(details['files_missing'])}"
            if not details.get("size_ok", True):
                actual = details.get("total_size_mb", 0)
                expected = details.get("expected_size_mb", 0)
                msg += f"\n  大小不足: {actual}MB < 预期 {expected}MB"
            msg += "\n  建议: 请重新下载模型以确保文件完整性"
            self._log(msg, "#FF9800")
        # 更新模型管理UI
        self._update_model_management_ui()
    
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
        """一键验证所有模型安装 - 最简版，不使用线程避免闪退"""
        try:
            if self.is_deleting or self.is_downloading or self.is_verifying:
                self._log("[警告] 正在执行其他操作，请等待...", "#FF9800")
                return
            
            self.is_verifying = True
            
            # 禁用验证按钮
            if hasattr(self, 'btn_verify_all'):
                self.btn_verify_all.setEnabled(False)
            
            # 禁用所有模型按钮
            self._set_model_buttons_enabled(False)
            
            self._log("🔍 开始验证模型...", "#2196F3")
            
            # 直接重新加载模型列表（会自动检查所有模型状态）
            self.model_list = []
            self._load_model_list()
            
            # 计算验证结果
            total_models = len(self.model_list)
            installed_models = sum(1 for m in self.model_list if m.get('exists', False))
            
            # 更新验证时间和结果
            from datetime import datetime
            verify_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 如果有模型管理器widget，更新它
            if self.model_manager_widget is not None:
                self.model_manager_widget.last_verify_time = verify_time
                self.model_manager_widget.last_verify_result = (total_models, installed_models)
                # 更新标签
                self.model_manager_widget.verify_time_label.setText(f"⏱ 上次验证: {verify_time}")
                result_text = f"✅ {installed_models}/{total_models} 模型已安装"
                self.model_manager_widget.verify_result_label.setText(result_text)
                self.model_manager_widget.verify_result_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
            
            # 更新UI
            self._update_model_management_ui()
            
            self._log(f"✅ 验证完成！{installed_models}/{total_models} 模型已安装", "#4CAF50")
            
            # 重置状态
            self.is_verifying = False
            if hasattr(self, 'btn_verify_all'):
                self.btn_verify_all.setEnabled(True)
            self._set_model_buttons_enabled(True)
            
        except Exception as e:
            import traceback
            try:
                self._log(f"❌ 验证出错: {str(e)}", "#F44336")
                self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
            except:
                pass
            # 即使出错也要确保状态重置
            self.is_verifying = False
            try:
                if hasattr(self, 'btn_verify_all'):
                    self.btn_verify_all.setEnabled(True)
                self._set_model_buttons_enabled(True)
            except:
                pass
    
    def _on_verify_all_finished(self, success: bool, model_name: str):
        """验证完成回调 - 增强版，更新模型状态"""
        try:
            self.is_verifying = False
            
            # 重新加载模型列表（更新exists状态）
            self.model_list = []
            self._load_model_list()
            
            # 重新启用验证按钮
            if hasattr(self, 'btn_verify_all'):
                self.btn_verify_all.setEnabled(True)
            
            # 重新启用所有按钮
            self._set_model_buttons_enabled(True)
            
            # 更新UI
            self._update_model_management_ui()
            
        except Exception as e:
            import traceback
            try:
                self._log(f"❌ 验证完成回调出错: {str(e)}", "#F44336")
                self._log(f"错误详情: {traceback.format_exc()}", "#F44336")
            except:
                pass
            # 即使出错也要确保状态重置
            self.is_verifying = False
            try:
                if hasattr(self, 'btn_verify_all'):
                    self.btn_verify_all.setEnabled(True)
                self._set_model_buttons_enabled(True)
            except:
                pass
    
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
        
        import psutil
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


def extract_scripts():
    """提取打包的脚本文件到工作目录的 scripts/ 文件夹"""
    import sys
    import shutil
    from pathlib import Path
    
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        base_path = Path(sys._MEIPASS)
        work_dir = Path.cwd()
        
        # 检查是否有 app/ 子目录
        app_dir = work_dir / "app"
        if app_dir.exists():
            work_dir = app_dir
        
        scripts_dir = work_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        scripts_to_extract = ["install-env.ps1", "start.ps1"]
        
        for script_name in scripts_to_extract:
            src_path = base_path / script_name
            dest_path = scripts_dir / script_name
            
            if src_path.exists() and not dest_path.exists():
                try:
                    shutil.copy2(src_path, dest_path)
                except Exception:
                    pass


def main():
    extract_scripts()
    
    NativeSplash.draw_progress(0.05, "正在启动应用...")
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0D0D0D"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#F0F0F0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1A1A1A"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#F0F0F0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1A1A1A"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F0F0F0"))
    app.setPalette(palette)
    
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    NativeSplash.draw_progress(0.1, "正在创建主窗口...")
    
    window = MainWindow()
    window.show()
    
    NativeSplash.close()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
