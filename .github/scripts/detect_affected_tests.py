#!/usr/bin/env python3
import json
import os
import sys

def main():
    # ========== 1. 优先从文件读取变更文件列表（最可靠的方式） ==========
    changed_files_path = os.environ.get("CHANGED_FILES_PATH", "")
    changed_files_raw = ""
    
    if changed_files_path and os.path.exists(changed_files_path):
        print(f"DEBUG: Reading changed files from file: {changed_files_path}")
        with open(changed_files_path, 'r') as f:
            changed_files_raw = f.read()
    else:
        # 回退到环境变量（兼容性）
        changed_files_raw = os.environ.get("CHANGED_FILES_SINGLELINE", "")
        if not changed_files_raw:
            changed_files_raw = os.environ.get("CHANGED_FILES", "")
        print(f"DEBUG: Reading changed files from environment variable")
    
    print(f"DEBUG: Raw CHANGED_FILES input: {repr(changed_files_raw)}")
    
    # 处理变更文件列表
    if "\n" in changed_files_raw:
        # 多行格式（来自文件）
        changed_files = [
            f.strip() 
            for f in changed_files_raw.split("\n") 
            if f.strip()
        ]
    else:
        # 单行格式（用空格分隔）
        changed_files = [
            f.strip() 
            for f in changed_files_raw.split() 
            if f.strip()
        ]
    
    print(f"DEBUG: Parsed changed files ({len(changed_files)}):")
    for cf in changed_files:
        print(f"  - {cf}")
    
    # 如果没有变更文件，触发全量测试
    if not changed_files:
        print("No changed files found.")
        print("selected_paths=source/tests")
        print("skip_all=false")
        print("need_full_test=true")
        sys.exit(0)
    
    # ========== 2. 加载全局映射 ==========
    mapping_path = ".global_test_mapping.json"
    if not os.path.exists(mapping_path):
        print(f"Mapping file {mapping_path} not found, fallback to full test.")
        print("selected_paths=source/tests")
        print("skip_all=false")
        print("need_full_test=true")
        sys.exit(0)
    
    with open(mapping_path, "r") as f:
        try:
            mapping = json.load(f)
        except json.JSONDecodeError:
            print("Invalid mapping JSON, fallback to full test.")
            print("selected_paths=source/tests")
            print("skip_all=false")
            print("need_full_test=true")
            sys.exit(0)
    
    # 过滤掉metadata字段
    mapping = {k: v for k, v in mapping.items() if k != "metadata"}
    print(f"DEBUG: Loaded {len(mapping)} test mappings (excluded metadata)")
    
    # ========== 3. 匹配变更文件和测试 ==========
    affected_tests = set()
    new_source_files_without_tests = []
    
    for cf in changed_files:
        print(f"DEBUG: Processing changed file: {cf}")
        
        # 情况A：变更的是测试文件，直接加入待运行列表
        if cf.startswith("source/tests/"):
            print(f"DEBUG: Changed file is a test file, adding to affected tests: {cf}")
            affected_tests.add(cf)
            continue
        
        # 情况B：变更的是源码文件，去映射里找依赖它的测试
        found_match = False
        for test_file, meta in mapping.items():
            dependencies = meta.get("dependencies", [])
            if cf in dependencies:
                print(f"DEBUG: Found test {test_file} depends on {cf}, adding to affected tests")
                affected_tests.add(test_file)
                found_match = True
        
        # 情况C：变更的是源码文件，但没有测试依赖它
        if not found_match and cf.startswith("source/deepmd/"):
            print(f"DEBUG: Changed source file {cf} has no test coverage, marking for full test")
            new_source_files_without_tests.append(cf)
    
    # ========== 4. 输出最终结果 ==========
    if new_source_files_without_tests:
        # 新增源码无测试覆盖，主动触发全量测试
        print(f"New source files without test coverage: {new_source_files_without_tests}")
        print("selected_paths=source/tests")
        print("skip_all=false")
        print("need_full_test=true")
    elif affected_tests:
        # 匹配到受影响的测试，只运行这些测试
        selected = " ".join(sorted(affected_tests))
        print(f"Affected tests found: {selected}")
        print(f"selected_paths={selected}")
        print("skip_all=false")
        print("need_full_test=false")
    else:
        # 没有匹配到任何测试，且没有新增源码，跳过测试
        print("No affected tests found and no new source files.")
        print("selected_paths=")
        print("skip_all=true")
        print("need_full_test=false")

if __name__ == "__main__":
    main()
