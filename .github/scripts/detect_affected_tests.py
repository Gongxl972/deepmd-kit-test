#!/usr/bin/env python3
import json
import os
import sys
import sqlite3
import subprocess

def debug(msg):
    print(f"[DEBUG] {msg}", file=sys.stderr)

# 5. 粗粒度后端映射 (Fail-Closed)
BACKEND_MAPPING = {
    "source/deepmd/pt": ["source/tests/pt"],
    "source/deepmd/tf": ["source/tests/tf", "source/jax2tf_tests"],
    "source/deepmd/jax": ["source/tests/jax", "source/jax2tf_tests"],
    "source/deepmd/pd": ["source/tests/pd"],
    "source/deepmd/entrypoints": ["source/tests"],
    "source/deepmd/common.py": ["source/tests"],
}

def get_changed_files():
    path = os.environ.get("CHANGED_FILES_PATH")
    if path and os.path.exists(path):
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]
    return []

def query_testmon_affected(changed_files):
    db_path = ".testmondata"
    if not os.path.exists(db_path):
        return set()
    
    affected = set()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for f in changed_files:
            query = """
                SELECT DISTINCT node FROM block 
                WHERE select_id IN (
                    SELECT id FROM source_file WHERE filename LIKE ?
                )
            """
            cursor.execute(query, (f"%{f}%",))
            for row in cursor.fetchall():
                test_file = row[0].split("::")[0]
                if os.path.exists(test_file):
                    affected.add(test_file)
        conn.close()
    except Exception as e:
        debug(f"Query testmon failed: {e}")
    return affected

def main():
    changed_files = get_changed_files()
    if not changed_files:
        debug("No changed files found, skipping execution.")
        print("skip_all=true\nselected_paths=\nneed_full_test=false")
        sys.exit(0)

    selected_paths = set()
    need_full_test = False

    for cf in changed_files:
        # CI / C++ / 全局配置文件更改 -> 触发全量
        if any(cf.startswith(prefix) for prefix in [".github/", "CMakeLists.txt", "setup.py", "pyproject.toml"]):
            need_full_test = True
            break
        
        # 粗粒度后端映射匹配
        matched_backend = False
        for prefix, target_dirs in BACKEND_MAPPING.items():
            if cf.startswith(prefix):
                selected_paths.update(target_dirs)
                matched_backend = True
        
        if cf.startswith("source/tests/"):
            selected_paths.add(cf)

    if need_full_test:
        print("selected_paths=source/tests\nskip_all=false\nneed_full_test=true")
        sys.exit(0)

    # 6. pytest-testmon 真实执行轨迹扩展
    testmon_affected = query_testmon_affected(changed_files)
    selected_paths.update(testmon_affected)

    if not selected_paths:
        # 安全退化：改了 source 但没有命中任何映射 -> 运行全量 source/tests (Fail-Closed)
        print("selected_paths=source/tests\nskip_all=false\nneed_full_test=true")
    else:
        paths_str = " ".join(sorted(selected_paths))
        print(f"selected_paths={paths_str}\nskip_all=false\nneed_full_test=false")

if __name__ == "__main__":
    main()