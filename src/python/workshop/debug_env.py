#!/usr/bin/env python3
"""
Debug script to show which Python environment VS Code is using
"""

import sys
import os

print("=== VS Code Python Environment Debug ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[:3]}...")  # First 3 entries
print(f"Current working directory: {os.getcwd()}")

# Check if we're in a virtual environment
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"✅ Virtual environment detected")
    print(f"Virtual env prefix: {sys.prefix}")
else:
    print(f"❌ No virtual environment detected")

# Check key packages
packages_to_check = [
    'azure.ai.projects',
    'azure.ai.agents', 
    'azure.ai.evaluation',
    'streamlit'
]

print("\n=== Package Availability ===")
for package in packages_to_check:
    try:
        __import__(package)
        print(f"✅ {package}: Available")
    except ImportError as e:
        print(f"❌ {package}: Missing - {e}")

print("\n=== Environment Variables ===")
venv_vars = ['VIRTUAL_ENV', 'CONDA_DEFAULT_ENV', 'PYTHONPATH']
for var in venv_vars:
    value = os.environ.get(var)
    if value:
        print(f"{var}: {value}")
    else:
        print(f"{var}: Not set")
