#!/usr/bin/env python3
"""
文件用途: 标准EXE打包脚本（唯一推荐使用）
项目名称: 云集智能音乐创意台 (ACE-Step)
版本: v2.8.3+

核心功能:
1. 清理构建目录
2. 使用PyInstaller构建单文件EXE
3. 检测Git更改
4. 生成详细提交信息
5. 自动提交到Git
6. 自动推送到当前分支

输出位置: dist/云集智能音乐创意台-vYYYY.MM.DD.HHMM.exe

使用方式:
python build-correct.py

修改注意事项:
- 这是唯一的标准打包脚本
- 不要创建新的打包脚本
- 所有修改应在此脚本中进行

打包的源文件:
- launcher/main.py
- launcher/version_manager.py
- 1、install-uv-qinglong.ps1
- 2、run_gradio.ps1
- 3、run_server.ps1
- 4、run_npmgui.ps1
- acestep/ (完整包)
- ace-step-ui/ (子模块)
- assets/ (资源文件)

不打包的文件:
- BAK/ (归档文件)
- .ai-context/ (AI文档)
- docs/ (文档)
- .git/ (Git仓库)

更多信息请参考:
- .ai-context/FILE_INDEX.md
- .ai-context/KNOWLEDGE_GRAPH.md
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# 版本号基于打包日期和时间
now = datetime.now()
VERSION = now.strftime("%Y.%m.%d.%H%M")

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent
LAUNCHER_DIR = ROOT_DIR / "launcher"

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    dirs_to_remove = ['build']  # 只清理build目录，保留dist目录
    for dir_name in dirs_to_remove:
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_name}")

def build_exe():
    """构建 EXE"""
    print("🔨 构建 EXE...")
    
    os.chdir(ROOT_DIR)
    
    # PyInstaller 参数 - 只打包必要的文件
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"云集智能音乐创意台-v{VERSION}",
        "--onefile",
        "--windowed",
        "--icon", str(ROOT_DIR / "ico.png"),
        "--add-data", f"{ROOT_DIR / 'ico.png'};.",
        "--add-data", f"{ROOT_DIR / '1、install-uv-qinglong.ps1'};.",
        "--add-data", f"{ROOT_DIR / '2、run_gradio.ps1'};.",
        "--add-data", f"{ROOT_DIR / '3、run_server.ps1'};.",
        "--add-data", f"{ROOT_DIR / '4、run_npmgui.ps1'};.",
        "--clean",
        "--noconfirm",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "psutil",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "numpy",
        "--exclude-module", "tkinter",
        "--exclude-module", "tensorflow",
        "--exclude-module", "torch",
        "--exclude-module", "modelscope",
        "--exclude-module", "transformers",
        "--exclude-module", "datasets",
        "--exclude-module", "acestep",
        str(LAUNCHER_DIR / "main.py")
    ]
    
    print("  运行 PyInstaller...")
    subprocess.run(pyinstaller_args, check=True)

def check_output():
    """检查输出"""
    print("📦 检查输出文件...")
    
    exe_path = ROOT_DIR / "dist" / f"云集智能音乐创意台-v{VERSION}.exe"
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        print(f"  ✓ EXE 文件已生成: {exe_path}")
        print(f"  ✓ 文件大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"  ❌ 未找到 EXE 文件")
        return False

def get_git_changes():
    """获取Git更改描述"""
    print("📝 获取Git更改信息...")
    
    try:
        os.chdir(ROOT_DIR)
        
        # 获取git status
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if not status_result.stdout.strip():
            print("  未检测到文件更改")
            return "无文件更改"
        
        # 获取详细的git diff
        diff_result = subprocess.run(
            ['git', 'diff', '--stat'],
            capture_output=True,
            text=True,
            check=False
        )
        
        changes = []
        changes.append("版本更新内容：\n")
        
        # 分析状态
        for line in status_result.stdout.strip().split('\n'):
            if line.strip():
                status_code = line[:2].strip()
                file_path = line[3:].strip()
                
                status_desc = {
                    'M': '修改',
                    'A': '新增',
                    'D': '删除',
                    'R': '重命名',
                    'C': '复制'
                }.get(status_code, '更新')
                
                changes.append(f"- {status_desc}: {file_path}")
        
        if diff_result.stdout.strip():
            changes.append("\n文件变更统计：")
            changes.append(diff_result.stdout.strip())
        
        return '\n'.join(changes)
        
    except Exception as e:
        print(f"  获取Git信息时出错: {e}")
        return "获取变更信息失败"

def get_current_branch():
    """获取当前Git分支"""
    try:
        os.chdir(ROOT_DIR)
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"  获取当前分支失败: {e}")
        return None

def commit_and_push():
    """提交并推送到远程仓库（开发分支）"""
    print("🚀 提交并推送到远程仓库（开发分支）...")
    
    try:
        os.chdir(ROOT_DIR)
        
        # 获取当前分支
        current_branch = get_current_branch()
        if not current_branch:
            print("  ❌ 无法获取当前分支")
            return False
        
        print(f"  当前分支: {current_branch}")
        
        # 获取更改描述
        change_description = get_git_changes()
        
        # 构建提交信息
        commit_message = f"更新版本 v{VERSION}\n\n{change_description}"
        
        print(f"\n📄 提交信息：")
        print("=" * 60)
        print(commit_message)
        print("=" * 60)
        print()
        
        # 添加所有更改
        print("  添加文件到Git...")
        subprocess.run(['git', 'add', '-A'], check=True)
        
        # 提交
        print("  提交更改...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # 推送到远程仓库（使用当前分支）
        print(f"  推送到远程仓库（{current_branch}分支）...")
        push_result = subprocess.run(
            ['git', 'push', 'origin', current_branch],
            capture_output=True,
            text=True
        )
        
        if push_result.returncode == 0:
            print(f"  ✓ 成功推送到 {current_branch} 分支")
            return True
        else:
            print(f"  ⚠ 推送失败: {push_result.stderr}")
            print("  提示: 请检查远程仓库连接或手动推送")
            return False
            
    except subprocess.CalledProcessError as e:
        if e.returncode == 1 and 'nothing to commit' in str(e.stderr):
            print("  没有需要提交的更改")
            return True
        print(f"  ❌ Git操作失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 提交过程出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("  云集智能音乐创意台 - 打包工具")
    print(f"  版本: {VERSION}")
    print("=" * 60)
    print()
    
    try:
        clean_build()
        print()
        
        build_exe()
        print()
        
        if check_output():
            print()
            print("=" * 60)
            print("✅ 打包完成！")
            print(f"📦 EXE 文件: dist\\云集智能音乐创意台-v{VERSION}.exe")
            print("=" * 60)
            print()
            
            # 自动上传到远程仓库
            print("🚀 自动提交并推送到远程仓库...")
            print()
            
            if commit_and_push():
                print()
                print("=" * 60)
                print("🎉 全部完成！")
                print("=" * 60)
            else:
                print()
                print("=" * 60)
                print("⚠ 打包完成，但Git上传失败")
                print("=" * 60)
        else:
            print("\n❌ 打包失败")
            sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
