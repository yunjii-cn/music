# EXE 打包指南 - 云集智能音乐创意台

## 📦 快速打包

### 一键打包（推荐）

在项目根目录运行：

```bash
build-exe.bat
```

脚本会自动：
1. ✅ 检查 Python 和 PyInstaller 安装
2. ✅ 清理旧的打包文件
3. ✅ 执行打包
4. ✅ 生成发布包到 `dist/` 目录

### 手动打包

如果需要使用自定义配置：

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 使用 spec 文件打包
pyinstaller build.spec

# 或者使用命令行参数
pyinstaller --onefile --windowed --icon=ico.png --name="云集智能音乐创意台" --version-file=version_info.txt launcher/main.py
```

---

## 📋 打包前准备

### 1. 检查依赖

确保已安装所有必要的依赖：

```bash
pip install -r requirements.txt
```

**核心依赖：**
- PyQt6 >= 6.4.0
- psutil >= 5.9.0
- PyInstaller >= 5.0.0

### 2. 检查项目文件

确保以下文件存在：

```
✅ launcher/main.py           - 主程序入口
✅ launcher/version_manager.py - 版本管理器模块
✅ ico.png                     - 应用程序图标
✅ version_info.txt            - 版本信息文件
✅ build.spec                  - PyInstaller 配置文件
```

### 3. 清理临时文件（可选）

```bash
# 删除 Python 缓存
del /s /q *.pyc
rmdir /s /q __pycache__

# 删除旧的打包文件
rmdir /s /q build dist
```

---

## 🗂️ 打包模式

### 模式 1: 单文件模式 (--onefile)

**优点：**
- 只生成一个 `.exe` 文件
- 便于分发和复制
- 用户只需运行一个文件

**缺点：**
- 启动较慢（需要解压到临时目录）
- 文件体积较大（包含所有依赖）
- 每次启动都会解压

**打包命令：**
```bash
pyinstaller --onefile --windowed --icon=ico.png --version-file=version_info.txt --name="云集智能音乐创意台" launcher/main.py
```

**输出：**
```
dist/
└── 云集智能音乐创意台.exe  (约 100-150 MB)
```

### 模式 2: 目录模式 (--onedir)

**优点：**
- 启动较快（无需解压）
- 可以查看内部结构
- 便于调试和更新部分文件

**缺点：**
- 生成大量文件
- 分发时需要整个目录
- 用户可能误删文件

**打包命令：**
```bash
pyinstaller --windowed --icon=ico.png --version-file=version_info.txt --name="云集智能音乐创意台" launcher/main.py
```

**输出：**
```
dist/
└── 云集智能音乐创意台/
    ├── 云集智能音乐创意台.exe  (约 10 MB)
    ├── _internal/
    │   ├── python312.dll
    │   ├── PyQt6/
    │   ├── psutil/
    │   └── ... (所有依赖)
    ├── ico.png
    └── *.ps1 (PowerShell 脚本)
```

**当前配置：** 使用 **目录模式**（更稳定、便于维护）

---

## 📊 打包配置详解

### build.spec 关键配置

```python
# 不显示控制台窗口
console=False

# 使用图标
icon='ico.png'

# 版本信息
version='version_info.txt'

# 排除不需要的库
excludes=[
    'matplotlib',
    'scipy',
    'numpy.testing',
    'tkinter',
]

# UPX 压缩（减小文件体积）
upx=True
```

### version_info.txt 内容

```
CompanyName:        武汉市云集智能科技有限公司
FileDescription:    云集智能音乐创意台 - ACE-Step 音乐生成训练平台
FileVersion:        2026.03.19.0
ProductName:        云集智能音乐创意台
ProductVersion:     2026.03.19.0
LegalCopyright:     Copyright © 2026 武汉市云集智能科技有限公司
```

---

## 🔧 打包优化技巧

### 1. 减小文件体积

```bash
# 使用 UPX 压缩（已在 build.spec 中配置）
upx=True

# 排除不必要的库
excludes=['matplotlib', 'scipy', 'tkinter']

# 使用 --onefile 模式（但不推荐，启动慢）
```

### 2. 加快启动速度

```bash
# 使用 --onedir 模式（推荐）
# 避免每次启动都解压

# 禁用 UPX（某些情况下更快，但文件更大）
upx=False
```

### 3. 包含额外文件

在 `build.spec` 的 `datas` 列表中添加：

```python
datas = [
    ('ico.png', '.'),
    ('*.ps1', '.'),
    ('config/', 'config'),
    ('requirements.txt', '.'),
]
```

### 4. 隐藏控制台窗口

```python
# 在 build.spec 中设置
console=False
```

---

## 📦 发布包结构

### 标准发布包（目录模式）

```
云集智能音乐创意台/
├── 云集智能音乐创意台.exe      # 主程序
├── 云集智能音乐创意台.exe.manifest  # 清单文件
├── _internal/                   # 内部依赖目录
│   ├── python312.dll
│   ├── PyQt6/
│   ├── psutil/
│   └── ... (所有 Python 依赖)
├── ico.png                      # 图标文件
├── 1、install-uv-qinglong.ps1   # PowerShell 脚本
├── 2、run_gradio.ps1
├── 3、run_server.ps1
└── 4、run_npmgui.ps1
```

### 用户使用方法

1. **复制整个文件夹**到目标位置
   ```
   xcopy 云集智能音乐创意台\ \\target\path\ /E /I
   ```

2. **双击运行** `云集智能音乐创意台.exe`

3. **首次启动**可能较慢（需要初始化和加载依赖）

---

## 🧪 测试打包结果

### 测试步骤

1. **基本功能测试**
   ```
   ✓ 程序能否正常启动
   ✓ 界面是否显示正常
   ✓ 按钮点击是否响应
   ```

2. **版本管理器测试**
   ```
   ✓ 点击"📦 版本管理"按钮
   ✓ 下拉菜单是否正常显示
   ✓ 版本列表是否正确
   ✓ 快速切换功能是否正常
   ✓ 完整弹窗是否能打开
   ```

3. **兼容性测试**
   ```
   ✓ 在不同 Windows 版本上测试
   ✓ 在无 Python 环境的机器上测试
   ✓ 在有杀毒软件的机器上测试
   ```

### 常见问题排查

#### 问题 1: 程序启动后立即关闭

**原因：** 缺少依赖或代码错误

**解决方法：**
```bash
# 使用控制台模式重新打包查看错误
pyinstaller --console build.spec

