# 云集智能音乐创意台 - 项目开发指南

> ⚠️ **AI 开发助手必读！** 请严格按照本文档的规范进行所有开发操作！

---

## 📂 三目录核心结构

项目采用 **dev / dist / test** 三目录结构，各司其职：

```
云集智能音乐创意台/
├── dev/            # ⭐ 开发目录 — 源代码（Git管理）
├── dist/           # ⭐ 分发目录 — EXE打包输出（Git不管理）
└── test/           # ⭐ 测试目录 — 测试脚本与测试文件
```

### dev/ — 开发目录

- **定位**：唯一的日常开发工作区，所有源代码编写和修改在此进行
- **Git**：✅ Git管理，推送到远程仓库

```
dev/
├── app/                              # 项目源代码
│   ├── main.py                       # 启动器主程序（PyQt6 GUI）
│   ├── version_manager.py            # 版本管理器
│   ├── build-version.py              # EXE构建脚本
│   ├── icon.ico / ico.png            # 应用图标
│   ├── requirements.txt              # Python依赖
│   ├── version_history.json          # 版本历史
│   ├── versions.json                 # 版本列表
│   ├── ace-step-ui/                  # 青龙训练器前端
│   ├── acestep/                      # 核心后端
│   └── scripts/                      # ⚠️ 只放启动脚本（不含重复项目文件！）
│       ├── 1、install-uv-qinglong.ps1
│       ├── 2、run_gradio.ps1
│       ├── 3、run_server.ps1
│       ├── 4、run_npmgui.ps1
│       ├── 5、run_qinglong_backend.ps1
│       └── 6、run_qinglong_frontend.ps1
├── data/                             # 用户数据（Git不管理）
└── temp/                             # 临时文件（Git不管理）
```

### dist/ — 分发目录

- **定位**：EXE打包输出目录，`build-version.py` 执行后 EXE 自动输出到此
- **Git**：❌ Git不管理，被 `.gitignore` 忽略

```
dist/
└── 云集智能音乐创意台-vYYYY.MM.DD.HHMM.exe
```

### test/ — 测试目录

- **定位**：独立的测试工作区，存放所有测试脚本、测试配置和测试数据
- **Git**：✅ 推荐Git管理（测试代码纳入版本管理）

```
test/
├── test_*.py                         # 测试脚本（以 test_ 前缀命名）
├── test_*.bat                        # 批处理测试脚本
├── fixtures/                         # 测试数据/夹具
└── outputs/                          # 测试运行输出（Git不管理）
```

---

## 🎯 核心原则

1. **日常开发只在 dev/app/ 目录进行** — 不要直接修改其他目录
2. **EXE自动输出到 dist/ 目录** — 构建脚本自动写入，不要在 dev/ 目录放置EXE文件
3. **测试文件统一放到 test/ 目录** — 不要在 dev/ 目录散落测试文件
4. **ver/ 是正式版本分发目录** — 由开发者手动放入经过验证的稳定版EXE，构建脚本不写入
5. **dev/ 目录是 Git 管理的纯净整合包** — 推送到远程仓库
6. **build/ 目录保存版本历史** — 用于回滚和版本对比
7. **pack/ 目录存放发布给用户的纯净整合包**

---

## 📝 标准开发工作流

### 完整流程：dev → test → dist

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    dev/      │ ───→ │    test/     │ ───→ │    dist/     │
│  开发编码     │      │  测试验证     │      │  EXE打包输出  │
└──────────────┘      └──────────────┘      └──────────────┘
```

### 第一步：日常开发（在 dev/app/ 修改）
```
✅ 在 dev/app/ 目录修改和测试代码
   - dev/app/ 是唯一开发测试目录
   - 直接修改 app/ 下的文件
   - 不需要频繁创建版本
```

### 第二步：编写/运行测试（在 test/ 目录）
```
✅ 测试脚本放到 test/ 目录
   - 测试脚本以 test_ 前缀命名
   - 测试数据放到 test/fixtures/
   - 不在 dev/ 目录散落测试文件
