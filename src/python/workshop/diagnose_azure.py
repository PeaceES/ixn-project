#!/usr/bin/env python3
"""
Azure Configuration Diagnostic Script

This script checks what Azure AI connections and resources are available
for the evaluation module to use.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import ConnectionType

# Load environment variables
load_dotenv()

async def diagnose_azure_config():
    """Diagnose Azure configuration for evaluation."""
    
    print("🔍 Azure Configuration Diagnostic")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    azure_vars = {
        "PROJECT_CONNECTION_STRING": os.getenv("PROJECT_CONNECTION_STRING"),
        "MODEL_DEPLOYMENT_NAME": os.getenv("MODEL_DEPLOYMENT_NAME"),
        "BING_CONNECTION_NAME": os.getenv("BING_CONNECTION_NAME")
    }
    
    for var, value in azure_vars.items():
        if value:
            print(f"   ✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Check project client initialization
    print("\n🔧 Project Client:")
    try:
        connection_string = os.environ["PROJECT_CONNECTION_STRING"]
        parts = connection_string.split(';')
        
        if len(parts) != 4:
            print(f"   ❌ Invalid connection string format")
            return
        
        endpoint = f"https://{parts[0]}/agents/v1.0/subscriptions/{parts[1]}/resourceGroups/{parts[2]}/providers/Microsoft.MachineLearningServices/workspaces/{parts[3]}"
        print(f"   📍 Endpoint: {endpoint}")
        
        # Initialize project client
        project_client = AIProjectClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        print("   ✅ Project client initialized successfully")
        
        # Check available connections
        print("\n🔗 Available Connections:")
        try:
            connections = project_client.connections.list()
            connection_list = []
            async for conn in connections:
                connection_list.append(conn)
            
            print(f"   Found {len(connection_list)} connections:")
            for conn in connection_list:
                print(f"   - {conn.name} ({conn.connection_type})")
                if hasattr(conn, 'tags'):
                    print(f"     Tags: {conn.tags}")
                if hasattr(conn, 'properties'):
                    print(f"     Properties: {list(conn.properties.keys()) if conn.properties else 'None'}")
        
        except Exception as e:
            print(f"   ⚠️  Could not list connections: {e}")
        
        # Check for Azure OpenAI connection specifically
        print("\n🤖 Azure OpenAI Connection:")
        try:
            openai_conn = await project_client.connections.get_default(
                connection_type=ConnectionType.AZURE_OPEN_AI,
                include_credentials=True
            )
            print(f"   ✅ Default Azure OpenAI connection found: {openai_conn.name}")
            
            # Try to create model config
            try:
                model_config = openai_conn.to_evaluator_model_config(
                    deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4"),
                    api_version="2023-05-15",
                    include_credentials=True
                )
                print(f"   ✅ Model config created successfully")
                print(f"   📝 Deployment: {model_config.azure_deployment}")
                print(f"   🔗 Endpoint: {model_config.azure_endpoint}")
                
            except Exception as e:
                print(f"   ❌ Could not create model config: {e}")
                
        except Exception as e:
            print(f"   ❌ No default Azure OpenAI connection found: {e}")
        
        # Check other connection types
        print("\n📊 Other Connection Types:")
        connection_types = [
            ConnectionType.AZURE_AI_SEARCH,
            ConnectionType.AZURE_BLOB_STORAGE,
            ConnectionType.CUSTOM
        ]
        
        for conn_type in connection_types:
            try:
                conn = await project_client.connections.get_default(connection_type=conn_type)
                print(f"   ✅ {conn_type}: {conn.name}")
            except:
                print(f"   ❌ {conn_type}: Not available")
        
        await project_client.close()
        
    except Exception as e:
        print(f"   ❌ Project client initialization failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎯 Recommendation:")
    print("   If Azure OpenAI connection is missing, you need to:")
    print("   1. Set up an Azure OpenAI connection in your Azure AI project")
    print("   2. Make sure it's set as the default connection")
    print("   3. Ensure proper permissions for the evaluation SDK")

async def main():
    """Main diagnostic function."""
    await diagnose_azure_config()

if __name__ == "__main__":
    asyncio.run(main())
