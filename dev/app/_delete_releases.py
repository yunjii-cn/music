#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除指定版本的 Gitee + GitHub Release（含 tag）。先 --dry-run 核对，再正式删。"""
import os, sys, json, requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_GITEE = os.path.join(PROJECT_ROOT, "dev", "app", ".gitee_token")
TOKEN_GITHUB = os.path.join(PROJECT_ROOT, "dev", "app", ".github_token")

GITEE_OWNER, GITEE_REPO = "yunjii", "music"
GITHUB_OWNER, GITHUB_REPO = "yunjii-cn", "music"
GITEE_API = "https://gitee.com/api/v5"
GITHUB_API = "https://api.github.com"

TARGETS = ["2026.08.01.1423", "2026.07.03.0635", "2026.05.26.0336"]


def read_token(p):
    if not os.path.isfile(p):
        return ""
    return open(p, encoding="utf-8").read().strip()


def main():
    dry = "--dry-run" in sys.argv
    gitee_tok = read_token(TOKEN_GITEE)
    github_tok = read_token(TOKEN_GITHUB)
    print(f"gitee_token={'Y' if gitee_tok else 'N'}  github_token={'Y' if github_tok else 'N'}  dry_run={dry}")

    # ---- Gitee ----
    print("\n=== Gitee ===")
    if gitee_tok:
        rels = requests.get(f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/releases",
                            params={"access_token": gitee_tok, "per_page": 100}, timeout=15).json()
        by_tag = {r.get("tag_name"): r for r in rels}
        for v in TARGETS:
            tag = f"v{v}"
            r = by_tag.get(tag)
            if not r:
                print(f"  [Gitee] {tag}: 未找到 release，跳过")
                continue
            rid = r.get("id")
            print(f"  [Gitee] {tag}: release id={rid} name={r.get('name')}")
            if not dry:
                d = requests.delete(f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/{rid}",
                                    params={"access_token": gitee_tok}, timeout=15)
                print(f"    -> DELETE release: {d.status_code}")
                # 删 tag
                dt = requests.delete(f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/tags/{tag}",
                                     params={"access_token": gitee_tok}, timeout=15)
                print(f"    -> DELETE tag: {dt.status_code}")

    # ---- GitHub ----
    print("\n=== GitHub ===")
    if github_tok:
        hdr = {"Authorization": f"Bearer {github_tok}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "YunJii-Publisher/1.0"}
        rels = requests.get(f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
                            headers=hdr, params={"per_page": 100}, timeout=15).json()
        by_tag = {r.get("tag_name"): r for r in rels}
        for v in TARGETS:
            tag = f"v{v}"
            r = by_tag.get(tag)
            if not r:
                print(f"  [GitHub] {tag}: 未找到 release，跳过")
                continue
            rid = r.get("id")
            print(f"  [GitHub] {tag}: release id={rid}")
            if not dry:
                d = requests.delete(f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/{rid}",
                                    headers=hdr, timeout=15)
                print(f"    -> DELETE release: {d.status_code}")
                dt = requests.delete(f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/refs/tags/{tag}",
                                     headers=hdr, timeout=15)
                print(f"    -> DELETE tag ref: {dt.status_code}")


if __name__ == "__main__":
    main()
