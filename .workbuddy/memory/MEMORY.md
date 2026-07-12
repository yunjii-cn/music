# 项目长期记忆 (云集智能音乐创意台 / 青龙音乐训练器)

## 构建与打包规范（Launcher EXE）
- 入口程序是 `dev/app/launcher.py`（非 main.py）；单实例保护与版本号靠 **exe 文件名中的 `-v`** 解析（`launcher.py` 内 `_kill_old_instances` + `main.py` 的 `get_version_from_filename`）。**最终 exe 命名为「项目名 + `-v` + 版本号」**，例如 `云集智能音乐创意台-v2.8.3.exe`（用户 2026-07-12 指定，弃用原 `launcher-vX.Y.Z.exe` 命名）。`-v` 标记必须保留，否则单实例/版本解析失效。
- `get_version_from_filename()` 正则已放宽：`v(\d+\.\d+\.\d+(?:\.\d+)?)` —— 同时接受 3 段（如 `2.8.3`）与 4 段（如 `2.8.3.0`）版本号；文件名用 3 段即可，版本资源(version_info.txt)仍按 Windows 惯例写 4 段(`2.8.3.0`)。
- 采用 **PyInstaller onedir**（非 onefile）：launcher 需通过相对路径找到同目录的 `python_embeded/`（嵌入式 python）与项目目录；onefile 解压到临时目录会破坏该相对路径。
- **重型依赖（torch/gradio/transformers/diffusers 等）不打进 exe**——它们在 `python_embeded` 里运行，launcher 只打包 PyQt6 + loguru + psutil + huggingface_hub。打包时须在 spec 的 `excludes` 里排除这些，否则体积 GB 级且易构建失败。
- 发布 spec：`dev/app/release.spec`（引用 `dev/app/version_info.txt` 写 Windows 版本资源）；构建脚本：`dev/pack/build_exe.ps1`（本地发布包，gitignore 不入库）。两者均 gitignore。
- 发版需同步四处版本号：`release.spec` 的 `APP_VERSION`、`version_info.txt` 的 `filevers/prodvers/FileVersion/ProductVersion`、`build_exe.ps1` 的 `$APP_VERSION` 与 `$ProjectName`，并让最终 exe 名为 `<项目名>-vX.Y.Z.exe`（如 `云集智能音乐创意台-v2.8.3.exe`）。
- 专业分发建议：windowed（无黑框）+ 代码签名（signtool，消除 SmartScreen 未知发布者）+ Inno Setup 生成单个 Setup.exe。现有 `debug_full.spec` 等仅为本地调试用（console=True、未签名）。
- 数据文件：`qt.conf`→`PyQt6/Qt6`、`icon.ico`、`splash.png` 须作为 datas 打入（已有 splash 启动屏降低 PyQt6 导入卡顿观感）。
