#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def analyze_test_changes(changed_files_path):
    if not Path(changed_files_path).exists():
        return "low"
    
    with open(changed_files_path, 'r') as f:
        changed_files = [line.strip() for line in f if line.strip()]
    
    test_files = [f for f in changed_files if f.startswith("source/tests/") and f.endswith(".py")]
    if not test_files:
        return "low"
    
    risk_level = "low"
    high_risk_keywords = [
        r"assert\s+(energy|force|virial)",
        r"tolerance\s*=",
        r"check_consistency",
        r"source/tests/consistent/",
        r"@pytest\.fixture",
        r"def\s+test_.*energy",
        r"def\s+test_.*force",
        r"def\s+test_.*virial",
        r"def\s+test_.*stress",
    ]
    medium_risk_keywords = [
        r"np\.allclose",
        r"pytest\.approx",
        r"def\s+test_",
        r"@pytest\.mark\.parametrize",
    ]
    
    for test_file in test_files:
        try:
            content = Path(test_file).read_text()
            for kw in high_risk_keywords:
                if re.search(kw, content, re.IGNORECASE | re.MULTILINE):
                    risk_level = "high"
                    break
            if risk_level == "high":
                break
            for kw in medium_risk_keywords:
                if re.search(kw, content, re.IGNORECASE | re.MULTILINE):
                    risk_level = "medium"
                    break
        except FileNotFoundError:
            continue
        except Exception:
            risk_level = "high"
            break
    
    return risk_level

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)
    risk = analyze_test_changes(sys.argv[1])
    print(f"test_change_risk={risk}")
