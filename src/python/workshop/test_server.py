#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from services.calendar_mcp_server import startup_event

async def main():
    print("Testing MCP server startup...")
    await startup_event()
    print("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
