#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布脚本: 将 ver/ 中的 EXE 发布到 Gitee + GitHub Releases
- 创建 Release + 上传 EXE 附件
- 更新 versions.json 中的 download_url
"""
import os
import sys
import json
import time
import re
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_PATH_GITEE = os.path.join(PROJECT_ROOT, "dev", "app", ".gitee_token")
TOKEN_PATH_GITHUB = os.path.join(PROJECT_ROOT, "dev", "app", ".github_token")
VER_DIR = os.path.join(PROJECT_ROOT, "dev", "ver")
VERSIONS_JSON = os.path.join(PROJECT_ROOT, "dev", "app", "versions.json")

BRAND_NAME = "云集智能音乐创意台"

GITEE_OWNER = "yunjii"
GITEE_REPO = "music"
GITEE_API = "https://gitee.com/api/v5"

GITHUB_OWNER = "yunjii-cn"
GITHUB_REPO = "music"
GITHUB_API = "https://api.github.com"
GITHUB_UPLOAD = "https://uploads.github.com"


KNOWN_BODIES = {
    "2026.07.03.0635": "修复单实例保护（消除双托盘图标）\n\n- 修复单实例保护（消除双托盘图标）\n- 修复gradio SOCKS代理导入崩溃\n- 修复REQUIRED_DEPS中lycoris_lora模块名\n- 清理代理环境变量",
    "2026.05.26.0502": "改用 --console 模式调试闪退问题",
    "2026.05.26.0447": "改用 --hide-console hide-early 替代 --windowed",
    "2026.05.26.0430": "修复 windowed 模式下 _NullWriter 导致闪退",
    "2026.05.26.0336": "重构目录结构和路径解析，参考视频创意站三目录原则",
    "2026.05.26.0133": "修复 base_dir 支持 dev/app/ 兄弟目录查找",
    "2026.05.26.0131": "修复 base_dir 路径解析优先查找真实源码目录",
    "2026.05.26.0120": "修复 base_dir 路径解析优先查找真实源码目录",
    "2026.05.26.0117": "修复 frozen 模式下脚本找不到和 base_dir 路径解析问题",
    "2026.05.26.0043": "修复 qt.conf 缺失导致 Qt 平台插件加载失败",
    "2026.05.12.0918": "架构升级：adapter适配层+acestep-sync同步脚本",
    "2026.04.30.2114": "修复青龙训练器启动问题：删除pyi_rth_subprocess.py中的SetWinEventHook全局钩子",
}


def _read_token(path, name):
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def get_gitee_token():
    return _read_token(TOKEN_PATH_GITEE, "Gitee")


def get_github_token():
    return _read_token(TOKEN_PATH_GITHUB, "GitHub")


def extract_version(filename):
    m = re.search(r'v(\d{4}\.\d{2}\.\d{2}\.\d{4})', filename)
    if m:
        return m.group(1)
    m = re.search(r'v(\d+\.\d+\.\d+\.\d+)', filename)
    return m.group(1) if m else None


# ═════════════ Gitee ═════════════
def gitee_list_releases(token):
    r = requests.get(
        f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/releases",
        params={"access_token": token, "per_page": 100},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def gitee_create_release(token, tag_name, name, body, target_commitish="main"):
    return requests.post(
        f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/releases",
        params={"access_token": token},
        json={
            "tag_name": tag_name,
            "name": name,
            "body": body,
            "target_commitish": target_commitish,
            "prerelease": False,
        },
        timeout=30,
    )


def gitee_upload_asset(token, release_id, file_path):
    upload_url = f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/{release_id}/attach_files"
    fname = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        files = {"file": (fname, f, "application/octet-stream")}
        return requests.post(
            upload_url,
            params={"access_token": token},
            files=files,
            timeout=1200,
        )


def publish_to_gitee(exe_path, version, body, dry_run=False, existing_tags=None):
    token = get_gitee_token()
    if not token:
        print("    [Gitee] ✗ 无 token,跳过")
        return False
    tag_name = f"v{version}"

    if existing_tags is None:
        existing_tags = [r.get("tag_name") for r in gitee_list_releases(token)]
    if tag_name in existing_tags:
        print(f"    [Gitee] 跳过(已存在): {tag_name}")
        return "skip"

    if dry_run:
        print(f"    [Gitee] [DRY-RUN] 将创建 {tag_name} 并上传 {os.path.basename(exe_path)}")
        return True

    r = gitee_create_release(token, tag_name, tag_name, body)
    if r.status_code >= 300:
        print(f"    [Gitee] ✗ 创建 release 失败: {r.status_code} {r.text[:200]}")
        return False
    release_id = r.json().get("id")
    if not release_id:
        print(f"    [Gitee] ✗ 创建 release 失败: 无 id,响应 {r.text[:200]}")
        return False
    print(f"    [Gitee] ✓ release 创建 (id={release_id})")

    r = gitee_upload_asset(token, release_id, exe_path)
    if r.status_code >= 300:
        print(f"    [Gitee] ✗ 上传 EXE 失败: {r.status_code} {r.text[:200]}")
        return False
    print(f"    [Gitee] ✓ EXE 上传成功 ({os.path.getsize(exe_path)/1024/1024:.1f} MB)")
    return True


# ═════════════ GitHub ═════════════
def _gh_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "YunJii-Publisher/1.0",
    }


def github_list_release_tags(token):
    r = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
        headers=_gh_headers(token),
        params={"per_page": 100},
        timeout=15,
    )
    r.raise_for_status()
    return [r0.get("tag_name") for r0 in r.json()]


def github_create_release(token, tag_name, name, body, target_commitish="main"):
    return requests.post(
        f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
        headers=_gh_headers(token),
        json={
            "tag_name": tag_name,
            "target_commitish": target_commitish,
            "name": name,
            "body": body,
            "draft": False,
            "prerelease": False,
            "generate_release_notes": False,
        },
        timeout=30,
    )


def github_release_fname(version):
    return f"yunji-music-creative-v{version}.exe"


def github_upload_asset(token, upload_url_template, file_path, fname=None):
    from requests import Request
    if fname is None:
        fname = os.path.basename(file_path)
    upload_url = upload_url_template.replace("{?name,label}", f"?name={requests.utils.quote(fname)}")
    with open(file_path, "rb") as f:
        raw = f.read()
    req = Request(
        method="POST",
        url=upload_url,
        headers={
            **_gh_headers(token),
            "Content-Type": "application/octet-stream",
        },
        data=raw,
    )
    prepared = req.prepare()
    return requests.Session().send(prepared, timeout=1200)


def publish_to_github(exe_path, version, body, dry_run=False, existing_tags=None):
    token = get_github_token()
    if not token:
        print("    [GitHub] ✗ 无 token,跳过")
        return False
    tag_name = f"v{version}"
    gh_fname = github_release_fname(version)

    if existing_tags is None:
        existing_tags = github_list_release_tags(token)

    if dry_run:
        if tag_name in existing_tags:
            print(f"    [GitHub] [DRY-RUN] {tag_name} 已存在,跳过")
        else:
            print(f"    [GitHub] [DRY-RUN] 将创建 {tag_name} 并上传 {gh_fname}")
        return "skip" if tag_name in existing_tags else True

    if tag_name not in existing_tags:
        r = github_create_release(token, tag_name, tag_name, body)
        if r.status_code >= 300:
            print(f"    [GitHub] ✗ 创建 release 失败: {r.status_code} {r.text[:200]}")
            return False
        rel = r.json()
        release_id = rel.get("id")
        upload_url_tpl = rel.get("upload_url", "")
        if not release_id or not upload_url_tpl:
            print(f"    [GitHub] ✗ 创建 release 失败: id/upload_url 缺失")
            return False
        print(f"    [GitHub] ✓ release 创建 (id={release_id})")
    else:
        print(f"    [GitHub] tag {tag_name} 已存在,尝试直接上传 asset")
        # Find existing release
        releases = requests.get(
            f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
            headers=_gh_headers(token),
            params={"per_page": 100},
            timeout=15,
        ).json()
        target_rel = next((r for r in releases if r.get("tag_name") == tag_name), None)
        if not target_rel:
            print(f"    [GitHub] ✗ 未找到 release for tag {tag_name}")
            return False
        upload_url_tpl = target_rel.get("upload_url", "")
        if not upload_url_tpl:
            print(f"    [GitHub] ✗ release {tag_name} 无 upload_url")
            return False

    # Check if asset already exists
    if tag_name in existing_tags:
        target_rel = next((r for r in requests.get(
            f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
            headers=_gh_headers(token),
            params={"per_page": 100}, timeout=15
        ).json() if r.get("tag_name") == tag_name), None)
        if target_rel:
            for asset in target_rel.get("assets", []):
                if asset.get("name") == gh_fname:
                    print(f"    [GitHub] asset {gh_fname} 已存在,跳过")
                    return "skip"

    r = github_upload_asset(token, upload_url_tpl, exe_path, fname=gh_fname)
    if r.status_code >= 300:
        print(f"    [GitHub] ✗ 上传 EXE 失败: {r.status_code} {r.text[:200]}")
        return False
    print(f"    [GitHub] ✓ EXE 上传成功 ({os.path.getsize(exe_path)/1024/1024:.1f} MB)")
    return True


# ═════════════ versions.json 更新 ═════════════
def update_versions_json_download_url(version, gitee_dl_url, github_dl_url):
    if not os.path.isfile(VERSIONS_JSON):
        print(f"  ✗ {VERSIONS_JSON} 不存在")
        return False
    try:
        with open(VERSIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ✗ 读取 versions.json 失败: {e}")
        return False

    updated = False
    for entry in data:
        if entry.get("version") == version:
            url = gitee_dl_url or github_dl_url or ""
            if url:
                entry["download_url"] = url
                updated = True
            break

    if updated:
        with open(VERSIONS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ versions.json download_url 已更新")
    else:
        print(f"  - versions.json 中未找到 version={version},跳过更新")
    return updated


# ═════════════ Main ═════════════
def main():
    import argparse
    parser = argparse.ArgumentParser(description="发布 EXE 到 Gitee + GitHub Releases")
    parser.add_argument("--dry-run", action="store_true", help="仅预览,不实际发布")
    parser.add_argument("--version", help="仅发布指定的版本号")
    parser.add_argument("--exe", help="直接指定 EXE 文件路径")
    parser.add_argument("--skip-gitee", action="store_true", help="跳过 Gitee")
    parser.add_argument("--skip-github", action="store_true", help="跳过 GitHub")
    args = parser.parse_args()

    if args.exe:
        exe_files = [args.exe]
    else:
        if not os.path.isdir(VER_DIR):
            print(f"✗ 目录不存在: {VER_DIR}")
            return 1
        exe_files = sorted(
            [os.path.join(VER_DIR, f) for f in os.listdir(VER_DIR) if f.endswith(".exe")],
            key=lambda p: os.path.getmtime(p), reverse=True
        )

    if not exe_files:
        print("✗ 没有找到 EXE 文件")
        return 1

    # Pre-fetch existing tags
    gitee_token = get_gitee_token()
    github_token = get_github_token()

    gitee_existing = None
    github_existing = None
    if not args.skip_gitee and gitee_token:
        try:
            gitee_existing = [r.get("tag_name") for r in gitee_list_releases(gitee_token)]
            print(f"✓ Gitee 已有 {len(gitee_existing)} 个 release")
        except Exception as e:
            print(f"  Gitee 获取列表失败: {e}")
    if not args.skip_github and github_token:
        try:
            github_existing = github_list_release_tags(github_token)
            print(f"✓ GitHub 已有 {len(github_existing)} 个 release")
        except Exception as e:
            print(f"  GitHub 获取列表失败: {e}")

    published = 0
    for exe_path in exe_files:
        fname = os.path.basename(exe_path)
        version = extract_version(fname)
        if not version:
            print(f"  ✗ 无法从文件名提取版本: {fname},跳过")
            continue
        if args.version and version != args.version:
            continue

        body = KNOWN_BODIES.get(version, f"云集智能音乐创意台 v{version} 发布")
        print(f"\n{'='*60}")
        print(f"  版本: v{version}")
        print(f"  文件: {fname}")
        print(f"  大小: {os.path.getsize(exe_path)/1024/1024:.1f} MB")
        print(f"{'='*60}")

        gitee_ok = True
        github_ok = True

        if not args.skip_gitee:
            print("\n  --- Gitee ---")
            result = publish_to_gitee(exe_path, version, body, dry_run=args.dry_run, existing_tags=gitee_existing)
            if result == "skip":
                print(f"  [Gitee] 已存在,跳过")
            elif not result:
                gitee_ok = False

        if not args.skip_github:
            print("\n  --- GitHub ---")
            result = publish_to_github(exe_path, version, body, dry_run=args.dry_run, existing_tags=github_existing)
            if result == "skip":
                print(f"  [GitHub] 已存在,跳过")
            elif not result:
                github_ok = False

        if not args.dry_run:
            gitee_dl = f"https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/releases/download/v{version}/{fname}"
            github_dl = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{version}/{github_release_fname(version)}"
            update_versions_json_download_url(version, gitee_dl, github_dl)

        if gitee_ok or github_ok:
            published += 1

    print(f"\n{'='*60}")
    print(f"  完成: {published}/{len(exe_files)} 个版本已发布")
    return 0


if __name__ == "__main__":
    sys.exit(main())
