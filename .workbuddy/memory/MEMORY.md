# 项目长期记忆 (云集智能音乐创意台 / 青龙音乐训练器)

## 构建与打包（Launcher EXE）— 现行权威方案
- **方案**：极简 `launcher.py` + `build-version.py` 文件夹模型（对照 git `07a04da` 复刻）。入口是 `launcher.py`（非 main.py），单实例靠 `_kill_old_instances()` 按品牌前缀杀旧进程；`-v` 版本号由 exe 文件名携带，`main.py` 的 `get_version_from_filename()` 解析。版本号格式 `v2026.07.21.1734`，正则 `v(\d+\.\d+\.\d+(?:\.\d+)?)`。
- **launcher 拆进程启动屏**：`_kill_old_instances()` → `_self_relocate()`（首次部署建文件夹）→ supervisor `Popen([exe,'--splash-child','--progress-ready=<temp>'], CREATE_NO_WINDOW)` 拉起**只加载 PyQt6 + yunji_splash、绝不 `import main`** 的子进程显示转圈光带；主进程后台 `import main` 后调 `main.main()`，`main.main()` 用 `QTimer.singleShot(0, _mark_progress_ready)` 把 `YUNJI_PROGRESS_READY` 哨兵推迟到事件循环启动后回写，子进程轮询到即 `raise_`+`app.quit()` 平滑交替。**必须拆进程**（import main 占 GIL 会让同体启动屏卡顿）。子进程用 ctypes `OpenProcess/GetExitCodeProcess` 的 `_parent_alive()` 探父存活、180s 兜底。品牌 LOGO = `dev/app/ico.png`（红云+音乐柱），`_draw_logo` 优先加载它。
- **build-version.py**：PyInstaller `--onefile --windowed`（GUI 子系统、无控制台；`sys.stdout/stderr` 为 None，launcher.py 用 `_NullWriter` 兜底）。`post_build()` 把 `app/acestep/`、`app/ace-step-ui/`、`scripts/`、`data/{outputs,models,config}/` 复制进 `build/云集智能音乐创意台-v<版本>/` 发布文件夹，单文件 exe 复制进 `dist/`。文件名带连字符，不能直接 `import`，当脚本跑 `python build-version.py "说明"` 或 `importlib.util.spec_from_file_location` 加载。构建环境用 `D:\Programs\Python312\python.exe`（PyInstaller 6.20.0）；受管 3.13.12 无 PyInstaller。
- **⚠️ pyi_splash 致命坑**：`--splash`（PyInstaller 6.20.0）在用户 Win 上 IPC 失败（WinError 10061）直接崩 exe。必须双管齐下：① `launcher.py` 删掉 `import pyi_splash`/`pyi_splash.close()`；② `build-version.py` 加 `--exclude-module pyi_splash`。构建后搜 exe 字节 `b"pyi_splash"` 必须为 0（`b"_PYI_SPLASH_IPC"` 出现 1 次是引导器惰性常量，无害）。
- **🚨 main.py 必须 `--add-data` 随 exe 打包**：`build_exe()` 加 `--add-data "main.py;."`，否则运行时 `import main` 命中磁盘旧版 `app/main.py`、哨兵逻辑不生效（表现："刚出现就淡出+黑屏空档"）。改 `main.main()` 启动屏逻辑后**务必重打包**。验证脚本 `dev/app/verify_exe.py` + 项目根 `_verify_bundle.py`（注意：`launcher` 是裸 marshal 码对象用 `marshal.loads` 扫，勿拿源码文本搜 `.pyc` 字节）。
- **MainWindow 显示铁律**：`_deferred_init` 里 `self.show()` 必须无条件执行，前面加载步骤（config/UI/monitor/resize）全包 try/except，否则异常被 `SafeApplication.notify` 吞掉→托盘在、界面不显示、无弹窗。加载异常一律 `_write_crash_log`。resize 后必须 `move` 居中到主屏 `availableGeometry()`（别交给 OS 记忆，跨分辨率/小屏会越界）；show() 后立即 `splash.finish(self)+deleteLater()+_splash=None`（不留 WindowStaysOnTopHint 启动屏盖窗口）。
- **🚨 首跑「窗口可见但看不到」= Windows 前台锁（2026-08-01 定位）**：supervisor 经 `Popen` 拉起 entry，entry 是 **Popen 子进程、不继承前台权限**，其 `activateWindow()`→`SetForegroundWindow` 被 Windows 前台锁**静默拒绝** → `isVisible()=True` 但窗口在后台、用户只看到托盘。**第二次双击 entry（Explorer 启动）和开发模式（终端启动）自带前台权，故正常**——这正是「首跑失败、二次/开发正常」的根因。⚠️ 但 `AllowSetForegroundWindow`/`AttachThreadInput` 这套**前台锁 hack 在真机不可靠**（0722 实测仍失败）。0842 曾改为「首跑不 spawn、直接在便携 exe（有前台权）跑 main」，显示 OK 但删除不行（self-delete-helper 等主进程退出才删、app 运行期永不触发，且用户要「打开就删」）。**0901 折中（当前权威）**：删除恢复 f7d9105 proven「首跑 spawn entry + `--cleanup`=便携exe + `os._exit`，入口 already 分支 `os.remove` 立即删便携 exe」（用户明确要此机制）；显示仍靠 main.py `_deferred_init` 的**居中**（已验证：几何 `(680,232,1200,988)` 是主屏2560×1440居中1200×988的**正确结果**、非屏外）+ show 后立即 `splash.finish+deleteLater` + `_force_foreground`(AttachThreadInput 突破前台锁) + 15s `_force_show_window` 兜底。f7d9105 同款 spawn 用户说能首跑显示，证明 spawn 本身不阻断显示；若 0901 首跑又「只见托盘」，需对比 f7d9105 的 main.py `_deferred_init`（可能当时无「独立 splash 子进程」遮挡或 show 路径不同）。
- **分发物**：`build/云集智能音乐创意台-v<版本>/`（exe+app/+data/，用户拿此文件夹双击 exe）+ `dist/云集智能音乐创意台-v<版本>.exe`（裸单文件，依赖发布文件夹的 app/）。轻量 `build_light.py` 只打 exe。

