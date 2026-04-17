#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试 as_widget=True 模式下的版本管理器
"""
import sys
from pathlib import Path

# 添加 app 目录到路径
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from version_manager import HybridVersionManagerDialog

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试版本管理器 - as_widget=True")
        self.setMinimumSize(1050, 750)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 计算 base_dir - 应该是 app 目录的父目录，即 dev 目录
        base_dir = Path(__file__).parent
        
        print(f"[DEBUG] TestMainWindow")
        print(f"[DEBUG] app_dir: {app_dir}")
        print(f"[DEBUG] base_dir: {base_dir}")
        
        # 创建版本管理器 as_widget=True
        self.version_widget = HybridVersionManagerDialog(
            parent=self,
            base_dir=str(base_dir),
            as_widget=True
        )
        
        layout.addWidget(self.version_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())