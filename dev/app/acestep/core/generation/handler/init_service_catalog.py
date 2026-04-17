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

    def get_available_acestep_v15_models(self) -> List[str]:
        """Scan and return all model directory names that are valid ACE-Step DiT models."""
        import sys
        from pathlib import Path
        
        # 统一使用model_downloader.py的逻辑
        try:
            from acestep.model_downloader import list_available_models, get_checkpoints_dir, check_model_exists
            
            checkpoints_dir = get_checkpoints_dir()
            logger.info(f"[ModelScan] Using checkpoints_dir: {checkpoints_dir}")
            
            # 列出所有可用模型，但只返回DiT模型
            exclude_models = ["Qwen3-Embedding-0.6B", "acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B", "acestep-5Hz-lm-4B", "vae"]
            
            models = []
            
            # 扫描checkpoints目录
            if checkpoints_dir.exists():
                logger.info(f"[ModelScan] Scanning: {checkpoints_dir}")
                for item in checkpoints_dir.iterdir():
                    if item.is_dir():
                        model_name = item.name
                        if model_name in exclude_models:
                            logger.info(f"[ModelScan] Skipping excluded: {model_name}")
                            continue
                        
                        # 检查是否是有效的模型目录（使用check_model_exists验证）
                        if check_model_exists(model_name, checkpoints_dir):
                            # 只添加DiT模型（排除LM模型）
                            if not model_name.endswith("-lm-0.6B") and not model_name.endswith("-lm-1.7B") and not model_name.endswith("-lm-4B"):
                                models.append(model_name)
                                logger.info(f"[ModelScan] ✅ Added model: {model_name}")
            
            # 也尝试检查models目录（如果存在）
            project_root = Path(__file__).resolve().parent.parent.parent
            models_dir = project_root / "models"
            if models_dir.exists() and models_dir != checkpoints_dir:
                logger.info(f"[ModelScan] Also scanning models_dir: {models_dir}")
                for item in models_dir.iterdir():
                    if item.is_dir():
                        model_name = item.name
                        if model_name in exclude_models:
                            continue
                        if check_model_exists(model_name, models_dir):
                            if not model_name.endswith("-lm-0.6B") and not model_name.endswith("-lm-1.7B") and not model_name.endswith("-lm-4B"):
                                if model_name not in models:
                                    models.append(model_name)
                                    logger.info(f"[ModelScan] ✅ Added model from models_dir: {model_name}")
            
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
