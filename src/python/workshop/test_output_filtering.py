#!/usr/bin/env python3
"""
Test script to verify the output filtering works correctly.
This simulates the terminal output with intermediate steps and final response.
"""
import time

def simulate_agent_interaction():
    """Simulate an agent processing a request with intermediate output."""
    
    print("Processing your request...")
    time.sleep(0.5)
    
    # Simulate intermediate processing output (should be filtered out in web UI)
    print("[AgentCore] Agent or thread not initialized.")
    time.sleep(0.2)
    print("[AgentCore] Message created for thread ID: abc123")
    time.sleep(0.2)
    print("[AgentCore] Using non-streaming approach for reliability")
    time.sleep(0.2)
    print("[AgentCore] Run started for thread ID: abc123, Agent ID: def456")
    time.sleep(0.2)
    print("[AgentCore] Iteration 1: Run def456 status: requires_action")
    time.sleep(0.2)
    print("[AgentCore] Handling required actions in iteration 1")
    time.sleep(0.2)
    print("[AgentCore] After iteration 1: Run def456 status: completed")
    time.sleep(0.2)
    print("[AgentCore] Run def456 finished with status: completed")
    time.sleep(0.2)
    
    # This is the final response that should be shown in both terminal and web UI
    print("FINAL_AGENT_RESPONSE_START")
    print("Agent response: I found 3 available meeting rooms for tomorrow at 2 PM: Alpha Meeting Room, Beta Conference Room, and Gamma Studio. Would you like me to book one of these rooms for you?")
    print("FINAL_AGENT_RESPONSE_END")

if __name__ == "__main__":
    print("=== Testing Output Filtering ===")
    print("This simulates agent output with intermediate steps and final response.")
    print("In the web UI, only the final response should be highlighted when filtering is enabled.")
    print()
    
    simulate_agent_interaction()
    
    print()
    print("=== Test Complete ===")
    print("Expected behavior:")
    print("- Terminal: Shows everything including intermediate steps")
    print("- Web UI with 'Show intermediate steps' ON: Shows everything")
    print("- Web UI with 'Show intermediate steps' OFF: Shows only final response")
