#!/usr/bin/env python3
"""
Setup script for Maintenance Agent - Creates virtual environment and installs dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return True
    
    print("🔨 Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_activation_command():
    """Get the correct activation command based on OS"""
    if os.name == 'nt':  # Windows
        return "venv\\Scripts\\activate"
    else:  # macOS/Linux
        return "source venv/bin/activate"

def install_dependencies_in_venv():
    """Install dependencies in the virtual environment"""
    print("📦 Installing dependencies in virtual environment...")
    
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = Path("venv/Scripts/pip")
    else:  # macOS/Linux
        pip_path = Path("venv/bin/pip")
    
    try:
        # Upgrade pip first
        subprocess.check_call([str(pip_path), "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([str(pip_path), "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully in virtual environment")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_requirements_file():
    """Check if requirements.txt exists"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print("✅ Found requirements.txt")
    return True

def create_activation_script():
    """Create a script to activate the environment and run the agent"""
    activate_cmd = get_activation_command()
    
    if os.name == 'nt':  # Windows
        script_content = f'''@echo off
echo 🔧 Maintenance Agent - Activating Virtual Environment
echo ====================================================
call {activate_cmd}
echo ✅ Virtual environment activated
echo 🚀 Starting maintenance agent test...
python test_agent.py
'''
        script_name = "run_agent.bat"
    else:  # macOS/Linux
        script_content = f'''#!/bin/bash
echo "🔧 Maintenance Agent - Activating Virtual Environment"
echo "===================================================="
{activate_cmd}
echo "✅ Virtual environment activated"
echo "🚀 Starting maintenance agent test..."
python test_agent.py
'''
        script_name = "run_agent.sh"
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod(script_name, 0o755)
    
    print(f"✅ Created activation script: {script_name}")

def main():
    """Main setup function"""
    print("🔧 Maintenance Agent Setup")
    print("=" * 30)
    
    # Step 1: Check requirements file
    print("\n1️⃣ Checking requirements file...")
    if not check_requirements_file():
        return
    
    # Step 2: Create virtual environment
    print("\n2️⃣ Setting up virtual environment...")
    if not create_virtual_environment():
        return
    
    # Step 3: Install dependencies
    print("\n3️⃣ Installing dependencies...")
    if not install_dependencies_in_venv():
        return
    
    # Step 4: Create activation script
    print("\n4️⃣ Creating run script...")
    create_activation_script()
    
    # Final instructions
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. To run the agent with virtual environment:")
    if os.name == 'nt':
        print("   run_agent.bat")
    else:
        print("   ./run_agent.sh")
    
    print("\n2. To manually activate virtual environment:")
    print(f"   {get_activation_command()}")
    
    print("\n3. Then run the agent:")
    print("   python test_agent.py")
    
    print("\n📁 Project structure:")
    print("   venv/                - Virtual environment")
    print("   main.py              - Main agent logic")
    print("   test_agent.py        - Test and launch script")
    print("   setup.py             - This setup script")
    print("   run_agent.sh/bat     - Run script with venv activation")

if __name__ == "__main__":
    main()
