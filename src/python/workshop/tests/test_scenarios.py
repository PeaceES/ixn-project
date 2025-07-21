#!/usr/bin/env python3
"""
Scenario-Based Test Cases for Group Booking System
Tests realistic university calendar booking scenarios.
"""

def test_booking_scenarios():
    """Test realistic booking scenarios"""
    print("\n🎓 University Booking Scenarios")
    print("=" * 50)
    
    try:
        from services.simple_permissions import SimplePermissionChecker
        
        checker = SimplePermissionChecker()
        
        scenarios = [
            {
                "name": "Professor books faculty lounge for department meeting",
                "user": "prof001",
                "room": "room001", 
                "group": "cs_faculty",
                "expected": True
            },
            {
                "name": "Student tries to book faculty lounge",
                "user": "student001",
                "room": "room001",
                "group": "cs_faculty", 
                "expected": False
            },
            {
                "name": "Admin books conference room for staff meeting",
                "user": "admin001",
                "room": "room002",
                "group": "admin_staff",
                "expected": True
            },
            {
                "name": "Student books study room for group project",
                "user": "student001", 
                "room": "room005",
                "group": "math_students",
                "expected": True
            },
            {
                "name": "Professor tries to book room for wrong department",
                "user": "prof001",
                "room": "room003",
                "group": "physics_faculty",
                "expected": False
            }
        ]
        
        passed = 0
        failed = 0
        
        for scenario in scenarios:
            can_book, reason = checker.can_user_book_room_for_group(
                scenario["user"], 
                scenario["room"], 
                scenario["group"]
            )
            
            if can_book == scenario["expected"]:
                print(f"{scenario['name']}")
                print(f"   Result: {reason}")
                passed += 1
            else:
                print(f"{scenario['name']}")
                print(f"   Expected: {scenario['expected']}, Got: {can_book}")
                print(f"   Reason: {reason}")
                failed += 1
            print()
        
        print(f"Scenario Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"Scenario testing failed: {e}")
        return False

if __name__ == "__main__":
    test_booking_scenarios()