```

### 第三步：构建EXE（输出到 dist/ 目录）
```bash
cd dev/app/
python build-version.py 修改内容1 修改内容2
```
**构建脚本自动完成**：
1. 从 `dev/app/` 当前代码直接构建 EXE
2. EXE 输出到 `dist/` 目录
3. 自动更新 `version_history.json` 和 `versions.json`
4. 自动 Git 提交和推送

### 第四步：保存版本（复制到 build/）
```
测试通过后，在 build/ 目录创建新的时间版本文件夹
将 dev/app/ 内容复制到新版本文件夹（不含 .venv/.cache 等）
```

### 第五步：回滚版本（如果需要）
```
从 build/ 的旧版本文件夹复制内容到 dev/app/
```

### 第六步：发布稳定版
```
从 build/ 的某个版本创建纯净整合包到 pack/
```

### 第七步：Git 提交
```
提交 dev/ 目录的更改并推送到远程仓库
```

---

## 📋 Git 管理范围

| 目录 | Git管理 | 说明 |
|------|---------|------|
| **dev/app/** | ✅ 管理 | 源代码，推送远程 |
| **dev/app/scripts/** | ✅ 管理 | 启动脚本 |
| **dev/data/** | ❌ 不管理 | 用户数据、模型、虚拟环境 |
| **dev/temp/** | ❌ 不管理 | 临时文件 |
| **dist/** | ❌ 不管理 | EXE构建产物 |
| **test/** | ✅ 管理（推荐） | 测试脚本纳入版本管理 |
| **test/outputs/** | ❌ 不管理 | 测试运行输出 |
| **ver/** | ❌ 不管理 | 正式版本分发，手动放入 |
| **build/** | ❌ 不管理 | 版本历史备份 |
| **pack/** | ❌ 不管理 | 本地发布包 |

---

## 🔴 关键规则

### 必须遵守

1. **EXE自动封装规则**：任何涉及 EXE 相关文件的修改（main.py、version_manager.py、launcher.py、icon.ico 等），任务完成后 **必须自动执行 `python build-version.py` 封装新 EXE**，确保 EXE 与源码同步
2. **封装脚本**：使用 `dev/app/build-version.py`，直接从 dev/app/ 构建，EXE 输出到 `dist/` 目录
3. **EXE 不放在 dev/ 中**：所有 EXE 统一放在 `dist/` 目录
4. **测试不放在 dev/ 中**：所有测试相关文件统一放在 `test/` 目录
5. **dev/app/scripts/ 只放启动脚本**：不要重复放置 ace-step-ui/、acestep/ 等项目文件
6. **main.py、version_manager.py、icon.ico、requirements.txt 保持在 dev/app/ 根目录**

### 严禁操作

1. ❌ 不要在 dev/ 目录放置 EXE 文件（EXE 统一放到 dist/）
2. ❌ 不要在 dev/ 目录放置测试文件（测试文件统一放到 test/）
3. ❌ 不要在 dev/app/scripts/ 下放置重复的项目文件
4. ❌ 不要直接修改 build/ 或 pack/ 目录
5. ❌ 不要在根目录创建项目文件
6. ❌ 不要跳过本指南直接开始编码

---

## 🚀 构建EXE命令

```bash
cd dev/app/
python build-version.py 修改内容1 修改内容2    # 指定修改内容并构建
python build-version.py                        # 交互式输入修改内容
```

构建后 EXE 位于 `项目根目录/dist/云集智能音乐创意台-vYYYY.MM.DD.HHMM.exe`。

---

## 📝 Git 提交信息规范

**格式**：`版本号: 简要描述`

**示例**：
```
v2026.04.14.0600: 互换软件更新和模型管理按钮位置
v2026.04.14.0600: 添加青龙训练器模型检测功能
v2026.04.14.0600: 修复某个bug
```

**不要写**：`更新`、`修改`、`优化` 等无意义描述。

---

## 📖 详细文档参考

完整的开发流程和细节，请查看：
- **`docs/开发指南.md`** — 完整开发指南
- **`docs/三目录文件夹结构.md`** — 三目录结构详细说明
- **`docs/EXE 打包指南.md`** — EXE打包详细指南

---

> 🚨 **AI 开发助手记住：** 所有开发操作都必须遵循上述流程！dev → test → dist，三步走！