# 运行生成的 exe，查看控制台输出的错误信息
```

#### 问题 2: 缺少某些模块

**原因：** 未正确包含依赖

**解决方法：**
```bash
# 在 build.spec 中添加 hiddenimports
hiddenimports += ['missing_module_name']

# 或者使用 --hidden-import 参数
pyinstaller --hidden-import missing_module_name build.spec
```

#### 问题 3: 文件体积过大

**原因：** 包含了不必要的库

**解决方法：**
```bash
# 在 build.spec 的 excludes 中添加
excludes += ['large_unneeded_library']

# 分析打包内容
python -m PyInstaller.utils.win32.versioninfo dist/云集智能音乐创意台/_internal/
```

#### 问题 4: 杀毒软件误报

**原因：** PyInstaller 打包的程序可能被误报

**解决方法：**
1. 添加数字签名（需要购买证书）
2. 向杀毒软件厂商提交白名单
3. 在程序中添加说明文档
4. 使用微软应用商店认证

---

## 📝 打包检查清单

### 打包前

- [ ] 所有代码已提交到 Git
- [ ] 已测试所有功能正常
- [ ] 已安装 PyInstaller
- [ ] 已准备好图标文件
- [ ] 已更新版本号

### 打包后

- [ ] EXE 文件生成成功
- [ ] 文件大小合理（100-200 MB）
- [ ] 程序能正常启动
- [ ] 所有功能测试通过
- [ ] 版本信息显示正确
- [ ] 图标显示正常

### 发布前

- [ ] 在无 Python 环境的机器上测试
- [ ] 在多个 Windows 版本上测试
- [ ] 编写使用说明
- [ ] 准备安装包或压缩包
- [ ] 更新版本文档

---

## 🚀 自动化打包脚本

### build-exe.bat 功能

```batch
✓ 检查 Python 和 PyInstaller 安装
✓ 自动安装缺失的依赖
✓ 清理旧的打包文件
✓ 执行打包
✓ 检查输出文件
✓ 显示文件大小
✓ 可选：测试运行
✓ 可选：打开输出文件夹
```

### 自定义打包脚本

如果需要特殊配置，可以创建自定义脚本：

```batch
@echo off
REM 自定义打包配置

REM 设置打包模式（onefile 或 onedir）
set BUILD_MODE=onedir

REM 设置是否显示控制台
set SHOW_CONSOLE=false

REM 设置 UPX 压缩
set USE_UPX=true

REM 执行打包
python -m PyInstaller custom.spec
```

---

## 📖 相关文档

- [混合式版本管理器使用指南](docs/混合式版本管理器使用指南.md)
- [混合式版本管理器测试指南](docs/混合式版本管理器测试指南.md)
- [CHANGELOG](CHANGELOG-2026-03-19.md)

---

## 💡 提示与技巧

### 技巧 1: 快速测试打包

```bash
# 使用 --clean 清除缓存，确保使用最新代码
pyinstaller --clean build.spec
```

### 技巧 2: 分析打包内容

```bash
# 查看打包了哪些文件
pyinstaller --log-level=DEBUG build.spec
```

### 技巧 3: 多版本打包

```bash
# 为不同版本创建不同的 spec 文件
copy build.spec build-stable.spec
copy build.spec build-dev.spec

# 修改版本号后分别打包
```

### 技巧 4: 批量打包

```batch
@echo off
for %%v in (stable beta dev) do (
    echo 打包 %%v 版本...
    copy build.spec build-%%v.spec
    pyinstaller build-%%v.spec
)
```

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **使用目录模式** - 启动快、便于维护
2. **包含完整依赖** - 确保在无 Python 环境运行
3. **添加版本信息** - 显示公司信息和版本号
4. **使用图标** - 提升用户体验
5. **测试多种环境** - 确保兼容性

### ❌ 避免做法

1. **不要使用 --onefile** - 启动慢、临时文件多
2. **不要排除核心依赖** - 可能导致运行时错误
3. **不要忘记测试** - 打包后务必全面测试
4. **不要忽略杀毒软件** - 提前准备解决方案

---

**最后更新：** 2026-03-19  
**适用版本：** 云集智能音乐创意台 v2026.03.19+  
**打包工具：** PyInstaller 6.x
