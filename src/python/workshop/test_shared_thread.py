#!/usr/bin/env python3
"""
Test script to verify the shared thread persistence functionality.
This script simulates agent initialization to test if shared thread IDs are properly saved.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the workshop directory to Python path
workshop_dir = Path(__file__).parent.parent.parent / "src" / "python" / "workshop"
sys.path.insert(0, str(workshop_dir))

from services.async_sql_store import async_set_shared_thread, async_get_shared_thread

async def test_shared_thread_persistence():
    """Test the shared thread persistence functionality"""
    print("Testing shared thread persistence...")
    
    # Test setting a shared thread
    test_thread_id = "test_thread_12345"
    test_email = "test@example.com"
    
    try:
        # Set the shared thread
        result = await async_set_shared_thread(test_thread_id, test_email)
        print(f"✅ Successfully set shared thread: {test_thread_id} by {test_email}")
        print(f"   Result: {result}")
        
        # Get the shared thread back
        retrieved = await async_get_shared_thread()
        print(f"✅ Retrieved shared thread: {retrieved}")
        
        if retrieved and retrieved.get('thread_id') == test_thread_id:
            print("🎉 Test PASSED: Shared thread ID was successfully saved and retrieved!")
        else:
            print("❌ Test FAILED: Retrieved thread ID doesn't match what was saved")
            
    except Exception as e:
        print(f"❌ Test FAILED with error: {e}")

if __name__ == "__main__":
    print("Shared Thread Persistence Test")
    print("=" * 40)
    asyncio.run(test_shared_thread_persistence())
