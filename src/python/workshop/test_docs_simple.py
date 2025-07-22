#!/usr/bin/env python3

import asyncio
import httpx
import json

async def test_microsoft_docs():
    print("🔍 Testing Microsoft Docs MCP Server...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test tools/list first
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            print(f"📤 Sending request to: https://learn.microsoft.com/api/mcp")
            print(f"📋 Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                "https://learn.microsoft.com/api/mcp",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📝 Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_microsoft_docs())
