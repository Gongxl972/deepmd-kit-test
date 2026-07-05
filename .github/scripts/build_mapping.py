import json
import sys
import os
import ast
import time

def main():
    print(f"Starting AST parsing at {time.strftime('%H:%M:%S')}")
    start_time = time.time()

    mapping = {}
    processed = 0

    with open("test_files.txt") as f:
        test_files = [line.strip() for line in f if line.strip()]

    for test_file in test_files:
        processed += 1
        if processed % 100 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {processed}/{len(test_files)} files ({elapsed:.1f}s)")
        
        if not os.path.exists(test_file):
            continue
        
        mapping[test_file] = {
            "dependencies": [],
            "test_functions": []
        }
        
        try:
            with open(test_file, "r") as f:
                content = f.read()
            
            # 跳过过大的文件（防止内存问题）
            if len(content) > 1024000:  # 1MB限制
                print(f"Skipping large file: {test_file} ({len(content)} bytes)")
                continue
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # 收集测试函数
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        mapping[test_file]["test_functions"].append(node.name)
                
                # 收集import deepmd.*
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("deepmd"):
                            module_path = alias.name.replace(".", "/") + ".py"
                            dep = "source/" + module_path
                            if dep not in mapping[test_file]["dependencies"]:
                                mapping[test_file]["dependencies"].append(dep)
                
                # 收集from deepmd.xxx import yyy
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("deepmd"):
                        base = node.module.replace(".", "/")
                        if node.names:
                            for alias in node.names:
                                if alias.name == "*":
                                    dep = f"source/{base}.py"
                                else:
                                    dep = f"source/{base}/{alias.name}.py"
                                # 如果文件不存在，尝试__init__.py
                                if not os.path.exists(dep):
                                    dep = f"source/{base}.py"
                                if dep not in mapping[test_file]["dependencies"]:
                                    mapping[test_file]["dependencies"].append(dep)
        except SyntaxError as e:
            print(f"SyntaxError in {test_file}: {e}", file=sys.stderr)
            continue
        except MemoryError:
            print(f"MemoryError processing {test_file}, skipping", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error parsing {test_file}: {e}", file=sys.stderr)
            continue

    # 保存全局映射
    with open(".global_test_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)

    elapsed = time.time() - start_time
    print(f"✅ Built global mapping with {len(mapping)} test files in {elapsed:.1f}s")

if __name__ == "__main__":
    main()