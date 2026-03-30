#!/usr/bin/env python3
"""
Python 3.12 便携版下载器 - 命令行版本
用于在PowerShell脚本中调用
"""

import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


# Python 3.12 便携版版本和镜像源
PYTHON_PORTABLE_VERSION = "3.12.7"
PYTHON_PORTABLE_FILENAME = f"python-{PYTHON_PORTABLE_VERSION}-embed-amd64.zip"
PYTHON_PORTABLE_SIZE_MB = 15  # 大约大小

# Python 3.12 下载镜像源
PYTHON_MIRRORS = [
    {
        "name": "淘宝镜像",
        "url": f"https://registry.npmmirror.com/-/binary/python/{PYTHON_PORTABLE_VERSION}/{PYTHON_PORTABLE_FILENAME}",
        "test_url": "https://registry.npmmirror.com/"
    },
    {
        "name": "华为镜像",
        "url": f"https://mirrors.huaweicloud.com/python/{PYTHON_PORTABLE_VERSION}/{PYTHON_PORTABLE_FILENAME}",
        "test_url": "https://mirrors.huaweicloud.com/"
    },
    {
        "name": "官方源",
        "url": f"https://www.python.org/ftp/python/{PYTHON_PORTABLE_VERSION}/{PYTHON_PORTABLE_FILENAME}",
        "test_url": "https://www.python.org/"
    }
]


def download_file(url, dest_path):
    """下载文件"""
    print(f"正在下载: {url}")
    
    try:
        request = Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with urlopen(request, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}%", end='')
        
        print("\n✅ 下载完成!")
        return True
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False


def extract_zip(zip_path, extract_dir):
    """解压ZIP文件"""
    print(f"正在解压: {zip_path.name}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print("✅ 解压完成!")
        return True
        
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Python 3.12 便携版下载器')
    parser.add_argument('--download-dir', type=str, required=True, 
                       help='下载目录')
    
    args = parser.parse_args()
    
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("  Python 3.12 便携版下载器")
    print("=" * 60)
    print()
    
    # 检查是否已下载
    python_dir = download_dir / f"python-{PYTHON_PORTABLE_VERSION}-embed-amd64"
    python_exe = python_dir / "python.exe"
    
    if python_exe.exists():
        print(f"✅ Python 3.12 便携版已存在: {python_exe}")
        print(f"PYTHON_PATH={python_exe}")
        return 0
    
    zip_path = download_dir / PYTHON_PORTABLE_FILENAME
    
    # 尝试从各个镜像源下载
    for mirror in PYTHON_MIRRORS:
        print()
        print(f"尝试镜像源: {mirror['name']}")
        
        if download_file(mirror['url'], zip_path):
            # 解压
            if extract_zip(zip_path, download_dir):
                # 删除ZIP文件
                try:
                    zip_path.unlink()
                except:
                    pass
                
                # 验证
                if python_exe.exists():
                    print()
                    print("=" * 60)
                    print("✅ Python 3.12 便携版安装成功!")
                    print(f"   位置: {python_exe}")
                    print("=" * 60)
                    print(f"PYTHON_PATH={python_exe}")
                    return 0
    
    print()
    print("❌ 所有镜像源下载失败!")
    return 1


if __name__ == "__main__":
    sys.exit(main())
