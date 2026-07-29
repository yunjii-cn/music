#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 dist/ 下本地构建的 exe 按版本号上传为 Gitee release 资产，
使「软件版本」栏的下载地址真正可用（下载 URL 模板指向
https://gitee.com/yunjii/music/releases/download/v{version}/{filename}）。

用法：
  python upload_releases.py            # 上传 dist/ 下所有 exe
  python upload_releases.py --only 2026.07.29.0631,2026.07.29.0530
  python upload_releases.py --dry-run  # 只打印将要上传的版本，不实际上传
"""
import os
import re
import sys
import time
import argparse
from pathlib import Path
from urllib.parse import quote

import requests

OWNER = "yunjii"
REPO = "music"
API = f"https://gitee.com/api/v5/repos/{OWNER}/{REPO}"

HERE = Path(__file__).resolve().parent
DIST = HERE.parent.parent / "dist"
TOKEN_FILE = HERE / ".gitee_token"


def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return os.environ.get("GITEE_TOKEN", "")


def log(msg):
    print(msg, flush=True)


def release_exists(token, tag):
    """返回已存在 release 的 id，否则 None"""
    r = requests.get(
        f"{API}/releases/tags/{tag}",
        params={"access_token": token},
        timeout=20,
    )
    if r.status_code == 200:
        try:
            return r.json().get("id")
        except Exception:
            return None
    return None


def create_release(token, tag, body):
    r = requests.post(
        f"{API}/releases",
        params={"access_token": token},
        json={
            "tag_name": tag,
            "name": tag,
            "body": body,
            "target_commitish": "main",
            "prerelease": False,
        },
        timeout=30,
    )
    if r.status_code in (200, 201):
        return r.json().get("id")
    # 标签已存在但无 release：尝试按 tag 取
    rid = release_exists(token, tag)
    if rid:
        return rid
    log(f"  [!] 创建 release {tag} 失败: HTTP {r.status_code} {r.text[:200]}")
    return None


def asset_already_present(token, release_id, filename):
    r = requests.get(
        f"{API}/releases/{release_id}/attach_files",
        params={"access_token": token},
        timeout=20,
    )
    if r.status_code == 200:
        try:
            for a in r.json():
                if a.get("name") == filename:
                    return True
        except Exception:
            pass
    return False


def upload_asset(token, release_id, filepath):
    with open(filepath, "rb") as f:
        r = requests.post(
            f"{API}/releases/{release_id}/attach_files",
            params={"access_token": token},
            files={"file": (filepath.name, f, "application/octet-stream")},
            timeout=600,
        )
    if r.status_code in (200, 201):
        return True
    log(f"  [!] 上传资产失败: HTTP {r.status_code} {r.text[:200]}")
    return False


# ── GitHub Releases 上传（国内走 ghproxy 镜像下载，此处为上传端）──
GITHUB_OWNER = "yunjii-cn"
GITHUB_REPO = "music"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_UPLOAD = f"https://uploads.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"


def get_github_token():
    p = HERE / ".github_token"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return os.environ.get("GITHUB_TOKEN", "")


def gh_release_exists(token, tag):
    r = requests.get(
        f"{GITHUB_API}/releases/tags/{tag}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=20,
    )
    if r.status_code == 200:
        return r.json().get("id")
    return None


def gh_create_release(token, tag):
    r = requests.post(
        f"{GITHUB_API}/releases",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={
            "tag_name": tag,
            "name": tag,
            "body": f"稳定版 {tag}",
            "target_commitish": "main",
            "prerelease": False,
        },
        timeout=30,
    )
    if r.status_code in (200, 201):
        return r.json().get("id")
    rid = gh_release_exists(token, tag)
    if rid:
        return rid
    log(f"  [!] 创建 GitHub release {tag} 失败: HTTP {r.status_code} {r.text[:200]}")
    return None


def gh_upload_asset(token, release_id, filepath):
    # GitHub release 资产名不支持中文（会被静默丢弃前缀），统一用 ASCII 名
    m = re.search(r"v(\d+\.\d+\.\d+\.\d+)\.exe$", filepath.name)
    ascii_name = f"yunji-music-v{m.group(1)}.exe" if m else filepath.name
    # 删除任何同名（中文原名或旧 ascii）资产，避免 422
    rel = requests.get(
        f"{GITHUB_API}/releases/{release_id}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=20,
    )
    if rel.status_code == 200:
        for a in rel.json().get("assets", []):
            _n = a.get("name", "")
            if _n in (filepath.name, ascii_name) or _n.startswith("-v"):
                requests.delete(
                    f"{GITHUB_API}/releases/assets/{a['id']}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=20,
                )
    with open(filepath, "rb") as f:
        r = requests.post(
            f"{GITHUB_UPLOAD}/{release_id}/assets",
            params={"name": ascii_name},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
            data=f,
            timeout=600,
        )
    if r.status_code in (200, 201):
        return True
    log(f"  [!] GitHub 上传资产失败: HTTP {r.status_code} {r.text[:200]}")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只上传指定版本，逗号分隔，如 2026.07.29.0631,2026.07.29.0530")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--github", action="store_true", help="同时上传到 GitHub Releases (yunjii-cn/music)，需 .github_token")
    args = ap.parse_args()

    token = get_token()
    if not token:
        log("[错误] 未找到 Gitee token（.gitee_token 或 GITEE_TOKEN 环境变量）")
        sys.exit(1)

    gh_token = ""
    if args.github:
        gh_token = get_github_token()
        if not gh_token:
            log("[错误] 启用 --github 但未找到 GitHub token（.github_token 或 GITHUB_TOKEN 环境变量）")
            sys.exit(1)

    exes = sorted(DIST.glob("*.exe"))
    if not exes:
        log(f"[错误] dist 目录无 exe: {DIST}")
        sys.exit(1)

    pattern = re.compile(r"v(\d+\.\d+\.\d+\.\d+)\.exe$")
    targets = []
    for p in exes:
        m = pattern.search(p.name)
        if m:
            targets.append((m.group(1), p))
        else:
            log(f"  [跳过] 无法解析版本: {p.name}")

    if args.only:
        want = set(args.only.split(","))
        targets = [(v, p) for v, p in targets if v in want]

    log(f"待处理版本数: {len(targets)}")
    ok, skip, fail = 0, 0, 0
    for ver, p in targets:
        tag = f"v{ver}"
        size_mb = p.stat().st_size / (1024 * 1024)
        log(f"\n== {tag}  ({size_mb:.1f} MB) ==")
        if args.dry_run:
            log("  [dry-run] 跳过实际上传")
            continue
        # 默认（无 --github）：仅上传 Gitee；--github：仅上传 GitHub（保持 Gitee 精简）。
        # 两者不混传，避免清理后的 Gitee 配额再次被旧版本占满。
        if args.github:
            if not gh_token:
                log("  [错误] 未找到 GitHub token")
                fail += 1
            else:
                grid = gh_release_exists(gh_token, tag)
                if grid is None:
                    grid = gh_create_release(gh_token, tag)
                if grid is None:
                    log("  [GitHub] 创建 release 失败")
                    fail += 1
                elif gh_upload_asset(gh_token, grid, p):
                    log("  [GitHub] 上传完成")
                    ok += 1
                else:
                    fail += 1
        else:
            rid = release_exists(token, tag)
            if rid is None:
                rid = create_release(token, tag, f"稳定版 {tag}")
            if rid is None:
                fail += 1
            elif asset_already_present(token, rid, p.name):
                log("  [Gitee] 资产已存在，跳过")
                skip += 1
            elif upload_asset(token, rid, p):
                log("  [Gitee] 上传完成")
                ok += 1
            else:
                fail += 1
        time.sleep(1)

    log(f"\n完成: 成功 {ok} / 已存在跳过 {skip} / 失败 {fail}")


if __name__ == "__main__":
    main()
