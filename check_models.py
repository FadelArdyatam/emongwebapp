#!/usr/bin/env python3
"""
Script untuk mengecek model files
"""

import os
import sys

def check_models():
    """Cek semua model files"""
    print("🤖 Checking AI Models...")
    print("=" * 40)
    
    # Model files yang diperlukan
    model_files = [
        'models/convertedmodels/emotion.onnx',
        'models/convertedmodels/arcface.onnx',
        'models/convertedmodels/retinaface_mobilenet25.onnx',
        'models/convertedmodels/retinaface_resnet50.onnx'
    ]
    
    all_found = True
    
    for model_file in model_files:
        exists = os.path.exists(model_file)
        status = "✅" if exists else "❌"
        print(f"{status} {model_file}")
        
        if not exists:
            all_found = False
    
    print("=" * 40)
    
    if all_found:
        print("🎉 All model files found!")
        return True
    else:
        print("⚠️ Some model files are missing!")
        return False

def check_model_sizes():
    """Cek ukuran model files"""
    print("\n📊 Model File Sizes:")
    print("=" * 40)
    
    model_files = [
        'models/convertedmodels/emotion.onnx',
        'models/convertedmodels/arcface.onnx',
        'models/convertedmodels/retinaface_mobilenet25.onnx',
        'models/convertedmodels/retinaface_resnet50.onnx'
    ]
    
    for model_file in model_files:
        if os.path.exists(model_file):
            size = os.path.getsize(model_file)
            size_mb = size / (1024 * 1024)
            print(f"📁 {os.path.basename(model_file):25} | {size_mb:8.2f} MB")
        else:
            print(f"❌ {os.path.basename(model_file):25} | Missing")

if __name__ == '__main__':
    success = check_models()
    check_model_sizes()
    
    if success:
        print("\n✅ Model check completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Model check failed!")
        sys.exit(1)
