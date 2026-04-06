"""
Python便携版下载器模块
检测Python版本，如果不是3.12则自动下载便携版
"""

import os
import sys
import subprocess
import zipfile
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QMessageBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from network_detector import NetworkDetector


# Python 3.12 便携版版本和镜像源
PYTHON_PORTABLE_VERSION = "3.12.7"
PYTHON_PORTABLE_FILENAME = f"python-{PYTHON_PORTABLE_VERSION}-embed-amd64.zip"
PYTHON_PORTABLE_SIZE_MB = 15  # 大约大小

# Python 3.12 下载镜像源
PYTHON_MIRRORS = [
    {
        "name": "官方源",
        "url": f"https://www.python.org/ftp/python/{PYTHON_PORTABLE_VERSION}/{PYTHON_PORTABLE_FILENAME}",
        "test_url": "https://www.python.org/"
    },
    {
        "name": "淘宝镜像",
        "url": f"https://registry.npmmirror.com/-/binary/python/{PYTHON_PORTABLE_VERSION}/{PYTHON_PORTABLE_FILENAME}",
        "test_url": "https://registry.npmmirror.com/"
    },
    {
        "name": "华为镜像",
        "url": f"https://mirrors.huaweicloud.com/python/{PYTHON_PORTABLE_VERSION}/{PYTHON_PORTABLE_FILENAME}",
        "test_url": "https://mirrors.huaweicloud.com/"
    }
]


