"""共享配置管理模块

管理项目的共享配置，支持配置文件和环境变量
"""

import os
import json
from pathlib import Path

class ConfigManager:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 获取项目根目录
        self.root_dir = Path(__file__).resolve().parent.parent
        self.config_dir = self.root_dir / "config"
        self.config_file = self.config_dir / "config.json"
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        # 首先检查环境变量
        env_key = key.upper().replace('.', '_')
        if env_key in os.environ:
            return os.environ[env_key]
        
        # 然后检查配置文件
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        # 导航到配置路径
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        return self.save_config()
    
    def get_checkpoints_dir(self):
        """获取模型存储目录"""
        return str(self.root_dir / "models")
    
    def get_output_dir(self):
        """获取输出目录"""
        return str(self.root_dir / "output")
    
    def get_data_dir(self):
        """获取数据目录"""
        return str(self.root_dir / "data")
    
    def get_cache_dir(self):
        """获取缓存目录"""
        return str(self.root_dir / "data" / "cache")
    
    def get_temp_dir(self):
        """获取临时文件目录"""
        return str(self.root_dir / "data" / "temp")

# 创建全局配置管理器实例
config_manager = ConfigManager()
