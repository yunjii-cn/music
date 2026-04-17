"""Catalog and capability helpers for initialization flow."""

import os
from typing import List, Optional

import torch
from loguru import logger


class InitServiceCatalogMixin:
    """Checkpoint discovery and backend capability helpers."""

    def _device_type(self) -> str:
        """Normalize the host device value to a backend type string."""
        if isinstance(self.device, str):
            return self.device.split(":", 1)[0]
        return self.device.type

    def get_available_checkpoints(self) -> List[str]:
        """Return available checkpoint directory paths under the project root."""
        # Use root-level checkpoints directory for shared models
        import os
        from pathlib import Path
        checkpoint_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "checkpoints"
        if os.path.exists(checkpoint_dir):
            return [str(checkpoint_dir)]
        return []

    def get_available_acestep_v15_models(self) -&gt; List[str]:
        """Scan and return all model directory names that are valid ACE-Step DiT models."""
        import sys
        from pathlib import Path
        
        # 直接计算模型目录 - 最可靠的方法
        try:
            # 方法1: 使用model_downloader.py
            try:
                from acestep.model_downloader import get_checkpoints_dir, check_model_exists
                
                checkpoints_dir = get_checkpoints_dir()
                logger.info(f"[ModelScan] Method 1 - Using checkpoints_dir: {checkpoints_dir}")
            except Exception as e1:
                logger.warning(f"[ModelScan] Method 1 failed: {e1}")
                # 方法2: 直接从__file__计算
                current_file = Path(__file__).resolve()
                # acestep/core/generation/handler/init_service_catalog.py
                # 向上4级到app目录
                app_dir = current_file.parent.parent.parent.parent
                checkpoints_dir = app_dir / "models"
                if not checkpoints_dir.exists():
                    checkpoints_dir = app_dir / "checkpoints"
                logger.info(f"[ModelScan] Method 2 - Using checkpoints_dir: {checkpoints_dir}")
                
                # 简化版的check_model_exists
                def simple_check_model_exists(mname, cdir):
                    mpath = cdir / mname
                    if not mpath.exists() or not mpath.is_dir():
                        return False
                    try:
                        return len(list(mpath.iterdir())) &gt; 0
                    except:
                        return False
                
                check_model_exists = simple_check_model_exists
            
            # 列出所有可用模型，但只返回DiT模型
            exclude_models = ["Qwen3-Embedding-0.6B", "acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B", "acestep-5Hz-lm-4B", "vae"]
            
            models = []
            
            # 扫描checkpoints目录
            if checkpoints_dir.exists():
                logger.info(f"[ModelScan] Scanning: {checkpoints_dir}")
                for item in checkpoints_dir.iterdir():
                    if item.is_dir():
                        model_name = item.name
                        if model_name in exclude_models or model_name.startswith('.'):
                            logger.info(f"[ModelScan] Skipping excluded: {model_name}")
                            continue
                        
                        # 只添加DiT模型（排除LM模型）
                        if not model_name.endswith("-lm-0.6B") and not model_name.endswith("-lm-1.7B") and not model_name.endswith("-lm-4B"):
                            # 检查是否是有效的模型目录
                            if check_model_exists(model_name, checkpoints_dir):
                                models.append(model_name)
                                logger.info(f"[ModelScan] ✅ Added model: {model_name}")
                            else:
                                logger.info(f"[ModelScan] Skipping invalid model: {model_name}")
            
            models.sort()
            logger.info(f"[ModelScan] Final models list: {models}")
            return models
            
        except Exception as e:
            logger.error(f"[ModelScan] Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def is_flash_attention_available(self, device: Optional[str] = None) -> bool:
        """Check whether flash attention can be used on the target device."""
        target_device = str(device or self.device or "auto").split(":", 1)[0]
        if target_device == "auto":
            if not torch.cuda.is_available():
                return False
        else:
            if target_device != "cuda" or not torch.cuda.is_available():
                return False

        try:
            major, _ = torch.cuda.get_device_capability()
            if major < 8:
                logger.info(
                    f"[is_flash_attention_available] GPU compute capability {major}.x < 8.0 "
                    f"(pre-Ampere) — FlashAttention not supported, will use SDPA instead."
                )
                return False
        except Exception:
            return False

        try:
            import flash_attn
            return True
        except ImportError:
            return False

    def is_turbo_model(self) -> bool:
        """Check whether the currently loaded model is a turbo variant."""
        if self.config is None:
            return False
        return getattr(self.config, "is_turbo", False)
