"""
Microsoft Learn Docs MCP Client

This client provides access to Microsoft's official documentation through the
Microsoft Learn Docs MCP Server. It enables the agent to search for and retrieve
up-to-date information from Microsoft Learn, Azure documentation, and other
official Microsoft sources.

MCP Server Endpoint: https://learn.microsoft.com/api/mcp
"""

import httpx
import json
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Microsoft Learn Docs MCP Server Configuration
MICROSOFT_DOCS_MCP_URL = "https://learn.microsoft.com/api/mcp"


class MicrosoftDocsMCPClient:
    """Client for interacting with the Microsoft Learn Docs MCP Server."""
    
    def __init__(self, base_url: str = MICROSOFT_DOCS_MCP_URL):
        self.base_url = base_url.rstrip('/')
        self.client_info = {
            "name": "calendar-scheduling-agent",
            "version": "1.0.0"
        }
        self._client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client
    
    async def cleanup(self) -> None:
        """Cleanup the HTTP client."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception as e:
                logger.warning(f"Error closing HTTP client: {e}")
            finally:
                self._client = None
    
    async def search_microsoft_docs(self, query: str) -> Dict[str, Any]:
        """
        Search Microsoft's official documentation using the MCP server.
        
        Args:
            query: The search query for retrieval
            
        Returns:
            Dictionary containing search results with documentation chunks
        """
        try:
            # Prepare the MCP request payload for streamable HTTP
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "microsoft_docs_search",
                    "arguments": {
                        "query": query
                    }
                }
            }
            
            # Use streamable HTTP headers as required by the MCP server
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"{self.client_info['name']}/{self.client_info['version']}",
                "Connection": "keep-alive"
            }
            
            client = await self._get_client()
            response = await client.post(
                self.base_url,
                json=mcp_request,
                headers=headers
            )
            
            # Handle MCP server specific responses
            if response.status_code == 405:
                return {
                    "success": False,
                    "error": "MCP server requires streamable HTTP transport (not supported in this implementation)",
                    "results": [],
                    "suggestion": "This endpoint requires a proper MCP client with streamable HTTP support"
                }
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                mcp_response = response.json()
            except json.JSONDecodeError:
                # If not JSON, it might be a streaming response
                return {
                    "success": False,
                    "error": "MCP server returned non-JSON response (likely requires streaming)",
                    "results": [],
                    "raw_response": response.text[:500] if response.text else "Empty response"
                }
            
            # Check for MCP errors
            if "error" in mcp_response:
                error_msg = mcp_response["error"].get("message", "Unknown MCP error")
                return {
                    "success": False, 
                    "error": f"MCP error: {error_msg}",
                    "results": []
                }
            
            # Extract results from MCP response
            if "result" in mcp_response and "content" in mcp_response["result"]:
                content = mcp_response["result"]["content"]
                
                # Parse the content - it should be an array of text blocks
                results = []
                for item in content:
                    if item.get("type") == "text":
                        results.append({
                            "content": item.get("text", ""),
                            "type": "documentation"
                        })
                
                return {
                    "success": True,
                    "results": results,
                    "query": query,
                    "source": "Microsoft Learn Docs"
                }
            else:
                return {
                    "success": False,
                    "error": "No results found in MCP response",
                    "results": []
                }
                
        except httpx.TimeoutException:
            return {
                "success": False, 
                "error": "Request timeout when searching Microsoft docs",
                "results": []
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 405:
                return {
                    "success": False,
                    "error": "MCP server requires streamable HTTP transport (Method Not Allowed)",
                    "results": [],
                    "status_code": 405
                }
            return {
                "success": False, 
                "error": f"HTTP error {e.response.status_code} when searching Microsoft docs",
                "results": []
            }
        except httpx.RequestError as e:
            return {
                "success": False, 
                "error": f"Network error when searching Microsoft docs: {e}",
                "results": []
            }
        except json.JSONDecodeError as e:
            return {
                "success": False, 
                "error": f"Invalid JSON response from Microsoft docs MCP server: {e}",
                "results": []
            }
        except Exception as e:
            logger.error(f"Unexpected error in Microsoft docs search: {e}")
            return {
                "success": False, 
                "error": f"Unexpected error: {e}",
                "results": []
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the Microsoft Learn Docs MCP server is available.
        
        Returns:
            Dictionary with health status
        """
        try:
            # The MCP server requires streamable HTTP transport, so we'll get a 405
            # but we can use this to verify the server is accessible
            client = await self._get_client()
            response = await client.get(
                self.base_url,
                headers={
                    "User-Agent": f"{self.client_info['name']}/{self.client_info['version']}"
                },
                timeout=10.0
            )
            
            # The MCP server returns 405 for GET/POST requests - this is expected
            if response.status_code == 405:
                # Check if the response mentions MCP server
                if "MCP server" in response.text and "streamable HTTP" in response.text:
                    return {
                        "status": "healthy",
                        "server": "Microsoft Learn Docs MCP",
                        "endpoint": self.base_url,
                        "note": "Server is accessible but requires streamable HTTP transport",
                        "limitation": "This implementation uses standard HTTP which is not fully supported"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Server returned 405 but doesn't appear to be MCP server",
                        "response": response.text[:200]
                    }
            
            # If we get any other response, try to parse it
            response.raise_for_status()
            return {
                "status": "healthy",
                "server": "Microsoft Learn Docs MCP",
                "endpoint": self.base_url,
                "unexpected": "Server accepted standard HTTP request"
            }
            
        except httpx.TimeoutException:
            return {
                "status": "unhealthy",
                "error": "Health check timeout"
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 405:
                # This is expected - the server is working but requires streamable HTTP
                return {
                    "status": "healthy",
                    "server": "Microsoft Learn Docs MCP",
                    "endpoint": self.base_url,
                    "note": "Server is accessible but requires streamable HTTP transport",
                    "limitation": "This implementation uses standard HTTP which is not fully supported"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP error: {e.response.status_code}",
                    "details": e.response.text[:200] if e.response.text else "No response body"
                }
        except httpx.RequestError as e:
            return {
                "status": "unhealthy",
                "error": f"Network error: {e}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Health check failed: {e}"
            }
    
    async def get_available_tools(self) -> Dict[str, Any]:
        """
        Get the list of available tools from the Microsoft Learn Docs MCP server.
        
        Returns:
            Dictionary containing available tools
        """
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            client = await self._get_client()
            response = await client.post(
                self.base_url,
                json=mcp_request,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"{self.client_info['name']}/{self.client_info['version']}"
                },
                timeout=15.0
            )
            
            response.raise_for_status()
            mcp_response = response.json()
            
            if "error" in mcp_response:
                return {
                    "success": False,
                    "error": mcp_response["error"].get("message", "Unknown error")
                }
            
            return {
                "success": True,
                "tools": mcp_response.get("result", {}).get("tools", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get available tools: {e}"
            }


# Convenience function for backward compatibility
async def search_microsoft_docs(query: str) -> Dict[str, Any]:
    """Convenience function for searching Microsoft documentation."""
    client = MicrosoftDocsMCPClient()
    return await client.search_microsoft_docs(query)
