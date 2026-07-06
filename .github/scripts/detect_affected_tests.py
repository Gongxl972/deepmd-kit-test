#!/usr/bin/env python3
import json
import os
import sys

def main():
    # ========== 1. 正确读取环境变量里的变更文件（核心修复点） ==========
    # CHANGED_FILES是通过<<EOF传入的，会保留换行符，需要split后过滤空行
    changed_files_raw = os.environ.get("CHANGED_FILES", "")
    print(f"DEBUG: Raw CHANGED_FILES from env: {repr(changed_files_raw)}")
    
    changed_files = [
        f.strip() 
        for f in changed_files_raw.split("\n") 
        if f.strip()
    ]
    print(f"DEBUG: Parsed changed files ({len(changed_files)}):")
    for cf in changed_files:
        print(f"  - {cf}")
    
    # 极端情况兜底：如果真的没读到变更，触发全量测试
    if not changed_files:
        print("No changed files found.")
        print("selected_paths=source/tests")
        print("skip_all=false")
        print("need_full_test=true")
        sys.exit(0)
    
    # ========== 2. 加载全局映射（过滤掉metadata字段） ==========
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
    
    # 过滤掉你映射里的metadata字段（它不是测试文件）
    mapping = {k: v for k, v in mapping.items() if k != "metadata"}
    print(f"DEBUG: Loaded {len(mapping)} test mappings (excluded metadata)")
    
    # ========== 3. 匹配变更文件和测试 ==========
    affected_tests = set()
    new_source_files_without_tests = []  # 记录新增的无覆盖源码
    
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
        
        # 情况C：变更的是源码文件，但没有测试依赖它（就是你这次的场景）
        if not found_match and cf.startswith("source/deepmd/"):
            print(f"DEBUG: Changed source file {cf} has no test coverage, marking for full test")
            new_source_files_without_tests.append(cf)
    
    # ========== 4. 输出最终结果（符合你的安全兜底逻辑） ==========
    if new_source_files_without_tests:
        # 新增源码无测试覆盖，主动触发全量测试（这才是预期的兜底逻辑）
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
