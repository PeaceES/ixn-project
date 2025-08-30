#!/usr/bin/env python3
"""
Verification script to ensure the agent doesn't announce user identity
when context is provided via the web interface.
"""

import re

def check_agent_response(response):
    """Check if an agent response inappropriately announces user identity."""
    
    # Patterns that indicate the agent is announcing identity
    announce_patterns = [
        r"you're logged in as",
        r"you are logged in as", 
        r"i see you're",
        r"i see you are",
        r"hello .+, i know",
        r"since you're logged in",
        r"i can see you're",
        r"your user id is",
        r"you're user \d+",
        r"logged in as .+ \(user id:",
        r"welcome .+, user id:",
        r"greetings .+, i see"
    ]
    
    # Check if response contains any announce patterns
    response_lower = response.lower()
    for pattern in announce_patterns:
        if re.search(pattern, response_lower):
            return False, pattern
    
    return True, None

def test_responses():
    """Test various agent responses."""
    print("=== Agent Response Verification ===\n")
    
    # Test responses
    test_cases = [
        # Bad responses (should fail)
        ("You're logged in as Shannon Ray (user ID: 7). What entity are you booking for?", False),
        ("I see you're Shannon Ray. Let me check what you can book for.", False),
        ("Hello Shannon Ray, I know you're user ID 7. How can I help?", False),
        ("Since you're logged in as Shannon Ray, you can book for these entities:", False),
        
        # Good responses (should pass)
        ("What entity are you booking for? You can book for:", True),
        ("Let me check what you can book for...", True),
        ("I'll help you book a room. Which entity are you booking for?", True),
        ("Based on your permissions, you can book for:", True),
        ("Here are the entities you have access to:", True),
        ("To book a room, please select which entity you're booking for:", True)
    ]
    
    passed = 0
    failed = 0
    
    for response, expected_pass in test_cases:
        is_good, pattern = check_agent_response(response)
        
        if is_good == expected_pass:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status}: {response[:60]}...")
        if not is_good and pattern:
            print(f"         Found pattern: '{pattern}'")
        print()
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ All tests passed! The agent response checker is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the implementation.")

def show_instructions():
    """Show the current instructions to the user."""
    print("\n=== Current Agent Instructions ===")
    print("The agent has been instructed to:")
    print("1. NOT announce or mention that it knows who the user is")
    print("2. NOT say things like 'You're logged in as...' or 'I see you're...'")
    print("3. Use the user context information naturally without announcing it")
    print("4. Proceed directly with helping the user")
    
    print("\n=== Next Steps ===")
    print("If the agent is still announcing your identity:")
    print("1. Restart the agent to ensure it loads the updated instructions")
    print("2. Clear any browser cache if using the web interface")
    print("3. Try a fresh booking request")
    
    print("\n=== Quick Test ===")
    print("Try saying: 'I want to book a room'")
    print("The agent should respond with something like:")
    print("'What entity are you booking for? You can book for: ...'")
    print("NOT: 'You're logged in as [name]...'")

if __name__ == "__main__":
    test_responses()
    show_instructions()
