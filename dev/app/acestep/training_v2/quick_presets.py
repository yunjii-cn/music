"""
Single source of truth for the "one-click training" (开箱即用) feature.

This module is *imported by both* the Python backend (``/v1/training/env-profile``
and the export step) and is mirrored by the TypeScript preset file on the
frontend (``ace-step-ui/data/qualityPresets.ts``) for UI preview / parameter
estimation.  Keep the two in sync.

Exposes:

* ``CAPTION_TEMPLATE``     -- default caption template (``{tag}`` placeholder)
* ``QUALITY_PRESETS``      -- fast / balanced / quality hyper-parameter presets
* ``VARIANT_DEFAULTS``     -- per base-model-variant timestep defaults
* ``classify_vram_tier``   -- map total VRAM (MiB) to a capability tier
* ``pick_variant``         -- choose the best downloaded variant
* ``resolve_training_params`` -- merge quality preset + advanced overrides
"""

from __future__ import annotations

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Caption template
# ---------------------------------------------------------------------------

#: Default caption template.  ``{tag}`` is replaced with the user's style tag.
CAPTION_TEMPLATE: str = "a {tag} style song"

# ---------------------------------------------------------------------------
# Quality presets (fast / balanced / quality)
# ---------------------------------------------------------------------------

#: ``rank`` / ``alpha`` are absolute LoRA hyper-parameters.
#: ``epochs`` is the default training epoch count.
#: ``lr`` is the learning rate, ``grad_checkpoint`` the default gradient
#: checkpointing flag for the tier.
QUALITY_PRESETS: Dict[str, Dict] = {
    "fast": {
        "rank": 32,
        "alpha": 64,
        "epochs": 300,
        "lr": 3e-4,
        "grad_checkpoint": False,
        "label": "fast",
        "description": "Fastest turnaround, lower fidelity.",
    },
    "balanced": {
        "rank": 64,
        "alpha": 128,
        "epochs": 600,
        "lr": 3e-4,
        "grad_checkpoint": False,
        "label": "balanced",
        "description": "Good balance of speed and quality.",
    },
    "quality": {
        "rank": 128,
        "alpha": 256,
        "epochs": 1000,
        "lr": 2e-4,
        "grad_checkpoint": True,
        "label": "quality",
        "description": "Best fidelity, longest training time.",
    },
}

# ---------------------------------------------------------------------------
# Per base-model-variant timestep defaults
# ---------------------------------------------------------------------------

#: Turbo uses a short 8-step schedule with a high shift; base / sft use the
#: full 50-step schedule with a low shift.
VARIANT_DEFAULTS: Dict[str, Dict] = {
    "turbo": {"shift": 3.0, "steps": 8},
    "base": {"shift": 1.0, "steps": 50},
    "sft": {"shift": 1.0, "steps": 50},
}

#: Preference order when auto-selecting the best downloaded variant.
_VARIANT_PREFERENCE: List[str] = ["sft", "base", "turbo"]

# Known variants (used to compute ``missing_variants``).
ALL_VARIANTS: List[str] = ["turbo", "base", "sft"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def classify_vram_tier(vram_total_mb: Optional[float]) -> str:
    """Map total VRAM (MiB) to a capability tier.

    * ``full`` : >= 16 GiB  -- full-precision training available
    * ``fp8``  : 8-12 GiB   -- use FP8 + gradient checkpointing
    * ``low``  : < 8 GiB    -- not enough VRAM for reliable training
    * ``unknown`` : VRAM could not be determined (CPU / MPS)
    """
    if vram_total_mb is None:
        return "unknown"
    gb = vram_total_mb / 1024.0
    if gb >= 16:
        return "full"
    if gb >= 8:
        return "fp8"
    return "low"


def pick_variant(downloaded_variants: Optional[List[str]], tier: str = "full") -> Optional[str]:
    """Pick the best available variant from *downloaded_variants*.

    Preference order is ``sft > base > turbo``.  Returns ``None`` when nothing
    suitable is downloaded.
    """
    have = set(downloaded_variants or [])
    for variant in _VARIANT_PREFERENCE:
        if variant in have:
            return variant
    return None


def resolve_training_params(
    quality: str,
    advanced: Optional[Dict] = None,
    variant: Optional[str] = None,
) -> Dict:
    """Merge the quality preset with optional advanced overrides + variant defaults.

    Returns a flat dict suitable for the ``/v1/training/start`` payload (minus
    ``tensor_dir`` / ``lora_output_dir`` which the orchestrator supplies).
    """
    preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["balanced"])
    variant_defaults = VARIANT_DEFAULTS.get(variant or "turbo", VARIANT_DEFAULTS["turbo"])

    params: Dict = {
        "lora_rank": preset["rank"],
        "lora_alpha": preset["alpha"],
        "lora_dropout": 0.1,
        "learning_rate": preset["lr"],
        "train_epochs": preset["epochs"],
        "train_batch_size": 1,
        "gradient_accumulation": 4,
        "save_every_n_epochs": 50,
        "training_shift": variant_defaults["shift"],
        "training_seed": 42,
        "use_fp8": False,
        "gradient_checkpointing": preset["grad_checkpoint"],
    }

    adv = advanced or {}
    for key in (
        "lora_rank",
        "lora_alpha",
        "lora_dropout",
        "learning_rate",
        "train_epochs",
        "train_batch_size",
        "gradient_accumulation",
        "save_every_n_epochs",
        "training_shift",
        "training_seed",
        "use_fp8",
        "gradient_checkpointing",
    ):
        if adv.get(key) is not None:
            params[key] = adv[key]

    # VRAM-driven adjustments when the caller did not force fp8 / checkpointing.
    if tier == "fp8":
        params["use_fp8"] = adv.get("use_fp8", True)
        params["gradient_checkpointing"] = adv.get("gradient_checkpointing", True)
    elif tier == "low":
        params["use_fp8"] = adv.get("use_fp8", True)
        params["gradient_checkpointing"] = adv.get("gradient_checkpointing", True)

    return params
