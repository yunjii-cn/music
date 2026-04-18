#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建红色云朵图标
"""
from PIL import Image, ImageDraw

def create_cloud_icon():
    """创建红色云朵图标"""
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []
    
    for size in sizes:
        w, h = size
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 红色背景
        bg_color = (211, 47, 47)  # #D32F2F
        radius = int(w * 0.25)
        
        # 绘制圆角矩形
        draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=bg_color)
        
        # 绘制白色云朵（简化版）
        cloud_color = (255, 255, 255, 255)
        
        # 根据尺寸缩放
        scale = w / 256.0
        
        # 云朵的几个圆弧
        # 左半部分
        draw.ellipse([
            int(40 * scale), int(80 * scale),
            int(120 * scale), int(160 * scale)
        ], fill=cloud_color)
        
        # 上半部分
        draw.ellipse([
            int(80 * scale), int(40 * scale),
            int(176 * scale), int(136 * scale)
        ], fill=cloud_color)
        
        # 右半部分
        draw.ellipse([
            int(140 * scale), int(60 * scale),
            int(216 * scale), int(140 * scale)
        ], fill=cloud_color)
        
        # 底部
        draw.ellipse([
            int(60 * scale), int(110 * scale),
            int(196 * scale), int(196 * scale)
        ], fill=cloud_color)
        
        images.append(img)
    
    # 保存为ICO
    ico_path = "icon.ico"
    # 从最大尺寸开始保存
    images[0].save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    
    return ico_path

if __name__ == "__main__":
    print("正在创建红色云朵图标...")
    try:
        ico_path = create_cloud_icon()
        print(f"✓ 图标已保存到: {ico_path}")
        print("✓ 支持的尺寸: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16")
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