class PythonDownloadThread(QThread):
    """Python下载线程"""
    
    progress_updated = pyqtSignal(int, str)  # 进度百分比, 消息
    speedtest_result = pyqtSignal(object, object)  # best_mirror, all_results
    download_finished = pyqtSignal(bool, str, Path)  # 是否成功, 消息, 路径
    extract_finished = pyqtSignal(bool, str, Path)  # 是否成功, 消息, Python路径
    
    def __init__(self, download_dir: Path):
        super().__init__()
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.current_download_url = None
        self.current_mirror_name = None
    
    def run(self):
        """执行下载"""
        try:
            # 测速，选择最优镜像源
            self.progress_updated.emit(0, "正在检测网络，选择最优下载源...")
            download_url, mirror_name, all_results = self._do_speedtest()
            if not download_url:
                self.download_finished.emit(False, "无法连接到下载服务器，请检查网络", None)
                return
            
            self.current_download_url = download_url
            self.current_mirror_name = mirror_name
            self.speedtest_result.emit(
                {"name": mirror_name, "url": download_url},
                all_results
            )
            
            # 下载
            self.progress_updated.emit(10, f"正在从 {mirror_name} 下载...")
            python_path = self._download_python(download_url)
            if not python_path:
                return
            
            # 解压
            self.progress_updated.emit(90, "正在解压...")
            python_dir = self._extract_python(python_path)
            if python_dir:
                self.extract_finished.emit(True, f"Python 3.12 便携版已就绪！", python_dir)
            
        except Exception as e:
            self.download_finished.emit(False, f"下载失败：{str(e)}", None)
    
    def _do_speedtest(self):
        """执行测速"""
        try:
            # 检查网络是否可用
            if not NetworkDetector.is_network_available():
                return None, None, []
            
            # 使用自定义Python镜像测速
            best_mirror, all_results = self._test_python_mirrors()
            
            if best_mirror:
                return best_mirror["url"], best_mirror["name"], all_results
            else:
                return PYTHON_MIRRORS[0]["url"], PYTHON_MIRRORS[0]["name"], all_results
                
        except Exception as e:
            print(f"测速失败：{e}")
            return PYTHON_MIRRORS[0]["url"], PYTHON_MIRRORS[0]["name"], []
    
    def _test_python_mirrors(self):
        """测试Python镜像源速度"""
        results = []
        best_mirror = None
        best_latency = float('inf')
        
        for mirror in PYTHON_MIRRORS:
            try:
                latency = NetworkDetector.test_latency(mirror["test_url"])
                success = latency is not None
                results.append({
                    "mirror": mirror,
                    "latency": latency if latency is not None else 9999,
                    "success": success
                })
                
                if success and latency < best_latency:
                    best_latency = latency
                    best_mirror = mirror
            except Exception as e:
                results.append({
                    "mirror": mirror,
                    "latency": 9999,
                    "success": False
                })
        
        return best_mirror, results
    
    def _download_python(self, download_url) -> Path:
        """下载Python"""
        file_path = self.download_dir / PYTHON_PORTABLE_FILENAME
        
        try:
            self.progress_updated.emit(10, f"正在从 {self.current_mirror_name} 下载 Python {PYTHON_PORTABLE_VERSION}...")
            
            # 使用请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            request = Request(download_url, headers=headers)
            with urlopen(request, timeout=60) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                
                with open(file_path, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        downloaded += len(buffer)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 75) + 15
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            self.progress_updated.emit(
                                progress,
                                f"正在下载 ({self.current_mirror_name})... {mb_downloaded:.1f}MB / {mb_total:.1f}MB"
                            )
            
            self.progress_updated.emit(90, "下载完成！")
            return file_path
            
        except Exception as e:
            self.download_finished.emit(False, f"下载失败：{str(e)}", None)
            return None
    
    def _extract_python(self, python_path: Path) -> Path:
        """解压Python"""
        try:
            extract_dir = self.download_dir / f"python-{PYTHON_PORTABLE_VERSION}-embed"
            
            # 如果目标目录已存在，先删除
            if extract_dir.exists():
                import shutil
                shutil.rmtree(extract_dir)
            
            # 解压zip文件
            with zipfile.ZipFile(python_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 删除安装包
            try:
                python_path.unlink()
            except:
                pass
            
            # 返回Python目录
            python_exe = extract_dir / "python.exe"
            if python_exe.exists():
                return extract_dir
            
            return None
                
        except Exception as e:
            self.extract_finished.emit(False, f"解压失败：{str(e)}", None)
            return None


class PythonDownloadDialog(QDialog):
    """Python下载对话框"""
    
    def __init__(self, parent=None, download_dir=None):
        super().__init__(parent)
        self.download_dir = Path(download_dir) if download_dir else Path.cwd() / "tools" / "python"
        self.python_path = None
        
        self.setWindowTitle("下载Python 3.12")
        self.setMinimumSize(550, 220)
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0D0D;
            }
        """)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self._setup_ui()
        self._start_download()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("📥 正在下载Python 3.12")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "检测到您使用的Python版本不是3.12，正在自动下载便携版...\n"
            "下载完成后将自动配置，无需您手动操作。"
        )
        desc_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addSpacing(15)
        
        # 测速结果区域
        self.speedtest_container = QWidget()
        self.speedtest_layout = QVBoxLayout(self.speedtest_container)
        self.speedtest_layout.setSpacing(8)
        self.speedtest_layout.setContentsMargins(0, 0, 0, 0)
        
        self.speedtest_label = QLabel("🔍 正在检测下载源...")
        self.speedtest_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.speedtest_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speedtest_layout.addWidget(self.speedtest_label)
        
        self.speedtest_scroll = QScrollArea()
        self.speedtest_scroll.setWidget(self.speedtest_container)
        self.speedtest_scroll.setWidgetResizable(True)
        self.speedtest_scroll.setMaximumHeight(150)
        self.speedtest_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #333333;
                border-radius: 5px;
                background-color: #121212;
            }
        """)
        self.speedtest_scroll.hide()
        layout.addWidget(self.speedtest_scroll)
        
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
                height: 28px;
                text-align: center;
                color: #FFFFFF;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #1565C0;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备开始...")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: #CCCCCC;
                border: none;
                border-radius: 5px;
                padding: 8px 18px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _start_download(self):
        """开始下载"""
        self.worker = PythonDownloadThread(self.download_dir)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.speedtest_result.connect(self._on_speedtest_result)
        self.worker.download_finished.connect(self._on_download_finished)
        self.worker.extract_finished.connect(self._on_extract_finished)
        self.worker.start()
    
    def _on_speedtest_result(self, best_mirror, all_results):
        """测速结果回调"""
        self.speedtest_scroll.show()
        self.speedtest_label.hide()
        
        # 清空之前的内容
        while self.speedtest_layout.count():
            item = self.speedtest_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 显示最优选择
        best_label = QLabel(f"✨ 最优选择：{best_mirror['name']}")
        best_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
        best_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speedtest_layout.addWidget(best_label)
        
        # 显示所有测速结果
        for result in all_results:
            mirror = result['mirror']
            latency = result['latency']
            success = result['success']
            
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setSpacing(10)
            row_layout.setContentsMargins(10, 5, 10, 5)
            
            # 镜像名称
            name_label = QLabel(mirror['name'])
            name_label.setStyleSheet(f"color: {'#4CAF50' if success else '#888888'}; font-size: 11px;")
            row_layout.addWidget(name_label)
            
            row_layout.addStretch()
            
            # 延迟
            latency_text = NetworkDetector.format_latency(latency)
            latency_label = QLabel(latency_text)
            color = "#888888"
            if success:
                if latency < 100:
                    color = "#4CAF50"
                elif latency < 500:
                    color = "#FF9800"
                else:
                    color = "#F44336"
            latency_label.setStyleSheet(f"color: {color}; font-size: 11px;")
            row_layout.addWidget(latency_label)
            
            self.speedtest_layout.addWidget(row)
    
    def _on_progress_updated(self, progress, message):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_download_finished(self, success, message, path):
        """下载完成"""
        if not success:
            QMessageBox.critical(self, "下载失败", message)
            self.reject()
    
    def _on_extract_finished(self, success, message, python_path):
        """解压完成"""
        if success:
            self.python_path = python_path
            self.status_label.setText("✅ " + message)
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.cancel_btn.setText("完成")
            self.cancel_btn.setEnabled(False)
            
            # 延迟关闭
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.accept)
        else:
            QMessageBox.critical(self, "解压失败", message)
            self.reject()


