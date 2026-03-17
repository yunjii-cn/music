# 青龙音乐训练器项目结构说明

本文档详细描述了青龙音乐训练器（Qinglong Music Trainer）的项目结构，帮助开发者了解项目的组织方式和各组件的功能。

## 项目根目录结构

```
qinglong-music-trainer-2.8.3/
├── ace-step-ui/           # 前端界面代码
├── acestep/              # 核心音乐生成引擎
├── assets/               # 静态资源文件
├── BAK/                  # 备份目录，存放旧版本文件
├── build/                # 构建输出目录
├── config/               # 配置文件目录
├── data/                 # 数据目录
├── docs/                 # 项目文档
├── launcher/             # 启动器相关文件
├── models/               # 模型文件目录
├── output/               # 输出目录
├── scripts/              # 脚本文件
├── shared/               # 共享代码
├── .env                  # 环境配置文件
├── .env.example          # 环境配置示例
├── .gitignore            # Git忽略文件配置
├── AGENTS.md             # AI代理开发指南
├── CONTRIBUTING.md       # 贡献指南
├── INTEGRATED_PROJECT.md # 集成项目说明
├── INTEGRATION_PLAN.md   # 集成计划
├── LICENSE               # 许可证文件
├── README.md             # 项目说明文件
├── SECURITY.md           # 安全说明
├── ace-step-launcher.ps1 # ACE-Step启动脚本
└── ace-step-ui-launcher.ps1 # ACE-Step UI启动脚本
```

## 主要目录说明

### ace-step-ui/
前端界面代码，基于React和TypeScript开发，提供用户交互界面。

**子目录结构**：
- `components/` - React组件
- `context/` - React上下文
- `data/` - 前端数据
- `i18n/` - 国际化文件
- `server/` - 前端服务器代码

### acestep/
核心音乐生成引擎，包含模型定义、推理逻辑等。

**子目录结构**：
- `core/` - 核心功能模块
- `models/` - 模型定义
- `api/` - API接口
- `ui/` - 界面相关代码
- `training/` - 训练相关代码
- `third_parts/` - 第三方库

### models/
模型文件目录，按照模型类型组织。

**子目录结构**：
- `dit/` - DiT（Diffusion Transformer）模型
  - `acestep-v15-base/` - 基础模型
  - `acestep-v15-sft/` - 监督微调模型
  - `acestep-v15-turbo/` -  turbo模型
  - `acestep-v15-turbo-continuous/` - 连续生成模型
  - `acestep-v15-turbo-shift1/` - 位移模型1
  - `acestep-v15-turbo-shift3/` - 位移模型3
- `lm/` - 语言模型
  - `acestep-5Hz-lm-0.6B/` - 0.6B语言模型
  - `acestep-5Hz-lm-1.7B/` - 1.7B语言模型
  - `acestep-5Hz-lm-4B/` - 4B语言模型
- `embedding/` - 嵌入模型
  - `Qwen3-Embedding-0.6B/` - Qwen3嵌入模型
- `vae/` - VAE模型

### docs/
项目文档，包含使用指南、API文档等。

**子目录结构**：
- `en/` - 英文文档
- `zh/` - 中文文档
- `ja/` - 日文文档
- `ko/` - 韩文文档
- `sidestep/` - SideStep相关文档

### scripts/
脚本文件，包含各种工具脚本。

### shared/
共享代码，包含配置管理等通用功能。

## 配置文件

- `.env` - 环境配置文件，包含API密钥、路径配置等
- `config/config.json` - 项目配置文件

## 启动方式

### 启动ACE-Step核心服务
```powershell
./ace-step-launcher.ps1
```

### 启动ACE-Step UI界面
```powershell
./ace-step-ui-launcher.ps1
```

## 模型管理

模型文件存放在 `models/` 目录下，按照模型类型进行组织。模型文件较大，建议通过Git LFS或其他方式管理。

## 输出文件

生成的音乐文件和其他输出文件存放在 `output/` 目录下。

## 备份

备份文件存放在 `BAK/` 目录下，包括旧版本的代码和配置文件。

## 开发指南

1. **环境配置**：复制 `.env.example` 为 `.env` 并填写相关配置
2. **依赖安装**：使用 uv 或 pip 安装依赖
3. **启动开发服务器**：运行启动脚本
4. **代码规范**：遵循项目的代码风格和规范

## 安全注意事项

- 不要将API密钥等敏感信息提交到版本控制系统
- 定期更新依赖库以修复安全漏洞
- 遵循安全最佳实践

## 贡献指南

详见 `CONTRIBUTING.md` 文件。

---

本文档由AI生成，如有更新请及时修改。
