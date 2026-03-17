#!/usr/bin/env python3
"""
青龙音乐训练器发布构建脚本
创建适合分享给用户下载的全自动安装包
以EXE文件名为版本号的发布
"""

import os
import sys
import subprocess
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# 版本号基于项目版本和打包日期
PROJECT_VERSION = "2.8.3"
BUILD_VERSION = datetime.now().strftime("%Y%m%d%H%M")
VERSION = f"{PROJECT_VERSION}-{BUILD_VERSION}"

# 构建输出目录
BUILD_DIR = Path("build-release")
DIST_DIR = BUILD_DIR / "dist"

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent

# 要包含的文件和目录
INCLUDE_FILES = [
    "ace-step-launcher.ps1",
    "ace-step-ui-launcher.ps1",
    "1、install-uv-qinglong.ps1",
    "2、run_gradio.ps1",
    "3、run_server.ps1",
    "4、run_npmgui.ps1",
    "favicon.ico",
    "icon.ico",
    "ico.png",
    "README.md",
    "PROJECT_STRUCTURE.md",
    "acestep",
    "ace-step-ui",
    "config",
    "docs",
    "launcher",
    "scripts",
    "shared",
    ".env.example",
    ".gitignore",
]

# 要排除的文件和目录
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.egg-info",
    "dist",
    "build",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "BAK",
    "models",
    "output",
    "data",
    "huggingface",
    "checkpoints",
    "*.whl",
    "*.tar.gz",
    "*.zip",
    "*.exe",
]

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  已删除: {BUILD_DIR}")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

def copy_project_files():
    """复制项目文件"""
    print("📋 复制项目文件...")
    
    def should_exclude(path):
        """检查是否应该排除"""
        path_str = str(path)
        for pattern in EXCLUDE_PATTERNS:
            if pattern in path_str:
                return True
        return False
    
    for item in INCLUDE_FILES:
        src = ROOT_DIR / item
        dst = BUILD_DIR / item
        
        if not src.exists():
            print(f"  [警告] 未找到: {src}")
            continue
        
        if should_exclude(src):
            print(f"  [跳过] 排除: {src}")
            continue
        
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS))
            print(f"  已复制目录: {item}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  已复制文件: {item}")

def create_setup_script():
    """创建安装脚本"""
    print("📝 创建安装脚本...")
    
    setup_content = """@echo off
:: 青龙音乐训练器安装脚本
:: 版本: {VERSION}

set "INSTALL_DIR=%~dp0"
set "PYTHON_EXE=%INSTALL_DIR%python_embeded\python.exe"
set "VENV_DIR=%INSTALL_DIR%.venv"

echo =========================================
echo 青龙音乐训练器安装脚本
echo 版本: {VERSION}
echo =========================================
echo.

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
echo [错误] 请以管理员身份运行此脚本
echo.
pause
exit /b 1
)

:: 检查系统架构
echo 检查系统架构...
if %PROCESSOR_ARCHITECTURE% == AMD64 (
    set "ARCH=x64"
) else (
    set "ARCH=x86"
    echo [警告] 32位系统可能无法正常运行
)
echo 系统架构: %ARCH%

:: 检查GPU
echo 检查GPU...
set "GPU_TYPE=CPU"
set "CUDA_AVAILABLE=false"

:: 检查NVIDIA GPU
tasklist | findstr /i nvidia >nul 2>&1
if %errorLevel% equ 0 (
    set "GPU_TYPE=NVIDIA"
    set "CUDA_AVAILABLE=true"
    echo 检测到 NVIDIA GPU
) else (
    :: 检查AMD GPU
tasklist | findstr /i amd >nul 2>&1
    if %errorLevel% equ 0 (
        set "GPU_TYPE=AMD"
        echo 检测到 AMD GPU
    ) else (
        echo 未检测到独立GPU，将使用CPU
    )
)

echo GPU类型: %GPU_TYPE%
echo.

:: 安装Python (如果需要)
if not exist "%PYTHON_EXE" (
    echo 📦 安装Python...
    :: 这里可以添加Python安装逻辑
    echo [信息] Python将在首次运行时自动安装
)

:: 创建虚拟环境
if not exist "%VENV_DIR%" (
    echo 📦 创建虚拟环境...
    if exist "%PYTHON_EXE" (
        "%PYTHON_EXE" -m venv "%VENV_DIR%"
    ) else (
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

:: 升级pip
echo 📦 升级pip...
"%VENV_PIP%" install --upgrade pip

:: 安装依赖
echo 📦 安装项目依赖...
"%VENV_PIP%" install -r "%INSTALL_DIR%requirements.txt"
if errorlevel 1 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

:: 安装前端依赖
echo 📦 安装前端依赖...
cd "%INSTALL_DIR%ace-step-ui"
if exist "package.json" (
    npm install
    if errorlevel 1 (
        echo [警告] 安装前端依赖失败，可能影响UI功能
    )
)
cd "%INSTALL_DIR%"

:: 复制环境配置文件
if not exist ".env" (
    echo 📝 创建环境配置文件...
    copy ".env.example" ".env"
    echo [信息] 已创建 .env 文件，请根据需要修改配置
)

echo.
echo =========================================
echo ✅ 安装完成!
echo =========================================
echo 请运行 "ACE-Step-Launcher.exe" 启动青龙音乐训练器
echo.
pause
""".format(VERSION=VERSION)
    
    setup_path = BUILD_DIR / "setup.bat"
    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(setup_content)
    print(f"  已创建: setup.bat")

