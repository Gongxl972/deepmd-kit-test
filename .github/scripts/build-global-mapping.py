- name: Build global test mapping (Safe Mode)
       run: |
         set -x
         echo "=========================================="
         echo "🔨 BUILDING GLOBAL TEST MAPPING (SAFE MODE)"
         echo "=========================================="
         
         # 如果缓存中有映射文件，直接使用
         if [ -f ".global_test_mapping.json" ] && [ -s ".global_test_mapping.json" ]; then
           echo "✅ Using cached global mapping"
           python .github/scripts/build_mapping.py
           echo "=========================================="
           echo "✅ GLOBAL MAPPING READY"
           echo "=========================================="
           exit 0
         fi
         
         echo "🆕 Building fresh global mapping..."
         
         # 方法1：使用find命令收集测试文件（永不触发段错误）
         echo "📁 Collecting test files using find..."
         find source/tests -name "test_*.py" -type f > test_files.txt || true
         
         # 验证收集结果
         if [ ! -s "test_files.txt" ]; then
           echo "❌ ERROR: No test files collected!"
           echo "{}" > .global_test_mapping.json
           exit 1
         fi
         
         TOTAL_FILES=$(wc -l < test_files.txt)
         echo "Found $TOTAL_FILES test files"
         
         # 构建全局映射（带超时保护和重试）
         MAX_RETRIES=3
         RETRY_DELAY=10
         SUCCESS=false
         
         for ((retry=1; retry<=MAX_RETRIES; retry++)); do
           echo "Attempt $retry of $MAX_RETRIES..."
           
           if timeout 600 python .github/scripts/build_mapping.py; then
             # 验证映射文件
             if [ -s ".global_test_mapping.json" ]; then
               echo "✅ Mapping built successfully"
               python -c '
               import json
               with open(".global_test_mapping.json", "r") as f:
                   mapping = json.load(f)
               print(f"Final mapping contains {len(mapping)} test files")
               '
               SUCCESS=true
               break
             else
               echo "❌ ERROR: Mapping file is empty!"
             fi
           else
             echo "❌ Attempt $retry failed!"
             if [ $retry -lt $MAX_RETRIES ]; then
               echo "Waiting ${RETRY_DELAY}s before retry..."
               sleep $RETRY_DELAY
             fi
           fi
         done
         
         if [ "$SUCCESS" = "true" ]; then
           echo "=========================================="
           echo "✅ GLOBAL MAPPING READY"
           echo "=========================================="
           exit 0
         else
           echo "❌ ERROR: Failed to build global mapping after $MAX_RETRIES attempts!"
           echo "Creating empty mapping as fallback..."
           echo "{}" > .global_test_mapping.json
           exit 1
         fi