#!/usr/bin/env python3
"""
Simple verification that the testing setup is working.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_setup():
    """Test that basic setup is working."""
    print("🔍 Testing basic setup...")
    
    # Check if required files exist
    required_files = [
        "pytest.ini",
        "requirements-test.txt",
        "tests/conftest.py",
        "tests/test_framework.py",
        "tests/fixtures/test_data.py",
        "run_tests.py",
        "Makefile"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Test basic imports
    try:
        from tests.fixtures.test_data import SAMPLE_EVENTS, SAMPLE_ROOMS
        print(f"✅ Test fixtures loaded: {len(SAMPLE_EVENTS)} events, {len(SAMPLE_ROOMS)} rooms")
    except ImportError as e:
        print(f"❌ Failed to import test fixtures: {e}")
        return False
    
    # Test test framework
    try:
        from tests.test_framework import BaseTestCase, MockResponseBuilder
        print("✅ Test framework imports working")
    except ImportError as e:
        print(f"❌ Failed to import test framework: {e}")
        return False
    
    return True

def test_project_structure():
    """Test project structure."""
    print("\n📁 Testing project structure...")
    
    expected_dirs = [
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "services",
        "agent",
        "utils",
        "config",
        "evaluation"
    ]
    
    for dir_path in expected_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"⚠️  {dir_path} (missing)")
    
    return True

def test_configuration():
    """Test configuration files."""
    print("\n⚙️ Testing configuration...")
    
    # Check pytest.ini
    pytest_ini = project_root / "pytest.ini"
    if pytest_ini.exists():
        print("✅ pytest.ini exists")
        with open(pytest_ini) as f:
            content = f.read()
            if "testpaths = tests" in content:
                print("✅ pytest.ini configured correctly")
            else:
                print("⚠️  pytest.ini may need configuration")
    
    # Check requirements-test.txt
    req_test = project_root / "requirements-test.txt"
    if req_test.exists():
        print("✅ requirements-test.txt exists")
        with open(req_test) as f:
            content = f.read()
            if "pytest" in content:
                print("✅ pytest in requirements")
            else:
                print("⚠️  pytest not found in requirements")
    
    return True

def main():
    """Main test function."""
    print("🧪 Calendar Scheduler Agent - Testing Setup Verification")
    print("=" * 60)
    
    tests = [
        test_basic_setup,
        test_project_structure,
        test_configuration
    ]
    
    all_passed = True
    for test in tests:
        try:
            result = test()
            all_passed = all_passed and result
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Testing setup is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: make install-dev")
        print("2. Run tests: make test")
        print("3. Run specific tests: python run_tests.py --unit")
        print("4. Run full test suite: python run_tests.py --full-suite")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
