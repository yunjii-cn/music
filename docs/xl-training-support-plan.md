# 改造方案：支持在 XL (acestep-v15-xl-turbo) 底座上训练 LoRA

> 状态：**方案文档（未实施）**。用户已确认先出方案、暂不改动代码、暂不下载权重。
> 调研日期：2026-07-19。训练机显存：**24GB**（宽裕，见 §5）。

---

## 1. 背景与目标

用户希望用 `acestep-v15-xl-turbo`（4B DiT，8 步蒸馏）作为 LoRA 训练底座，而非当前的 1.5B 家族（`acestep-v15-turbo` / `base` / `sft`）。

**核心结论：可以改造，且工作量主要是"变体注册"（低风险加法），不是重写训练数学。** 真正的不确定性在于 XL 模型代码与现有训练接口的兼容性，这部分无法纯静态验证，需在下载后做一次实跑校验（见 §4）。

> 前置提醒：现有的、在 1.5B 上训出来的 LoRA **不能复用到 XL**（隐藏维度/层数不同，维度对不上）。要在 XL 上获得专属 LoRA，必须在 XL 底座上**重训**一个，无法迁移。

---

## 2. 可行性依据（为什么是"架构无感"）

我逐层核对了训练链路，**三个关键环节都没有把底座架构写死**：

| 环节 | 位置 | 现状 | 是否架构无感 |
|---|---|---|---|
| 底座加载 | `training_v2/model_loader.py:load_decoder_for_training` | `AutoModel.from_pretrained(..., trust_remote_code=True)` + HF `auto_map` 自动实例化 | ✅ 靠 `config.json` 推断类，不写死 `AceStepConditionGenerationModel` |
| LoRA 注入 | `training/lora_utils.py:get_dit_target_modules` | 按 `q/k/v/o_proj` **子串**动态扫 `model.decoder.named_modules()` 找 `nn.Linear` | ✅ 1.5B / 4B 同样适用，无硬编码层数 |
| 训练器 | `training_v2/trainer_fixed.py` / `fixed_lora_module.py` | 只碰 `.model` / `.model.decoder` / `.forward(hidden_states, encoder_hidden_states, ...)` | ✅ 不关心底座多大 |

**关键佐证**：XL 的模型代码 `modeling_acestep_v15_xl.py` 已被 `model_downloader.py:410` 登记为权重同包文件（`config.json` / `model.safetensors` / `modeling_acestep_v15_xl.py`），下载后由 `auto_map` 在加载时自动拉取并实例化。它**不在本仓库**，这就是兼容性无法静态保证的根本原因（详见 §4 风险）。

---

## 3. 改造清单（逐文件，均为加法）

> 所有改动都不触碰训练数学，只做"让 `variant='xl'` 一路透传并正确解析"的注册工作。

### 3.1 `dev/app/acestep/training_v2/model_loader.py`
`_VARIANT_DIR`（约 L54）目前只有 turbo/base/sft，补 XL 三件套：
```python
_VARIANT_DIR = {
    "turbo":   "acestep-v15-turbo",
    "base":    "acestep-v15-base",
    "sft":     "acestep-v15-sft",
    "xl":      "acestep-v15-xl-turbo",   # 默认 XL = turbo 蒸馏版
    "xl-sft":  "acestep-v15-xl-sft",
    "xl-base": "acestep-v15-xl-base",
}
```
> 注意：`load_silence_latent`（L346）有兜底 `_VARIANT_DIR.get(variant, f"acestep-v15-{variant}")`——裸 `"xl"` 会被拼成不存在的 `acestep-v15-xl`，故必须显式登记。登记后 `_resolve_model_dir` 即可定位 `dev/data/models/acestep-v15-xl-turbo` 目录。

