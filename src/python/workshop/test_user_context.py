#!/usr/bin/env python3
"""
Test script to verify user context injection in messages.
This demonstrates how the agent handles messages with and without user context.
"""

import os
import sys

def test_message_processing():
    """Test how messages are processed with and without user context."""
    
    # Example messages
    test_messages = [
        # Message without context (terminal style)
        "I want to book a room for tomorrow",
        
        # Message with context (web interface style)
        "[System: User context - ID: 5, Name: John Doe, Email: john@example.com]\nI want to book a room for tomorrow",
        
        # Non-booking message (shouldn't have context even from web)
        "What's the weather like?",
        
        # Another booking-related message with context
        "[System: User context - ID: 3, Name: Jane Smith, Email: jane@example.com]\nWhat can I book for?",
    ]
    
    print("=== User Context Message Processing Test ===\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}:")
        print(f"Input: {repr(message)}")
        
        # Check if message contains user context
        if message.startswith("[System: User context"):
            lines = message.split('\n', 1)
            context_line = lines[0]
            actual_message = lines[1] if len(lines) > 1 else ""
            
            # Parse context
            import re
            context_match = re.search(r'ID: ([^,]+), Name: ([^,]+), Email: ([^\]]+)', context_line)
            if context_match:
                user_id = context_match.group(1)
                user_name = context_match.group(2)
                user_email = context_match.group(3)
                print(f"Detected user context:")
                print(f"  - ID: {user_id}")
                print(f"  - Name: {user_name}")
                print(f"  - Email: {user_email}")
                print(f"Actual message: {actual_message}")
                print(f"Agent action: Will use user ID {user_id} directly without asking")
            else:
                print("Invalid context format")
        else:
            print("No user context detected")
            print(f"Agent action: Will ask for user ID if booking-related")
        
        print("-" * 50)

def test_booking_keywords():
    """Test the booking keyword detection."""
    print("\n=== Booking Keyword Detection Test ===\n")
    
    booking_keywords = ['book', 'schedule', 'reserve', 'meeting', 'event', 'room', 'what can i book', 'calendar', 'available']
    
    test_phrases = [
        "I want to book a room",
        "Schedule a meeting for tomorrow",
        "Is the lecture hall available?",
        "What can I book for?",
        "Tell me about the weather",
        "How does Python work?",
        "Reserve conference room A",
        "Show me the calendar",
    ]
    
    for phrase in test_phrases:
        needs_context = any(keyword in phrase.lower() for keyword in booking_keywords)
        status = "✓ Context will be injected" if needs_context else "✗ No context injection"
        print(f"{status}: '{phrase}'")

if __name__ == "__main__":
    test_message_processing()
    test_booking_keywords()
    
    print("\n=== Configuration ===")
    print(f"AUTO_INJECT_USER_CONTEXT: {os.getenv('AUTO_INJECT_USER_CONTEXT', 'true')}")
    print("\nTo disable context injection, set: export AUTO_INJECT_USER_CONTEXT=false")
