#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly after reorganization.
"""

print("🧪 Testing imports after file reorganization...")

try:
    # Test utils imports
    print("Testing utils imports...")
    from utils.utilities import Utilities
    from utils.terminal_colors import TerminalColors
    from utils.events_data import EventsData
    print("Utils imports successful")
    
    # Test services imports  
    print("📁 Testing services imports...")
    from services.calendar_service import CalendarServiceInterface
    from services.synthetic_calendar_service import SyntheticCalendarService
    from services.mcp_client import CalendarMCPClient
    from services.simple_permissions import SimplePermissionChecker, permission_checker
    print("Services imports successful")
    
    # Test agent imports
    print("Testing agent imports...")
    from agent.stream_event_handler import StreamEventHandler
    print("Agent imports successful")
    
    # Test permission checker functionality
    print("Testing permission checker...")
    checker = SimplePermissionChecker()
    print(f"Permission checker created - Users: {len(checker.users)}, Groups: {len(checker.groups)}, Rooms: {len(checker.rooms)}")
    
    print("\n All imports successful! Repository reorganization completed successfully.")
    
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
