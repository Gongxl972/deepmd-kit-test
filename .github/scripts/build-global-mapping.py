#!/usr/bin/env python3
"""
构建全局测试映射的脚本
用于 GitHub Actions 工作流中
"""

import json
import sys
import os
import ast
import time

def extract_dependencies_and_functions(test_file):
    """从测试文件中提取依赖和测试函数"""
    dependencies = []
    test_functions = []
    
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 跳过过大的文件
        if len(content) > 1024000:  # 1MB限制
            print(f"Skipping large file: {test_file}", file=sys.stderr)
            return None
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            # 收集测试函数
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_functions.append(node.name)
            
            # 收集 import deepmd.*
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("deepmd"):
                        module_path = alias.name.replace(".", "/") + ".py"
                        dep = "source/" + module_path
                        dependencies.append(dep)
            
            # 收集 from deepmd.xxx import yyy
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("deepmd"):
                base = node.module.replace(".", "/")
                if node.names:
                    for alias in node.names:
                        if alias.name == "*":
                            dep = f"source/{base}.py"
                        else:
                            dep = f"source/{base}/{alias.name}.py"
                        
                        if not os.path.exists(dep):
                            dep = f"source/{base}.py"
                        
                        dependencies.append(dep)
    except SyntaxError:
        # 忽略语法错误（可能是正在开发的代码）
        pass
    except Exception as e:
        print(f"Error parsing {test_file}: {e}", file=sys.stderr)
    
    return {
        "dependencies": sorted(set(dependencies)),
        "test_functions": sorted(set(test_functions))
    }

def main():
    # 检查测试文件列表是否存在
    if not os.path.exists("test_files.txt"):
        print("Error: test_files.txt not found!", file=sys.stderr)
        sys.exit(1)
    
    # 读取测试文件列表
    with open("test_files.txt", "r") as f:
        test_files = [line.strip() for line in f if line.strip()]
    
    mapping = {}
    processed = 0
    total = len(test_files)
    start_time = time.time()
    
    for test_file in test_files:
        processed += 1
        if processed % 100 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {processed}/{total} files ({elapsed:.1f}s)", file=sys.stderr)
        
        if not os.path.exists(test_file):
            continue
        
        result = extract_dependencies_and_functions(test_file)
        if result:
            mapping[test_file] = result
    
    # 清理空条目
    mapping = {k: v for k, v in mapping.items() 
               if v["dependencies"] or v["test_functions"]}
    
    # 写入全局映射文件
    with open(".global_test_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    
    elapsed = time.time() - start_time
    print(f"✅ Built global mapping with {len(mapping)} test files in {elapsed:.1f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
