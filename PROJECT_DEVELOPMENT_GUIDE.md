# 云集智能音乐创意台 - 项目开发指南

## 📋 目录

- [项目概述](#项目概述)
- [目录结构](#目录结构)
- [核心文件说明](#核心文件说明)
- [开发工作流](#开发工作流)
- [分支管理策略](#分支管理策略)
- [打包和发布](#打包和发布)
- [遗留文件清理](#遗留文件清理)

---

## 项目概述

**项目名称**: 云集智能音乐创意台 (ACE-Step)
**版本**: v2.8.3+
**核心功能**:
- AI音乐生成 (Gradio界面)
- LoRA模型训练器 (青龙训练器)
- 模型管理
- 环境管理

---

## 目录结构

```
云集智能音乐创意台/
├── .claude/                    # Claude AI技能配置 (保留)
├── .github/                    # GitHub配置 (保留)
├── .githooks/                  # Git钩子 (保留)
├── ace-step-ui/                # 青龙训练器前端 (保留)
├── acestep/                    # 核心Python包 (保留)
│   ├── api/                    # API服务
│   ├── core/                   # 核心功能
│   ├── dataset/                # 数据集处理
│   ├── third_parts/            # 第三方库
│   ├── training/               # 训练功能
│   ├── training_v2/            # 训练功能v2
│   └── ui/                     # UI组件
├── assets/                     # 静态资源 (保留)
├── docs/                       # 文档 (保留)
├── launcher/                   # 启动器模块 (核心)
│   ├── main.py                 # 启动器主程序 (核心)
│   └── version_manager.py      # 版本管理器 (核心)
├── scripts/                    # 工具脚本 (核心脚本保留)
├── presets/                    # 预设配置 (保留)
│
│ # ========== 核心启动脚本 ==========
├── 1、install-uv-qinglong.ps1  # 环境安装脚本 (核心)
├── 2、run_gradio.ps1          # Gradio界面启动 (核心)
├── 3、run_server.ps1          # API服务启动 (核心)
├── 4、run_npmgui.ps1          # 青龙训练器前端启动 (核心)
│
│ # ========== 打包工具 ==========
├── build-correct.py           # 正确的打包脚本 (核心)
│
│ # ========== 配置文件 ==========
├── .gitignore                 # Git忽略配置 (保留)
├── .gitmodules                # Git子模块 (保留)
├── .env.example               # 环境变量示例 (保留)
├── requirements.txt           # Python依赖 (保留)
├── AGENTS.md                  # AI代理指南 (保留)
├── CONTRIBUTING.md            # 贡献指南 (保留)
├── LICENSE                    # 许可证 (保留)
├── README.md                  # 项目说明 (保留)
├── SECURITY.md                # 安全说明 (保留)
├── ico.png                    # 图标文件 (保留)
```

---

## 核心文件说明

### 🚀 启动器模块 (`launcher/`)

| 文件 | 用途 | 说明 |
|------|------|------|
| `main.py` | 启动器主程序 | PyQt6 GUI界面，统一管理所有服务 |
| `version_manager.py` | 版本管理器 | Git版本切换和管理 |

### 📦 启动脚本 (根目录)

| 文件 | 用途 | 端口 |
|------|------|------|
| `1、install-uv-qinglong.ps1` | 环境安装 | - |
| `2、run_gradio.ps1` | 官方音乐演练场 | 7860 |
| `3、run_server.ps1` | 核心API服务 | 8001 |
| `4、run_npmgui.ps1` | 青龙训练器前端 | 3000 |

### 🔧 打包工具

| 文件 | 用途 |
|------|------|
| `build-correct.py` | 标准打包脚本 - **使用此脚本** |

### 📚 文档文件

| 文件 | 用途 |
|------|------|
| `README.md` | 项目主说明 |
| `AGENTS.md` | AI代理开发指南 |
| `CONTRIBUTING.md` | 贡献指南 |

---

## 开发工作流

### 1. 环境准备

```bash
# 1. 确保在main分支
git checkout main

# 2. 运行环境维护
# 启动器 -> 环境维护
```

### 2. 开发流程

#### 步骤1: 功能开发
- 在 `main` 分支进行日常开发
- 修改代码后测试
- 确保功能正常

#### 步骤2: 打包测试
```bash
# 运行标准打包脚本
python build-correct.py

# 脚本会自动:
# 1. 清理构建目录
# 2. 构建EXE文件
# 3. 检测Git更改
# 4. 自动提交并推送到main分支
```

#### 步骤3: 测试验证
- 使用生成的EXE文件测试
- 验证所有功能正常

---

## 分支管理策略

### 分支说明

| 分支 | 用途 | 操作方式 |
|------|------|----------|
| **main** | 开发分支 | 自动打包上传 |
| **beta** | 测试分支 | 手动合并和推送 |
| **stable** | 稳定版分支 | 手动合并和打标签 |

### 分支工作流

```
main (开发) 
  ↓ (测试通过后)
beta (测试)
  ↓ (充分测试后)
stable (稳定版 + 标签)
```

### 详细操作

#### 1. 开发分支 (main)
- **日常开发在此分支进行**
- 运行 `python build-correct.py` 会自动提交和推送
- 适用于快速迭代和功能开发

#### 2. 测试分支 (beta)
```bash
# 切换到beta分支
git checkout beta

# 合并main分支的更改
git merge main

# 手动测试
# ... 测试 ...

# 手动推送
git push origin beta
```

#### 3. 稳定版分支 (stable)
```bash
# 切换到stable分支
git checkout stable

# 合并beta分支的更改
git merge beta

# 打版本标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签
git push origin stable --tags
```

---

## 打包和发布

### 使用标准打包脚本

**唯一推荐使用**: `build-correct.py`

```bash
python build-correct.py
```

**脚本功能**:
1. ✅ 清理构建目录
2. ✅ 构建单文件EXE
3. ✅ 检测文件更改
4. ✅ 生成详细提交信息
5. ✅ 自动提交到Git
6. ✅ 自动推送到当前分支

### 输出位置

```
dist/
└── 云集智能音乐创意台-vYYYY.MM.DD.HHMM.exe
```

---

## 遗留文件清理

### ❌ 已废弃的文件 (将被清理)

#### 废弃的打包脚本
- ❌ `build-exe.bat`
- ❌ `build-single.bat`
- ❌ `build-versioned.bat`
- ❌ `build-with-version.py`
- ❌ `build-release.py`
- ❌ `create-v29-launcher.ps1`
- ❌ `create-launcher-with-model-download.ps1`
- ❌ `create-sfx.ps1`

#### 废弃的启动脚本
- ❌ `ace-step-launcher.ps1`
- ❌ `ace-step-ui-launcher.ps1`
- ❌ `launch-ace-step.ps1`
- ❌ `start-ace-step*.ps1` (多个版本)
- ❌ `start-ace-step*.bat` (多个版本)

#### 废弃的测试和临时脚本
- ❌ `demo-hybrid-version-manager.py`
- ❌ `test-version-list.py`
- ❌ `test-version-manager.bat`
- ❌ `test-hybrid-version-manager.bat`
- ❌ `check-before-build.bat`
- ❌ `quick-build.bat`
- ❌ `check-update.bat`
- ❌ `check-update.sh`
- ❌ `merge-config.bat`
- ❌ `quick-test.bat`
- ❌ `install_uv.bat`

#### 废弃的临时Python文件
- ❌ `fix_*.py` (多个修复脚本)
- ❌ `replace_*.py` (多个替换脚本)
- ❌ `restore_backup.py`
- ❌ `simple_replace.py`
- ❌ `create_zip.py`
- ❌ `list_endpoints.py`

#### 废弃的文档和临时文件
- ❌ `BUGFIX-*.md`
- ❌ `CHANGELOG-*.md`
- ❌ `EXE 打包完成总结.md`
- ❌ `INTEGRATED_PROJECT.md`
- ❌ `INTEGRATION_PLAN.md`
- ❌ `QUICKSTART-VERSION-MANAGER.md`
- ❌ `PROJECT_STRUCTURE.md` (被本文档替代)

#### launcher目录中的备份文件
- ❌ `launcher/main.py.backup`
- ❌ `launcher/main.py.backup2`
- ❌ `launcher/main.py.fixed`
- ❌ `launcher/main.py.git-original`
- ❌ `launcher/main.py.original`
- ❌ `launcher/build.bat`
- ❌ `launcher/build.py`

#### scripts目录中的废弃文件
- ❌ `scripts/cleanup*.py`
- ❌ `scripts/cleanup-report.txt`
- ❌ `scripts/create-versioned-launcher.py`
- ❌ `scripts/organize_project.py`
- ❌ `scripts/rename-launchers.py`
- ❌ `scripts/verify_structure.py`
- ❌ `scripts/项目结构优化报告.md`

### ✅ 保留的核心文件

**请确保以下文件永远不被删除**:

```
# 核心启动脚本
1、install-uv-qinglong.ps1
2、run_gradio.ps1
3、run_server.ps1
4、run_npmgui.ps1

# 打包工具
build-correct.py

# 启动器
launcher/main.py
launcher/version_manager.py

# 项目配置
.gitignore
.gitmodules
.env.example
requirements.txt
AGENTS.md
README.md
LICENSE
CONTRIBUTING.md
SECURITY.md
ico.png

# 核心包 (完整目录)
acestep/
ace-step-ui/
assets/
docs/
scripts/check_gpu.py
scripts/prepare_vae_calibration_data.py
scripts/profile_vram.py
scripts/lora_data_prepare/
scripts/start-all.ps1
scripts/new_pr_branch.ps1
```

---

## AI助手上下文指南

### 首次接触项目

当新的AI助手开始工作时，请按以下步骤操作:

1. **阅读本文档** - 了解项目结构
2. **查看 `launcher/main.py`** - 理解启动器逻辑
3. **查看 `build-correct.py`** - 理解打包流程
4. **不要修改核心启动脚本** - 除非明确要求

### 修改原则

- ✅ **只修改明确要求的文件**
- ✅ **使用标准打包脚本** `build-correct.py`
- ✅ **保持main分支用于开发**
- ✅ **充分测试后再合并到beta**
- ✅ **稳定版本才合并到stable**

### 避免的操作

- ❌ 不要创建新的临时修复脚本
- ❌ 不要修改多个启动脚本
- ❌ 不要使用废弃的打包方式
- ❌ 不要删除核心文件
- ❌ 不要跳过本文档直接开始编码

---

## 总结

本文档提供了:
- ✅ 清晰的项目结构说明
- ✅ 核心文件用途列表
- ✅ 标准化的开发工作流
- ✅ 明确的分支管理策略
- ✅ 完整的遗留文件清理清单
- ✅ AI助手上下文指南

**请确保所有开发工作都遵循本文档的规范！**

---

*最后更新: 2026-03-20*
