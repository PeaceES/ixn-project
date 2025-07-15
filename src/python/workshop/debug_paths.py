#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services.calendar_mcp_server import ROOMS_FILE, EVENTS_FILE, USER_DIRECTORY_LOCAL_FILE, DATA_DIR

async def test():
    with open('debug_paths.txt', 'w') as f:
        f.write("=== File Paths Debug ===\n")
        f.write(f"DATA_DIR: {DATA_DIR}\n")
        f.write(f"ROOMS_FILE: {ROOMS_FILE}\n")
        f.write(f"EVENTS_FILE: {EVENTS_FILE}\n")
        f.write(f"USER_DIRECTORY_LOCAL_FILE: {USER_DIRECTORY_LOCAL_FILE}\n")
        f.write(f"\n=== File Existence Check ===\n")
        f.write(f"DATA_DIR exists: {os.path.exists(DATA_DIR)}\n")
        f.write(f"ROOMS_FILE exists: {os.path.exists(ROOMS_FILE)}\n")
        f.write(f"EVENTS_FILE exists: {os.path.exists(EVENTS_FILE)}\n")
        f.write(f"USER_DIRECTORY_LOCAL_FILE exists: {os.path.exists(USER_DIRECTORY_LOCAL_FILE)}\n")
        
        f.write(f"\n=== Current Working Directory ===\n")
        f.write(f"Current dir: {os.getcwd()}\n")
        f.write(f"Script dir: {os.path.dirname(__file__)}\n")

if __name__ == "__main__":
    asyncio.run(test())
