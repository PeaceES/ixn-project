"""
FastAPI wrapper for Calendar Agent Core
Provides HTTP endpoints for the agent functionality
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import os
import sys
import logging

# Add parent directory to path to import agent_core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core import CalendarAgentCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Calendar Agent API",
    description="Backend API for Calendar Scheduling Agent",
    version="1.0.0"
)

# Global agent instance
agent_instance = None
agent_lock = asyncio.Lock()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    agent_initialized: bool
    mcp_status: Optional[str] = None
    agent_id: Optional[str] = None

# Helper function to get or create agent
async def get_agent():
    global agent_instance
    async with agent_lock:
        if agent_instance is None:
            agent_instance = CalendarAgentCore(
                enable_tools=True,
                enable_code_interpreter=True
            )
            success, message = await agent_instance.initialize_agent()
            if not success:
                agent_instance = None
                raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {message}")
        return agent_instance

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {"status": "healthy", "service": "Calendar Agent API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Calendar Agent API",
        "version": "1.0.0"
    }

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get agent status"""
    try:
        if agent_instance is None:
            return StatusResponse(
                status="not_initialized",
                agent_initialized=False,
                mcp_status=None,
                agent_id=None
            )
        
        status = await agent_instance.get_agent_status()
        return StatusResponse(
            status="ready",
            agent_initialized=True,
            mcp_status=status.get("mcp_status"),
            agent_id=status.get("agent_id")
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return StatusResponse(
            status="error",
            agent_initialized=False,
            mcp_status=None,
            agent_id=None
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message with the agent"""
    try:
        agent = await get_agent()
        
        # Set user context if provided
        if request.user_context:
            agent.default_user_context = request.user_context
        
        # Process the message
        success, response = await agent.process_message(request.message)
        
        if not success:
            return ChatResponse(
                response="",
                success=False,
                error=response
            )
        
        return ChatResponse(
            response=response,
            success=True,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return ChatResponse(
            response="",
            success=False,
            error=str(e)
        )

@app.post("/initialize")
async def initialize_agent():
    """Initialize the agent"""
    try:
        agent = await get_agent()
        return {"success": True, "message": "Agent initialized successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/reset")
async def reset_agent():
    """Reset the agent instance"""
    global agent_instance
    async with agent_lock:
        if agent_instance:
            await agent_instance.cleanup()
        agent_instance = None
    return {"success": True, "message": "Agent reset successfully"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_instance
    if agent_instance:
        await agent_instance.cleanup()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)