#!/usr/bin/env python3
"""
Analyze test changes and determine risk level.
Risk levels:
- low: Pure scaffolding changes (logging, skip conditions, non-validation logic)
- medium: Test validation logic tweaks (tolerance adjustments, data preprocessing)
- high: Core test scenarios or consistency changes (new boundary cases, consistency tests)
"""
import sys
import re
from pathlib import Path

def analyze_test_changes(changed_files_path):
    """Analyze test changes and return risk level."""
    if not Path(changed_files_path).exists():
        return "low"
    
    with open(changed_files_path, 'r') as f:
        changed_files = [line.strip() for line in f if line.strip()]
    
    # Only consider Python test files
    test_files = [f for f in changed_files if f.startswith("source/tests/") and f.endswith(".py")]
    if not test_files:
        return "low"
    
    risk_level = "low"
    
    # High-risk keywords (core validation changes)
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
    
    # Medium-risk keywords (validation tweaks)
    medium_risk_keywords = [
        r"np\.allclose",
        r"pytest\.approx",
        r"def\s+test_",
        r"@pytest\.mark\.parametrize",
    ]
    
    for test_file in test_files:
        try:
            content = Path(test_file).read_text()
            
            # Check for high-risk patterns first
            for kw in high_risk_keywords:
                if re.search(kw, content, re.IGNORECASE | re.MULTILINE):
                    risk_level = "high"
                    print(f"High-risk pattern found in {test_file}: {kw}", file=sys.stderr)
                    break
            
            if risk_level == "high":
                break
                
            # Check for medium-risk patterns
            for kw in medium_risk_keywords:
                if re.search(kw, content, re.IGNORECASE | re.MULTILINE):
                    risk_level = "medium"
                    print(f"Medium-risk pattern found in {test_file}: {kw}", file=sys.stderr)
                    break
                    
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Error reading {test_file}: {e}", file=sys.stderr)
            risk_level = "high"  # Conservative approach on error
            break
    
    return risk_level

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze_test_changes.py <changed_files_path>", file=sys.stderr)
        sys.exit(1)
    
    risk = analyze_test_changes(sys.argv[1])
    print(f"test_change_risk={risk}")
    sys.exit(0)
