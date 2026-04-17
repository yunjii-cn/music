#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的版本列表调试
"""

import sys
import json
from pathlib import Path
import re
from datetime import datetime

def main():
    base_dir = Path(__file__).parent.parent
    
    print("=== Base directory ===")
    print(base_dir)
    
    # 检查版本历史
    print("\n=== Checking version_history.json ===")
    ver_hist_path = base_dir / "version_history.json"
    if ver_hist_path.exists():
        with open(ver_hist_path, "r", encoding="utf-8") as f:
            ver_hist = json.load(f)
        print(f"Version history found, {len(ver_hist)} entries")
        print(f"Keys: {list(ver_hist.keys())[:5]}...")
    else:
        print("version_history.json NOT FOUND!")
        return
    
    # 检查 ver 目录
    print("\n=== Checking ver folders ===")
    dev_dir = base_dir.parent
    ver_dir = dev_dir / "ver" if dev_dir.exists() else None
    app_ver_dir = base_dir / "ver"
    version_dir = base_dir / "ver"
    
    print(f"ver_dir: {ver_dir} exists? {ver_dir.exists() if ver_dir else 'n/a'}")
    print(f"app_ver_dir: {app_ver_dir} exists? {app_ver_dir.exists()}")
    
    version_dict = {}
    
    # 从版本历史加载
    for version_name in ver_hist:
        match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', version_name)
        if match:
            version = match.group(1)
            version_dict[version] = {
                'version': version,
                'name': version_name,
                'available': False,
                'path': None,
                'size': None,
                'date': None
            }
            print(f"  Added from history: v{version} - {version_name}")
    
    # 检查 ver_folder 中的文件
    print(f"\n=== Checking EXE files ===")
    for ver_folder in [ver_dir, app_ver_dir, version_dir]:
        if ver_folder and ver_folder.exists():
            print(f"Checking {ver_folder}")
            exe_files = list(ver_folder.glob("*.exe"))
            print(f"  Found {len(exe_files)} exe files")
            for exe_file in exe_files:
                print(f"    - {exe_file.name}")
                match = re.search(r'v(\d+\.\d+\.\d+\.\d+)', exe_file.name)
                if match:
                    version = match.group(1)
                    file_size = exe_file.stat().st_size / (1024 * 1024)
                    mtime = datetime.fromtimestamp(exe_file.stat().st_mtime)
                    
                    if version in version_dict:
                        version_dict[version]['available'] = True
                        version_dict[version]['path'] = str(exe_file)
                        version_dict[version]['size'] = f"{file_size:.2f} MB"
                        version_dict[version]['date'] = mtime.strftime("%Y-%m-%d %H:%M")
                        version_dict[version]['name'] = exe_file.name
                        print(f"    ✓ Marked v{version} as available")
                    else:
                        version_dict[version] = {
                            'version': version,
                            'name': exe_file.name,
                            'available': True,
                            'path': str(exe_file),
                            'size': f"{file_size:.2f} MB",
                            'date': mtime.strftime("%Y-%m-%d %H:%M")
                        }
                        print(f"    + Added new v{version}")
    
    # 最终列表
    all_versions = list(version_dict.values())
    all_versions.sort(key=lambda x: x['version'], reverse=True)
    
    print("\n=== Final version list ===")
    print(f"Total versions: {len(all_versions)}")
    for v in all_versions:
        print(f"  v{v['version']} - {v['name']} - available: {v['available']}")

if __name__ == "__main__":
    main()
