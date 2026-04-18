#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换用户提供的PNG图标为ICO格式
"""
from PIL import Image
import os

def convert_user_icon():
    """转换用户的PNG图标"""
    # 用户提供的PNG路径
    png_path = r"E:\AI应用\云集智能音乐创意台\test\ico.png"
    
    if not os.path.exists(png_path):
        print(f"✗ 文件不存在: {png_path}")
        return None
    
    print(f"正在加载图标: {png_path}")
    img = Image.open(png_path).convert("RGBA")
    
    # 保存为ICO
    ico_path = "icon.ico"
    print(f"正在转换为ICO: {ico_path}")
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    
    print(f"✓ 图标已成功转换!")
    return ico_path

if __name__ == "__main__":
    try:
        ico_path = convert_user_icon()
        if ico_path:
            print("\n现在可以重新构建软件了！")
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
