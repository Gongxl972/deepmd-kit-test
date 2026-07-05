#!/usr/bin/env python3
import json
import os
import sys
import subprocess

def main():
    # 从环境变量获取参数
    mapping_file = ".global_test_mapping.json"
    changed_files_str = os.environ.get("CHANGED_FILES", "")
    base_sha = os.environ.get("BASE_SHA", "")
    
    if not changed_files_str:
        print("No changed files found.")
        sys.exit(0)
    
    changed_files = [f.strip() for f in changed_files_str.strip().split("\n") if f.strip()]
    
    # 加载全局映射
    with open(mapping_file, "r") as f:
        global_mapping = json.load(f)
    
    affected_tests = set()
    matched_files = 0
    unmatched_files = 0
    new_files = 0
    need_full_test = False
    
    for changed_file in changed_files:
        print(f"Processing changed file: {changed_file}")
        
        # 检查文件是否是新添加的
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{base_sha}:{changed_file}"],
            capture_output=True,
            text=True
        )
        is_new_file = (result.returncode != 0)
        
        if is_new_file:
            print(f"  🆕 File is newly added in this PR")
            new_files += 1
            if changed_file.startswith("source/deepmd/"):
                print(f"  ⚠️ New source file without test coverage - will trigger full test")
                need_full_test = True
            continue
        else:
            print(f"  ℹ️ File exists in base branch (modified)")
        
        # 规范化文件路径
        normalized_file = changed_file
        if changed_file.startswith("deepmd/"):
            normalized_file = "source/" + changed_file
        
        # 在全局映射中查找依赖此文件的测试
        matching_tests = []
        for test_file, info in global_mapping.items():
            deps = info.get("dependencies", [])
            if any(normalized_file in dep or dep in normalized_file for dep in deps):
                matching_tests.append(test_file)
        
        if matching_tests:
            print(f"  ✅ Found {len(matching_tests)} matching tests:")
            for test_file in matching_tests:
                print(f"    - {test_file}")
                affected_tests.update(matching_tests)
            matched_files += 1
        else:
            print(f"  ❌ No tests found depending on {normalized_file}")
            unmatched_files += 1
    
    print(f"\n📊 MAPPING SUMMARY:")
    print(f"  Total changed files: {len(changed_files)}")
    print(f"  Files with matching tests: {matched_files}")
    print(f"  Files without matches: {unmatched_files}")
    print(f"  New files added: {new_files}")
    print(f"  Need full test: {need_full_test}")
    
    # 去重并排序
    if affected_tests:
        affected_tests_sorted = sorted(affected_tests)
        print(f"\n🎯 AFFECTED TESTS: {' '.join(affected_tests_sorted)}")
    
    # 决定是否全量测试
    if need_full_test or not affected_tests:
        print(f"\n🚨 TRIGGERING FULL TEST SUITE")
        print("selected_paths=source/tests")
        print("skip_all=false")
        print("need_full_test=true")
    else:
        print(f"\n🎯 RUNNING INCREMENTAL TESTS ONLY")
        print(f"selected_paths={' '.join(affected_tests_sorted)}")
        print("skip_all=false")
        print("need_full_test=false")

if __name__ == "__main__":
    main()