### 3.2 `dev/app/acestep/training_v2/quick_presets.py`
- `VARIANT_DEFAULTS`（L74）补 XL（XL-turbo 同 8 步高 shift；xl-sft/xl-base 同 50 步低 shift）：
```python
"xl":      {"shift": 3.0, "steps": 8},
"xl-sft":  {"shift": 1.0, "steps": 50},
"xl-base": {"shift": 1.0, "steps": 50},
```
- `ALL_VARIANTS`（L84）补 `"xl"`（及 `xl-sft` / `xl-base`，影响"缺失变体"提示）。
- `_VARIANT_PREFERENCE`（L81）按质量档位插入（如 `xl-sft` 靠近 `sft`、`xl` 靠近 `turbo`）。

### 3.3 `dev/app/acestep/training_v2/model_discovery.py`
`detect_base_model`（L106）目前 `is_turbo` 为真就返回 `"turbo"`，会把 XL-turbo 误判成 `turbo`。**必须在 turbo 判断前加 xl 名称分支**：
```python
name_lower = dir_name.lower()
if "xl" in name_lower:        # acestep-v15-xl-turbo / xl-sft / xl-base
    return "xl"
if config.get("is_turbo", False):
    return "turbo"
for variant in ("turbo", "base", "sft"):
    if variant in name_lower:
        return variant
return "unknown"
```
> 同样地，`_BASE_DEFAULTS`（L24）与 `get_base_defaults`（L125）建议补 `xl` 项（推理时 timestep 默认值），否则回退到 `base`（50 步），对 XL-turbo 不准确。CLI 的 `cli/config_builder.py:86` 也走 `get_base_defaults`，故此处一并补。

### 3.4 配置 / CLI 透传
- `training_v2/configs.py:TrainingConfigV2`（L89）确认存在 `model_variant` 字段且为自由字符串（当前无 `assert` 拒绝，已 grep 确认全仓无 `variant in (...)` 白名单式硬校验，仅 `train_vanilla.py:96` 有 `if args.model_variant in ("base","sft")` 分支，非拒绝）。
- `cli/config_builder.py`：确认 `argparse` 的 `--model-variant` 没有 `choices=[...]` 限制；若有则放宽。
- 后端 `train_api_service.py`：grep 未发现对 `variant` 的硬编码校验，请求体的 `model_variant` 字段应直接透传到 `TrainingConfigV2`。建议顺手确认该 API 不限制取值。

### 3.5 前端（两份镜像）
- `dev/app/ace-step-ui/data/qualityPresets.ts`（L57-59）的 `VARIANT_DEFAULTS` 补 xl 三件套（与 §3.2 保持一致）。
- `dev/app/ace-step-ui/server/src/data/qualityPresets.ts`（L58-60）同一处镜像，必须同步改。
- **底座选择 UI**：下拉项来源应为后端 `/v1/training/env-profile`（读 `ALL_VARIANTS`）。§3.2 改完后 XL 会自动出现在选项里；需验证该下拉确实从 API 动态渲染、而非前端写死列表。

### 3.6 触发 XL 权重下载（~18.8GB bf16）
权重定义已就绪（`model_downloader.py:40/348/409`）。目标目录 `dev/data/models/acestep-v15-xl-turbo`（app 实际读取路径，见日志 2026-07-19）。触发方式任选其一：
- 模型管理栏"重新下载"选 XL 变体；
- 或直接 `python -m acestep.model_downloader --model acestep-v15-xl-turbo`（cwd=`dev/app`）。

---

## 4. 风险与去风险（"官方没支持"的真正含义）

### 4.1 风险点
**XL 模型代码不在本仓库**，训练时从 HF `ACE-Step/acestep-v15-xl-turbo` 现拉（`modeling_acestep_v15_xl.py`）。无法静态保证它与现有训练接口一致：
1. `forward()` 签名必须匹配 `FixedLoRAModule.training_step` 的调用（`hidden_states=xt, encoder_hidden_states=..., context_latents=..., attention_mask=..., encoder_attention_mask=...`）；
2. 必须暴露 `.decoder` 属性，且 decoder 内含 `q/k/v/o_proj` 的 `nn.Linear` 层（否则 LoRA 注入为空或错层）。

若上游 XL 实现与 1.5B 接口有差异，**表现将是运行时崩溃，或静默产出坏适配器（不报错但训了个寂寞）**。ACE-Step 官方未验证过 XL+LoRA，此兼容性为未证实项。

