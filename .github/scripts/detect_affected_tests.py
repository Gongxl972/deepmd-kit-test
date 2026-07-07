#!/usr/bin/env python3
import json
import os
import sys

def main():
    changed_files = []

    # ✅ 1️⃣ 优先从文件读取（最可靠）
    path = os.environ.get("CHANGED_FILES_PATH")
    if path and os.path.exists(path):
        print(f"DEBUG: Reading changed files from file: {path}")
        with open(path, "r") as f:
            changed_files = [l.strip() for l in f if l.strip()]
    else:
        # ✅ 2️⃣ 兜底：单行环境变量
        raw = os.environ.get("CHANGED_FILES", "")
        if raw:
            changed_files = raw.split()

    print(f"DEBUG: Parsed changed files ({len(changed_files)}):")
    for f in changed_files:
        print(f"  - {f}")

    if not changed_files:
        print("No changed files found.")
        print("selected_paths=source/tests")
        print("skip_all=false")
        print("need_full_test=true")
        sys.exit(0)

    # ✅ 后续逻辑不变 …
    
