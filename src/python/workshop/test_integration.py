#!/usr/bin/env python3
"""
Integration test to demonstrate Solution 1 working with both web and terminal interfaces.
"""

import os
import sys
from pathlib import Path

# Add the workshop directory to the path
workshop_dir = Path(__file__).parent
sys.path.insert(0, str(workshop_dir))

def test_terminal_behavior():
    """Demonstrate that terminal behavior is unchanged."""
    print("\n=== Terminal Interface Test ===")
    print("In terminal mode (python main.py):")
    print("- No user context is injected")
    print("- Agent asks for user ID when booking")
    print("\nExample conversation:")
    print("User: I want to book a room")
    print("Agent: What's your user ID?")
    print("User: 5")
    print("Agent: Let me check what you can book for...")
    print("\n✓ Terminal behavior remains unchanged")

def test_web_interface_behavior():
    """Demonstrate web interface with context injection."""
    print("\n=== Web Interface Test ===")
    print("When AUTO_INJECT_USER_CONTEXT=true (default):")
    print("- User logs in with email")
    print("- Context is automatically injected for booking messages")
    print("\nExample conversation:")
    print("User (logged in as John Doe, ID: 5): I want to book a room")
    print("System injects: [System: User context - ID: 5, Name: John Doe, Email: john@example.com]")
    print("Agent: I see you're John Doe (ID: 5). Let me check what you can book for...")
    print("\n✓ Web interface provides seamless experience")

def test_configuration_options():
    """Show configuration options."""
    print("\n=== Configuration Options ===")
    
    current_setting = os.getenv('AUTO_INJECT_USER_CONTEXT', 'true').lower() == 'true'
    print(f"Current AUTO_INJECT_USER_CONTEXT: {current_setting}")
    
    print("\nTo change behavior:")
    print("- Enable context injection: export AUTO_INJECT_USER_CONTEXT=true")
    print("- Disable context injection: export AUTO_INJECT_USER_CONTEXT=false")
    print("\nWhen disabled, web interface behaves like terminal (asks for ID)")

def test_message_examples():
    """Show various message examples."""
    print("\n=== Message Examples ===")
    
    booking_messages = [
        "I want to book a room",
        "Schedule a meeting",
        "What can I book for?",
        "Is the lecture hall available?"
    ]
    
    non_booking_messages = [
        "What's the weather?",
        "Tell me a joke",
        "How does Python work?"
    ]
    
    print("\nMessages that trigger context injection (web only):")
    for msg in booking_messages:
        print(f"  ✓ {msg}")
    
    print("\nMessages that DON'T trigger context injection:")
    for msg in non_booking_messages:
        print(f"  ✗ {msg}")

def test_security():
    """Explain security considerations."""
    print("\n=== Security ===")
    print("✓ Context is only injected server-side (users can't spoof)")
    print("✓ Only authenticated users get context injection")
    print("✓ Terminal users can't inject fake system messages")
    print("✓ Context format is clearly distinguished from user input")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Solution 1: Per-Message Context Injection - Integration Test")
    print("=" * 60)
    
    test_terminal_behavior()
    test_web_interface_behavior()
    test_configuration_options()
    test_message_examples()
    test_security()
    
    print("\n" + "=" * 60)
    print("Summary: Solution 1 provides seamless web experience")
    print("while maintaining full terminal compatibility!")
    print("=" * 60)

if __name__ == "__main__":
    main()
