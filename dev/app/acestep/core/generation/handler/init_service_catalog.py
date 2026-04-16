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
        # Use root-level checkpoints directory for shared models
        import os
        import sys
        
        # Try multiple possible checkpoint directory locations
        possible_checkpoint_dirs = []
        
        # Get app directory (not project root)
        def _get_app_dir() -> str:
            # Get the directory of the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up 4 levels to reach the app directory
            app_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
            return app_dir
        
        app_dir = _get_app_dir()
        
        # Add possible checkpoint directory locations (models directory first, then checkpoints)
        possible_checkpoint_dirs.append(os.path.join(app_dir, "models"))
        possible_checkpoint_dirs.append(os.path.join(os.getcwd(), "models"))
        possible_checkpoint_dirs.append(os.path.join(app_dir, "checkpoints"))
        possible_checkpoint_dirs.append(os.path.join(os.getcwd(), "checkpoints"))
        
        print(f"[DEBUG] Possible checkpoint directories: {possible_checkpoint_dirs}")

        models = []
        checked_dirs = set()
        
        # Exclude non-DiT models
        exclude_models = ["Qwen3-Embedding-0.6B", "acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B", "acestep-5Hz-lm-4B", "vae"]
        
        for checkpoint_dir in possible_checkpoint_dirs:
            if checkpoint_dir in checked_dirs:
                continue
            checked_dirs.add(checkpoint_dir)
            
            print(f"[DEBUG] Scanning for models in: {checkpoint_dir}")
            
            if os.path.exists(checkpoint_dir):
                print(f"[DEBUG] Checkpoint directory exists")
                items = os.listdir(checkpoint_dir)
                print(f"[DEBUG] Found items: {items}")
                for item in items:
                    # Skip excluded models
                    if item in exclude_models:
                        print(f"[DEBUG] Skipping excluded model: {item}")
                        continue
                        
                    item_path = os.path.join(checkpoint_dir, item)
                    if os.path.isdir(item_path):
                        try:
                            has_files = os.listdir(item_path)
                            print(f"[DEBUG] Item {item} is a directory with files: {has_files}")
                            if has_files:
                                # Accept models with various naming patterns
                                has_config = os.path.exists(os.path.join(item_path, "config.json"))
                                print(f"[DEBUG] Item {item} has config.json: {has_config}")
                                # Only accept DiT models (not LM models)
                                if not item.endswith("-lm-0.6B") and not item.endswith("-lm-1.7B") and not item.endswith("-lm-4B"):
                                    if (item.startswith("acestep-") or 
                                        item.startswith("qinglong-") or 
                                        has_config):
                                        models.append(item)
                                        print(f"[DEBUG] Added model: {item}")
                        except Exception as e:
                            print(f"[DEBUG] Error checking item {item}: {e}")
            else:
                print(f"[DEBUG] Checkpoint directory does not exist")

        # Remove duplicates
        models = list(set(models))
        print(f"[DEBUG] Final models list: {models}")
        models.sort()
        return models

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
