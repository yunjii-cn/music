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
        """Scan and return all model directory names that are valid ACE-Step DiT models.
        
        Uses the official `check_model_exists` function from model_downloader.py
        to ensure consistent validation logic with the model management interface.
        """
        import sys
        from pathlib import Path
        
        try:
            # Use official model validation logic
            from acestep.model_downloader import get_checkpoints_dir, check_model_exists, SUBMODEL_REGISTRY
            
            checkpoints_dir = get_checkpoints_dir()
            logger.info(f"[ModelScan] Using checkpoints_dir: {checkpoints_dir}")
            
            # List all DiT models from SUBMODEL_REGISTRY and check if they exist
            models = []
            
            # Check all registered models
            for model_name in SUBMODEL_REGISTRY.keys():
                # Skip LM models - we only want DiT models
                if "lm" in model_name.lower():
                    continue
                
                # Use official check_model_exists function
                if check_model_exists(model_name, checkpoints_dir):
                    models.append(model_name)
                    logger.info(f"[ModelScan] ✅ Added valid model: {model_name}")
                else:
                    logger.info(f"[ModelScan] ❌ Skipping invalid/missing model: {model_name}")
            
            # Also check for acestep-v15-turbo which might come from main model
            main_model_components = ["acestep-v15-turbo"]
            for model_name in main_model_components:
                if model_name not in models and check_model_exists(model_name, checkpoints_dir):
                    models.append(model_name)
                    logger.info(f"[ModelScan] ✅ Added main model component: {model_name}")
            
            models.sort()
            logger.info(f"[ModelScan] Final valid models list: {models}")
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
