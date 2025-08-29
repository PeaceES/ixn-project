#!/usr/bin/env python3
"""Test script to check function signatures and AsyncFunctionTool behavior"""

import inspect
import asyncio
from agent_core import CalendarAgentCore

def analyze_function_signature(func, func_name):
    """Analyze and print function signature details"""
    sig = inspect.signature(func)
    print(f"\n=== {func_name} ===")
    print(f"Function: {func}")
    print(f"Is coroutine: {inspect.iscoroutinefunction(func)}")
    print(f"Parameters:")
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
        if param.default != inspect.Parameter.empty:
            print(f"    Default: {param.default}")
    return sig

async def main():
    # Create agent core instance
    agent = CalendarAgentCore(enable_tools=True, enable_code_interpreter=False)
    
    # Functions to check
    functions_to_check = [
        ('get_events_via_mcp', agent.get_events_via_mcp),
        ('check_room_availability_via_mcp', agent.check_room_availability_via_mcp),
        ('get_rooms_via_mcp', agent.get_rooms_via_mcp),
        ('schedule_event_with_organizer', agent.schedule_event_with_organizer),
        ('schedule_event_with_permissions', agent.schedule_event_with_permissions),
        ('get_user_booking_entity', agent.get_user_booking_entity),
        ('get_user_groups', agent.get_user_groups),
    ]
    
    print("Analyzing function signatures...")
    for func_name, func in functions_to_check:
        analyze_function_signature(func, func_name)
    
    # Check if functions is properly initialized
    print("\n=== AsyncFunctionTool Analysis ===")
    if hasattr(agent, 'functions') and agent.functions:
        print(f"AsyncFunctionTool initialized: {agent.functions}")
        print(f"Type: {type(agent.functions)}")
        
        # Try to access the functions if possible
        if hasattr(agent.functions, 'functions'):
            print(f"Registered functions: {agent.functions.functions}")
    else:
        print("AsyncFunctionTool not initialized!")
    
    # Cleanup
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
