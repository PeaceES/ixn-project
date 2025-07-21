"""
Test script to debug Microsoft Docs MCP server connectivity.
"""

import asyncio
import json
from services.microsoft_docs_mcp_client import MicrosoftDocsMCPClient

async def test_microsoft_docs_mcp():
    """Test the Microsoft Docs MCP server connectivity and functionality."""
    
    print("🔍 Testing Microsoft Docs MCP Server...")
    
    # Initialize the client
    client = MicrosoftDocsMCPClient()
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    health = await client.health_check()
    print(f"   Health status: {json.dumps(health, indent=2)}")
    
    # Test 2: Get available tools
    print("\n2. Testing available tools...")
    tools = await client.get_available_tools()
    print(f"   Available tools: {json.dumps(tools, indent=2)}")
    
    # Test 3: Try a simple search
    print("\n3. Testing search functionality...")
    search_result = await client.search_microsoft_docs("Azure Container Apps")
    print(f"   Search result: {json.dumps(search_result, indent=2)}")
    
    # Test 4: Check if we can access the endpoint directly
    print("\n4. Testing direct endpoint access...")
    import httpx
    
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                "https://learn.microsoft.com/api/mcp",
                timeout=10.0
            )
            print(f"   Direct GET response: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            print(f"   Response content (first 200 chars): {response.text[:200]}")
    except Exception as e:
        print(f"   Direct GET error: {e}")
    
    # Test 5: Test with a simple MCP tools/list call
    print("\n5. Testing MCP tools/list call...")
    try:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                "https://learn.microsoft.com/api/mcp",
                json=mcp_request,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "calendar-scheduling-agent/1.0.0"
                },
                timeout=15.0
            )
            print(f"   MCP tools/list response: {response.status_code}")
            print(f"   Response content: {response.text}")
    except Exception as e:
        print(f"   MCP tools/list error: {e}")

if __name__ == "__main__":
    asyncio.run(test_microsoft_docs_mcp())
