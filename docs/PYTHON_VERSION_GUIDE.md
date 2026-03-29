# Python版本切换指南

## 当前状态
- 当前使用：Python 3.13.5
- 官方推荐：Python 3.12.x

## 方法一：使用Python Launcher（推荐）

如果你系统中有安装Python 3.12，可以使用以下命令：

```powershell
# 查看所有可用的Python版本
py --list

# 使用Python 3.12创建虚拟环境
py -3.12 -m venv venv312

# 激活虚拟环境
.\venv312\Scripts\Activate.ps1

# 验证Python版本
python --version
```

## 方法二：手动指定Python路径

如果你知道Python 3.12的安装路径：

```powershell
# 例如：如果Python 3.12安装在 C:\Python312
C:\Python312\python.exe -m venv venv312

# 激活虚拟环境
.\venv312\Scripts\Activate.ps1
```

## 方法三：下载并安装Python 3.12

如果系统中没有Python 3.12：

1. 访问 https://www.python.org/downloads/
2. 下载Python 3.12.x版本（推荐3.12.7或更高版本）
3. 安装时勾选 "Add Python to PATH"
4. 安装完成后使用方法一

## 安装依赖

激活虚拟环境后，安装项目依赖：

```powershell
# 激活虚拟环境
.\venv312\Scripts\Activate.ps1

# 升级pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

## 注意事项

1. **虚拟环境名称**：建议使用`venv312`作为虚拟环境目录名
2. **.gitignore**：`venv312/`已在.gitignore中，不会被提交到Git
3. **.python-version文件**：已创建，指定使用Python 3.12

## 当前环境检测

项目会在初始化时检测Python版本，并在系统信息中显示：
- ✅ 符合官方要求：Python 3.12.x
- ⚠️ 建议使用Python 3.12：其他版本
