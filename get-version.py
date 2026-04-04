#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取当前时间版本号
用于快速生成版本号，方便开发工作流

使用方法：
  python get-version.py
  # 输出：2026.04.02.0633
"""
from datetime import datetime

def get_version():
    """获取当前时间版本号"""
    return datetime.now().strftime("%Y.%m.%d.%H%M")

if __name__ == "__main__":
    print(get_version())
