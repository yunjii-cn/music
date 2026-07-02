#!/usr/bin/env python3
"""
文件用途: PyQt6 GUI启动器主程序
项目名称: 云集智能音乐创意台 (ACE-Step)
版本: v2.8.3+

核心功能:
- 环境维护与检测
- 模型管理界面
- 项目服务启动（青龙 LoRA 训练器等）
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
import re
import json
import time
import subprocess as _subprocess

if sys.platform == 'win32':
    if not getattr(_subprocess, '_pyi_hidden_patched', False):
        def _ensure_hidden(kwargs):
            si = kwargs.get('startupinfo', None)
            if si is None:
                si = _subprocess.STARTUPINFO()
            si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            kwargs['startupinfo'] = si
            flags = _subprocess.CREATE_NO_WINDOW
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

        # Clear proxy env that may affect httpx/gradio import (SOCKS proxy triggers socksio requirement)
        for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            os.environ.pop(proxy_var, None)

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

        _subprocess._pyi_hidden_patched = True

import subprocess
import threading
import socket
import traceback
import winreg
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

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
    QMenu, QStyle, QComboBox, QFileDialog, QLineEdit, QStackedWidget, QSizePolicy, QDialog,
    QSplashScreen
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess, QPropertyAnimation, QRectF, pyqtProperty, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction, QKeySequence, QPainter, QPixmap, QLinearGradient

# Version manager - lazy imported

# Version based on executable filename
def get_version_from_filename():
    """从可执行文件名称中提取版本号；开发模式下追加 -dev 后缀"""
    try:
        if hasattr(sys, 'frozen'):
            exe_path = sys.executable
            exe_name = os.path.basename(exe_path)
            import re
            match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_name)
            if match:
                return match.group(1)
        return datetime.now().strftime("%Y.%m.%d.%H%M") + "-dev"
    except:
        return datetime.now().strftime("%Y.%m.%d.%H%M") + "-dev"

VERSION = get_version_from_filename()

# 项目定义
PROJECTS = {
    "qinglong": {
        "name": "青龙 LoRA 训练器",
        "services": {
            "api": {
                "name": "API 服务",
                "port": 8001,
                "script": "scripts/3、run_server.ps1",
                "url": "http://127.0.0.1:8001/docs",
                "color": "#E53935",
                "icon": "🔌",
                "is_core": True
            },
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

MIRROR_SOURCES = {
    "tsinghua": {
        "pip": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "pip_extra": "https://download.pytorch.org/whl/cu128",
        "uv_urls": [
            "https://ghfast.top/https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
            "https://gh-proxy.com/https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
            "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
        ],
        "hf_endpoint": "https://hf-mirror.com",
        "test_host": "pypi.tuna.tsinghua.edu.cn",
        "label": "清华镜像",
    },
    "aliyun": {
        "pip": "https://mirrors.aliyun.com/pypi/simple/",
        "pip_extra": "https://download.pytorch.org/whl/cu128",
        "uv_urls": [
            "https://ghfast.top/https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
            "https://gh-proxy.com/https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
            "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
        ],
        "hf_endpoint": "https://hf-mirror.com",
        "test_host": "mirrors.aliyun.com",
        "label": "阿里云镜像",
    },
    "official": {
        "pip": "https://pypi.org/simple/",
        "pip_extra": "https://download.pytorch.org/whl/cu128",
        "uv_urls": [
            "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
        ],
        "hf_endpoint": "https://huggingface.co",
        "test_host": "pypi.org",
        "label": "官方源",
    },
}

PYTHON_VERSION = "3.12"

ACE_PIP_DEPS = [
    "torch==2.9.0",
    "torchaudio==2.9.0",
    "transformers>=4.51.0,<5.0",
    "diffusers",
    "gradio",
    "peft",
    "lycoris-lora",
    "accelerate",
    "fastapi",
    "uvicorn",
    "scipy",
    "soundfile",
    "einops",
    "loguru",
    "psutil",
    "matplotlib",
    "diskcache",
    "numba",
    "huggingface_hub",
    "safetensors",
    "lightning",
    "tensorboard",
    "modelscope",
]

ACE_PIP_VERSION_LOCKS = {
    "torch": ">=2.9.0,<3.0",
    "torchaudio": ">=2.9.0,<3.0",
    "transformers": ">=4.51.0,<5.0",
    "diffusers": ">=0.25,<1.0",
    "accelerate": ">=0.24,<2.0",
    "peft": ">=0.13,<1.0",
    "safetensors": ">=0.4,<1.0",
    "huggingface_hub": ">=0.23,<1.0",
    "einops": ">=0.8,<1.0",
    "scipy": ">=1.14,<2.0",
}


class ServiceMonitor(QThread):
    """服务状态监控线程"""
    status_changed = pyqtSignal(str, bool)
    
    def __init__(self, check_interval: int = 3):
        super().__init__()
        self.check_interval = check_interval
        self.running = True
        self._status_cache = {}
        self._paused = False
    
    def run(self):
        while self.running:
            if not self._paused:
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
    
    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False
        self._status_cache.clear()
    
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
            if hasattr(sys, '_MEIPASS'):
                exe_dir = os.path.abspath(os.path.dirname(sys.executable))
                script_path = os.path.join(exe_dir, "app", self.service_info["script"])
                real_working_dir = os.path.join(exe_dir, "app")
            else:
                script_path = os.path.join(working_dir, self.service_info["script"])
                real_working_dir = working_dir
            
            if not os.path.exists(script_path) and hasattr(sys, '_MEIPASS'):
                script_path = os.path.join(sys._MEIPASS, self.service_info["script"])
            
            if not os.path.exists(script_path):
                error_msg = f"[错误] 脚本不存在: {script_path}"
                self.output_received.emit(self.service_id, error_msg)
                return False
            
            self.working_dir = real_working_dir
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
                "-File", self.script_path,
                "-Port", str(self.service_info["port"])
            ]
            
            if self.service_id == "qinglong_frontend" and "qinglong_backend" in SERVICES:
                cmd.extend(["-BackendPort", str(SERVICES["qinglong_backend"]["port"])])
            elif self.service_id == "qinglong_backend" and "qinglong_api" in SERVICES:
                cmd.extend(["-ApiPort", str(SERVICES["qinglong_api"]["port"])])
            
            env = os.environ.copy()
            env["SERVICE_PORT"] = str(self.service_info["port"])
            
            if self.service_id == "qinglong_frontend" and "qinglong_backend" in SERVICES:
                env["BACKEND_URL"] = f"http://127.0.0.1:{SERVICES['qinglong_backend']['port']}"
            elif self.service_id == "qinglong_backend":
                if "qinglong_frontend" in SERVICES:
                    env["FRONTEND_URL"] = f"http://localhost:{SERVICES['qinglong_frontend']['port']}"
                if "qinglong_api" in SERVICES:
                    env["ACESTEP_API_URL"] = f"http://localhost:{SERVICES['qinglong_api']['port']}"
            
            self.process = hidden_popen(
                cmd,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
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
            venv_python = self._find_venv_python()
            
            # 检查虚拟环境是否存在
            if not os.path.exists(venv_python):
                self.log_received.emit("[错误] 虚拟环境不存在，请先运行环境检测")
                self.download_finished.emit(False, "虚拟环境不存在")
                return
            
            self.current_progress = 10
            self.progress_updated.emit(self.current_progress, "检查环境...")
            
            cmd_args = [venv_python, "-m", "acestep.model_downloader"]
            if self.model_name in ("main", "acestep-v15-turbo", "acestep-5Hz-lm-1.7B"):
                pass
            else:
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
            
            venv_python = self._find_venv_python()
            
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
                "start_sequence": ["api", "backend", "frontend"]
            },
            "ui": {
                "window_size": {"width": 1200, "height": 850},
                "last_tab": 0
            },
            "service_settings": {
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


PORT_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "port_config.json")


def load_port_config():
    """加载端口配置"""
    try:
        if os.path.exists(PORT_CONFIG_FILE):
            with open(PORT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_port_config(config):
    """保存端口配置"""
    try:
        with open(PORT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def apply_saved_ports():
    """将保存的端口配置应用到 SERVICES 和 PROJECTS"""
    saved = load_port_config()
    for service_id, port in saved.items():
        if service_id in SERVICES:
            old_port = SERVICES[service_id]["port"]
            if port != old_port and 1 <= port <= 65535:
                SERVICES[service_id]["port"] = port
                SERVICES[service_id]["url"] = SERVICES[service_id]["url"].replace(
                    f":{old_port}", f":{port}"
                )
                project_id = SERVICES[service_id]["project"]
                short_id = service_id.replace(f"{project_id}_", "", 1)
                if project_id in PROJECTS and short_id in PROJECTS[project_id]["services"]:
                    PROJECTS[project_id]["services"][short_id]["port"] = port
                    PROJECTS[project_id]["services"][short_id]["url"] = SERVICES[service_id]["url"]


apply_saved_ports()


class ServiceCard(QFrame):
    """服务状态卡片"""
    restart_clicked = pyqtSignal(str)
    open_clicked = pyqtSignal(str)
    port_changed = pyqtSignal(str, int)
    
    def __init__(self, service_id: str, parent=None):
        super().__init__(parent)
        self.service_id = service_id
        self.service_info = SERVICES[service_id]
        self.is_running = False
        self._editing_port = False
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            ServiceCard {{
                background-color: #1E1E1E;
                border-radius: 10px;
                border: 2px solid #333333;
            }}
            ServiceCard QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
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
        
        self.port_input = QLineEdit(str(self.service_info['port']))
        self.port_input.setFixedWidth(55)
        self.port_input.setMaxLength(5)
        self.port_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.port_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #1976D2;
                border-radius: 3px;
                padding: 1px 3px;
                font-size: 12px;
            }
        """)
        self.port_input.returnPressed.connect(self._confirm_port_edit)
        self.port_input.hide()
        top_row_layout.addWidget(self.port_input)
        
        self.edit_port_btn = QPushButton("修改")
        self.edit_port_btn.setFixedSize(48, 24)
        self.edit_port_btn.setStyleSheet("""
            QPushButton {
                background-color: #3D3D3D;
                color: #BBBBBB;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
                color: #FFFFFF;
                border-color: #666666;
            }
        """)
        self.edit_port_btn.clicked.connect(self._start_port_edit)
        top_row_layout.addWidget(self.edit_port_btn)
        
        self.save_port_btn = QPushButton("保存")
        self.save_port_btn.setFixedSize(48, 24)
        self.save_port_btn.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: #FFFFFF;
                border: 1px solid #EF5350;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #EF5350;
                border-color: #F44336;
            }
        """)
        self.save_port_btn.clicked.connect(self._confirm_port_edit)
        self.save_port_btn.hide()
        top_row_layout.addWidget(self.save_port_btn)
        
        self.cancel_port_btn = QPushButton("取消")
        self.cancel_port_btn.setFixedSize(48, 24)
        self.cancel_port_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: #AAAAAA;
                border: 1px solid #444444;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border-color: #555555;
            }
        """)
        self.cancel_port_btn.clicked.connect(self._cancel_port_edit)
        self.cancel_port_btn.hide()
        top_row_layout.addWidget(self.cancel_port_btn)
        
        top_row_layout.addStretch()
        
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
                border-color: #1E88E5;
            }
        """)
        self.restart_btn.clicked.connect(lambda: self.restart_clicked.emit(self.service_id))
        btn_layout.addWidget(self.restart_btn)
        
        self.open_btn = QPushButton("打开")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: #FFFFFF;
                border: 1px solid #EF5350;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF5350;
                border-color: #F44336;
            }
        """)
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(self.service_id))
        btn_layout.addWidget(self.open_btn)
        
        layout.addLayout(btn_layout)
    
    def _start_port_edit(self):
        if self._editing_port:
            return
        self._editing_port = True
        self.port_input.setText(str(self.service_info['port']))
        self.port_label.hide()
        self.edit_port_btn.hide()
        self.port_input.show()
        self.save_port_btn.show()
        self.cancel_port_btn.show()
        self.port_input.selectAll()
        self.port_input.setFocus()
    
    def _confirm_port_edit(self):
        if not self._editing_port:
            return
        self._editing_port = False
        try:
            new_port = int(self.port_input.text().strip())
        except ValueError:
            self._cancel_port_edit()
            return
        if not (1 <= new_port <= 65535) or new_port == self.service_info['port']:
            self._cancel_port_edit()
            return
        for sid, svc in SERVICES.items():
            if sid != self.service_id and svc['port'] == new_port:
                self._cancel_port_edit()
                return
        self.port_input.hide()
        self.port_label.show()
        self.edit_port_btn.show()
        self.save_port_btn.hide()
        self.cancel_port_btn.hide()
        self.port_changed.emit(self.service_id, new_port)
    
    def _cancel_port_edit(self):
        self._editing_port = False
        self.port_input.hide()
        self.port_label.show()
        self.edit_port_btn.show()
        self.save_port_btn.hide()
        self.cancel_port_btn.hide()
    
    def update_port_display(self):
        self.port_label.setText(f"端口:{self.service_info['port']}")
    
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


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(520, 360)
        pixmap.fill(QColor("#0D0D0D"))
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self._progress = 0.0
        self._message = "正在初始化..."
        self._icon_pixmap = None
        try:
            if hasattr(sys, '_MEIPASS'):
                base = sys._MEIPASS
            else:
                base = os.path.dirname(os.path.abspath(__file__))
            for name in ('icon.png', 'icon.ico'):
                p = os.path.join(base, name)
                if os.path.exists(p):
                    if name.endswith('.ico'):
                        self._icon_pixmap = QIcon(p).pixmap(QSize(256, 256))
                    else:
                        self._icon_pixmap = QPixmap(p)
                    if not self._icon_pixmap.isNull():
                        break
        except Exception:
            pass

    def _get_progress(self):
        return self._progress

    def _set_progress(self, val):
        self._progress = val
        self.repaint()

    progress = pyqtProperty(float, _get_progress, _set_progress)

    def set_progress(self, value, message=""):
        self._progress = value
        if message:
            self._message = message
        self.repaint()

    def drawContents(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor("#0D0D0D"))

        if self._icon_pixmap:
            icon_size = 80
            scaled = self._icon_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            ix = (w - scaled.width()) // 2
            painter.drawPixmap(ix, 60, scaled)

        painter.setPen(QColor("#F0F0F0"))
        title_font = QFont("Microsoft YaHei", 22, QFont.Weight.Bold)
        painter.setFont(title_font)
        title = "云集智能音乐创意台"
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(title)
        painter.drawText((w - tw) // 2, 180, title)

        bar_x, bar_y, bar_w, bar_h = 60, 240, w - 120, 10
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#222222"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 5, 5)

        fill_w = bar_w * min(self._progress, 1.0)
        if fill_w > 0:
            grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
            grad.setColorAt(0, QColor("#1565C0"))
            grad.setColorAt(1, QColor("#42A5F5"))
            painter.setBrush(grad)
            painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 5, 5)

        painter.setPen(QColor("#888888"))
        msg_font = QFont("Microsoft YaHei", 10)
        painter.setFont(msg_font)
        msg = self._message
        fm2 = painter.fontMetrics()
        mw = fm2.horizontalAdvance(msg)
        painter.drawText((w - mw) // 2, 275, msg)

        pct = f"{int(min(self._progress, 1.0) * 100)}%"
        painter.setPen(QColor("#42A5F5"))
        pct_font = QFont("Microsoft YaHei", 9)
        painter.setFont(pct_font)
        fm3 = painter.fontMetrics()
        pw = fm3.horizontalAdvance(pct)
        painter.drawText((w - pw) // 2, 300, pct)


class MainWindow(QMainWindow):
    """主窗口"""
    log_signal = pyqtSignal(str, str)
    enable_buttons_signal = pyqtSignal()
    deploy_step_signal = pyqtSignal(str, str)
    
    def __init__(self, splash=None):
        super().__init__()
        self._splash = splash
        self._force_exit = False
        self.setWindowTitle(f"云集智能音乐创意台 v{VERSION}")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D0D0D;
            }
            QLabel {
                border: none;
            }
            QFrame#cardFrame {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 6px;
            }
            QFrame#cardFrame QLabel {
                background: transparent;
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
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            while not os.path.exists(os.path.join(self.base_dir, 'acestep')) and not os.path.exists(os.path.join(self.base_dir, '2、run_gradio.ps1')) and not os.path.exists(os.path.join(self.base_dir, 'scripts', 'install-env.ps1')):
                parent_dir = os.path.dirname(self.base_dir)
                if parent_dir == self.base_dir:
                    break
                self.base_dir = parent_dir
        
        self.service_processes: Dict[str, ServiceProcess] = {}
        self.service_cards: Dict[str, ServiceCard] = {}
        self.api_process = None
        self.is_starting = False
        self._running_services_count = 0
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
        self.deploy_page = None
        self._home_loaded = False
        
        self._setup_ui_skeleton()
        
        self.log_signal.connect(self._append_log_to_ui)
        self.enable_buttons_signal.connect(self._enable_buttons)
        self.deploy_step_signal.connect(self._update_deploy_step)
        
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
                border-color: #1E88E5;
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
        
        self.btn_deploy_nav = QPushButton("⚙️ 部署维护")
        self.btn_deploy_nav.setCheckable(True)
        self.btn_deploy_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_deploy_nav.setStyleSheet(menu_button_style)
        self.btn_deploy_nav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_deploy_nav.clicked.connect(lambda: self._switch_page(3))
        nav_bar_layout.addWidget(self.btn_deploy_nav)
        
        self.btn_model_nav = QPushButton("📦 模型管理")
        self.btn_model_nav.setCheckable(True)
        self.btn_model_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_model_nav.setStyleSheet(menu_button_style)
        self.btn_model_nav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_model_nav.clicked.connect(lambda: self._switch_page(1))
        nav_bar_layout.addWidget(self.btn_model_nav)
        
        self.btn_version_nav = QPushButton("🔄 软件更新")
        self.btn_version_nav.setCheckable(True)
        self.btn_version_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_version_nav.setStyleSheet(menu_button_style)
        self.btn_version_nav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_version_nav.clicked.connect(lambda: self._switch_page(2))
        nav_bar_layout.addWidget(self.btn_version_nav)
        
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
        self.page_stack.addWidget(QWidget())
        
        main_layout.addWidget(self.page_stack, 1)
        
        if self._splash:
            self._splash.set_progress(0.2, "正在初始化框架...")
    
    def _deferred_init(self):
        if self._home_loaded:
            return
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()

        def _pulse(msg, val):
            if self._splash:
                self._splash.set_progress(val, msg)
            if app:
                app.processEvents()

        _pulse("正在加载配置...", 0.3)
        self.config = ConfigManager(self.base_dir)

        _pulse("正在检测浏览器...", 0.4)
        self.browsers = self._detect_browsers()
        self.selected_browser = self.config.get("browser.default", "system")
        self.custom_browser_path = self.config.get("browser.custom_path", "")
        if self.custom_browser_path and os.path.exists(self.custom_browser_path):
            self.browsers["自定义浏览器"] = self.custom_browser_path
        self.selected_download_source = self.config.get("download.source", "auto")

        _pulse("正在构建主界面...", 0.5)

        while self.home_layout.count():
            item = self.home_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._populate_home_page(_pulse)

        _pulse("正在启动监控...", 0.75)
        self._setup_monitor()
        self._setup_tray()

        size = self.config.get("ui.window_size", {"width": 1200, "height": 1100})
        self.resize(size["width"], size["height"])

        self._home_loaded = True

        _pulse("加载完成！", 1.0)
    
    def _populate_home_page(self, _pulse=None):
        """填充首页内容到已有的home_layout"""
        
        # 日志区域（高度紧凑结构：系统信息+日志融合）
        self.log_group = QFrame()
        self.log_group.setFrameShape(QFrame.Shape.NoFrame)
        self.log_group.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 6px;
            }
            QFrame QLabel {
                border: none;
                background: transparent;
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
                background-color: #3D3D3D;
                color: #BBBBBB;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2E7D32;
                color: #FFFFFF;
                border-color: #388E3C;
            }
            QPushButton:!checked {
                background-color: #3D3D3D;
                color: #BBBBBB;
                border-color: #555555;
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
                background-color: #2D2D2D;
                color: #AAAAAA;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #C62828;
                border-color: #D32F2F;
            }
        """)
        self.expand_switch.clicked.connect(self._on_expand_toggled)
        header_layout.addWidget(self.expand_switch)
        
        self.btn_save_log = QPushButton("💾 保存日志")
        self.btn_save_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_log.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: 1px solid #1976D2;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1E88E5;
            }
        """)
        self.btn_save_log.clicked.connect(self._save_runtime_log)
        header_layout.addWidget(self.btn_save_log)
        
        self.btn_clear_log = QPushButton("🗑 清空")
        self.btn_clear_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_log.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: #E0E0E0;
                border: 1px solid #616161;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
                border-color: #757575;
            }
        """)
        self.btn_clear_log.clicked.connect(self._clear_runtime_log)
        header_layout.addWidget(self.btn_clear_log)
        
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

        if _pulse:
            _pulse("正在构建控制面板...", 0.55)

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
        
        # 1. 浏览器设置面板 - 单排三栏饱满布局
        browser_panel = QFrame()
        browser_panel.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame QLabel {
                border: none;
                background: transparent;
            }
        """)
        browser_layout = QHBoxLayout(browser_panel)
        browser_layout.setSpacing(10)
        browser_layout.setContentsMargins(10, 10, 10, 10)

        # 统一的内联卡片样式
        def _make_browser_section(inner_layout):
            section = QFrame()
            section.setStyleSheet("""
                QFrame {
                    background-color: #252525;
                    border: 1px solid #333333;
                    border-radius: 6px;
                }
            """)
            section_layout = QHBoxLayout(section)
            section_layout.setSpacing(8)
            section_layout.setContentsMargins(10, 8, 10, 8)
            section_layout.addLayout(inner_layout)
            return section

        # 第1栏：浏览器选择
        browser_sel_layout = QHBoxLayout()
        browser_sel_layout.setSpacing(8)
        browser_label = QLabel("🌐 浏览器")
        browser_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #B0B0B0;")
        browser_sel_layout.addWidget(browser_label)

        self.browser_combo = QComboBox()
        self.browser_combo.setStyleSheet("""
            QComboBox {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 6px 30px 6px 10px;
                font-size: 12px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #555555;
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
                background-color: #1A1A1A;
                border: 1px solid #444444;
                border-radius: 6px;
                outline: none;
                selection-background-color: #C62828;
                selection-color: #FFFFFF;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
            }
        """)

        # 添加浏览器选项
        for browser_name, browser_path in self.browsers.items():
            self.browser_combo.addItem(browser_name, browser_path)
        self.browser_combo.addItem("📁 自定义浏览器...", "custom")

        is_custom = self.selected_browser == "自定义浏览器" or self.selected_browser == "custom"
        if is_custom and self.custom_browser_path:
            found = False
            for i in range(self.browser_combo.count()):
                if self.browser_combo.itemText(i) == self.selected_browser:
                    self.browser_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                for i in range(self.browser_combo.count()):
                    if self.browser_combo.itemData(i) == "custom":
                        self.browser_combo.setCurrentIndex(i)
                        break
        else:
            for i in range(self.browser_combo.count()):
                if self.browser_combo.itemText(i) == self.selected_browser:
                    self.browser_combo.setCurrentIndex(i)
                    break

        self.browser_combo.currentIndexChanged.connect(self._on_browser_changed)
        browser_sel_layout.addWidget(self.browser_combo, 1)
        browser_sel_section = _make_browser_section(browser_sel_layout)
        browser_layout.addWidget(browser_sel_section, 1)

        # 第2栏：浏览器路径（始终显示，非自定义时只读）
        browser_path_layout = QHBoxLayout()
        browser_path_layout.setSpacing(8)
        path_label = QLabel("📁 路径")
        path_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #B0B0B0;")
        browser_path_layout.addWidget(path_label)

        self.browser_path_edit = QLineEdit()
        self.browser_path_edit.setReadOnly(True)
        self.browser_path_edit.setPlaceholderText("选择浏览器后显示路径...")
        self.browser_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1A1A1A;
                color: #A0A0A0;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:hover {
                border-color: #555555;
            }
            QLineEdit:enabled {
                color: #F0F0F0;
            }
        """)
        browser_path_layout.addWidget(self.browser_path_edit, 1)

        self.btn_select_browser = QPushButton("📂 选择")
        self.btn_select_browser.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_browser.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #E0E0E0;
                border: 1px solid #1976D2;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1E88E5;
            }
        """)
        self.btn_select_browser.clicked.connect(self._select_custom_browser)
        self.btn_select_browser.setVisible(is_custom)
        browser_path_layout.addWidget(self.btn_select_browser)
        browser_path_section = _make_browser_section(browser_path_layout)
        browser_layout.addWidget(browser_path_section, 2)

        # 第3栏：使用说明按钮（带图标文字）
        self.btn_help = QPushButton("📖 使用说明")
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setStyleSheet("""
            QPushButton {
                background-color: #263238;
                color: #FFFFFF;
                border: 1px solid #37474F;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #37474F;
                border-color: #546E7A;
            }
        """)
        self.btn_help.clicked.connect(self._show_help_dialog)
        browser_layout.addWidget(self.btn_help, 0, Qt.AlignmentFlag.AlignVCenter)

        settings_layout.addWidget(browser_panel)

        self.services_layout.addWidget(settings_container)

        qinglong_project = PROJECTS["qinglong"]
        self.qinglong_group = QFrame()
        self.qinglong_group.setFrameShape(QFrame.Shape.NoFrame)
        self.qinglong_group.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 6px;
            }
            QFrame QLabel {
                border: none;
                background: transparent;
            }
        """)
        qinglong_layout = QGridLayout(self.qinglong_group)

        col = 0
        for service_id, service in qinglong_project["services"].items():
            full_service_id = f"qinglong_{service_id}"
            card = ServiceCard(full_service_id)
            card.restart_clicked.connect(self._restart_service)
            card.open_clicked.connect(self._open_service)
            card.port_changed.connect(self._on_port_changed)
            qinglong_layout.addWidget(card, 0, col)
            self.service_cards[full_service_id] = card
            col += 1

        self.services_layout.addWidget(self.qinglong_group)

        # 底部操作栏：三按钮布局，中间按钮占一半宽度
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)
        bottom_bar.setContentsMargins(0, 6, 0, 0)

        # 左侧：重启服务
        self.btn_bottom_restart = QPushButton("🔄 重启服务")
        self.btn_bottom_restart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bottom_restart.setFixedHeight(44)
        self.btn_bottom_restart.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: 2px solid #1976D2;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1E88E5;
            }
            QPushButton:disabled {
                background-color: #424242;
                border-color: #616161;
                color: #888888;
            }
        """)
        self.btn_bottom_restart.clicked.connect(self._restart_all_services)
        bottom_bar.addWidget(self.btn_bottom_restart, 1)

        # 中间：启动音乐创意台（占一半宽度）
        self.btn_start_qinglong = QPushButton("🎵 启动音乐创意台")
        self.btn_start_qinglong.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start_qinglong.setFixedHeight(48)
        self.btn_start_qinglong.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: 2px solid #E53935;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C62828;
                border-color: #C62828;
            }
            QPushButton:disabled {
                background-color: #424242;
                border-color: #616161;
                color: #AAAAAA;
            }
        """)
        self.btn_start_qinglong.clicked.connect(lambda: self._start_project("qinglong"))
        bottom_bar.addWidget(self.btn_start_qinglong, 2)

        # 右侧：停止服务
        self.btn_bottom_stop = QPushButton("⏹ 停止服务")
        self.btn_bottom_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bottom_stop.setFixedHeight(44)
        self.btn_bottom_stop.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: #E0E0E0;
                border: 2px solid #616161;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
                border-color: #757575;
            }
            QPushButton:disabled {
                background-color: #424242;
                border-color: #616161;
                color: #888888;
            }
        """)
        self.btn_bottom_stop.clicked.connect(self._stop_all_services)
        bottom_bar.addWidget(self.btn_bottom_stop, 1)

        self.services_layout.addLayout(bottom_bar)

        self.home_layout.addWidget(self.services_container)

        if _pulse:
            _pulse("正在完成初始化...", 0.65)

    
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
                    background-color: #3D3D3D;
                    color: #BBBBBB;
                    border: 1px solid #555555;
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
    
    def _save_runtime_log(self):
        """保存运行日志到文件"""
        if not hasattr(self, 'log_output') or self.log_output is None:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"runtime_log_{timestamp}.txt"
        
        output_dir = self.config.get("output.directory", "") if hasattr(self, 'config') else ""
        if not output_dir or not os.path.exists(output_dir):
            output_dir = os.path.join(self.base_dir, "output")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存运行日志", os.path.join(output_dir, default_name),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_output.toPlainText())
                self._log(f"✓ 日志已保存: {file_path}", "#4CAF50")
            except Exception as e:
                self._log(f"[错误] 保存日志失败: {e}", "#F44336")
    
    def _clear_runtime_log(self):
        """清空运行日志"""
        if hasattr(self, 'log_output') and self.log_output is not None:
            self.log_output.clear()
    
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
    
    def _create_deploy_page(self):
        """创建部署维护页面（参考视频创意站左右分栏布局）"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        deploy_frame = QFrame()
        deploy_frame.setObjectName("cardFrame")
        deploy_layout = QHBoxLayout(deploy_frame)
        deploy_layout.setSpacing(10)
        deploy_layout.setContentsMargins(14, 10, 14, 10)
        
        deploy_title = QLabel("🔧 部署维护")
        deploy_title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        deploy_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        deploy_layout.addWidget(deploy_title)
        
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: #333333; background: transparent;")
        deploy_layout.addWidget(sep1)
        
        source_label = QLabel("下载源")
        source_label.setStyleSheet("font-size: 11px; color: #888888; background: transparent;")
        deploy_layout.addWidget(source_label)
        
        self.deploy_source_combo = QComboBox()
        self.deploy_source_combo.setStyleSheet("""
            QComboBox {
                background-color: #252525; color: #FFFFFF;
                border: 1px solid #333333; border-radius: 4px;
                padding: 4px 22px 4px 8px; font-size: 11px; min-width: 130px;
            }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox::down-arrow {
                image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent; border-top: 4px solid #888888;
            }
            QComboBox QAbstractItemView {
                background-color: #252525; border: 1px solid #333333;
                selection-background-color: #1976D2;
            }
        """)
        self.deploy_source_combo.addItem("自动选择", "auto")
        self.deploy_source_combo.addItem("清华镜像", "tsinghua")
        self.deploy_source_combo.addItem("阿里云镜像", "aliyun")
        self.deploy_source_combo.addItem("官方源", "official")
        deploy_layout.addWidget(self.deploy_source_combo)
        
        deploy_layout.addStretch()
        
        self.deploy_progress_label = QLabel("")
        self.deploy_progress_label.setStyleSheet("font-size: 11px; color: #FFA726; background: transparent;")
        self.deploy_progress_label.setWordWrap(True)
        deploy_layout.addWidget(self.deploy_progress_label, 1)
        
        self.btn_one_click_deploy = QPushButton("🔧 一键部署维护")
        self.btn_one_click_deploy.setFixedWidth(120)
        self.btn_one_click_deploy.setStyleSheet("""
            QPushButton {
                background-color: #1B5E20; color: #FFFFFF;
                border: 1px solid #2E7D32; border-radius: 6px;
                padding: 6px 12px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2E7D32; }
            QPushButton:disabled { background-color: #1A1A1A; color: #555555; border-color: #222222; }
        """)
        self.btn_one_click_deploy.clicked.connect(self._deploy_maintenance)
        deploy_layout.addWidget(self.btn_one_click_deploy)
        
        layout.addWidget(deploy_frame)
        
        content_row = QHBoxLayout()
        content_row.setSpacing(8)
        
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        
        env_frame = QFrame()
        env_frame.setObjectName("cardFrame")
        env_layout = QVBoxLayout(env_frame)
        env_layout.setSpacing(4)
        env_layout.setContentsMargins(12, 10, 12, 10)
        
        env_header = QHBoxLayout()
        env_title = QLabel("🔍 环境检测")
        env_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        env_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        env_header.addWidget(env_title)
        env_header.addStretch()
        
        refresh_env_btn = QPushButton("🔄 重新检测")
        refresh_env_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_env_btn.setStyleSheet("""
            QPushButton { background-color: #1A3A5C; color: #8BB8E8; border: 1px solid #1E4D7A; border-radius: 4px; padding: 4px 12px; font-size: 11px; }
            QPushButton:hover { background-color: #1E4D7A; color: #FFFFFF; }
        """)
        refresh_env_btn.clicked.connect(self._refresh_deploy_env_status)
        env_header.addWidget(refresh_env_btn)
        env_layout.addLayout(env_header)
        
        env_grid = QGridLayout()
        env_grid.setSpacing(3)
        env_grid.setContentsMargins(0, 4, 0, 0)
        self._env_labels = {}
        env_items = [
            ("powershell", "PowerShell"),
            ("nodejs", "Node.js"),
            ("uv", "UV 包管理器"),
            ("venv", "Python 环境"),
            ("python_deps", "Python 依赖"),
            ("frontend_deps", "前端依赖"),
            ("scripts", "启动脚本"),
            ("gpu", "GPU / VRAM"),
        ]
        for i, (key, text) in enumerate(env_items):
            row_idx = i // 2
            col_idx = i % 2
            cell = QHBoxLayout()
            cell.setSpacing(4)
            name_lbl = QLabel(text)
            name_lbl.setFixedWidth(80)
            name_lbl.setStyleSheet("font-size: 10px; color: #888888; background: transparent;")
            cell.addWidget(name_lbl)
            lbl = QLabel("检测中...")
            lbl.setStyleSheet("font-size: 10px; background: transparent;")
            lbl.setWordWrap(True)
            cell.addWidget(lbl, 1)
            self._env_labels[key] = lbl
            env_grid.addLayout(cell, row_idx, col_idx)
        env_layout.addLayout(env_grid)
        
        left_col.addWidget(env_frame)
        
        deps_frame = QFrame()
        deps_frame.setObjectName("cardFrame")
        deps_layout_v = QVBoxLayout(deps_frame)
        deps_layout_v.setSpacing(3)
        deps_layout_v.setContentsMargins(12, 8, 12, 8)
        
        deps_header = QHBoxLayout()
        deps_title = QLabel("📦 依赖版本")
        deps_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        deps_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        deps_header.addWidget(deps_title)
        deps_header.addStretch()
        
        refresh_deps_btn = QPushButton("🔄 刷新版本")
        refresh_deps_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_deps_btn.setStyleSheet("""
            QPushButton { background-color: #1A3A5C; color: #8BB8E8; border: 1px solid #1E4D7A; border-radius: 4px; padding: 4px 12px; font-size: 11px; }
            QPushButton:hover { background-color: #1E4D7A; color: #FFFFFF; }
        """)
        refresh_deps_btn.clicked.connect(self._refresh_deps_list)
        deps_header.addWidget(refresh_deps_btn)
        deps_layout_v.addLayout(deps_header)
        
        self._deps_grid = QGridLayout()
        self._deps_grid.setSpacing(2)
        self._deps_grid.setContentsMargins(0, 2, 0, 0)
        deps_layout_v.addLayout(self._deps_grid)
        
        left_col.addWidget(deps_frame)
        
        dir_frame = QFrame()
        dir_frame.setObjectName("cardFrame")
        dir_layout = QVBoxLayout(dir_frame)
        dir_layout.setSpacing(6)
        dir_layout.setContentsMargins(12, 10, 12, 10)
        
        dir_header = QHBoxLayout()
        dir_title = QLabel("📁 目录配置")
        dir_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        dir_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        dir_header.addWidget(dir_title)
        dir_header.addStretch()
        dir_layout.addLayout(dir_header)
        
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        output_dir_label = QLabel("输出")
        output_dir_label.setFixedWidth(32)
        output_dir_label.setStyleSheet("font-size: 10px; color: #888888; background: transparent;")
        output_row.addWidget(output_dir_label)
        self.output_dir_edit = QLineEdit()
        saved_output_dir = self.config.get("output.directory", "")
        if not saved_output_dir:
            saved_output_dir = os.path.join(self.base_dir, "output")
        self.output_dir_edit.setText(saved_output_dir)
        self.output_dir_edit.setPlaceholderText("默认：项目目录/output")
        self.output_dir_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E; color: #CCCCCC;
                border: 1px solid #2A2A2A; border-radius: 4px;
                padding: 4px 8px; font-size: 10px;
            }
            QLineEdit:focus { border-color: #1976D2; }
        """)
        output_row.addWidget(self.output_dir_edit, 1)
        
        output_browse_btn = QPushButton("📂")
        output_browse_btn.setFixedSize(28, 24)
        output_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A3A5C; color: #8BB8E8;
                border: 1px solid #1E4D7A; border-radius: 4px;
                padding: 2px; font-size: 10px;
            }
            QPushButton:hover { background-color: #1E4D7A; color: #FFFFFF; }
        """)
        output_browse_btn.clicked.connect(self._browse_output_directory)
        output_row.addWidget(output_browse_btn)
        
        output_save_btn = QPushButton("💾")
        output_save_btn.setFixedSize(28, 24)
        output_save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4332; color: #7BC47F;
                border: 1px solid #2D6A4F; border-radius: 4px;
                padding: 2px; font-size: 10px;
            }
            QPushButton:hover { background-color: #2D6A4F; color: #FFFFFF; }
        """)
        output_save_btn.clicked.connect(self._save_output_directory)
        output_row.addWidget(output_save_btn)
        
        open_output_btn = QPushButton("📂 打开")
        open_output_btn.setFixedWidth(50)
        open_output_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A3A5C; color: #8BB8E8;
                border: 1px solid #1E4D7A; border-radius: 4px;
                padding: 2px 6px; font-size: 10px;
            }
            QPushButton:hover { background-color: #1E4D7A; color: #FFFFFF; }
        """)
        open_output_btn.clicked.connect(self._open_output_directory)
        output_row.addWidget(open_output_btn)
        
        dir_layout.addLayout(output_row)
        
        left_col.addWidget(dir_frame)
        left_col.addStretch()
        
        content_row.addLayout(left_col, 4)
        
        deploy_log_frame = QFrame()
        deploy_log_frame.setObjectName("cardFrame")
        deploy_log_layout = QVBoxLayout(deploy_log_frame)
        deploy_log_layout.setSpacing(4)
        deploy_log_layout.setContentsMargins(12, 10, 12, 10)
        
        deploy_log_header = QHBoxLayout()
        deploy_log_title = QLabel("📋 运行日志")
        deploy_log_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        deploy_log_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        deploy_log_header.addWidget(deploy_log_title)
        deploy_log_header.addStretch()
        
        self.deploy_auto_scroll_switch = QPushButton("🔄 自动滚动")
        self.deploy_auto_scroll_switch.setCheckable(True)
        self.deploy_auto_scroll_switch.setChecked(True)
        self.deploy_auto_scroll_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.deploy_auto_scroll_switch.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32; color: white;
                border: 1px solid #388E3C; border-radius: 4px;
                padding: 4px 10px; font-size: 11px; font-weight: bold;
            }
            QPushButton:!checked {
                background-color: #3D3D3D; color: #BBBBBB; border-color: #555555;
            }
        """)
        self.deploy_auto_scroll_switch.clicked.connect(self._on_deploy_auto_scroll_toggled)
        deploy_log_header.addWidget(self.deploy_auto_scroll_switch)
        
        self.deploy_expand_switch = QPushButton("📐 展开")
        self.deploy_expand_switch.setCheckable(True)
        self.deploy_expand_switch.setChecked(False)
        self.deploy_expand_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.deploy_expand_switch.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D; color: #AAAAAA;
                border: 1px solid #444444; border-radius: 4px;
                padding: 4px 10px; font-size: 11px; font-weight: bold;
            }
            QPushButton:checked { background-color: #C62828; border-color: #D32F2F; }
        """)
        self.deploy_expand_switch.clicked.connect(self._on_deploy_expand_toggled)
        deploy_log_header.addWidget(self.deploy_expand_switch)
        
        clear_deploy_log_btn = QPushButton("🗑️ 清空")
        clear_deploy_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A2A2A; color: #888888;
                border: 1px solid #3A3A3A; border-radius: 4px;
                padding: 4px 10px; font-size: 11px;
            }
            QPushButton:hover { background-color: #3A3A3A; color: #CCCCCC; }
        """)
        clear_deploy_log_btn.clicked.connect(lambda: self.deploy_log_output.clear())
        deploy_log_header.addWidget(clear_deploy_log_btn)
        
        save_deploy_log_btn = QPushButton("💾 保存")
        save_deploy_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A3A5C; color: #8BB8E8;
                border: 1px solid #1E4D7A; border-radius: 4px;
                padding: 4px 10px; font-size: 11px;
            }
            QPushButton:hover { background-color: #1E4D7A; color: #FFFFFF; }
        """)
        save_deploy_log_btn.clicked.connect(self._save_deploy_log)
        deploy_log_header.addWidget(save_deploy_log_btn)
        
        deploy_log_layout.addLayout(deploy_log_header)
        
        self.deploy_log_output = QTextEdit()
        self.deploy_log_output.setReadOnly(True)
        self.deploy_log_output.setStyleSheet("""
            QTextEdit {
                background-color: #0A0A0A; color: #BBBBBB;
                border: 1px solid #1A1A1A; border-radius: 4px;
                font-family: 'Consolas', 'Microsoft YaHei'; font-size: 10px;
                padding: 4px;
            }
        """)
        deploy_log_layout.addWidget(self.deploy_log_output, 1)
        
        content_row.addWidget(deploy_log_frame, 6)
        
        layout.addLayout(content_row, 1)
        
        self.deploy_env_group = env_frame
        self.deploy_output_group = dir_frame
        
        return page
    
    def _switch_page(self, index):
        """切换页面"""
        self.btn_home.setChecked(index == 0)
        self.btn_model_nav.setChecked(index == 1)
        self.btn_version_nav.setChecked(index == 2)
        self.btn_deploy_nav.setChecked(index == 3)
        
        if index == 1 and self.model_page is None:
            self.model_page = self._create_model_page()
            self.page_stack.removeWidget(self.page_stack.widget(1))
            self.page_stack.insertWidget(1, self.model_page)
        
        if index == 2 and self.version_page is None:
            self.version_page = self._create_version_page()
            self.page_stack.removeWidget(self.page_stack.widget(2))
            self.page_stack.insertWidget(2, self.version_page)
        
        if index == 3 and self.deploy_page is None:
            self.deploy_page = self._create_deploy_page()
            self.page_stack.removeWidget(self.page_stack.widget(3))
            self.page_stack.insertWidget(3, self.deploy_page)
        
        self.page_stack.setCurrentIndex(index)
        
        if index == 1 and self.model_manager_widget is not None:
            if not self._model_list_loaded:
                self._model_list_loaded = True
                self._load_model_list()
            self.model_manager_widget._update_ui()
        
        if index == 2 and self.version_manager_widget is not None:
            if not self.version_manager_widget._versions_loaded:
                QTimer.singleShot(300, self._delayed_load_versions)
        
        if index == 3:
            QTimer.singleShot(200, self._refresh_deploy_env_status)
            QTimer.singleShot(500, self._refresh_deps_list)
    
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
        
        # 跟踪运行中的服务数量，更新底部按钮显示
        if is_running:
            self._running_services_count += 1
        else:
            self._running_services_count = max(0, self._running_services_count - 1)
        
        self._update_bottom_bar()
    
    def _update_bottom_bar(self):
        """根据服务运行状态更新底部按钮状态"""
        has_running = self._running_services_count > 0
        is_starting = getattr(self, 'is_starting', False)
        
        if is_starting:
            self.btn_bottom_restart.setEnabled(False)
            self.btn_bottom_stop.setEnabled(False)
            self.btn_start_qinglong.setText("⏳ 正在启动...")
            self.btn_start_qinglong.setEnabled(False)
        elif has_running:
            self.btn_bottom_restart.setEnabled(True)
            self.btn_bottom_stop.setEnabled(True)
            self.btn_start_qinglong.setText("🎵 音乐创意台运行中")
            self.btn_start_qinglong.setStyleSheet("""
                QPushButton {
                    background-color: #2E7D32;
                    color: white;
                    border: 2px solid #2E7D32;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1B5E20;
                    border-color: #1B5E20;
                }
                QPushButton:disabled {
                    background-color: #424242;
                    border-color: #616161;
                    color: #AAAAAA;
                }
            """)
            self.btn_start_qinglong.setEnabled(False)
        else:
            self.btn_bottom_restart.setEnabled(True)
            self.btn_bottom_stop.setEnabled(True)
            self.btn_start_qinglong.setText("🎵 启动音乐创意台")
            self.btn_start_qinglong.setStyleSheet("""
                QPushButton {
                    background-color: #E53935;
                    color: white;
                    border: 2px solid #E53935;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #C62828;
                    border-color: #C62828;
                }
                QPushButton:disabled {
                    background-color: #424242;
                    border-color: #616161;
                    color: #AAAAAA;
                }
            """)
            self.btn_start_qinglong.setEnabled(True)
    
    def _append_log_to_ui(self, message: str, color: str):
        """在主线程中添加日志到UI（由信号调用）"""
        if not hasattr(self, 'log_output') or self.log_output is None:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_output.append(html)
        if hasattr(self, 'auto_scroll_switch') and self.auto_scroll_switch.isChecked():
            scrollbar = self.log_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        if hasattr(self, 'deploy_log_output') and self.deploy_log_output is not None:
            self.deploy_log_output.append(html)
            if hasattr(self, 'deploy_auto_scroll_switch') and self.deploy_auto_scroll_switch.isChecked():
                scrollbar2 = self.deploy_log_output.verticalScrollBar()
                scrollbar2.setValue(scrollbar2.maximum())
    
    def _append_deploy_log(self, message: str, color: str = "#00FF00"):
        """添加日志到部署维护页面（线程安全）"""
        self.log_signal.emit(message, color)
    
    def _clear_deploy_log(self):
        """清空部署维护日志"""
        if hasattr(self, 'deploy_log_output') and self.deploy_log_output is not None:
            self.deploy_log_output.clear()
    
    def _save_deploy_log(self):
        """保存部署维护日志到文件"""
        if not hasattr(self, 'deploy_log_output') or self.deploy_log_output is None:
            return
        
        from PyQt6.QtWidgets import QFileDialog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"deploy_log_{timestamp}.txt"
        
        output_dir = self.config.get("output.directory", "")
        if not output_dir or not os.path.exists(output_dir):
            output_dir = os.path.join(self.base_dir, "output")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存维护日志", os.path.join(output_dir, default_name),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.deploy_log_output.toPlainText())
                self._log(f"✓ 日志已保存: {file_path}", "#4CAF50")
            except Exception as e:
                self._log(f"[错误] 保存日志失败: {e}", "#F44336")
    
    def _on_deploy_auto_scroll_toggled(self, checked):
        """部署维护自动滚动开关切换"""
        if checked:
            self.deploy_auto_scroll_switch.setStyleSheet("""
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
            self.deploy_auto_scroll_switch.setStyleSheet("""
                QPushButton {
                    background-color: #3D3D3D;
                    color: #BBBBBB;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
    
    def _on_deploy_expand_toggled(self, checked):
        """部署维护展开窗口切换"""
        if checked:
            if hasattr(self, 'deploy_env_group'):
                self.deploy_env_group.hide()
            if hasattr(self, 'deploy_output_group'):
                self.deploy_output_group.hide()
            self.deploy_expand_switch.setText("📐 收起")
        else:
            if hasattr(self, 'deploy_env_group'):
                self.deploy_env_group.show()
            if hasattr(self, 'deploy_output_group'):
                self.deploy_output_group.show()
            self.deploy_expand_switch.setText("📐 展开")
    
    def _open_output_directory(self):
        """打开输出目录"""
        output_dir = self.config.get("output.directory", "")
        if not output_dir:
            output_dir = os.path.join(self.base_dir, "output")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        try:
            os.startfile(output_dir)
        except Exception as e:
            self._log(f"[错误] 打开输出目录失败: {e}", "#F44336")
    
    def _browse_output_directory(self):
        """浏览选择输出目录"""
        from PyQt6.QtWidgets import QFileDialog
        current_dir = self.output_dir_edit.text() if hasattr(self, 'output_dir_edit') else ""
        if not current_dir or not os.path.exists(current_dir):
            current_dir = os.path.join(self.base_dir, "output")
        
        selected_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", current_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if selected_dir:
            self.output_dir_edit.setText(selected_dir)
    
    def _save_output_directory(self):
        """保存输出目录设置"""
        if not hasattr(self, 'output_dir_edit'):
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            self._log("[警告] 输出目录不能为空", "#FF9800")
            return
        
        if not os.path.isabs(output_dir):
            self._log("[警告] 请使用绝对路径作为输出目录", "#FF9800")
            return
        
        self.config.set("output.directory", output_dir)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                self._log(f"✓ 输出目录已创建: {output_dir}", "#4CAF50")
            except Exception as e:
                self._log(f"[错误] 创建输出目录失败: {e}", "#F44336")
                return
        
        self._log(f"✓ 输出目录已保存: {output_dir}", "#4CAF50")
    
    def _log(self, message: str, color: str = "#00FF00"):
        """添加日志（线程安全）"""
        self.log_signal.emit(message, color)
    
    def _start_project(self, project_id: str):
        """启动单个项目"""
        if self.is_starting:
            self._log("正在启动中，请稍候...", "#616161")
            return
        
        self.is_starting = True
        self._update_bottom_bar()
        
        self.start_thread = threading.Thread(target=self._start_project_services, args=(project_id,))
        self.start_thread.start()
    
    def _show_version_manager(self):
        """切换到版本管理器页面"""
        self._switch_page(2)
    
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
        self._switch_page(1)
    
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
                            fix_cmd = [python_exe, "-m", "pip", "install", "transformers>=4.51.0,<4.58.0", "--quiet"]
                            fix_process = hidden_popen(
                                fix_cmd,
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
            
            if project_id == "qinglong":
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
        self.is_starting = False
        self._update_bottom_bar()
        
        if hasattr(self, 'btn_one_click_deploy'):
            self.btn_one_click_deploy.setEnabled(True)
    
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
    
    def _ensure_uv_python_healthy(self, uv_path, scripts_dir):
        """确保 uv 管理的 Python 可用，损坏则修复。返回 (python_ok, venv_python_path)"""
        python_ok = False
        found_python = None
        
        try:
            process = hidden_popen(
                [uv_path, "python", "find", "3.12"],
                cwd=scripts_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, _ = process.communicate(timeout=10)
            if process.returncode == 0 and stdout.strip():
                found_python = stdout.strip().split('\n')[0].strip()
                self._log(f"[信息] 找到 Python: {found_python}")
                process2 = hidden_popen(
                    [found_python, "-c", "print('ok')"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout2, _ = process2.communicate(timeout=10)
                if process2.returncode == 0 and "ok" in stdout2:
                    python_ok = True
                else:
                    self._log("[警告] uv 管理的 Python 无法运行，需要重新安装", "#FF9800")
        except Exception:
            self._log("[警告] 无法查找 uv 管理的 Python", "#FF9800")
        
        if not python_ok:
            if found_python and os.path.exists(found_python):
                broken_dir = os.path.dirname(found_python)
                self._log(f"[信息] 删除损坏的 Python: {broken_dir}")
                try:
                    import shutil
                    shutil.rmtree(broken_dir, ignore_errors=True)
                except Exception:
                    pass
            
            self._log("[信息] 正在重新安装 Python 3.12...")
            try:
                process = hidden_popen(
                    [uv_path, "python", "install", "3.12"],
                    cwd=scripts_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                stdout, _ = process.communicate(timeout=300)
                if stdout:
                    for line in stdout.splitlines():
                        if line.strip():
                            self._log(f"[安装Python] {line.strip()}")
                if process.returncode == 0:
                    self._log("✓ Python 3.12 安装完成")
                    python_ok = True
                else:
                    self._log("[错误] Python 3.12 安装失败", "#F44336")
                    return False, None
            except Exception as e:
                self._log(f"[错误] Python 3.12 安装失败: {e}", "#F44336")
                return False, None
        
        return python_ok, found_python

    def _install_missing_dependencies(self, venv_python, scripts_dir):
        """检测并安装缺失的依赖"""
        uv_path = os.path.expanduser("~/.local/bin/uv.exe")
        if not os.path.exists(uv_path):
            self._log("[错误] uv 未安装，无法自动修复依赖", "#F44336")
            return
        
        venv_broken = False
        if os.path.exists(venv_python):
            try:
                process = hidden_popen(
                    [venv_python, "-c", "print('ok')"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=10)
                if process.returncode != 0 or "ok" not in stdout:
                    venv_broken = True
                    self._log("[警告] 虚拟环境 Python 无法正常运行，需要重建", "#FF9800")
                    if stderr:
                        for line in stderr.splitlines()[:3]:
                            if line.strip():
                                self._log(f"  {line.strip()}", "#FF9800")
            except Exception:
                venv_broken = True
                self._log("[警告] 虚拟环境 Python 无法启动，需要重建", "#FF9800")
        else:
            venv_broken = True
            self._log("[警告] 虚拟环境 Python 不存在，需要重建", "#FF9800")
        
        if venv_broken:
            self._log("[信息] 虚拟环境损坏，重新运行安装脚本...")
            install_script = os.path.join(self.base_dir, "scripts", "install-env.ps1")
            if os.path.exists(install_script):
                try:
                    result = hidden_run(
                        ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_script],
                        cwd=self.base_dir,
                        capture_output=False,
                        text=True,
                        timeout=1800
                    )
                    if result.returncode == 0:
                        self._log("✅ 环境重建完成", "#4CAF50")
                        return
                    else:
                        self._log(f"[警告] 安装脚本返回码: {result.returncode}，尝试手动修复...", "#FF9800")
                except Exception as e:
                    self._log(f"[警告] 安装脚本执行失败: {e}，尝试手动修复...", "#FF9800")
            else:
                self._log("[警告] 安装脚本不存在，尝试手动修复...", "#FF9800")
            
            venv_dir = os.path.join(scripts_dir, ".venv")
            self._log("[信息] 正在删除损坏的虚拟环境...")
            try:
                import shutil
                shutil.rmtree(venv_dir, ignore_errors=True)
                self._log("✓ 损坏的虚拟环境已删除")
            except Exception as e:
                self._log(f"[警告] 删除虚拟环境失败: {e}", "#FF9800")
            
            python_ok, _ = self._ensure_uv_python_healthy(uv_path, scripts_dir)
            if not python_ok:
                return
            
            self._log("[信息] 正在重新创建虚拟环境...")
            try:
                process = hidden_popen(
                    [uv_path, "venv", "-p", "3.12", "--seed"],
                    cwd=scripts_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                stdout, _ = process.communicate(timeout=60)
                if stdout:
                    for line in stdout.splitlines():
                        if line.strip():
                            self._log(f"[创建venv] {line.strip()}")
                if process.returncode == 0:
                    self._log("✓ 虚拟环境重建完成")
                    venv_python = os.path.join(scripts_dir, ".venv", "Scripts", "python.exe")
                else:
                    self._log("[错误] 虚拟环境重建失败", "#F44336")
                    return
            except Exception as e:
                self._log(f"[错误] 虚拟环境重建失败: {e}", "#F44336")
                return
        
        env = os.environ.copy()
        env["UV_INDEX_URL"] = "https://pypi.tuna.tsinghua.edu.cn/simple/"
        env["UV_EXTRA_INDEX_URL"] = "https://download.pytorch.org/whl/cu128"
        env["UV_LINK_MODE"] = "copy"
        
        required_deps = [
            ("loguru", "日志库"),
            ("psutil", "系统监控"),
            ("torch", "PyTorch 核心"),
            ("torchaudio", "音频处理"),
            ("transformers", "模型加载"),
            ("diffusers", "扩散模型"),
            ("peft", "LoRA/训练"),
            ("lycoris", "LoKr 训练"),
            ("fastapi", "API 框架"),
            ("uvicorn", "ASGI 服务器"),
            ("gradio", "Web UI"),
            ("accelerate", "加速库"),
            ("scipy", "科学计算"),
            ("soundfile", "音频文件"),
            ("einops", "张量操作"),
            ("matplotlib", "图表绘制"),
            ("diskcache", "磁盘缓存"),
            ("numba", "JIT 编译"),
            ("lightning", "训练框架"),
            ("tensorboard", "训练日志"),
            ("modelscope", "模型下载"),
            ("huggingface_hub", "HF 下载"),
            ("safetensors", "安全张量"),
        ]
        
        missing = []
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
                if process.returncode != 0:
                    missing.append(dep)
                    self._log(f"[信息] {dep} ({desc}) 缺失，需要安装")
            except Exception:
                missing.append(dep)
        
        if not missing:
            return
        
        self._log(f"[信息] 共 {len(missing)} 个依赖缺失，开始安装...")
        
        version_constraints = {
            "transformers": "transformers>=4.51.0,<5.0",
            "peft": "peft>=0.18.0",
            "diffusers": "diffusers",
            "loguru": "loguru>=0.7.3",
            "psutil": "psutil",
            "lycoris": "lycoris-lora",
            "fastapi": "fastapi>=0.110.0",
            "uvicorn": "uvicorn[standard]>=0.27.0",
            "gradio": "gradio>=6.2.0,<7.0.0",
            "accelerate": "accelerate>=1.12.0",
            "scipy": "scipy>=1.10.1",
            "soundfile": "soundfile>=0.13.1",
            "einops": "einops>=0.8.1",
            "matplotlib": "matplotlib>=3.7.5",
            "diskcache": "diskcache",
            "numba": "numba>=0.63.1",
            "lightning": "lightning>=2.0.0",
            "tensorboard": "tensorboard>=2.0.0",
            "modelscope": "modelscope",
            "huggingface_hub": "huggingface_hub",
            "safetensors": "safetensors",
        }
        
        self._log("[信息] 清理 uv 等可能残留的冲突包...")
        for stale_pkg in ["hf-xet"]:
            try:
                p = hidden_popen(
                    [venv_python, "-m", "pip", "uninstall", stale_pkg, "-y", "--quiet"],
                    cwd=scripts_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                out, _ = p.communicate(timeout=30)
                if out and "Successfully uninstalled" in out:
                    self._log(f"[信息] 已清理残留包: {stale_pkg}")
            except:
                pass
        
        pip_deps = []
        for d in missing:
            if d == "torch":
                pip_deps.append("torch>=2.9.0,<3.0")
            elif d == "torchaudio":
                pip_deps.append("torchaudio>=2.9.0,<3.0")
            elif d in version_constraints:
                pip_deps.append(version_constraints[d])
            else:
                pip_deps.append(d)
        
        pip_torch_deps = [d for d in pip_deps if d.startswith("torch")]
        pip_other_deps = [d for d in pip_deps if not d.startswith("torch")]
        
        if pip_other_deps:
            self._log(f"[信息] 安装基础依赖: {', '.join(pip_other_deps)}")
            try:
                cmd = [venv_python, "-m", "pip", "install"] + pip_other_deps
                p = hidden_popen(
                    cmd, cwd=scripts_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                out, _ = p.communicate(timeout=600)
                if out:
                    for line in out.splitlines():
                        if line.strip():
                            self._log(f"[安装] {line.strip()}")
                if p.returncode == 0:
                    self._log("✓ 基础依赖安装完成")
                else:
                    self._log(f"[警告] 基础依赖安装返回码: {p.returncode}", "#FF9800")
            except Exception as e:
                self._log(f"[警告] 基础依赖安装失败: {e}", "#FF9800")
        
        if pip_torch_deps:
            self._log(f"[信息] 安装 PyTorch 依赖: {', '.join(pip_torch_deps)}")
            try:
                cmd = [venv_python, "-m", "pip", "install", "--index-url", "https://download.pytorch.org/whl/cu128"] + pip_torch_deps
                p = hidden_popen(
                    cmd, cwd=scripts_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                out, _ = p.communicate(timeout=1200)
                if out:
                    for line in out.splitlines():
                        if line.strip():
                            self._log(f"[安装PyTorch] {line.strip()}")
                if p.returncode == 0:
                    self._log("✓ PyTorch 依赖安装完成")
                else:
                    self._log(f"[警告] PyTorch 依赖安装返回码: {p.returncode}", "#FF9800")
            except Exception as e:
                self._log(f"[警告] PyTorch 依赖安装失败: {e}", "#FF9800")
        
        self._log("[信息] 验证安装结果...")
        still_missing = []
        for dep, desc in required_deps:
            import_name = dep
            try:
                p = hidden_popen(
                    [venv_python, "-c", f"import {import_name}"],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                out, err = p.communicate(timeout=30)
                if p.returncode != 0:
                    still_missing.append(dep)
                    if err:
                        for line in err.splitlines():
                            if line.strip():
                                self._log(f"[诊断] {dep} 导入失败: {line.strip()}", "#FF9800")
                    try:
                        detail = hidden_popen(
                            [venv_python, "-c", f"import traceback, sys\ntry:\n    import {import_name}\nexcept:\n    traceback.print_exc(file=sys.stdout)"],
                            cwd=self.base_dir,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                        )
                        dout, derr = detail.communicate(timeout=15)
                        for line in (dout or "").splitlines():
                            if line.strip():
                                self._log(f"[诊断] {line.strip()}", "#FF9800")
                    except:
                        pass
            except Exception:
                still_missing.append(dep)
        
        if still_missing:
            self._log(f"[警告] 以下依赖仍缺失: {', '.join(still_missing)}", "#FF9800")
            self._log("[建议] 请手动运行 scripts/install-env.ps1 安装", "#FF9800")
        else:
            self._log("✓ 所有缺失依赖已安装完成")
    
    def _install_minimal_dependencies(self, venv_python, uv_path, scripts_dir, env):
        """安装最小化的关键依赖（备用方案）"""
        self._log("[信息] 正在安装关键依赖...")

        
        minimal_deps = [
            "loguru",
            "psutil",
            "fastapi",
            "uvicorn",
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
        """快速检查关键依赖是否已安装 - 返回缺失依赖列表（空列表表示全部OK）"""
        
        deps_to_check = ["loguru", "psutil", "torch", "torchaudio", "transformers", "diffusers", "gradio", "peft", "lycoris", "fastapi", "uvicorn", "accelerate", "scipy", "soundfile", "einops", "matplotlib", "diskcache", "numba", "lightning", "tensorboard", "modelscope", "huggingface_hub", "safetensors"]
        
        check_code = "import json; results={};\n"
        for dep in deps_to_check:
            check_code += f"try:\n    import {dep}; results['{dep}']=True\nexcept:\n    results['{dep}']=False\n"
        check_code += "print(json.dumps(results))"
        
        try:
            process = hidden_popen(
                [venv_python, "-c", check_code],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=60)
            if process.returncode == 0 and stdout.strip():
                import json
                results = json.loads(stdout.strip())
                missing = [dep for dep, ok in results.items() if not ok]
                return missing
        except Exception:
            pass
        
        return deps_to_check
    
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
            ("fastapi", "API 框架"),
            ("uvicorn", "ASGI 服务器"),
            ("gradio", "Web UI"),
            ("accelerate", "加速库"),
            ("scipy", "科学计算"),
            ("soundfile", "音频文件"),
            ("einops", "张量操作"),
            ("matplotlib", "图表绘制"),
            ("diskcache", "磁盘缓存"),
            ("numba", "JIT 编译"),
            ("lightning", "训练框架"),
            ("tensorboard", "训练日志"),
            ("modelscope", "模型下载"),
            ("huggingface_hub", "HF 下载"),
            ("safetensors", "安全张量"),
        ]
        # 可选加速 - 缺失只影响性能，不影响功能（部署维护时会自动安装）
        optional_deps = [
            ("flash_attn", "Flash Attention 加速推理（推荐安装）"),
        ]
        
        all_ok = True
        
        self._log("[信息] 验证必须依赖...")
        check_code = "import json; results={};\n"
        for dep, desc in required_deps:
            check_code += f"try:\n    import {dep}; results['{dep}']=True\nexcept:\n    results['{dep}']=False\n"
        check_code += "print(json.dumps(results))"
        try:
            process = hidden_popen(
                [venv_python, "-c", check_code],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=60)
            if process.returncode == 0 and stdout.strip():
                import json
                results = json.loads(stdout.strip())
                for dep, desc in required_deps:
                    if results.get(dep, False):
                        self._log(f"✓ {dep} ({desc}) 已安装")
                    else:
                        self._log(f"✗ {dep} ({desc}) 未安装", "#FF9800")
                        all_ok = False
            else:
                for dep, desc in required_deps:
                    self._log(f"✗ {dep} ({desc}) 检测失败", "#FF9800")
                    all_ok = False
        except Exception as e:
            self._log(f"✗ 依赖检测失败: {e}", "#FF9800")
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
                self._log("[信息] 正在自动修复: 降级 transformers...", "#FF9800")
                try:
                    fix_cmd = [venv_python, "-m", "pip", "install", "transformers>=4.51.0,<5.0", "--quiet"]
                    fix_process = hidden_popen(
                        fix_cmd,
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    fix_process.communicate(timeout=120)
                    if fix_process.returncode == 0:
                        self._log("✓ transformers 已降级到兼容版本", "#4CAF50")
                    else:
                        self._log("[警告] transformers 降级失败", "#FF9800")
                except Exception as e:
                    self._log(f"[警告] transformers 降级失败: {e}", "#FF9800")
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
            venv_python = self._find_venv_python()
            missing_deps = self._quick_check_dependencies(venv_python)
            if missing_deps:
                self._log(f"[警告] 检测到关键依赖缺失: {', '.join(missing_deps)}", "#FF9800")
                scripts_dir = os.path.join(self.base_dir, "scripts")
                self._install_missing_dependencies(venv_python, scripts_dir)
            else:
                self._log("✓ 关键依赖已完整安装")
            self._verify_dependencies(venv_python)
            
            # 6. 检查 Web 前端（可选）
            self._log("6. 检查 Web 前端（可选）...")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            if os.path.exists(ace_step_ui_path):
                git_dir = os.path.join(ace_step_ui_path, ".git")
                if os.path.exists(git_dir):
                    self._log("✓ ace-step-ui git 子模块已初始化")
                else:
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    if os.path.exists(node_modules_path):
                        self._log("✓ ace-step-ui node_modules 已存在")
                package_json_path = os.path.join(ace_step_ui_path, "package.json")
                if os.path.exists(package_json_path):
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    if os.path.exists(node_modules_path):
                        self._log("✓ Web 前端依赖已安装")
                    else:
                        self._log("○ Web 前端依赖未安装（可选，不影响核心功能）")
            else:
                self._log("○ ace-step-ui 未检出（可选 Web 前端，不影响核心功能）")
            
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
            self.deploy_step_signal.emit("nodejs", "running")
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
                python_ok, _ = self._ensure_uv_python_healthy(uv_path, scripts_dir)
                if not python_ok:
                    self._log("[错误] Python 环境不可用，无法创建虚拟环境", "#F44336")
                    return
                
                self._log("[信息] 虚拟环境不存在，正在创建...")
                try:
                    process = hidden_popen(
                        [uv_path, "venv", "-p", "3.12", "--seed"],
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
                venv_python = self._find_venv_python()
                
                missing_deps = self._quick_check_dependencies(venv_python)
                
                if not missing_deps:
                    self._log("✓ 关键依赖已完整安装，跳过依赖安装步骤")
                else:
                    self._log(f"[信息] 检测到依赖缺失: {', '.join(missing_deps)}，开始安装...")
                    self._install_missing_dependencies(venv_python, scripts_dir)
            except Exception as e:
                self._log(f"[警告] 安装项目依赖失败: {e}", "#FF9800")
            
            # 验证关键依赖是否安装
            self._verify_dependencies(venv_python)
            
            # 6. 检查 Web 前端（可选）
            self._log("6. 检查 Web 前端（可选）...")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            
            if not os.path.exists(ace_step_ui_path):
                self._log("○ ace-step-ui 未检出，跳过（可选 Web 前端）")
            else:
                git_dir = os.path.join(ace_step_ui_path, ".git")
                if not os.path.exists(git_dir):
                    self._log("[信息] ace-step-ui git子模块未初始化，尝试初始化...")
                    try:
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
                            self._log("[警告] git子模块初始化超时，跳过继续", "#FF9800")
                    except Exception as e:
                        self._log(f"[警告] 初始化git子模块失败: {e}", "#FF9800")
                else:
                    self._log("✓ git子模块已初始化")
            
            # 7. 安装/修复前端依赖（可选）
            self._log("7. 安装/修复前端依赖（可选）...")
            if os.path.exists(ace_step_ui_path):
                package_json_path = os.path.join(ace_step_ui_path, "package.json")
                if os.path.exists(package_json_path):
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    server_node_modules_path = os.path.join(ace_step_ui_path, "server", "node_modules")
                    
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
                            venv_python = self._find_venv_python()
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
                    self._log("○ package.json 不存在，跳过（可选 Web 前端）")
            else:
                self._log("○ ace-step-ui 目录不存在，跳过（可选 Web 前端）")
            
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
    
    def _find_venv_python(self):
        """统一查找虚拟环境 Python 路径，兼容多种目录结构"""
        candidates = [
            os.path.join(self.base_dir, "scripts", ".venv", "Scripts", "python.exe"),
            os.path.join(self.base_dir, ".venv", "Scripts", "python.exe"),
            os.path.join(self.base_dir, "app", "scripts", ".venv", "Scripts", "python.exe"),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return os.path.join(self.base_dir, "scripts", ".venv", "Scripts", "python.exe")
    
    def _check_deploy_env(self):
        """检测部署环境各步骤状态"""
        checks = {}
        
        try:
            ps_ok = False
            try:
                process = hidden_popen(
                    ["powershell.exe", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                stdout, stderr = process.communicate(timeout=10)
                if process.returncode == 0 and stdout.strip():
                    ps_ok = True
            except:
                pass
            if not ps_ok:
                ps_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
                if os.path.exists(ps_path):
                    ps_ok = True
            if not ps_ok:
                try:
                    process = hidden_popen(
                        ["where", "powershell"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    stdout, stderr = process.communicate(timeout=5)
                    if process.returncode == 0 and stdout.strip():
                        ps_ok = True
                except:
                    pass
            checks["powershell"] = ps_ok
        except:
            checks["powershell"] = False
        
        try:
            node_ok = False
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
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    stdout, stderr = process.communicate(timeout=5)
                    if process.returncode == 0 and stdout.strip():
                        node_ok = True
                        break
                except:
                    continue
            checks["nodejs"] = node_ok
        except:
            checks["nodejs"] = False
        
        try:
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            checks["uv"] = os.path.exists(uv_path)
        except:
            checks["uv"] = False
        
        try:
            venv_python = self._find_venv_python()
            checks["venv"] = os.path.exists(venv_python)
        except:
            checks["venv"] = False
        
        try:
            venv_python = self._find_venv_python()
            if os.path.exists(venv_python):
                REQUIRED_DEPS = {
                    "loguru": "loguru",
                    "psutil": "psutil",
                    "torch": "torch>=2.9.0",
                    "torchaudio": "torchaudio>=2.9.0",
                    "transformers": "transformers>=4.51.0,<5.0",
                    "diffusers": "diffusers",
                    "gradio": "gradio",
                    "peft": "peft",
                    "lycoris": "lycoris-lora",
                    "fastapi": "fastapi",
                    "uvicorn": "uvicorn",
                    "accelerate": "accelerate",
                    "scipy": "scipy",
                    "soundfile": "soundfile",
                    "einops": "einops",
                    "matplotlib": "matplotlib",
                    "diskcache": "diskcache",
                    "numba": "numba",
                    "lightning": "lightning",
                    "tensorboard": "tensorboard",
                    "modelscope": "modelscope",
                    "huggingface_hub": "huggingface_hub",
                    "safetensors": "safetensors",
                }
                check_code = "import json; results={};\n"
                for dep_module in REQUIRED_DEPS.keys():
                    check_code += f"try:\n    import {dep_module}; results['{dep_module}']=True\nexcept:\n    results['{dep_module}']=False\n"
                check_code += "print(json.dumps(results))"
                all_ok = True
                failed_deps = []
                try:
                    process = hidden_popen(
                        [venv_python, "-c", check_code],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    stdout, stderr = process.communicate(timeout=60)
                    if process.returncode == 0 and stdout.strip():
                        import json
                        results = json.loads(stdout.strip())
                        failed_deps = [dep for dep, ok in results.items() if not ok]
                        all_ok = len(failed_deps) == 0
                    else:
                        all_ok = False
                        failed_deps = list(REQUIRED_DEPS.keys())
                except:
                    all_ok = False
                    failed_deps = list(REQUIRED_DEPS.keys())
                if failed_deps:
                    self._failed_deps_cache = failed_deps
                else:
                    self._failed_deps_cache = []
                checks["python_deps"] = all_ok
            else:
                checks["python_deps"] = False
        except:
            checks["python_deps"] = False
        
        try:
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            # ace-step-ui 是可选 Web 前端，不存在不影响核心功能
            if os.path.exists(ace_step_ui_path):
                package_json_path = os.path.join(ace_step_ui_path, "package.json")
                node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                checks["frontend_deps"] = os.path.exists(package_json_path) and os.path.exists(node_modules_path)
            else:
                checks["frontend_deps"] = True  # 可选组件，不存在视为正常
        except:
            checks["frontend_deps"] = True
        
        try:
            scripts = [
                "2、run_gradio.ps1",
                "3、run_server.ps1",
                "4、run_npmgui.ps1"
            ]
            scripts_ok = True
            for script in scripts:
                script_path = os.path.join(self.base_dir, "scripts", script)
                if not os.path.exists(script_path):
                    scripts_ok = False
                    break
            checks["scripts"] = scripts_ok
        except:
            checks["scripts"] = False
        
        return checks
    
    def _refresh_deploy_env_status(self):
        """刷新部署维护页面的环境状态"""
        if not hasattr(self, '_env_labels') or not self._env_labels:
            return
        
        if self.is_starting:
            return
        
        self._log("正在检测环境状态...", "#4CAF50")
        
        def _do_check():
            checks = self._check_deploy_env()
            
            gpu_detected = False
            try:
                venv_python = self._find_venv_python()
                if os.path.exists(venv_python):
                    result = hidden_run(
                        [venv_python, "-c",
                         "import torch; name=torch.cuda.get_device_name(0) if torch.cuda.is_available() else ''; mem=torch.cuda.get_device_properties(0).total_mem//1024//1024//1024 if torch.cuda.is_available() else 0; print(name+'|'+str(mem)+'GB') if name else print('NO_CUDA')"
                         ],
                        capture_output=True, text=True, timeout=20
                    )
                    output = result.stdout.strip() if result.returncode == 0 else ""
                    if output and output != "NO_CUDA" and "|" in output:
                        checks["gpu"] = output
                        gpu_detected = True
            except:
                pass
            
            if not gpu_detected:
                try:
                    result = hidden_run(
                        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        line = result.stdout.strip().split("\n")[0]
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 2:
                            checks["gpu"] = f"{parts[0]} | {parts[1]}GB"
                            gpu_detected = True
                except:
                    pass
            
            self.deploy_step_signal.emit("__refresh__", "")
            for key, value in checks.items():
                self.deploy_step_signal.emit(key, "done" if value else "fail")
                if key == "gpu" and isinstance(value, str):
                    self.deploy_step_signal.emit("gpu_info", value)
            
            self._log("✓ 环境状态检测完成", "#4CAF50")
        
        t = threading.Thread(target=_do_check, daemon=True)
        t.start()
    
    def _update_deploy_step(self, key: str, status: str):
        """更新环境检测标签状态"""
        if key == "__refresh__":
            return
        
        if key == "gpu_info":
            if hasattr(self, '_env_labels') and 'gpu' in self._env_labels:
                self._env_labels["gpu"].setText(f"✅ {status}")
                self._env_labels["gpu"].setStyleSheet("font-size: 10px; color: #66BB6A; background: transparent;")
            return
        
        if not hasattr(self, '_env_labels') or key not in self._env_labels:
            return
        
        lbl = self._env_labels[key]
        
        status_map = {
            "done": ("✅ 已就绪", "#66BB6A"),
            "fail": ("❌ 未就绪", "#EF5350"),
            "running": ("⏳ 检测中...", "#888888"),
            "partial": ("⚠️ 部分损坏", "#FFA726"),
        }
        
        text, color = status_map.get(status, ("❓ 未知", "#888888"))
        
        if key == "python_deps" and status == "fail" and hasattr(self, '_failed_deps_cache') and self._failed_deps_cache:
            failed = ", ".join(self._failed_deps_cache)
            text = f"❌ 缺失: {failed}"
            lbl.setText(text)
            lbl.setToolTip(f"以下 Python 依赖未安装:\n{chr(10).join(self._failed_deps_cache)}")
        else:
            lbl.setText(text)
        
        lbl.setStyleSheet(f"font-size: 10px; color: {color}; background: transparent;")
    
    def _refresh_deps_list(self):
        """刷新依赖版本列表"""
        if not hasattr(self, '_deps_grid'):
            return
        
        while self._deps_grid.count():
            item = self._deps_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
        
        venv_python = self._find_venv_python()
        if not os.path.exists(venv_python):
            lbl = QLabel("❌ Python 未就绪")
            lbl.setStyleSheet("font-size: 10px; color: #EF5350; background: transparent;")
            self._deps_grid.addWidget(lbl, 0, 0)
            return
        
        try:
            dep_names = [re.split(r'[><=!~\[]', d)[0].strip() for d in ACE_PIP_DEPS]
            lock_items = list(ACE_PIP_VERSION_LOCKS.items())
            lock_names = [name for name, _ in lock_items]
            check_names = list(dict.fromkeys(lock_names + dep_names))
            
            check_script = "import importlib.metadata\n"
            check_script += "deps = " + str(check_names) + "\n"
            check_script += "locks = " + str({k: v for k, v in lock_items}) + "\n"
            check_script += """
for d in deps:
    try:
        v = importlib.metadata.version(d)
        if d in locks:
            print(f"LOCK|{d}|{v}|{locks[d]}")
        else:
            print(f"OK|{d}|{v}|")
    except:
        print(f"MISS|{d}|0|")
"""
            result = hidden_run(
                [venv_python, "-c", check_script],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return
            
            row = 0
            import re as _re
            for line in result.stdout.strip().split('\n'):
                if '|' not in line:
                    continue
                parts = line.split('|')
                if len(parts) < 3:
                    continue
                status, name, ver = parts[0], parts[1], parts[2]
                lock_info = parts[3] if len(parts) > 3 else ""
                col = row % 2
                display_row = row // 2
                cell = QHBoxLayout()
                cell.setSpacing(3)
                short = (name.replace("huggingface_hub", "hf_hub")
                         .replace("lycoris-lora", "lycoris"))
                name_lbl = QLabel(short)
                name_lbl.setFixedWidth(82)
                if status == "OK":
                    name_lbl.setStyleSheet("font-size: 9px; color: #888888; background: transparent;")
                    ver_lbl = QLabel(f"✅ {ver}")
                    ver_lbl.setStyleSheet("font-size: 9px; color: #66BB6A; background: transparent;")
                elif status == "LOCK":
                    name_lbl.setStyleSheet("font-size: 9px; color: #888888; background: transparent;")
                    ver_lbl = QLabel(f"✅ {ver} (需{lock_info})")
                    ver_lbl.setStyleSheet("font-size: 9px; color: #66BB6A; background: transparent;")
                elif status == "BAD":
                    name_lbl.setStyleSheet("font-size: 9px; color: #FF8A80; background: transparent;")
                    ver_lbl = QLabel(f"⚠️ {ver} (需{lock_info})")
                    ver_lbl.setStyleSheet("font-size: 9px; color: #FFA726; background: transparent;")
                else:
                    name_lbl.setStyleSheet("font-size: 9px; color: #EF5350; background: transparent;")
                    ver_lbl = QLabel("❌ 未安装")
                    ver_lbl.setStyleSheet("font-size: 9px; color: #EF5350; background: transparent;")
                cell.addWidget(name_lbl)
                cell.addWidget(ver_lbl, 1)
                self._deps_grid.addLayout(cell, display_row, col)
                row += 1
        except Exception:
            pass

    def _on_install_single_step(self, component: str):
        """安装单个步骤组件"""
        if self.is_starting:
            self._log("正在运行中，请稍候...", "#616161")
            return
        
        self.is_starting = True
        self.deploy_step_signal.emit(component, "running")
        
        if hasattr(self, 'btn_one_click_deploy'):
            self.btn_one_click_deploy.setEnabled(False)
        if hasattr(self, 'btn_bottom_restart'):
            self.btn_bottom_restart.setEnabled(False)
        if hasattr(self, 'btn_start_qinglong'):
            self.btn_start_qinglong.setEnabled(False)
        if hasattr(self, 'btn_bottom_stop'):
            self.btn_bottom_stop.setEnabled(False)
        
        def _install():
            try:
                success = False
                
                if component == "powershell":
                    self._log("[信息] PowerShell 为系统组件，无法自动安装", "#FF9800")
                    self._log("[建议] 请通过 Windows 设置安装 PowerShell", "#FF9800")
                    checks = self._check_deploy_env()
                    success = checks.get("powershell", False)
                
                elif component == "nodejs":
                    self._log("正在安装 Node.js...")
                    success = self._install_nodejs()
                
                elif component == "uv":
                    self._log("正在安装 uv 包管理器...")
                    success = self._install_uv()
                
                elif component == "venv":
                    self._log("正在创建 Python 虚拟环境...")
                    success = self._create_venv()
                
                elif component == "python_deps":
                    self._log("正在安装 Python 依赖包...")
                    success = self._install_python_deps()
                
                elif component == "frontend_deps":
                    self._log("正在安装前端 npm 依赖...")
                    success = self._install_frontend_deps()
                
                elif component == "scripts":
                    self._log("正在检查启动脚本...")
                    self._ensure_scripts_available()
                    checks = self._check_deploy_env()
                    success = checks.get("scripts", False)
                
                if success:
                    self.deploy_step_signal.emit(component, "done")
                    self._log(f"✓ {self.deploy_steps[component]['label']} 安装完成", "#4CAF50")
                else:
                    self.deploy_step_signal.emit(component, "fail")
                    self._log(f"✗ {self.deploy_steps[component]['label']} 安装失败", "#F44336")
            
            except Exception as e:
                self.deploy_step_signal.emit(component, "fail")
                self._log(f"[错误] 安装 {component} 失败: {e}", "#F44336")
            finally:
                self.is_starting = False
                if hasattr(self, 'btn_one_click_deploy'):
                    self.btn_one_click_deploy.setEnabled(True)
                self._update_bottom_bar()
        
        t = threading.Thread(target=_install, daemon=True)
        t.start()
    
    def _install_nodejs(self):
        """安装 Node.js"""
        try:
            portable_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
            if os.path.exists(os.path.join(portable_node24_dir, "node.exe")):
                return True
            
            tools_dir = os.path.join(self.base_dir, "tools")
            os.makedirs(tools_dir, exist_ok=True)
            node24_zip = os.path.join(tools_dir, "node-v24.14.1-win-x64.zip")
            node24_url = "https://nodejs.org/dist/v24.14.1/node-v24.14.1-win-x64.zip"
            
            import urllib.request
            self._log(f"[信息] 下载 Node.js 24 便携版...")
            
            def _progress(block_num, block_size, total_size):
                pct = min(block_num * block_size * 100 / total_size, 100) if total_size > 0 else 0
                if block_num % 500 == 0:
                    self._log(f"[下载] Node.js 24: {pct:.1f}%")
            
            urllib.request.urlretrieve(node24_url, node24_zip, _progress)
            self._log("✓ Node.js 24 下载完成", "#4CAF50")
            
            import zipfile
            with zipfile.ZipFile(node24_zip, 'r') as zf:
                zf.extractall(tools_dir)
            self._log("✓ Node.js 便携版解压完成", "#4CAF50")
            
            try:
                os.remove(node24_zip)
            except:
                pass
            
            return os.path.exists(os.path.join(portable_node24_dir, "node.exe"))
        except Exception as e:
            self._log(f"[错误] 安装 Node.js 失败: {e}", "#F44336")
            return False
    
    def _install_uv(self):
        """安装 uv 包管理器"""
        try:
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            if os.path.exists(uv_path):
                return True
            
            install_script = os.path.join(self.base_dir, "scripts", "1、install-uv-qinglong.ps1")
            if not os.path.exists(install_script):
                self._log("[错误] uv 安装脚本不存在", "#F44336")
                return False
            
            result = hidden_run(
                ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_script],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return os.path.exists(uv_path)
        except Exception as e:
            self._log(f"[错误] 安装 uv 失败: {e}", "#F44336")
            return False
    
    def _create_venv(self):
        """创建 Python 虚拟环境"""
        try:
            venv_path = os.path.join(self.base_dir, "scripts", ".venv")
            if os.path.exists(venv_path):
                return True
            
            install_script = os.path.join(self.base_dir, "scripts", "install-env.ps1")
            if os.path.exists(install_script):
                result = hidden_run(
                    ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_script],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=1800
                )
                return os.path.exists(venv_path)
            
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            if os.path.exists(uv_path):
                scripts_dir = os.path.join(self.base_dir, "scripts")
                os.makedirs(scripts_dir, exist_ok=True)
                process = hidden_popen(
                    [uv_path, "venv", os.path.join(scripts_dir, ".venv")],
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                process.communicate(timeout=120)
                return os.path.exists(venv_path)
            
            self._log("[错误] 无法创建虚拟环境，缺少安装脚本和 uv", "#F44336")
            return False
        except Exception as e:
            self._log(f"[错误] 创建虚拟环境失败: {e}", "#F44336")
            return False
    
    def _install_python_deps(self):
        """安装 Python 依赖包（带版本控制）"""
        try:
            venv_python = self._find_venv_python()
            if not os.path.exists(venv_python):
                self._log("[错误] Python 虚拟环境不存在，请先创建虚拟环境", "#F44336")
                return False
            
            install_script = os.path.join(self.base_dir, "scripts", "install-env.ps1")
            if os.path.exists(install_script):
                self._log("[信息] 使用安装脚本安装依赖（含版本控制）...")
                result = hidden_run(
                    ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", install_script],
                    cwd=os.path.join(self.base_dir, "scripts"),
                    capture_output=True,
                    text=True,
                    timeout=1800
                )
                return result.returncode == 0
            
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            if os.path.exists(uv_path):
                self._log("[信息] 使用 uv 安装依赖（带版本约束）...")
                
                self._log("[信息] 安装基础依赖...")
                base_deps = ["wheel_stub", "psutil", "hatchling", "editables"]
                self._log("[信息] 清空 uv 缓存以确保强制重新下载...")
                try:
                    subprocess.run([uv_path, "cache", "clean"], capture_output=True, timeout=30)
                except:
                    pass

                reinstall_flags = []
                for dep in base_deps:
                    pkg = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
                    reinstall_flags.extend(["--reinstall-package", pkg])
                process = hidden_popen(
                    [uv_path, "pip", "install", "--python", venv_python, "--refresh", "--upgrade"] + reinstall_flags + base_deps,
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                process.communicate(timeout=300)
                
                self._log("[信息] 安装 PyTorch 2.9.0 + torchaudio 2.9.0 (CUDA 12.8)...")
                pytorch_deps = [
                    "torch>=2.9.0,<3.0",
                    "torchaudio>=2.9.0,<3.0",
                ]
                env = os.environ.copy()
                env["UV_INDEX_URL"] = "https://pypi.tuna.tsinghua.edu.cn/simple/"
                env["UV_EXTRA_INDEX_URL"] = "https://download.pytorch.org/whl/cu128"
                reinstall_flags = []
                for dep in pytorch_deps:
                    pkg = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
                    reinstall_flags.extend(["--reinstall-package", pkg])
                process = hidden_popen(
                    [uv_path, "pip", "install", "--python", venv_python, "--refresh"] + reinstall_flags + pytorch_deps,
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    env=env
                )
                process.communicate(timeout=600)
                if process.returncode != 0:
                    self._log("[警告] PyTorch 安装可能失败，尝试不带版本约束...", "#FF9800")
                    process = hidden_popen(
                        [uv_path, "pip", "install", "--python", venv_python, "--refresh", "torch", "torchaudio"],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                        env=env
                    )
                    process.communicate(timeout=600)
                
                self._log("[信息] 安装项目核心依赖...")
                project_deps = [
                    "transformers>=4.51.0,<5.0",
                    "diffusers",
                    "gradio",
                    "matplotlib",
                    "scipy",
                    "soundfile",
                    "loguru",
                    "einops",
                    "accelerate",
                    "fastapi",
                    "diskcache",
                    "uvicorn",
                    "numba",
                    "peft",
                    "lycoris-lora",
                    "lightning",
                    "tensorboard",
                    "modelscope",
                    "huggingface_hub",
                    "safetensors",
                ]
                reinstall_flags = []
                for dep in project_deps:
                    pkg = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
                    reinstall_flags.extend(["--reinstall-package", pkg])
                process = hidden_popen(
                    [uv_path, "pip", "install", "--python", venv_python, "--refresh"] + reinstall_flags + project_deps,
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    env=env
                )
                process.communicate(timeout=600)
                
                flash_attn_wheel = os.path.join(self.base_dir, "scripts", "flash_attn-2.8.3+cu128torch2.9.0cxx11abiTRUE-cp312-cp312-win_amd64.whl")
                if os.path.exists(flash_attn_wheel):
                    self._log("[信息] 安装 flash_attn 加速库...")
                    process = hidden_popen(
                        [uv_path, "pip", "install", "--python", venv_python, "--reinstall-package", "flash-attn", "--refresh", flash_attn_wheel],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                        env=env
                    )
                    process.communicate(timeout=300)
                    if process.returncode == 0:
                        self._log("✓ flash_attn 安装完成", "#4CAF50")
                    else:
                        self._log("[警告] flash_attn 安装失败（不影响核心功能）", "#FF9800")
                
                return True
            
            self._log("[错误] 无法安装 Python 依赖，缺少安装脚本和 uv", "#F44336")
            return False
        except Exception as e:
            self._log(f"[错误] 安装 Python 依赖失败: {e}", "#F44336")
            return False
    
    def _install_frontend_deps(self):
        """安装前端 npm 依赖"""
        try:
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
            
            if os.path.exists(node_modules_path):
                return True
            
            portable_node24_dir = os.path.join(self.base_dir, "tools", "node-v24.14.1-win-x64", "node-v24.14.1-win-x64")
            portable_node22_dir = os.path.join(self.base_dir, "tools", "node-v22.22.2-win-x64", "node-v22.22.2-win-x64")
            
            npm_path = None
            for node_dir in [portable_node24_dir, portable_node22_dir]:
                candidate = os.path.join(node_dir, "npm.cmd")
                if os.path.exists(candidate):
                    npm_path = candidate
                    break
            
            if not npm_path:
                npm_path = "npm"
            
            self._log(f"[信息] 正在运行 npm install...")
            process = hidden_popen(
                [npm_path, "install"],
                cwd=ace_step_ui_path,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            process.communicate(timeout=600)
            
            return os.path.exists(node_modules_path)
        except Exception as e:
            self._log(f"[错误] 安装前端依赖失败: {e}", "#F44336")
            return False
    
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
        self._update_bottom_bar()
        
        if hasattr(self, 'btn_one_click_deploy'):
            self.btn_one_click_deploy.setEnabled(False)
        
        self.deploy_thread = threading.Thread(target=self._deploy_maintenance_thread)
        self.deploy_thread.daemon = True
        self.deploy_thread.start()
    
    def _deploy_maintenance_thread(self):
        """部署维护线程函数"""
        self._log("========================================")
        self._log("开始部署维护...")
        self._log("========================================")
        self._log(f"[调试] 当前工作目录: {self.base_dir}")
        
        self._ensure_scripts_available()
        
        try:
            # 1. 首先检查PowerShell
            self._log("1. 检查 PowerShell...")
            self.deploy_step_signal.emit("powershell", "running")
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
                    self.deploy_step_signal.emit("powershell", "fail")
                    return
                else:
                    self.deploy_step_signal.emit("powershell", "done")
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
                self.deploy_step_signal.emit("nodejs", "fail")
                return
            
            if node_available:
                self.deploy_step_signal.emit("nodejs", "done")
            
            # 3. 检查环境是否已安装
            self._log("3. 检查环境安装状态...")
            
            uv_path = os.path.expanduser("~/.local/bin/uv.exe")
            venv_path = os.path.join(self.base_dir, "scripts", ".venv")
            ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
            
            self.deploy_step_signal.emit("uv", "running")
            if os.path.exists(uv_path):
                self.deploy_step_signal.emit("uv", "done")
            else:
                self.deploy_step_signal.emit("uv", "fail")
            
            self.deploy_step_signal.emit("venv", "running")
            if os.path.exists(venv_path):
                self.deploy_step_signal.emit("venv", "done")
            else:
                self.deploy_step_signal.emit("venv", "fail")
            
            environment_installed = bool(os.path.exists(uv_path) and os.path.exists(venv_path))
            if environment_installed:
                ace_step_ui_path = os.path.join(self.base_dir, "ace-step-ui")
                if os.path.exists(ace_step_ui_path):
                    node_modules_path = os.path.join(ace_step_ui_path, "node_modules")
                    if os.path.exists(node_modules_path):
                        self._log("✓ 环境已完全安装（含 Web 前端）")
                    else:
                        self._log("✓ 核心环境已就绪（Web 前端可选，未安装 node_modules）")
                else:
                    self._log("✓ 核心环境已就绪（Web 前端可选，未检出 ace-step-ui）")
            
            if not environment_installed:
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
                            self.deploy_step_signal.emit("python_deps", "done")
                            self.deploy_step_signal.emit("frontend_deps", "done")
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
            
            # 6. 安装 flash_attn 加速库（如果有 wheel 文件）
            venv_python = self._find_venv_python()
            flash_attn_wheel = os.path.join(self.base_dir, "scripts", "flash_attn-2.8.3+cu128torch2.9.0cxx11abiTRUE-cp312-cp312-win_amd64.whl")
            if os.path.exists(venv_python) and os.path.exists(flash_attn_wheel):
                try:
                    process = hidden_popen(
                        [venv_python, "-c", "import flash_attn; print(flash_attn.__version__)"],
                        cwd=self.base_dir,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    stdout, _ = process.communicate(timeout=10)
                    if process.returncode == 0:
                        self._log(f"✓ flash_attn 已安装: v{stdout.strip()}")
                    else:
                        self._log("[信息] flash_attn 未安装，正在从本地 wheel 安装...")
                        uv_path = os.path.expanduser("~/.local/bin/uv.exe")
                        if os.path.exists(uv_path):
                            install_process = hidden_popen(
                                [uv_path, "pip", "install", "--python", venv_python, "--reinstall", "--refresh", flash_attn_wheel],
                                cwd=self.base_dir,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                            )
                            install_process.communicate(timeout=300)
                            if install_process.returncode == 0:
                                self._log("✓ flash_attn 加速库安装完成", "#4CAF50")
                            else:
                                self._log("[警告] flash_attn 安装失败（不影响核心功能，将使用 SDPA 回退）", "#FF9800")
                except Exception as e:
                    self._log(f"[警告] flash_attn 检测/安装失败: {e}（不影响核心功能）", "#FF9800")
            
            # 7. 最终检查 - 重新验证所有环境项，确保全绿
            self._log("7. 最终检查（重新验证所有环境项）...")
            
            final_checks = self._check_deploy_env()
            
            all_green = True
            for key, value in final_checks.items():
                if key == "gpu":
                    if isinstance(value, str) and value:
                        self.deploy_step_signal.emit("gpu", "done")
                        self.deploy_step_signal.emit("gpu_info", value)
                    else:
                        all_green = False
                        self.deploy_step_signal.emit("gpu", "fail")
                elif value:
                    self.deploy_step_signal.emit(key, "done")
                else:
                    all_green = False
                    self.deploy_step_signal.emit(key, "fail")
            
            if not all_green:
                self._log("[警告] 部分环境项未通过，尝试自动修复...", "#FF9800")
                
                if not final_checks.get("uv"):
                    self._log("[修复] 重新安装 uv...")
                    self._install_uv()
                
                if not final_checks.get("venv"):
                    self._log("[修复] 重新创建虚拟环境...")
                    self._create_venv()
                
                if not final_checks.get("python_deps"):
                    self._log("[修复] 重新安装 Python 依赖...")
                    venv_python = self._find_venv_python()
                    if os.path.exists(venv_python):
                        self._install_missing_dependencies(venv_python, os.path.join(self.base_dir, "scripts"))
                
                self._log("[信息] 修复完成，重新验证...")
                retry_checks = self._check_deploy_env()
                
                retry_all_green = True
                for key, value in retry_checks.items():
                    if key == "gpu":
                        if isinstance(value, str) and value:
                            self.deploy_step_signal.emit("gpu", "done")
                            self.deploy_step_signal.emit("gpu_info", value)
                        else:
                            retry_all_green = False
                            self.deploy_step_signal.emit("gpu", "fail")
                    elif value:
                        self.deploy_step_signal.emit(key, "done")
                    else:
                        retry_all_green = False
                        self.deploy_step_signal.emit(key, "fail")
                
                if retry_all_green:
                    all_green = True
                    self._log("✅ 修复成功，所有环境项已通过验证", "#4CAF50")
                else:
                    failed_items = [k for k, v in retry_checks.items() if k not in ("gpu", "frontend_deps") and not v]
                    if not (isinstance(retry_checks.get("gpu"), str) and retry_checks.get("gpu")):
                        failed_items.append("gpu")
                    if failed_items:
                        self._log(f"[错误] 以下环境项仍未通过: {', '.join(failed_items)}", "#F44336")
                    else:
                        self._log("⚠ 环境核心项已通过（Web 前端等可选组件未就绪）", "#FF9800")
                        all_green = True
            
            if all_green:
                self._log("")
                self._log("========================================")
                self._log("✅ 部署维护完成！所有环境项已就绪", "#4CAF50")
                self._log("========================================")
            else:
                self._log("")
                self._log("========================================")
                self._log("❌ 部署维护未完全成功，请查看上方日志", "#F44336")
                self._log("========================================")
            
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
                        self._log("  建议：先启动青龙 LoRA 训练器来启动API服务", "#FF9800")
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
        
        self.monitor.pause()
        
        if hasattr(self, 'api_process') and self.api_process:
            try:
                self.api_process.kill()
                self._log("已终止 API 进程")
            except:
                pass
            self.api_process = None
        
        for service_id in SERVICES:
            self._stop_service(service_id, skip_pause=True)
        
        self.monitor.resume()
        
        self._log("")
        self._log("========================================")
        self._log("所有服务已停止")
        self._log("========================================")
    
    def _restart_all_services(self):
        """重启所有服务：停止后启动青龙 LoRA 训练器"""
        self._log("========================================")
        self._log("正在重启所有服务...")
        self._log("========================================")
        
        self._stop_all_services()
        
        self._log("")
        self._log("2 秒后自动启动青龙 LoRA 训练器...")
        
        def delayed_start():
            time.sleep(2)
            self._start_project("qinglong")
        
        threading.Thread(target=delayed_start, daemon=True).start()
    
    def _stop_service(self, service_id: str, skip_pause=False):
        """停止单个服务"""
        service = SERVICES[service_id]
        self._log(f"正在停止 {service['name']}...")
        
        if not skip_pause:
            self.monitor.pause()
        
        if service_id in self.service_processes:
            process = self.service_processes[service_id]
            if process.state() != 0:
                try:
                    process.terminate()
                    self._log(f"✓ {service['name']} 进程已终止")
                except:
                    pass
            del self.service_processes[service_id]
        
        port = service["port"]
        try:
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
                                    ["taskkill", "/F", "/T", "/PID", pid],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    timeout=5
                                )
                                self._log(f"已终止占用端口 {port} 的进程 (PID: {pid})")
                            except:
                                pass
        except:
            pass
        
        if service_id in self.service_cards:
            self.service_cards[service_id].update_status(False)
        
        if not skip_pause:
            self.monitor.resume()
    
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
    
    def _on_port_changed(self, service_id: str, new_port: int):
        old_port = SERVICES[service_id]["port"]
        
        SERVICES[service_id]["port"] = new_port
        SERVICES[service_id]["url"] = SERVICES[service_id]["url"].replace(
            f":{old_port}", f":{new_port}"
        )
        
        project_id = SERVICES[service_id]["project"]
        short_id = service_id.replace(f"{project_id}_", "", 1)
        if project_id in PROJECTS and short_id in PROJECTS[project_id]["services"]:
            PROJECTS[project_id]["services"][short_id]["port"] = new_port
            PROJECTS[project_id]["services"][short_id]["url"] = SERVICES[service_id]["url"]
        
        saved = load_port_config()
        saved[service_id] = new_port
        save_port_config(saved)
        
        if service_id in self.service_cards:
            self.service_cards[service_id].update_port_display()
        
        self._log(f"✓ {SERVICES[service_id]['name']} 端口已修改: {old_port} → {new_port}", "#4CAF50")
        
        was_running = service_id in self.service_cards and self.service_cards[service_id].is_running
        if was_running:
            self._log(f"正在重启 {SERVICES[service_id]['name']} 使新端口生效...", "#FFA726")
            self._restart_service(service_id)
    
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
        """检测本地已安装的浏览器（注册表 + 常见路径 + 便携版扫描）"""
        browsers = {
            "系统默认": "system"
        }

        # 浏览器可执行文件名与显示名称、图标的映射
        browser_registry_map = {
            "chrome.exe": ("Chrome", "🌐"),
            "msedge.exe": ("Edge", "🌊"),
            "firefox.exe": ("Firefox", "🦊"),
            "brave.exe": ("Brave", "🦁"),
            "opera.exe": ("Opera", "🔴"),
            "launcher.exe": ("Opera", "🔴"),  # Opera launcher
            "vivaldi.exe": ("Vivaldi", "🌈"),
            "centbrowser.exe": ("Cent Browser", "🌀"),
            "360chrome.exe": ("360 浏览器", "🛡"),
            "360se.exe": ("360 安全浏览器", "🛡"),
            "qqbrowser.exe": ("QQ 浏览器", "🐧"),
            "ucweb.exe": ("UC 浏览器", "🌎"),
            "maxthon.exe": ("傲游浏览器", "🛥"),
            "sogouexplorer.exe": ("搜狗浏览器", "🐶"),
            "liebao.exe": ("猎豹浏览器", "🐆"),
        }

        # 1. 通过注册表 App Paths 查找
        try:
            app_paths_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, app_paths_key) as root_key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(root_key, i)
                        i += 1
                        exe_name = subkey_name.lower()
                        if exe_name not in browser_registry_map:
                            continue
                        with winreg.OpenKey(root_key, subkey_name) as sub_key:
                            try:
                                path, _ = winreg.QueryValueEx(sub_key, None)
                                if path and os.path.exists(path):
                                    display_name, icon = browser_registry_map[exe_name]
                                    if exe_name == "launcher.exe":
                                        display_name = "Opera"
                                    unique_name = f"{icon} {display_name}"
                                    base_name = unique_name
                                    counter = 2
                                    while unique_name in browsers:
                                        unique_name = f"{base_name} ({counter})"
                                        counter += 1
                                    browsers[unique_name] = path
                            except OSError:
                                continue
                    except OSError:
                        break
        except Exception:
            pass

        # 2. 补充常见安装路径（覆盖未写入注册表或便携版）
        common_paths = [
            # Chrome
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            # Edge
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            # Firefox
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            # Brave
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            # Opera
            r"C:\Program Files\Opera\launcher.exe",
            r"C:\Program Files (x86)\Opera\launcher.exe",
            r"C:\Program Files\Opera\opera.exe",
            r"C:\Program Files (x86)\Opera\opera.exe",
            # Vivaldi
            r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
            r"C:\Program Files (x86)\Vivaldi\Application\vivaldi.exe",
            # Cent Browser
            r"C:\Program Files\CentBrowser\centbrowser.exe",
            r"C:\Program Files (x86)\CentBrowser\centbrowser.exe",
            # 360 Chrome
            r"C:\Program Files (x86)\360\360Chrome\Chrome\Application\360chrome.exe",
            r"C:\Program Files\360\360Chrome\Chrome\Application\360chrome.exe",
            # 360 Safe Browser
            r"C:\Program Files (x86)\360\360se6\360se.exe",
            r"C:\Program Files\360\360se6\360se.exe",
            # QQ Browser
            r"C:\Program Files (x86)\Tencent\QQBrowser\QQBrowser.exe",
            r"C:\Program Files\Tencent\QQBrowser\QQBrowser.exe",
            r"C:\Program Files (x86)\Tencent\QQBrowser\qqbrowser.exe",
            r"C:\Program Files\Tencent\QQBrowser\qqbrowser.exe",
            # UC Browser
            r"C:\Program Files (x86)\UCBrowser\Application\UCWeb.exe",
            r"C:\Program Files\UCBrowser\Application\UCWeb.exe",
            # Maxthon
            r"C:\Program Files (x86)\Maxthon\Maxthon.exe",
            r"C:\Program Files\Maxthon\Maxthon.exe",
            # Sogou
            r"C:\Program Files (x86)\SogouExplorer\SogouExplorer.exe",
            r"C:\Program Files\SogouExplorer\SogouExplorer.exe",
            # Liebao
            r"C:\Program Files (x86)\liebao\liebao.exe",
            r"C:\Program Files\liebao\liebao.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                exe_name = os.path.basename(path).lower()
                if exe_name in browser_registry_map:
                    display_name, icon = browser_registry_map[exe_name]
                    unique_name = f"{icon} {display_name}"
                    base_name = unique_name
                    counter = 2
                    while unique_name in browsers:
                        unique_name = f"{base_name} ({counter})"
                        counter += 1
                    browsers[unique_name] = path

        # 3. 在常用父目录下扫描 portable 版本
        try:
            for drive in ["C:", "D:", "E:", "F:", "G:"]:
                if not os.path.exists(drive):
                    continue
                for tools_dir in ["Tools", "Software", "Browser", "App", "Programs"]:
                    base = os.path.join(drive, tools_dir)
                    if not os.path.isdir(base):
                        continue
                    for root, dirs, files in os.walk(base):
                        depth = root[len(base):].count(os.sep)
                        if depth > 2:
                            del dirs[:]
                            continue
                        for file in files:
                            file_lower = file.lower()
                            if file_lower in browser_registry_map:
                                full_path = os.path.join(root, file)
                                display_name, icon = browser_registry_map[file_lower]
                                unique_name = f"{icon} {display_name} (便携)"
                                base_name = unique_name
                                counter = 2
                                while unique_name in browsers:
                                    unique_name = f"{base_name} ({counter})"
                                    counter += 1
                                browsers[unique_name] = full_path
        except Exception:
            pass

        return browsers
    
    def _on_browser_changed(self, index):
        """处理浏览器选择变化"""
        selected_browser = self.browser_combo.itemText(index)
        selected_data = self.browser_combo.itemData(index)
        
        # 检查是否选择了自定义浏览器
        is_custom = selected_data == "custom" or selected_browser == "自定义浏览器"
        
        # 显示/隐藏自定义设置
        self.browser_path_edit.setReadOnly(not is_custom)
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
        
        # 更新路径显示
        self._update_browser_path_display()
    
    def _update_browser_path_display(self):
        """根据当前浏览器选择更新路径显示"""
        if self.selected_browser == "custom" or self.selected_browser == "自定义浏览器":
            self.browser_path_edit.setText(self.custom_browser_path)
            self.browser_path_edit.setPlaceholderText("粘贴或输入浏览器路径...")
        elif self.selected_browser == "系统默认" or self.selected_browser == "system":
            self.browser_path_edit.setText("")
            self.browser_path_edit.setPlaceholderText("使用系统默认浏览器")
        else:
            path = self.browsers.get(self.selected_browser, "")
            self.browser_path_edit.setText(path)
            self.browser_path_edit.setPlaceholderText("选择浏览器后显示路径...")
    
    def _on_custom_browser_path_changed(self, path):
        """处理自定义浏览器路径变化"""
        self.custom_browser_path = path
        self.config.set("browser.custom_path", path)
        if path and os.path.exists(path):
            self.selected_browser = "custom"
            self.config.set("browser.default", "custom")
            self._log(f"已设置自定义浏览器: {path}")
        self._update_browser_path_display()
    
    def _open_url_in_browser(self, url: str):
        """使用选择的浏览器打开URL"""
        if (self.selected_browser == "custom" or self.selected_browser == "自定义浏览器") and self.custom_browser_path and os.path.exists(self.custom_browser_path):
            try:
                hidden_popen([self.custom_browser_path, url])
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
                        hidden_popen([browser_path, url])
                        self._log(f"使用 {selected_browser} 打开: {url}")
                    except Exception as e:
                        self._log(f"打开浏览器失败: {e}", "#F44336")
                        import webbrowser
                        webbrowser.open(url)
                else:
                    import webbrowser
                    webbrowser.open(url)
    
    def _show_help_dialog(self):
        """显示使用说明对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("使用说明")
        dialog.setMinimumSize(650, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1A1A1A;
            }
            QTextEdit {
                background-color: #252525;
                color: #F0F0F0;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
            }
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: 1px solid #1976D2;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>云集智能音乐创意台 - 使用说明</h2>
        
        <h3>快速入门</h3>
        <ul>
            <li><b>启动服务</b>：点击底部"🎵 启动音乐创意台"按钮，按顺序启动 API 服务、青龙后端、青龙前端</li>
            <li><b>打开界面</b>：服务就绪后，点击对应服务卡片的"打开"按钮在浏览器中访问</li>
            <li><b>停止服务</b>：点击底部"⏹ 停止服务"按钮，一键终止所有后台进程</li>
            <li><b>重启服务</b>：点击底部"🔄 重启服务"按钮，停止所有服务后重新启动</li>
        </ul>
        
        <h3>服务管理</h3>
        <ul>
            <li>API 服务（端口 8001）：核心模型推理与 API 接口</li>
            <li>青龙后端（端口 3001）：Express.js 业务后端</li>
            <li>青龙前端（端口 3000）：Vite 用户界面</li>
            <li>每个服务卡片显示运行状态，可单独重启或修改端口</li>
        </ul>
        
        <h3>浏览器设置</h3>
        <ul>
            <li>顶部面板可选择系统默认浏览器或已安装的浏览器</li>
            <li>支持 Chrome、Edge、Firefox、Brave、Opera、Vivaldi 等常见浏览器</li>
            <li>选择"自定义浏览器"可手动指定 .exe 路径</li>
        </ul>
        
        <h3>模型管理</h3>
        <ul>
            <li>切换到"📦 模型管理"页面可查看、下载、删除模型</li>
            <li>支持 HuggingFace、ModelScope 等下载源</li>
        </ul>
        
        <h3>软件更新</h3>
        <ul>
            <li>切换到"🔄 软件更新"页面检查并安装新版本</li>
        </ul>
        
        <h3>日志查看</h3>
        <ul>
            <li>底部日志区域实时显示启动、运行、错误信息</li>
            <li>可开启/关闭自动滚动以便查看历史日志</li>
        </ul>
        """)
        layout.addWidget(help_text)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()
    
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
            if hasattr(self, 'qinglong_group'):
                self.qinglong_group.hide()
        else:
            # 折叠时显示服务管理区域
            if hasattr(self, 'qinglong_group'):
                self.qinglong_group.show()
    
    def _get_model_verify_info(self, model_name):
        """获取模型验证信息 - 与青龙训练器前端 /api/generate/models 保持一致"""
        try:
            import sys
            sys.path.insert(0, self.base_dir)
            from acestep.model_downloader import check_model_exists, verify_model, get_checkpoints_dir
            checkpoints_dir = get_checkpoints_dir()
            is_installed = check_model_exists(model_name, checkpoints_dir)
            if is_installed:
                return {"integrity_status": "complete", "integrity_details": None}
            model_path = checkpoints_dir / model_name if hasattr(checkpoints_dir, '__truediv__') else None
            if model_path and model_path.exists():
                _, _, details = verify_model(model_name, checkpoints_dir)
                integrity_details = {
                    "files_found": details.get("files_found", []),
                    "files_missing": details.get("files_missing", []),
                    "total_size_mb": round(details.get("total_size", 0) / 1e6, 2),
                    "expected_size_mb": round(details.get("expected_size", 0) / 1e6, 2),
                    "size_ok": details.get("size_ok", False),
                }
                return {"integrity_status": "incomplete", "integrity_details": integrity_details}
            return {"integrity_status": "missing", "integrity_details": None}
        except Exception as e:
            return {"integrity_status": "missing", "integrity_details": None}

    def _load_model_list(self):
        """加载模型列表 - 与青龙训练器前端模型描述保持同步"""
        MODEL_SHORT_NAMES = {
            "acestep-v15-base": "1.5B",
            "acestep-v15-sft": "1.5S",
            "acestep-v15-turbo": "1.5T",
            "acestep-v15-turbo-shift1": "1.5TS1",
            "acestep-v15-turbo-shift3": "1.5TS3",
            "acestep-v15-turbo-continuous": "1.5TC",
            # XL models (4B DiT, requires >=12GB VRAM)
            "acestep-v15-xl-turbo": "XL-T",
            "acestep-v15-xl-sft": "XL-S",
            "acestep-v15-xl-base": "XL-B",
            "acestep-5Hz-lm-0.6B": "LM 0.6B",
            "acestep-5Hz-lm-1.7B": "LM 1.7B",
            "acestep-5Hz-lm-4B": "LM 4B",
        }

        self.model_list.append({
            "name": "main",
            "display_name": "Main Model",
            "short_name": "主模型",
            "repo": "ACE-Step/Ace-Step1.5",
            "category": "main",
            "description": "完整基础模型包，包含核心组件",
            "info": "包含VAE、Qwen3-Embedding-0.6B、acestep-v15-turbo、acestep-5Hz-lm-1.7B等核心组件。适合初次使用的用户，提供一站式完整解决方案。",
            "exists": self._check_main_model_exists(),
            "integrity_status": "complete" if self._check_main_model_exists() else "missing",
            "integrity_details": None,
        })

        lm_models = {
            "acestep-5Hz-lm-0.6B": {
                "repo": "ACE-Step/acestep-5Hz-lm-0.6B",
                "description": "最轻量语言模型（~0.5 GB VRAM）",
                "info": "0.6B参数的语言模型，速度极快，资源占用低，适合快速原型开发和资源有限的环境。未安装时自动下载。",
            },
            "acestep-5Hz-lm-1.7B": {
                "repo": "ACE-Step/acestep-5Hz-lm-1.7B",
                "description": "平衡语言模型（~1.5 GB VRAM）",
                "info": "1.7B参数的语言模型，平衡速度与质量，是默认LM模型，随主模型一起安装。",
            },
            "acestep-5Hz-lm-4B": {
                "repo": "ACE-Step/acestep-5Hz-lm-4B",
                "description": "最高品质语言模型（~4 GB VRAM）",
                "info": "4B参数的语言模型，生成质量最高，能理解更复杂的音乐结构和风格，适合专业音乐创作。未安装时自动下载。",
            },
        }

        for model_name, model_info in lm_models.items():
            verify_info = self._get_model_verify_info(model_name)
            self.model_list.append({
                "name": model_name,
                "display_name": model_name,
                "short_name": MODEL_SHORT_NAMES.get(model_name, model_name),
                "repo": model_info["repo"],
                "category": "lm",
                "description": model_info["description"],
                "info": model_info["info"],
                "exists": self._check_model_exists(model_name),
                "integrity_status": verify_info["integrity_status"],
                "integrity_details": verify_info["integrity_details"],
            })

        dit_models = {
            "acestep-v15-base": {
                "repo": "ACE-Step/acestep-v15-base",
                "description": "基础模型，适合从零开始创作，生成风格多样的音乐。",
                "info": "v1.5版本的基础模型，适合从零开始创作，能生成风格多样的音乐，是最灵活的选择。非Turbo模型，默认20步推理+ADG。",
            },
            "acestep-v15-sft": {
                "repo": "ACE-Step/acestep-v15-sft",
                "description": "SFT微调模型，更适合风格延续和参考创作，旋律还原度较高。",
                "info": "经过监督微调的模型，更适合风格延续和参考创作，旋律还原度较高，生成更加稳定可控。非Turbo模型，默认20步推理+ADG。",
            },
            "acestep-v15-turbo": {
                "repo": "ACE-Step/Ace-Step1.5",
                "description": "Turbo快速模型，生成速度快，适合快速迭代和测试想法。",
                "info": "Turbo系列默认模型，随主模型一起安装，生成速度快，适合快速迭代和测试想法。",
            },
            "acestep-v15-turbo-shift1": {
                "repo": "ACE-Step/acestep-v15-turbo-shift1",
                "description": "Turbo Shift 1模型，平衡速度与质量，是日常创作的首选。",
                "info": "Turbo系列，Shift 1采样，平衡速度与质量，适合日常创作和快速迭代。",
            },
            "acestep-v15-turbo-shift3": {
                "repo": "ACE-Step/acestep-v15-turbo-shift3",
                "description": "Turbo Shift 3模型，质量更好的快速模型，推荐用于正式创作。",
                "info": "Turbo系列，Shift 3采样，质量更好的快速模型，推荐用于正式创作。是默认推荐的DiT模型。",
            },
            "acestep-v15-turbo-continuous": {
                "repo": "ACE-Step/acestep-v15-turbo-continuous",
                "description": "Turbo Continuous模型，适合长音频生成，稳定性极佳。",
                "info": "Turbo系列，支持连续生成，适合长音频创作，稳定性极佳，能生成连贯的完整音乐作品。",
            },
            # XL models (4B DiT, requires >=12GB VRAM)
            "acestep-v15-xl-turbo": {
                "repo": "ACE-Step/acestep-v15-xl-turbo",
                "description": "XL Turbo快速模型（4B DiT），8步推理，音质极佳，需要≥12GB VRAM。",
                "info": "4B参数DiT解码器，Turbo蒸馏加速仅需8步推理，音频质量显著优于2B模型。最低12GB VRAM（offload+INT8），推荐20GB+。",
            },
            "acestep-v15-xl-sft": {
                "repo": "ACE-Step/acestep-v15-xl-sft",
                "description": "XL SFT微调模型（4B DiT），50步推理，品质最高，需要≥12GB VRAM。",
                "info": "4B参数DiT解码器，经过监督微调，品质最高，适合专业音乐创作。最低12GB VRAM，推荐20GB+。",
            },
            "acestep-v15-xl-base": {
                "repo": "ACE-Step/acestep-v15-xl-base",
                "description": "XL 基础模型（4B DiT），50步推理，多样性最高，支持extract/lego/complete。",
                "info": "4B参数DiT解码器，多样性最高，支持所有高级任务（音频提取、Lego拼接、完整生成）。最低12GB VRAM，推荐20GB+。",
            },
        }

        for model_name, model_info in dit_models.items():
            verify_info = self._get_model_verify_info(model_name)
            self.model_list.append({
                "name": model_name,
                "display_name": model_name,
                "short_name": MODEL_SHORT_NAMES.get(model_name, model_name),
                "repo": model_info["repo"],
                "category": "dit",
                "description": model_info["description"],
                "info": model_info["info"],
                "exists": self._check_model_exists(model_name),
                "integrity_status": verify_info["integrity_status"],
                "integrity_details": verify_info["integrity_details"],
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
        
        try:
            self.is_downloading = True
            self.current_operation_model = model_name
            
            self._update_model_management_ui()
            
            if self.model_manager_widget is not None:
                self.model_manager_widget.show_progress(f"正在下载: {model_name}")
            
            self.model_download_thread = ModelDownloadThread(
                model_name, 
                self.base_dir, 
                self.selected_download_source
            )
            
            self.model_download_thread.log_received.connect(self._log)
            self.model_download_thread.download_finished.connect(self._on_download_finished)
            self.model_download_thread.progress_updated.connect(self._on_download_progress_updated)
            
            self._set_model_buttons_enabled(False)
            
            self.model_download_thread.start()
        except Exception as e:
            self.is_downloading = False
            self.current_operation_model = None
            self._log(f"[错误] 启动下载失败: {str(e)}", "#F44336")
            if self.model_manager_widget is not None:
                try:
                    self.model_manager_widget.hide_progress()
                except Exception:
                    pass
            self._set_model_buttons_enabled(True)
    
    def _on_download_progress_updated(self, value: int, desc: str):
        """下载进度更新回调"""
        try:
            if hasattr(self, '_model_progress_bars') and self.current_operation_model in self._model_progress_bars:
                bar, label = self._model_progress_bars[self.current_operation_model]
                bar.setValue(value)
                if desc:
                    label.setText(desc)
            if self.model_manager_widget is not None:
                self.model_manager_widget.update_progress(value, desc)
        except Exception:
            pass
    
    def _on_download_finished(self, success: bool, model_name: str):
        """下载完成回调"""
        self.is_downloading = False
        self.current_operation_model = None
        
        try:
            if self.model_manager_widget is not None:
                self.model_manager_widget.hide_progress()
        except Exception:
            pass
        
        if success:
            self.model_list = []
            try:
                self._load_model_list()
            except Exception as e:
                self._log(f"[警告] 刷新模型列表失败: {str(e)}", "#FF9800")
        try:
            self._update_model_management_ui()
        except Exception as e:
            self._log(f"[警告] 更新模型UI失败: {str(e)}", "#FF9800")
        
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
                
                short_name = model.get("short_name", model["display_name"])
                name_label = QLabel(f"{short_name}")
                name_label.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 12px;")
                row1.addWidget(name_label)
                
                model_id_label = QLabel(model["display_name"])
                model_id_label.setStyleSheet("font-size: 10px; color: #888888;")
                row1.addWidget(model_id_label)
                
                row1.addStretch()
                
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
                status_label.setStyleSheet(f"font-size: 11px; color: {status_color}; font-weight: bold;")
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
                    is_main_component = model["name"] in ("acestep-v15-turbo", "acestep-5Hz-lm-1.7B")
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
                    if is_main_component:
                        delete_btn.setEnabled(False)
                        delete_btn.setToolTip("主模型组件，请删除主模型")
                    delete_btn.clicked.connect(lambda checked, m=model["name"]: self._delete_model(m))
                    btn_layout.addWidget(delete_btn)
                else:
                    # 未安装的模型：下载按钮
                    download_btn = QPushButton("下载")
                    download_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #C62828;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            padding: 3px 10px;
                            font-size: 11px;
                            font-weight: normal;
                        }
                        QPushButton:hover {
                            background-color: #D32F2F;
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
                            background-color: #C62828;
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
                
                desc_label = QLabel(model["description"])
                desc_label.setStyleSheet("font-size: 11px; color: #AAAAAA;")
                desc_label.setWordWrap(True)
                model_item_layout.addWidget(desc_label)
                
                if "info" in model:
                    info_label = QLabel(model["info"])
                    info_label.setStyleSheet("font-size: 10px; color: #888888;")
                    info_label.setWordWrap(True)
                    model_item_layout.addWidget(info_label)
                
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
                        warn_text = "⚠ " + "，".join(warn_parts) + "，建议重新下载"
                        warn_label = QLabel(warn_text)
                        warn_label.setStyleSheet("font-size: 10px; color: #FF9800; font-weight: bold;")
                        warn_label.setWordWrap(True)
                        model_item_layout.addWidget(warn_label)
                
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
        
        try:
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
        except ImportError:
            self._log("[警告] psutil 未安装，跳过进程清理", "#FF9800")
        
        self._log("✓ 所有进程已退出")
        
        self.config.set("ui.window_size", {
            "width": self.width(),
            "height": self.height()
        })
        
        self._force_exit = True
        self.close()
    
    def closeEvent(self, event):
        """关闭事件：默认最小化到系统托盘，托盘退出时真正关闭"""
        if self._force_exit:
            self.config.set("ui.window_size", {
                "width": self.width(),
                "height": self.height()
            })
            
            self._debug_logging = False
            if self._debug_log_file:
                try:
                    self._debug_log_file.close()
                except Exception:
                    pass
                self._debug_log_file = None
            
            self.monitor.stop()
            self.monitor.wait()
            
            self.tray_icon.hide()
            
            event.accept()
        else:
            # 隐藏到系统托盘
            self.hide()
            self.tray_icon.show()
            try:
                self.tray_icon.showMessage(
                    "云集智能音乐创意台",
                    "程序已最小化到系统托盘，双击托盘图标可恢复窗口",
                    QIcon(),
                    3000
                )
            except Exception:
                pass
            event.ignore()


def extract_scripts():
    """提取打包的脚本文件到 app/scripts/ 文件夹（与开发结构一致）"""
    import sys
    import shutil
    from pathlib import Path
    
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        work_dir = Path.cwd()
        app_dir = work_dir / "app"
        app_dir.mkdir(exist_ok=True)
        
        scripts_dir = app_dir / "scripts"
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


def _ensure_single_instance():
    """确保只运行一个实例：已有实例则退出，新实例获得互斥体"""
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        mutex_name = "Global\\云集智能音乐创意台_SingleInstance"
        h_mutex = kernel32.CreateMutexW(None, True, mutex_name)
        if not h_mutex:
            return
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(h_mutex)
            print("[信息] 已有实例在运行，本次启动被阻止")
            sys.exit(0)
        import atexit
        atexit.register(lambda: kernel32.CloseHandle(h_mutex))
    except Exception:
        pass


def _kill_old_instances_sync():
    """同步查找并杀掉同名的旧进程实例"""
    import os
    import psutil
    try:
        my_pid = os.getpid()
    except Exception:
        return
    ancestor_pids = set()
    try:
        cur = psutil.Process(my_pid)
        while True:
            parent = cur.parent()
            if parent is None or parent.pid == cur.pid:
                break
            ancestor_pids.add(parent.pid)
            cur = parent
            if len(ancestor_pids) > 20:
                break
    except Exception:
        pass
    for proc in psutil.process_iter(["pid", "exe", "ppid", "cmdline"]):
        try:
            pid = proc.info["pid"]
            if pid == my_pid:
                continue
            if pid in ancestor_pids:
                continue
            if proc.info.get("ppid") == my_pid:
                continue
            exe = proc.info.get("exe") or ""
            cmdline = ' '.join(proc.info.get("cmdline") or [])
            is_self_instance = (
                "云集智能音乐创意台" in exe or
                "云集智能音乐创意台" in os.path.dirname(exe) or
                ("云集智能音乐创意台" in cmdline and "main.py" in cmdline)
            )
            if not is_self_instance:
                continue
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def _kill_old_instances_async():
    """后台查找并杀掉同名的旧进程实例"""
    try:
        import threading
        threading.Thread(target=_kill_old_instances_sync, daemon=True).start()
    except Exception:
        pass


def main(app=None, splash=None):
    # Kill old instances FIRST (protects against stale orphaned processes)
    _kill_old_instances_sync()
    # Now claim the singleton mutex — if another process already holds it, exit
    _ensure_single_instance()
    # Second pass: kill any remaining instances that raced past the mutex
    # (e.g., two processes started at identical wall-clock time)
    if "--no-dedup" not in sys.argv:
        _kill_old_instances_sync()

    extract_scripts()
    
    if app is None:
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
    
    if splash is None:
        splash = SplashScreen()
    
    screen = app.primaryScreen().geometry()
    x = (screen.width() - splash.width()) // 2
    y = (screen.height() - splash.height()) // 2
    splash.move(x, y)
    splash.show()
    splash.repaint()
    app.processEvents()
    
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass
    
    splash.set_progress(0.1, "正在创建主窗口...")
    app.processEvents()

    window = MainWindow(splash=splash)

    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
