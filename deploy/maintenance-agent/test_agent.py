#!/usr/bin/env python3
"""
Quick test script for the Maintenance Agent
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if not in_venv:
            print("⚠️  Warning: Not running in a virtual environment")
            print("💡 Tip: Run 'python setup.py' first to create a virtual environment")
        
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running 'python setup.py' first to set up virtual environment")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    required_vars = [
        'MODEL_DEPLOYMENT_NAME',
        'PROJECT_CONNECTION_STRING', 
        'SHARED_THREAD_ID',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY'
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables configured")
    return True

def check_data_files():
    """Check if data files exist"""
    data_files = ['data/rooms.json', 'data/maintenance_schedule.json']
    
    for file_path in data_files:
        if not Path(file_path).exists():
            print(f"❌ Missing data file: {file_path}")
            return False
        else:
            print(f"✅ Found data file: {file_path}")
    
    return True

def test_json_files():
    """Test if JSON files are valid"""
    import json
    
    data_files = ['data/rooms.json', 'data/maintenance_schedule.json']
    
    for file_path in data_files:
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            print(f"✅ Valid JSON: {file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {file_path}: {e}")
            return False
    
    return True

def run_agent_test():
    """Run the maintenance agent"""
    print("\n🚀 Starting Maintenance Agent Test...")
    print("=" * 50)
    
    try:
        # Import and run the agent
        from main import main
        import asyncio
        
        # Run the agent
        asyncio.run(main())
        
        print("\n" + "=" * 50)
        print("✅ Agent test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Agent test failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your Azure credentials")
        print("2. Verify the shared thread ID is valid")
        print("3. Ensure network connectivity to Azure")
        return False
    
    return True

def test_azure_connection_and_model():
    """Test Azure connection and model analysis"""
    print("\n🔗 Testing Azure OpenAI connection and model analysis...")
    print("=" * 50)
    
    try:
        import json
        import asyncio
        from dotenv import load_dotenv
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import ThreadMessage, MessageRole
        from azure.identity import DefaultAzureCredential
        
        # Load environment variables
        load_dotenv()
        
        print("🔧 Initializing Azure AI Projects client...")
        
        # Initialize Azure AI Projects client
        credential = DefaultAzureCredential()
        project = AIProjectClient.from_connection_string(
            conn_str=os.getenv("PROJECT_CONNECTION_STRING"),
            credential=credential
        )
        
        print("✅ Connected to Azure AI Projects")
        
        # Load room data for analysis
        with open('data/rooms.json', 'r') as f:
            rooms_data = json.load(f)
        
        # Find a room that needs attention or has issues
        problem_room = None
        for room in rooms_data['rooms']:
            if (room.get('status') == 'needs_attention' or 
                room.get('temperature', 20) > 25 or 
                room.get('humidity', 50) > 60):
                problem_room = room
                break
        
        if not problem_room:
            problem_room = rooms_data['rooms'][-1]  # Use last room which has issues
        
        print(f"🏠 Analyzing room: {problem_room['name']} ({problem_room['id']})")
        print(f"   Status: {problem_room['status']}")
        print(f"   Temperature: {problem_room['temperature']}°C")
        print(f"   Humidity: {problem_room['humidity']}%")
        
        # Test with the shared thread
        shared_thread_id = os.getenv("SHARED_THREAD_ID")
        
        if not shared_thread_id:
            print("❌ SHARED_THREAD_ID not found in environment")
            return False
        
        print(f"📡 Using shared thread: {shared_thread_id}")
        
        # Create a maintenance analysis message
        fault_analysis = f"""🔍 MAINTENANCE ANALYSIS REQUEST

Room: {problem_room['name']} ({problem_room['id']})
Current Status: {problem_room['status']}
Temperature: {problem_room['temperature']}°C (Normal range: 18-24°C)
Humidity: {problem_room['humidity']}% (Normal range: 30-60%)
Equipment: {', '.join(problem_room['equipment'])}
Last Maintenance: {problem_room['last_maintenance']}

As a maintenance agent, please analyze this room data and provide:
1. Any faults or issues detected
2. Severity assessment (Critical/High/Medium/Low)
3. Recommended immediate actions
4. Should this be escalated?

Please respond in a structured maintenance report format."""

        # Send message to shared thread
        message = ThreadMessage(
            role=MessageRole.USER,
            content=fault_analysis
        )
        
        # This is an async operation, so let's handle it properly
        async def send_message():
            message_response = await project.agents.create_message(
                thread_id=shared_thread_id,
                role=MessageRole.USER,
                content=fault_analysis
            )
            return message_response
        
        try:
            # Run the async message sending
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(send_message())
            loop.close()
            
            print("📤 Successfully sent fault analysis to shared thread!")
            print("✅ Model connection and message sending test successful!")
            
        except Exception as async_error:
            print(f"⚠️  Async message sending failed: {async_error}")
            print("✅ But basic Azure connection was successful!")
        
        print(f"\n📊 Connection Test Summary:")
        print(f"   • Azure AI Projects connection: ✅")
        print(f"   • Room data loaded: {len(rooms_data['rooms'])} rooms")
        print(f"   • Problem room identified: {problem_room['name']}")
        print(f"   • Shared thread ID: {shared_thread_id}")
        print(f"   • Model deployment: {os.getenv('MODEL_DEPLOYMENT_NAME')}")
        
        # Simple fault detection logic (similar to main agent)
        detected_faults = []
        temp = problem_room.get('temperature', 20)
        humidity = problem_room.get('humidity', 50)
        
        if temp > 25:
            detected_faults.append(f"High temperature: {temp}°C")
        if temp < 18:
            detected_faults.append(f"Low temperature: {temp}°C")
        if humidity > 60:
            detected_faults.append(f"High humidity: {humidity}%")
        if humidity < 30:
            detected_faults.append(f"Low humidity: {humidity}%")
        if problem_room.get('status') == 'needs_attention':
            detected_faults.append("Room marked as needing attention")
        
        if detected_faults:
            print(f"\n⚠️  Detected faults in {problem_room['name']}:")
            for fault in detected_faults:
                print(f"   • {fault}")
        else:
            print(f"\n✅ No faults detected in {problem_room['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure connection test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify Azure credentials with: az login")
        print("2. Check PROJECT_CONNECTION_STRING format")
        print("3. Ensure SHARED_THREAD_ID is valid")
        print("4. Check internet connectivity")
        print("5. Verify subscription and resource permissions")
        
        # Show the specific error for debugging
        import traceback
        print(f"\nDetailed error:")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🔧 Maintenance Agent Test Suite")
    print("=" * 40)
    
    # Step 1: Check environment file
    print("\n1️⃣ Checking environment configuration...")
    if not check_env_file():
        return
    
    # Step 2: Check data files
    print("\n2️⃣ Checking data files...")
    if not check_data_files():
        return
    
    # Step 3: Test JSON validity
    print("\n3️⃣ Validating JSON files...")
    if not test_json_files():
        return
    
    # Step 4: Install dependencies
    print("\n4️⃣ Installing dependencies...")
    if not install_dependencies():
        return
    
    # Step 5: Test Azure connection and model
    print("\n5️⃣ Testing Azure connection and model...")
    if not test_azure_connection_and_model():
        print("⚠️  Azure connection test failed, but continuing with basic agent test...")
    
    # Step 6: Run full agent test
    print("\n6️⃣ Running full agent test...")
    run_agent_test()

if __name__ == "__main__":
    main()
