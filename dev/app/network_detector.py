"""
网络检测和测速模块
检测网络环境，选择最优下载源，测速
"""

import os
import sys
import time
import socket
import threading
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed


# 常用的Git下载镜像源
GIT_MIRRORS = [
    {
        "name": "GitHub 官方",
        "url": "https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/PortableGit-2.45.1-64-bit.7z.exe",
        "test_url": "https://github.com",
        "region": "global"
    },
    {
        "name": "GitHub 镜像 (GHProxy)",
        "url": "https://ghproxy.com/https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/PortableGit-2.45.1-64-bit.7z.exe",
        "test_url": "https://ghproxy.com",
        "region": "cn"
    },
    {
        "name": "GitHub 镜像 (FastGit)",
        "url": "https://download.fastgit.org/git-for-windows/git/releases/download/v2.45.1.windows.1/PortableGit-2.45.1-64-bit.7z.exe",
        "test_url": "https://download.fastgit.org",
        "region": "cn"
    }
]


class NetworkDetector:
    """网络检测器"""
    
    @staticmethod
    def is_network_available(timeout=5):
        """检查网络是否可用"""
        try:
            # 尝试连接多个常用DNS服务器
            hosts = [
                ("8.8.8.8", 53),      # Google DNS
                ("114.114.114.114", 53),  # 114 DNS
                ("223.5.5.5", 53)    # Ali DNS
            ]
            
            for host, port in hosts:
                try:
                    sock = socket.create_connection((host, port), timeout=timeout)
                    sock.close()
                    return True
                except:
                    continue
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def test_url_speed(url, timeout=10):
        """测试单个URL的速度（返回响应时间，毫秒）"""
        try:
            start_time = time.time()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            request = Request(url, headers=headers, method='HEAD')
            with urlopen(request, timeout=timeout):
                elapsed = (time.time() - start_time) * 1000
                return elapsed, True
                
        except Exception as e:
            return float('inf'), False
    
    @staticmethod
    def find_best_mirror(mirrors=None, max_workers=3):
        """
        并行测速，找到最快的镜像源
        
        返回：(best_mirror, all_results)
        """
        if mirrors is None:
            mirrors = GIT_MIRRORS
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_mirror = {
                executor.submit(NetworkDetector.test_url_speed, mirror["test_url"]): mirror
                for mirror in mirrors
            }
            
            for future in as_completed(future_to_mirror):
                mirror = future_to_mirror[future]
                try:
                    latency, success = future.result()
                    results.append({
                        "mirror": mirror,
                        "latency": latency,
                        "success": success
                    })
                except Exception as e:
                    results.append({
                        "mirror": mirror,
                        "latency": float('inf'),
                        "success": False
                    })
        
        # 按延迟排序
        results.sort(key=lambda x: x["latency"])
        
        # 找到第一个成功的
        best_mirror = None
        for result in results:
            if result["success"]:
                best_mirror = result["mirror"]
                break
        
        return best_mirror, results
    
    @staticmethod
    def format_latency(latency_ms):
        """格式化延迟显示"""
        if latency_ms == float('inf'):
            return "超时"
        elif latency_ms < 100:
            return f"{latency_ms:.0f}ms (快)"
        elif latency_ms < 500:
            return f"{latency_ms:.0f}ms (中)"
        else:
            return f"{latency_ms:.0f}ms (慢)"


class SpeedTestThread(threading.Thread):
    """测速线程"""
    
    def __init__(self, mirrors=None, callback=None):
        super().__init__()
        self.mirrors = mirrors if mirrors else GIT_MIRRORS
        self.callback = callback
        self.daemon = True
    
    def run(self):
        """执行测速"""
        best_mirror, results = NetworkDetector.find_best_mirror(self.mirrors)
        
        if self.callback:
            self.callback(best_mirror, results)


def get_git_download_url_with_speedtest(callback=None):
    """
    获取Git下载URL（带测速）
    
    返回：(download_url, best_mirror_name, all_results)
    """
    # 先检查网络
    if not NetworkDetector.is_network_available():
        return None, "网络不可用", []
    
    # 测速
    best_mirror, results = NetworkDetector.find_best_mirror()
    
    if callback:
        callback(best_mirror, results)
    
    if best_mirror:
        return best_mirror["url"], best_mirror["name"], results
    else:
        # 所有测速都失败，返回默认
        return GIT_MIRRORS[0]["url"], GIT_MIRRORS[0]["name"], results
