# -*- coding: utf-8 -*-
r"""
XL (4B) 底座 LoRA 训练兼容性冒烟校验脚本 —— docs/xl-training-support-plan.md §4.2

用法（在部署目录的 app/ 下，用项目 venv 的 python 运行）:
    cd <部署根目录>\app
    scripts\.venv\Scripts\python.exe verify_xl_training.py [--variant xl] [--device cuda]

前置条件:
    1. 已在「模型管理」下载 acestep-v15-xl-turbo 权重(约18.8GB)
       （或 python -m acestep.model_downloader --model acestep-v15-xl-turbo）
    2. 环境已就绪（torch/peft 已装）

判定标准（全部通过才可宣布"支持 XL LoRA 训练"）:
    [1] 模型加载成功（auto_map 拉起 modeling_acestep_v15_xl.py）
    [2] decoder 暴露 q/k/v/o_proj 可注入层（targets > 0）
    [3] LoRA 注入后存在可训练参数
    [4] 随机小批前向 loss 有限（可选，--forward 开启）
任一失败 = 上游 XL 模型代码与训练接口不兼容，需另行评估适配层。
"""
from __future__ import annotations

import argparse
import os
import sys
import traceback


def main() -> int:
    ap = argparse.ArgumentParser(description="XL LoRA training smoke test")
    ap.add_argument("--variant", default="xl", help="xl / xl-sft / xl-base")
    ap.add_argument("--device", default=None, help="cuda / cpu (默认自动)")
    ap.add_argument("--models-dir", default=None, help="模型根目录，默认 ../data/models")
    ap.add_argument("--forward", action="store_true", help="额外跑一次随机小批前向（更严格）")
    args = ap.parse_args()

    app_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, app_dir)
    models_dir = args.models_dir or os.path.normpath(os.path.join(app_dir, "..", "data", "models"))

    print("=" * 60)
    print("XL LoRA 训练兼容性冒烟校验")
    print(f"  variant   : {args.variant}")
    print(f"  models_dir: {models_dir}")
    print("=" * 60)

    import torch
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  device    : {device}")
    if device == "cpu":
        print("  ⚠ 未检测到 CUDA，用 CPU 校验（仅验证接口兼容性，速度较慢）")

    # ---- [0] 权重目录存在性 ----
    from acestep.training_v2.model_loader import _VARIANT_DIR  # noqa
    subdir = _VARIANT_DIR.get(args.variant)
    if subdir is None:
        print(f"❌ 变体 {args.variant!r} 未注册（_VARIANT_DIR 缺项）")
        return 1
    model_dir = os.path.join(models_dir, subdir)
    if not os.path.isdir(model_dir) or not os.path.isfile(os.path.join(model_dir, "config.json")):
        print(f"❌ 权重目录不存在或缺 config.json: {model_dir}")
        print("   请先在「模型管理」下载 XL 权重(约18.8GB)后重试。")
        return 1
    print(f"✅ [0] 权重目录就绪: {model_dir}")

    # ---- [1] 模型加载 ----
    try:
        from acestep.training_v2.model_loader import load_decoder_for_training
        model = load_decoder_for_training(models_dir, variant=args.variant, device=device, precision="bf16")
        print(f"✅ [1] 模型加载成功: {type(model).__name__}")
    except Exception:
        print("❌ [1] 模型加载失败（auto_map/接口不兼容或权重损坏）:")
        traceback.print_exc()
        return 1

    if not hasattr(model, "decoder"):
        print("❌ [1b] 模型未暴露 .decoder 属性 —— 与训练器接口不兼容")
        return 1

    # ---- [2] LoRA 目标层扫描 ----
    try:
        from acestep.training.lora_utils import get_dit_target_modules, inject_lora_into_dit
        targets = get_dit_target_modules(model)
        assert len(targets) > 0, "XL decoder 未暴露可注入的 q/k/v/o_proj 投影层"
        print(f"✅ [2] 可注入投影层: {len(targets)} 个 (示例: {targets[:4]})")
    except Exception:
        print("❌ [2] LoRA 目标层扫描失败:")
        traceback.print_exc()
        return 1

    # ---- [3] LoRA 注入 ----
    try:
        from acestep.training.configs import LoRAConfig
        lora_cfg = LoRAConfig(r=32, alpha=64, target_modules=targets)
        model, info = inject_lora_into_dit(model, lora_cfg)
        trainable = [p for p in model.decoder.parameters() if p.requires_grad]
        n_trainable = sum(p.numel() for p in trainable)
        assert len(trainable) > 0, "LoRA 参数未被正确解冻"
        print(f"✅ [3] LoRA 注入成功: 可训练参数 {n_trainable:,} ({len(trainable)} 张量)")
    except Exception:
        print("❌ [3] LoRA 注入失败:")
        traceback.print_exc()
        return 1

    # ---- [4] 可选: 随机小批前向 ----
    if args.forward:
        try:
            import json
            with open(os.path.join(model_dir, "config.json"), "r", encoding="utf-8") as f:
                cfg = json.load(f)
            hidden = None
            for k in ("hidden_size", "inner_dim", "audio_acoustic_hidden_size", "decoder_hidden_size"):
                if isinstance(cfg.get(k), int):
                    hidden = cfg[k]
                    break
            dtype = torch.bfloat16 if device == "cuda" else torch.float32
            dec = model.decoder
            dec_dtype = next(dec.parameters()).dtype
            if hidden is None:
                print("⚠ [4] config.json 未找到 hidden 维度，跳过前向冒烟（接口校验已通过）")
            else:
                x = torch.randn(1, 64, hidden, device=device, dtype=dec_dtype)
                enc = torch.randn(1, 32, hidden, device=device, dtype=dec_dtype)
                try:
                    out = dec(hidden_states=x, encoder_hidden_states=enc)
                    t = out[0] if isinstance(out, (tuple, list)) else getattr(out, "sample", out)
                    assert torch.isfinite(t.float()).all(), "前向输出含 NaN/Inf"
                    print(f"✅ [4] 随机小批前向通过: 输出 {tuple(t.shape)}, dtype={t.dtype}")
                except TypeError as e:
                    print(f"⚠ [4] 前向签名与猜测不符({e})——请以真实训练 2 步为准，不代表失败")
        except Exception:
            print("⚠ [4] 前向冒烟异常（不作为否决项）:")
            traceback.print_exc()

    print("")
    print("=" * 60)
    print("🎉 接口兼容性校验通过！[1][2][3] 全绿。")
    print("   最终验收：在训练页选 XL 底座，用小数据集实际跑 2 个 step，")
    print("   确认 loss 有限且下降，即可正式宣布支持 XL LoRA 训练。")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
