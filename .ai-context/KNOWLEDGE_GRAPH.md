# 项目知识图谱

> **文件关系地图**: 本文档描述项目中文件之间的依赖关系和调用关系，帮助AI快速理解项目架构。

---

## 📋 目录

- [整体架构](#整体架构)
- [启动器模块关系](#启动器模块关系)
- [启动脚本关系](#启动脚本关系)
- [服务端口映射](#服务端口映射)
- [打包流程关系](#打包流程关系)
- [分支工作流](#分支工作流)

---

## 整体架构

```
云集智能音乐创意台
│
├── [用户界面层]
│   ├── launcher/main.py (PyQt6启动器)
│   │   ├── 调用 → launcher/version_manager.py
│   │   ├── 启动 → 2、run_gradio.ps1
│   │   ├── 启动 → 3、run_server.ps1
│   │   └── 启动 → 4、run_npmgui.ps1
│   │
│   ├── 2、run_gradio.ps1 (Gradio界面)
│   │   └── 使用 → acestep/ui/gradio/
│   │
│   └── 4、run_npmgui.ps1 (青龙前端)
│       └── 使用 → ace-step-ui/ (React)
│
├── [服务层]
│   └── 3、run_server.ps1 (API服务)
│       └── 使用 → acestep/api/
│
├── [核心逻辑层]
│   └── acestep/ (核心Python包)
│       ├── api/ (API接口)
│       ├── core/ (核心功能)
│       ├── training/ (训练功能)
│       └── ui/ (UI组件)
│
├── [工具层]
│   ├── build-correct.py (打包脚本)
│   │   ├── 读取 → Git状态
│   │   ├── 生成 → dist/EXE文件
│   │   └── 提交 → Git仓库
│   │
│   └── 1、install-uv-qinglong.ps1 (环境安装)
│       └── 安装 → requirements.txt
│
└── [文档层]
    ├── .ai-context/ (AI理解文档)
    ├── PROJECT_DEVELOPMENT_GUIDE.md
    ├── AGENTS.md
    └── BAK/README.md
```

---

## 启动器模块关系

### launcher/main.py 的依赖和调用

```
launcher/main.py
│
├── [导入的模块]
│   ├── PyQt6 (GUI框架)
│   ├── subprocess (进程管理)
│   ├── threading (多线程)
│   └── launcher/version_manager.py
│
├── [启动的服务]
│   ├── 青龙 LoRA 训练器
│   │   ├── 3、run_server.ps1 (API服务，端口8001)
│   │   └── 4、run_npmgui.ps1 (前端，端口3000)
│   │
│   └── 官方音乐演练场
│       └── 2、run_gradio.ps1 (Gradio，端口7860)
│
└── [集成的功能]
    ├── 环境维护
    ├── 模型管理
    ├── 版本管理
    └── 日志显示
```

### launcher/version_manager.py 的关系

```
launcher/version_manager.py
│
├── [依赖]
│   ├── Git命令行工具
│   └── PyQt6
│
└── [功能]
    ├── 读取Git分支
    ├── 切换Git分支
    └── 显示版本历史
```

---

## 启动脚本关系

### 四个启动脚本的职责

```
┌─────────────────────────────────────────────────────────────────┐
│                     launcher/main.py                              │
│                    (PyQt6 启动器)                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│2、run_gradio │ │3、run_server  │ │4、run_npmgui  │
│.ps1          │ │.ps1          │ │.ps1          │
│(Gradio界面)  │ │(API服务)     │ │(青龙前端)    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│acestep/ui/   │ │acestep/api/  │ │ace-step-ui/  │
│gradio/       │ │              │ │(React)       │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 1、install-uv-qinglong.ps1 的关系

```
1、install-uv-qinglong.ps1
│
├── [执行步骤]
│   1. 安装 uv 包管理器
│   2. 创建虚拟环境
│   3. 安装 requirements.txt 中的依赖
│   4. 初始化 Git 子模块 (ace-step-ui)
│
└── [依赖文件]
    └── requirements.txt
```

---

## 服务端口映射

| 服务 | 启动脚本 | 端口 | 技术栈 | 依赖 |
|------|---------|------|--------|------|
| **官方音乐演练场** | `2、run_gradio.ps1` | 7860 | Gradio | acestep/ui/gradio/ |
| **核心API服务** | `3、run_server.ps1` | 8001 | FastAPI | acestep/api/ |
| **青龙训练器前端** | `4、run_npmgui.ps1` | 3000 | React + Vite | ace-step-ui/ |

### 服务调用关系

```
┌─────────────────────────────────────────────────────────┐
│                    用户浏览器                            │
└────────────┬──────────────────────────┬─────────────────┘
             │                          │
    :7860    │                          │    :3000
             ▼                          ▼
┌─────────────────────┐      ┌─────────────────────┐
│  2、run_gradio.ps1  │      │  4、run_npmgui.ps1  │
│   (Gradio界面)      │      │   (React前端)       │
└──────────┬──────────┘      └──────────┬──────────┘
           │                              │
           └──────────────┬───────────────┘
                          │
                          ▼ :8001
                 ┌─────────────────┐
                 │ 3、run_server.ps1│
                 │   (API服务)     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   acestep/core/  │
                 │   (核心逻辑)     │
                 └─────────────────┘
```

---

## 打包流程关系

### build-correct.py 的工作流

```
build-correct.py
│
├── [第1步] 清理构建目录
│   └── 删除 build/ 和 dist/
│
├── [第2步] 构建EXE
│   ├── 使用 → PyInstaller
│   ├── 读取 → launcher/main.py
│   ├── 包含 → 所有依赖资源
│   └── 生成 → dist/云集智能音乐创意台-vYYYY.MM.DD.HHMM.exe
│
├── [第3步] Git操作
│   ├── 检测 → Git状态 (git status)
│   ├── 获取 → Git更改 (git diff)
│   ├── 生成 → 提交信息
│   ├── 提交 → git commit
│   └── 推送 → git push
│
└── [输出]
    └── dist/EXE文件
```

### 打包的文件依赖

```
build-correct.py
│
├── [打包的源文件]
│   ├── launcher/main.py
│   ├── launcher/version_manager.py
│   ├── 1、install-uv-qinglong.ps1
│   ├── 2、run_gradio.ps1
│   ├── 3、run_server.ps1
│   ├── 4、run_npmgui.ps1
│   ├── acestep/ (完整包)
│   ├── ace-step-ui/ (子模块)
│   └── assets/ (资源文件)
│
└── [不打包的文件]
    ├── BAK/ (归档文件)
    ├── .ai-context/ (AI文档)
    ├── docs/ (文档)
    └── .git/ (Git仓库)
```

---

## 分支工作流

### 三个分支的关系

```
┌─────────────────────────────────────────────────────────┐
│                    开发工作流                             │
└─────────────────────────────────────────────────────────┘

┌─────────────┐
│   main      │  ← 日常开发，自动打包上传
│ (开发分支)   │
└──────┬──────┘
       │ 测试通过后手动合并
       ▼
┌─────────────┐
│   beta      │  ← 测试验证，手动合并推送
│ (测试分支)   │
└──────┬──────┘
       │ 充分测试后手动合并
       ▼
┌─────────────┐
│   stable    │  ← 正式发布，打版本标签
│ (稳定分支)   │
└─────────────┘
```

### 分支与打包的关系

| 分支 | 打包方式 | 推送方式 | 用途 |
|------|---------|---------|------|
| **main** | `build-correct.py` | 自动推送 | 日常开发 |
| **beta** | 手动打包 | 手动推送 | 测试验证 |
| **stable** | 手动打包 | 手动推送 + 打标签 | 正式发布 |

---

## 文件修改影响范围

### 修改某个文件时需要注意的影响

| 如果你修改了 | 可能影响的文件/功能 | 需要测试的内容 |
|------------|-------------------|--------------|
| `launcher/main.py` | 整个启动器界面 | 所有按钮、功能 |
| `2、run_gradio.ps1` | Gradio界面启动 | 官方音乐演练场 |
| `3、run_server.ps1` | API服务 | 所有后端功能 |
| `4、run_npmgui.ps1` | 青龙前端 | 青龙训练器 |
| `build-correct.py` | 打包流程 | EXE生成、Git提交 |
| `acestep/` 下的文件 | 核心功能 | 对应功能模块 |

---

## 常见任务的文件路径

| 任务 | 需要查看/修改的文件 |
|------|-------------------|
| 修改启动器UI | `launcher/main.py` |
| 修改版本管理 | `launcher/version_manager.py` |
| 修改Gradio启动 | `2、run_gradio.ps1` |
| 修改API启动 | `3、run_server.ps1` |
| 修改青龙前端启动 | `4、run_npmgui.ps1` |
| 修改环境安装 | `1、install-uv-qinglong.ps1` |
| 修改打包流程 | `build-correct.py` |
| 修改项目依赖 | `requirements.txt` |
| 修改核心逻辑 | `acestep/core/` |
| 修改API接口 | `acestep/api/` |
| 修改Gradio界面 | `acestep/ui/gradio/` |
| 归档遗留文件 | 移动到 `BAK/` 对应子文件夹 |

---

*最后更新: 2026-03-21*
