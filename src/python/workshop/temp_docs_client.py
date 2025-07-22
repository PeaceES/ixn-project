"""
Temporary Microsoft Docs MCP client for researching agent evaluation.
This is a simple HTTP client to query the official Microsoft Learn Docs MCP server.
"""

import httpx
import json
import asyncio
from typing import Dict, Any, List


class TempMicrosoftDocsClient:
    """Temporary client to query Microsoft Learn Docs MCP server."""
    
    def __init__(self):
        self.base_url = "https://learn.microsoft.com/api/mcp"
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def search_docs(self, query: str) -> Dict[str, Any]:
        """Search Microsoft documentation for the given query."""
        try:
            # MCP call to search Microsoft docs using the correct tool name
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "microsoft_docs_search",
                    "arguments": {
                        "question": query
                    }
                }
            }
            
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Handle Server-Sent Events (SSE) response
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    # Parse SSE response
                    return await self._parse_sse_response(response.text)
                else:
                    # Regular JSON response
                    return response.json()
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "message": f"Failed to search docs: {response.text}"
                }
                
        except Exception as e:
            return {
                "error": "Request failed",
                "message": str(e)
            }
    
    async def _parse_sse_response(self, sse_text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events response."""
        try:
            lines = sse_text.strip().split('\n')
            data_lines = []
            
            for line in lines:
                if line.startswith('data: '):
                    data_content = line[6:]  # Remove 'data: ' prefix
                    if data_content and data_content != '[DONE]':
                        try:
                            data = json.loads(data_content)
                            data_lines.append(data)
                        except json.JSONDecodeError:
                            continue
            
            if data_lines:
                # Return the last complete data object
                return data_lines[-1] if data_lines else {"error": "No valid data found"}
            else:
                return {
                    "error": "SSE parsing failed",
                    "message": "No valid JSON data found in SSE stream",
                    "raw_content": sse_text[:500] + "..." if len(sse_text) > 500 else sse_text
                }
                
        except Exception as e:
            return {
                "error": "SSE parsing error",
                "message": str(e),
                "raw_content": sse_text[:200] + "..." if len(sse_text) > 200 else sse_text
            }
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """List available tools in the Microsoft Docs MCP server."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Handle Server-Sent Events (SSE) response
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    # Parse SSE response
                    return await self._parse_sse_response(response.text)
                else:
                    # Regular JSON response
                    return response.json()
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "message": f"Failed to list tools: {response.text}"
                }
                
        except Exception as e:
            return {
                "error": "Request failed",
                "message": str(e)
            }


async def research_agent_evaluation():
    """Research Azure AI Agent Service evaluation methods."""
    
    print("🔍 Researching Azure AI Agent Service Evaluation...")
    print("=" * 60)
    
    async with TempMicrosoftDocsClient() as client:
        
        # First, let's see what tools are available
        print("\n📋 Checking available Microsoft Docs MCP tools...")
        tools_result = await client.list_available_tools()
        print(f"Tools response: {json.dumps(tools_result, indent=2)}")
        
        # Search queries related to agent evaluation
        search_queries = [
            "Azure AI Agent Service evaluation",
            "Azure AI Studio agent evaluation metrics",
            "Azure AI Foundry agent monitoring",
            "Azure AI agents performance evaluation",
            "Azure AI projects agent assessment"
        ]
        
        results = {}
        
        for query in search_queries:
            print(f"\n🔎 Searching: '{query}'")
            print("-" * 40)
            
            result = await client.search_docs(query)
            results[query] = result
            
            if "error" not in result:
                print("✅ Search successful!")
                
                # Debug: Print the full result structure to understand it
                print("🔍 Full result structure:")
                print(json.dumps(result, indent=2)[:1000] + "..." if len(json.dumps(result, indent=2)) > 1000 else json.dumps(result, indent=2))
                
                # Try different possible result structures
                content = None
                if "result" in result:
                    result_data = result["result"]
                    if "content" in result_data:
                        content = result_data["content"]
                    elif "text" in result_data:
                        content = result_data["text"]
                    elif isinstance(result_data, list):
                        content = result_data
                    elif isinstance(result_data, str):
                        content = [{"content": result_data}]
                
                if content:
                    if isinstance(content, list) and len(content) > 0:
                        print(f"📄 Found {len(content)} results")
                        for i, doc in enumerate(content[:2]):  # Show first 2 results
                            print(f"\n📋 Result {i+1}:")
                            if isinstance(doc, dict):
                                print(f"   Title: {doc.get('title', doc.get('name', 'N/A'))}")
                                print(f"   URL: {doc.get('url', doc.get('link', 'N/A'))}")
                                snippet = doc.get('content', doc.get('text', doc.get('snippet', '')))
                                if snippet:
                                    print(f"   Content: {snippet[:300]}...")
                            else:
                                print(f"   Content: {str(doc)[:300]}...")
                    elif isinstance(content, str):
                        print(f"📝 Content: {content[:500]}...")
                    else:
                        print("📝 Content:", str(content)[:300] + "..." if len(str(content)) > 300 else str(content))
                else:
                    print("⚠️  No content found in expected locations")
            else:
                print(f"❌ Search failed: {result.get('message', 'Unknown error')}")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        return results


if __name__ == "__main__":
    asyncio.run(research_agent_evaluation())