def get_python_path(base_dir=None):
    """
    获取Python路径
    优先检查当前Python是否为3.12，否则返回便携版路径（可能不存在）
    """
    # 1. 先检查当前Python版本
    import platform
    current_version = platform.python_version()
    current_major_minor = '.'.join(current_version.split('.')[:2])
    
    if current_major_minor == '3.12':
        return sys.executable  # 当前Python就是3.12
    
    # 2. 检查便携版Python
    if base_dir:
        base_path = Path(base_dir)
        python_dir = base_path / "tools" / "python" / f"python-{PYTHON_PORTABLE_VERSION}-embed"
        python_exe = python_dir / "python.exe"
        if python_exe.exists():
            return str(python_exe)
    
    return None


def is_python_312():
    """检查当前Python是否为3.12"""
    import platform
    current_version = platform.python_version()
    current_major_minor = '.'.join(current_version.split('.')[:2])
    return current_major_minor == '3.12'


def ensure_python_312(parent=None, base_dir=None, silent=False):
    """
    确保使用Python 3.12
    如果当前不是Python 3.12，自动下载便携版
    返回：(python_command, success)
    """
    python_cmd = get_python_path(base_dir)
    
    if python_cmd:
        return python_cmd, True
    
    # 如果静默模式，直接返回不下载
    if silent:
        return None, False
    
    # 需要下载
    reply = QMessageBox.question(
        parent,
        "需要Python 3.12",
        "本软件官方推荐使用Python 3.12。\n\n"
        "是否自动下载Python 3.12便携版？\n"
        f"（约 {PYTHON_PORTABLE_SIZE_MB}MB，无需安装）",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes
    )
    
    if reply == QMessageBox.StandardButton.No:
        return None, False
    
    # 显示下载对话框
    download_dir = Path(base_dir) / "tools" / "python" if base_dir else Path.cwd() / "tools" / "python"
    dialog = PythonDownloadDialog(parent, download_dir)
    
    if dialog.exec() == QDialog.DialogCode.Accepted and dialog.python_path:
        python_exe = dialog.python_path / "python.exe"
        if python_exe.exists():
            return str(python_exe), True
    
    return None, False


def ensure_python_312_silent(base_dir=None):
    """
    静默模式确保Python 3.12（不弹任何对话框）
    只检测，不下载
    返回：(python_command, success)
    """
    return ensure_python_312(parent=None, base_dir=base_dir, silent=True)
