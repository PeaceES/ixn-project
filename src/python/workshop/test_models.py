#!/usr/bin/env python3
"""
Test script to check available models in Azure AI Foundry project.
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

async def test_models():
    """Test what models are available and try different model names."""
    
    PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
    print(f"Testing models in project: {PROJECT_CONNECTION_STRING}")
    
    try:
        # Initialize the client
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING,
        )
        
        print("\n🔍 Testing different model names...")
        
        # Common model names to test
        model_names_to_test = [
            "gpt-5-chat",
            "gpt-4o", 
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-35-turbo",
            "gpt-3.5-turbo",
        ]
        
        working_models = []
        
        for model_name in model_names_to_test:
            try:
                print(f"\n📋 Testing model: {model_name}")
                
                # Try to create a simple agent with this model
                agent = await project_client.agents.create_agent(
                    model=model_name,
                    name=f"Test Agent - {model_name}",
                    instructions="You are a helpful assistant.",
                    temperature=0.1,
                )
                
                print(f"✅ Model '{model_name}' works! Agent ID: {agent.id}")
                working_models.append(model_name)
                
                # Clean up - delete the test agent
                try:
                    await project_client.agents.delete_agent(agent.id)
                    print(f"🗑️ Cleaned up test agent for {model_name}")
                except:
                    pass  # Ignore cleanup errors
                    
            except Exception as e:
                print(f"❌ Model '{model_name}' failed: {str(e)}")
                
        print(f"\n🎯 SUMMARY:")
        if working_models:
            print(f"✅ Working models: {', '.join(working_models)}")
            print(f"\n💡 RECOMMENDATION: Use one of these model names in your .env file:")
            for model in working_models:
                print(f"   MODEL_DEPLOYMENT_NAME=\"{model}\"")
        else:
            print("❌ No working models found. Check your AI Foundry project configuration.")
            
    except Exception as e:
        print(f"❌ Failed to connect to Azure AI Project: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your PROJECT_CONNECTION_STRING is correct")
        print("2. Ensure you have proper Azure CLI authentication (az login)")
        print("3. Verify your AI Foundry project has model deployments")

if __name__ == "__main__":
    asyncio.run(test_models())