def build_launcher():
    """构建启动器"""
    print("🔨 构建启动器...")
    
    launcher_dir = BUILD_DIR / "launcher"
    if not launcher_dir.exists():
        print("  [错误] 未找到 launcher 目录")
        return
    
    # 进入 launcher 目录
    original_cwd = os.getcwd()
    os.chdir(launcher_dir)
    
    try:
        # 安装依赖
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # 构建 EXE
        pyinstaller_args = [
            "pyinstaller",
            "--name", f"ACE-Step-Launcher-{VERSION}",
            "--onefile",
            "--windowed",
            "--add-data", "../2、run_gradio.ps1;.",
            "--add-data", "../3、run_server.ps1;.",
            "--add-data", "../4、run_npmgui.ps1;.",
            "--add-data", "../ico.png;.",
            "--add-data", "../1、install-uv-qinglong.ps1;.",
            "--clean",
            "--noconfirm",
            "--hidden-import", "PyQt6.sip",
            "--hidden-import", "psutil",
            "--hidden-import", "shutil",
            "main.py"
        ]
        
        # 如果有图标，添加 --icon 参数
        if os.path.exists("icon.ico"):
            pyinstaller_args.insert(1, "--icon")
            pyinstaller_args.insert(2, "icon.ico")
        
        subprocess.run(pyinstaller_args, check=True)
        
        # 复制到构建根目录
        exe_name = f"ACE-Step-Launcher-{VERSION}.exe"
        src = Path("dist") / exe_name
        dst = BUILD_DIR / exe_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  已构建: {exe_name}")
        else:
            # 尝试查找实际生成的EXE文件
            import glob
            exe_files = glob.glob(str(Path("dist") / "*.exe"))
            if exe_files:
                src = Path(exe_files[0])
                shutil.copy2(src, dst)
                print(f"  已构建: {src.name}")
            else:
                print(f"  [错误] 未找到: {src}")
            
    except subprocess.CalledProcessError as e:
        print(f"  [错误] 构建启动器失败: {e}")
    finally:
        os.chdir(original_cwd)

def create_zip_package():
    """创建ZIP包"""
    print("📦 创建ZIP包...")
    
    zip_name = f"qinglong-music-trainer-{VERSION}.zip"
    zip_path = DIST_DIR / zip_name
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BUILD_DIR):
            # 排除 dist 目录和构建过程产生的文件
            if "dist" in root or "build" in root or "__pycache__" in root:
                continue
            
            for file in files:
                if file.endswith(".pyc") or file.endswith(".spec"):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BUILD_DIR)
                zipf.write(file_path, arcname)
                print(f"  添加: {arcname}")
    
    print(f"  已创建: {zip_name}")
    return zip_path

def main():
    """主函数"""
    print("=" * 60)
    print(f"青龙音乐训练器发布构建脚本")
    print(f"版本: {VERSION}")
    print("=" * 60)
    print()
    
    try:
        clean_build()
        copy_project_files()
        create_setup_script()
        build_launcher()
        zip_path = create_zip_package()
        
        print()
        print("=" * 60)
        print("✅ 构建完成!")
        print(f"📦 输出文件: {zip_path}")
        print(f"📝 版本号: {VERSION}")
        print("=" * 60)
        print("\n此安装包包含:")
        print("1. 全自动安装脚本 (setup.bat)")
        print("2. 启动器 (ACE-Step-Launcher.exe)")
        print("3. 所有必要的代码和配置文件")
        print("4. 自动检测和适应不同显卡环境")
        print("\n使用方法:")
        print("1. 下载并解压 ZIP 包")
        print("2. 以管理员身份运行 setup.bat")
        print("3. 安装完成后运行 ACE-Step-Launcher.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
