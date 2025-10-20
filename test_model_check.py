#!/usr/bin/env python3
"""
Test script untuk model checking
"""

import os
import sys

# Import fungsi check_models dari start_app_safe.py
sys.path.append('.')
from start_app_safe import check_models

def main():
    print("🧪 Testing Model Check Function...")
    print("=" * 50)
    
    # Test check_models function
    result = check_models()
    
    print("=" * 50)
    if result:
        print("✅ Model check PASSED!")
        return 0
    else:
        print("❌ Model check FAILED!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