### 4.2 去风险：实跑 2 步冒烟测试（验收门槛）
下载 + 改码后，**不立即宣布"支持"**，先做最小实跑校验（约几分钟）：
```python
# 伪代码，cwd=dev/app，venv python
from acestep.training_v2.model_loader import load_decoder_for_training
from acestep.training.lora_utils import get_dit_target_modules, inject_lora_into_dit
from acestep.training.configs import LoRAConfig

model = load_decoder_for_training(dev_data_models, variant="xl", device="cuda", precision="bf16")
targets = get_dit_target_modules(model)          # 期望 > 0，且数量 ≈ XL decoder 的 q/k/v/o_proj 数
assert len(targets) > 0, "XL decoder 未暴露可注入的投影层"

lora_cfg = LoRAConfig(rank=32, alpha=64, target_modules=targets)
peft_model, info = inject_lora_into_dit(model, lora_cfg)
trainable = [p for p in peft_model.decoder.parameters() if p.requires_grad]
assert len(trainable) > 0, "LoRA 参数未被正确解冻"

# 用小样本跑 1~2 个 training_step，检查 loss 有限且下降
loss = module.training_step(tiny_batch)
assert torch.isfinite(loss), "loss 非有限 —— 前向/接口不匹配"
```
**判定标准**：上述断言全过 + 跑 2 步后 loss 有限且趋于下降 → 方可宣布"支持 XL 训练"。任一断言失败 = 兼容性未通过，需向上游报告或改造 `modeling_acestep_v15_xl.py` 的适配层（超出本次注册范围，需另行评估）。

---

## 5. 显存评估（用户 24GB → 宽裕）

- XL 4B bf16 权重 ≈ 18.8GB。
- 24GB 显存下：bf16 权重 + 优化器状态 + 激活值，**开启梯度检查点 + 编码器卸载**即可舒适容纳，留有约 4–5GB 余量；甚至可不用 fp8。
- 对比：本项目 `classify_vram_tier` 的门槛是 `full≥16GB / fp8 8–12GB / low<8GB`，24GB 落在 `full` 档，无需强制 fp8。
- 结论：**硬件门槛已过，改造可行性的唯一悬念在 §4.1 的接口兼容性**。

---

## 6. 实施顺序建议

1. **代码注册**（§3.1–§3.5，全加法，低风险）→ 静态自检（`py_compile` + 确认无白名单拦截）。
2. **下载 XL 权重**（§3.6，~18.8GB，需联网，耗时最长，可并行）。
3. **2 步冒烟校验**（§4.2）→ 这是"是否真支持"的唯一证据。
4. **通过则宣布支持**；**不通过则定位是 XL 代码接口差异还是注册遗漏**，给出后续改造量估算。

---

## 7. 回滚方案

- 代码改动全部为加法 / 字典新增，回滚 = `git checkout` 相关文件，无副作用。
- XL 权重位于独立目录 `dev/data/models/acestep-v15-xl-*`，仅在用户主动选择 `variant="xl"` 时才被引用；不删也不影响现有 1.5B 训练链路。如需回收空间，直接删除该目录即可。

---

## 8. 改造量小结

| 项 | 规模 | 风险 |
|---|---|---|
| 变体注册（loader / presets / discovery / configs） | ~6 处字典/分支新增 | 低 |
| 前端镜像 + 底座下拉 | 2 份 ts + 1 个 UI 校验 | 低 |
| XL 权重下载 | 1 条命令，~18.8GB | 低（仅耗时/网络） |
| 接口兼容性验证 | 2 步冒烟脚本 | **中（依赖上游代码）** |
| 若兼容性不通过需适配层 | 未定（依上游实现） | 中–高（超出本次范围） |

**一句话**：代码侧我能稳稳改完（低风险），但"XL 上 LoRA 到底训不训得动"只能在你本机下完 18.8GB 跑一次 2 步校验才能盖棺定论——这正是官方尚未支持的部分。