## 发布到双仓库下载页（Gitee + GitHub Releases）
- **构建 ≠ 发布**：`build-version.py` 只打包+git+插 `versions.json`（不写 `download_url`）。发布须另跑 `dev/app/_publish_releases.py`，把 `dev/ver/*.exe` 传 Gitee(`yunjii/music`)+GitHub(`yunjii-cn/music`) 并回写直链。
- ⚠️ 默认全量发布（glob `dev/ver/*.exe` 全传）。**必须加 `--version <v>` 才只发指定版本**，否则历史 exe 全传。支持 `--exe`、`--skip-gitee/github`、`--dry-run`。前置：`dev/app/.gitee_token`+`.github_token`、需 `requests`。`versions.json` 有 `download_url` 才亮下载按钮（截至 2026-07-31 仅 2 条带链接，其余显示"未提供"=没发布，非 bug）。

## 登录门控（ace-step-ui）
- `dev/app/ace-step-ui/LoginGate.tsx`（`<LoginGate><App/></LoginGate>`）。未登录→302 跳 `https://music.yunjii.cn/login?embed=1&redirect=<origin>&state=<rand>`；回跳 URL 带 base64 `yunji_user` → `loginWithUM` → `POST /api/auth/um` 签发 JWT。登录地址由 `UM_LOGIN_URL`（`VITE_UM_LOGIN_URL` 可覆盖）控制。改后须 `vite build` 重建 dist/（Express 3060 服务 dist/）。官网须把本应用 origin 加 redirect 白名单。

## flash_attn wheel 分发（2026-07-24 定稿）
- wheel = `flash_attn-2.8.3+cu128torch2.9.0cxx11abiTRUE-cp312-cp312-win_amd64.whl`（250MB，不进 exe，走运行时下载）。仅 NVIDIA 且 SM≥75 才装。下载源：GitHub `yunjii-cn/music` wheels → ghproxy 镜像 → 码云分卷兜底（Gitee `attach_files` 端点、单附件 100MB 上限→切 3 片 90+90+59MiB，release id=758333）。

## 目录约定
- `dev/app/`=源码(git)；`dev/dist/`=裸 exe(gitignore)；`dev/_build/`=发布文件夹(gitignore)；`dev/data/`=用户数据(gitignore)；`dev/ver/`=待发布版本 exe。`BAK/` 为备份。

## 沙箱 / 环境铁律
- **绝不在沙箱 `/tmp`（映射到 `D:\Temp`）跑 exe 冒烟测试**——曾把约 39GB 部署目录写入 D 盘、且残留清理进程逐文件删（杀软 3 文件/秒）把 D 盘 I/O 占满致整机卡顿。一律改 `E:\_smoke\` 且测完立即清理。D 盘空间紧张（640GB 已用、常剩 <5GB）。
