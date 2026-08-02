#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除指定版本的 Gitee + GitHub Release（含 tag）。先 --dry-run 核对，再正式删。

删除目标（推荐方案）：
- TARGETS   : 所有 v2026.07.* 应用版本（双仓库并集，GitHub 34 个已覆盖 Gitee 8 个），均为有问题历史 release。
- EXTRA_TAGS: 明确指向坏版本的独立 git tag（milestone / stable 早期版）。
保留：v2026.08.02.0810 / v2026.08.02.1135（官方正式版）、wheels / frontend（资源分发通道）。
"""
import os, sys, requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_GITEE = os.path.join(PROJECT_ROOT, "dev", "app", ".gitee_token")
TOKEN_GITHUB = os.path.join(PROJECT_ROOT, "dev", "app", ".github_token")

GITEE_OWNER, GITEE_REPO = "yunjii", "music"
GITHUB_OWNER, GITHUB_REPO = "yunjii-cn", "music"
GITEE_API = "https://gitee.com/api/v5"
GITHUB_API = "https://api.github.com"

TARGETS = [
    "2026.07.30.0710", "2026.07.30.0605", "2026.07.30.0526", "2026.07.30.0441",
    "2026.07.29.1022", "2026.07.29.0852", "2026.07.29.0748", "2026.07.29.0702",
    "2026.07.29.0631", "2026.07.29.0530", "2026.07.29.0451", "2026.07.29.0431",
    "2026.07.29.0417", "2026.07.28.0843", "2026.07.28.0800", "2026.07.28.0756",
    "2026.07.28.0621", "2026.07.28.0612", "2026.07.28.0340", "2026.07.28.0227",
    "2026.07.28.0041", "2026.07.27.2238", "2026.07.27.2233", "2026.07.27.2150",
    "2026.07.29.1015", "2026.07.29.0911", "2026.07.27.1140", "2026.07.27.0733",
    "2026.07.27.0339", "2026.07.27.0148", "2026.07.26.2338", "2026.07.26.1817",
]
EXTRA_TAGS = ["milestone-firstrun-v2026.08.01.1423", "stable-v2026.05.26.0336"]


def read_token(p):
    if not os.path.isfile(p):
        return ""
    return open(p, encoding="utf-8").read().strip()


def main():
    dry = "--dry-run" in sys.argv
    gitee_tok = read_token(TOKEN_GITEE)
    github_tok = read_token(TOKEN_GITHUB)
    print(f"gitee_token={'Y' if gitee_tok else 'N'}  github_token={'Y' if github_tok else 'N'}  dry_run={dry}")

    hdr = {"Authorization": f"Bearer {github_tok}", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "YunJii-Publisher/1.0"}

    # ---- Gitee ----
    print("\n=== Gitee (TARGETS) ===")
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
                dt = requests.delete(f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/tags/{tag}",
                                     params={"access_token": gitee_tok}, timeout=15)
                print(f"    -> DELETE tag: {dt.status_code}")

    # ---- GitHub ----
    print("\n=== GitHub (TARGETS) ===")
    if github_tok:
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

    # ---- EXTRA_TAGS（独立 git tag，仅删 ref）----
    print("\n=== EXTRA_TAGS (git tag ref only) ===")
    for tag in EXTRA_TAGS:
        if gitee_tok:
            st = "SKIP(dry)" if dry else ""
            if not dry:
                dt = requests.delete(f"{GITEE_API}/repos/{GITEE_OWNER}/{GITEE_REPO}/tags/{tag}",
                                     params={"access_token": gitee_tok}, timeout=15)
                st = f"DELETE tag -> {dt.status_code}"
            print(f"  [Gitee] {tag}: {st}")
        if github_tok:
            st = "SKIP(dry)" if dry else ""
            if not dry:
                dt = requests.delete(f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/refs/tags/{tag}",
                                     headers=hdr, timeout=15)
                st = f"DELETE tag ref -> {dt.status_code}"
            print(f"  [GitHub] {tag}: {st}")


if __name__ == "__main__":
    main()
