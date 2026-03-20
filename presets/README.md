# 预设包目录

这个目录用于存放预编译的Python包（.whl文件），可以加速环境部署。

## 使用方法

1. 将预编译的.whl文件放在此目录中
2. 环境维护时会优先使用本地预编译包

## 推荐的预编译包

### flash-attn
根据不同的CUDA版本和Python版本，预编译相应的flash-attn包：

- `flash_attn-2.8.3+cu118torch2.2.0cxx11abiTRUE-cp310-cp310-win_amd64.whl`
- `flash_attn-2.8.3+cu121torch2.3.0cxx11abiTRUE-cp311-cp311-win_amd64.whl`
- `flash_attn-2.8.3+cu128torch2.9.0cxx11abiTRUE-cp312-cp312-win_amd64.whl`

### 其他可能需要预编译的包
- `xformers`
- `bitsandbytes`
- `apex`

## 智能包选择策略

环境维护会根据以下信息自动选择合适的包：
1. 检测到的NVIDIA GPU型号
2. CUDA版本
3. Python版本
4. PyTorch版本
5. 网络条件（国内/国外）

## 国内镜像源

为了加速下载，环境维护会优先使用以下国内镜像源：
- PyPI: https://pypi.tuna.tsinghua.edu.cn/simple
- HuggingFace: https://hf-mirror.com
- ModelScope: https://www.modelscope.cn
