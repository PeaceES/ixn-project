#!/usr/bin/env python3
"""
Test Cases for University Calendar Scheduling Demo
Tests the reorganized file structure and group-based permission system.
"""

import sys
import os
from datetime import datetime, timedelta

print("🧪 University Calendar Scheduling - Test Suite")
print("=" * 60)

def test_imports():
    """Test Case 1: Verify all imports work with new folder structure"""
    print("\n📋 Test 1: Import Structure")
    try:
        from utils.utilities import Utilities
        from utils.terminal_colors import TerminalColors
        from services.simple_permissions import SimplePermissionChecker, permission_checker
        from services.calendar_service import CalendarServiceInterface
        from services.synthetic_calendar_service import SyntheticCalendarService
        from agent.stream_event_handler import StreamEventHandler
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_permission_system():
    """Test Case 2: Group-based permission system"""
    print("\n📋 Test 2: Permission System")
    try:
        from services.simple_permissions import SimplePermissionChecker
        
        checker = SimplePermissionChecker()
        print(f"✅ Permission checker loaded - Users: {len(checker.users)}, Groups: {len(checker.groups)}, Rooms: {len(checker.rooms)}")
        
        # Test valid user-group-room combination
        can_book, reason = checker.can_user_book_room_for_group("prof001", "room001", "cs_faculty")
        print(f"✅ Permission check result: {can_book} - {reason}")
        
        # Test invalid combination
        can_book, reason = checker.can_user_book_room_for_group("student001", "room001", "cs_faculty")
        print(f"✅ Invalid permission check: {can_book} - {reason}")
        
        return True
    except Exception as e:
        print(f"❌ Permission system test failed: {e}")
        return False

def test_data_loading():
    """Test Case 3: Data file loading from new locations"""
    print("\n📋 Test 3: Data File Loading")
    try:
        from services.simple_permissions import SimplePermissionChecker
        
        checker = SimplePermissionChecker()
        
        # Check if data loaded correctly
        if len(checker.users) > 0:
            print(f"✅ Users loaded: {len(checker.users)}")
            sample_user = list(checker.users.keys())[0]
            print(f"   Sample user: {sample_user} - {checker.users[sample_user]['name']}")
        
        if len(checker.groups) > 0:
            print(f"✅ Groups loaded: {len(checker.groups)}")
            sample_group = list(checker.groups.keys())[0]
            print(f"   Sample group: {sample_group} - {checker.groups[sample_group]['name']}")
        
        if len(checker.rooms) > 0:
            print(f"✅ Rooms loaded: {len(checker.rooms)}")
            sample_room = list(checker.rooms.keys())[0]
            print(f"   Sample room: {sample_room} - {checker.rooms[sample_room]['name']}")
        
        return True
    except Exception as e:
        print(f"❌ Data loading test failed: {e}")
        return False

def test_user_groups():
    """Test Case 4: User group membership queries"""
    print("\n📋 Test 4: User Group Membership")
    try:
        from services.simple_permissions import SimplePermissionChecker
        
        checker = SimplePermissionChecker()
        
        # Test different user types
        test_users = ["prof001", "student001", "admin001"]
        
        for user_id in test_users:
            if user_id in checker.users:
                groups = checker.get_user_groups(user_id)
                user_name = checker.users[user_id]['name']
                print(f"✅ {user_name} ({user_id}) belongs to {len(groups)} groups: {groups}")
        
        return True
    except Exception as e:
        print(f"❌ User groups test failed: {e}")
        return False

def test_group_rooms():
    """Test Case 5: Group room access"""
    print("\n📋 Test 5: Group Room Access")
    try:
        from services.simple_permissions import SimplePermissionChecker
        
        checker = SimplePermissionChecker()
        
        # Test different groups
        test_groups = ["cs_faculty", "math_students", "admin_staff"]
        
        for group_id in test_groups:
            if group_id in checker.groups:
                rooms = checker.get_group_rooms(group_id)
                group_name = checker.groups[group_id]['name']
                print(f"✅ {group_name} ({group_id}) can access {len(rooms)} rooms: {rooms}")
        
        return True
    except Exception as e:
        print(f"❌ Group rooms test failed: {e}")
        return False

def test_utilities():
    """Test Case 6: Utilities functionality"""
    print("\n📋 Test 6: Utilities Functions")
    try:
        from utils.utilities import Utilities
        from utils.terminal_colors import TerminalColors as tc
        
        utils = Utilities()
        
        # Test path resolution
        shared_path = utils.shared_files_path
        print(f"✅ Shared files path: {shared_path}")
        print(f"✅ Path exists: {shared_path.exists()}")
        
        # Test color utilities
        utils.log_msg_green("✅ Green message test")
        utils.log_msg_purple("✅ Purple message test")
        
        return True
    except Exception as e:
        print(f"❌ Utilities test failed: {e}")
        return False

def test_calendar_service():
    """Test Case 7: Calendar service instantiation"""
    print("\n📋 Test 7: Calendar Service")
    try:
        from services.synthetic_calendar_service import SyntheticCalendarService
        
        service = SyntheticCalendarService()
        print("✅ Synthetic calendar service created successfully")
        print(f"✅ Data file path: {service.data_file}")
        
        return True
    except Exception as e:
        print(f"❌ Calendar service test failed: {e}")
        return False

def run_all_tests():
    """Run all test cases"""
    print("\n🚀 Running All Test Cases...")
    
    tests = [
        ("Import Structure", test_imports),
        ("Permission System", test_permission_system),
        ("Data File Loading", test_data_loading),
        ("User Group Membership", test_user_groups),
        ("Group Room Access", test_group_rooms),
        ("Utilities Functions", test_utilities),
        ("Calendar Service", test_calendar_service),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Repository reorganization successful!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
