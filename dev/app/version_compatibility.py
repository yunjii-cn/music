"""
版本兼容性管理器
处理不同版本间的文件夹结构兼容性问题
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


class VersionCompatibilityManager:
    """版本兼容性管理器"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.compatibility_file = self.base_dir / ".version_compatibility"
        self.user_dirs = ['config', 'models', 'output', '.env']
        self._load_compatibility_data()
    
    def _load_compatibility_data(self):
        """加载兼容性数据"""
        self.compatibility_data = {
            'last_known_version': None,
            'folder_structure': {}
        }
        
        if self.compatibility_file.exists():
            try:
                with open(self.compatibility_file, 'r', encoding='utf-8') as f:
                    self.compatibility_data = json.load(f)
            except Exception as e:
                print(f"加载兼容性数据失败：{e}")
    
    def _save_compatibility_data(self):
        """保存兼容性数据"""
        try:
            with open(self.compatibility_file, 'w', encoding='utf-8') as f:
                json.dump(self.compatibility_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存兼容性数据失败：{e}")
    
    def _scan_folder_structure(self):
        """扫描当前文件夹结构"""
        structure = {}
        
        for dir_name in self.user_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                structure[dir_name] = {
                    'exists': True,
                    'files': self._list_files(dir_path),
                    'last_updated': datetime.fromtimestamp(dir_path.stat().st_mtime).isoformat()
                }
            else:
                structure[dir_name] = {'exists': False}
        
        return structure
    
    def _list_files(self, dir_path, max_depth=2):
        """递归列出文件（限制深度）"""
        files = []
        try:
            for item in dir_path.iterdir():
                if item.is_file():
                    files.append({
                        'name': item.name,
                        'size': item.stat().st_size,
                        'last_updated': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                elif item.is_dir() and max_depth > 0:
                    files.append({
                        'name': item.name,
                        'is_dir': True,
                        'children': self._list_files(item, max_depth - 1)
                    })
        except Exception as e:
            print(f"扫描目录失败 {dir_path}：{e}")
        return files
    
    def check_compatibility(self, target_version=None):
        """检查版本兼容性"""
        current_structure = self._scan_folder_structure()
        last_structure = self.compatibility_data.get('folder_structure', {})
        
        issues = []
        warnings = []
        
        for dir_name in self.user_dirs:
            current = current_structure.get(dir_name, {})
            last = last_structure.get(dir_name, {})
            
            # 检查目录是否存在
            if current.get('exists') and not last.get('exists'):
                warnings.append(f"目录 {dir_name} 是新增的")
            elif not current.get('exists') and last.get('exists'):
                issues.append(f"目录 {dir_name} 已被删除")
        
        return {
            'is_compatible': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'current_structure': current_structure,
            'last_structure': last_structure
        }
    
    def backup_current_state(self, version_name=None):
        """备份当前状态"""
        backup_dir = self.base_dir / f".compatibility_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)
        
        try:
            # 备份用户目录
            for dir_name in self.user_dirs:
                src = self.base_dir / dir_name
                dst = backup_dir / dir_name
                
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # 保存结构信息
            structure = self._scan_folder_structure()
            with open(backup_dir / "structure.json", 'w', encoding='utf-8') as f:
                json.dump({
                    'version': version_name,
                    'structure': structure,
                    'backup_time': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            print(f"已备份当前状态到：{backup_dir}")
            return backup_dir
        except Exception as e:
            print(f"备份失败：{e}")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            return None
    
    def update_compatibility_data(self, version_name=None):
        """更新兼容性数据"""
        self.compatibility_data['last_known_version'] = version_name
        self.compatibility_data['folder_structure'] = self._scan_folder_structure()
        self.compatibility_data['last_updated'] = datetime.now().isoformat()
        self._save_compatibility_data()
    
    def migrate_structure(self, backup_dir=None):
        """迁移文件夹结构"""
        if backup_dir and Path(backup_dir).exists():
            try:
                # 从备份恢复
                for dir_name in self.user_dirs:
                    src = Path(backup_dir) / dir_name
                    dst = self.base_dir / dir_name
                    
                    if src.exists():
                        if dst.exists():
                            # 备份现有
                            temp_backup = self.base_dir / f".{dir_name}_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            shutil.move(dst, temp_backup)
                        
                        if src.is_dir():
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                
                print(f"已从备份迁移结构：{backup_dir}")
                return True
            except Exception as e:
                print(f"迁移失败：{e}")
                return False
        
        return False
