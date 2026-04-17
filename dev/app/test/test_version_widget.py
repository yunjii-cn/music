#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版本管理器widget模式
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

sys.path.insert(0, str(Path(__file__).parent.parent))

from version_manager import HybridVersionManagerDialog

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("版本管理器测试")
        self.setGeometry(100, 100, 1100, 800)
        
        # 中央widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        
        # 创建版本管理器widget
        base_dir = str(Path(__file__).parent.parent)
        self.version_widget = HybridVersionManagerDialog(self, base_dir, as_widget=True)
        layout.addWidget(self.version_widget)
        
        print("=== 测试版本管理器 ===")
        print(f"versions_layout.count(): {self.version_widget.versions_layout.count()}")
        
def main():
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
