#!/usr/bin/env python3
"""
Comprehensive test runner for the Calendar Scheduler Agent project.
This script provides various test execution options and reporting capabilities.
"""

import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Test runner with comprehensive options and reporting."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.results = {}
        
    def run_command(self, cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(cmd)}")
        if capture_output:
            return subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        else:
            return subprocess.run(cmd, cwd=self.project_root)
    
    def run_unit_tests(self, verbose: bool = False) -> bool:
        """Run unit tests only."""
        print("🧪 Running unit tests...")
        cmd = ["python", "-m", "pytest", "tests/unit/", "-m", "unit"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd, capture_output=False)
        self.results["unit_tests"] = result.returncode == 0
        return result.returncode == 0
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests only."""
        print("🔗 Running integration tests...")
        cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd, capture_output=False)
        self.results["integration_tests"] = result.returncode == 0
        return result.returncode == 0
    
    def run_smoke_tests(self, verbose: bool = False) -> bool:
        """Run smoke tests only."""
        print("💨 Running smoke tests...")
        cmd = ["python", "-m", "pytest", "-m", "smoke"]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd, capture_output=False)
        self.results["smoke_tests"] = result.returncode == 0
        return result.returncode == 0
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = True) -> bool:
        """Run all tests with optional coverage."""
        print("🚀 Running all tests...")
        cmd = ["python", "-m", "pytest"]
        if verbose:
            cmd.append("-v")
        if coverage:
            cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
        
        result = self.run_command(cmd, capture_output=False)
        self.results["all_tests"] = result.returncode == 0
        return result.returncode == 0
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> bool:
        """Run a specific test file or test function."""
        print(f"🎯 Running specific test: {test_path}")
        cmd = ["python", "-m", "pytest", test_path]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd, capture_output=False)
        self.results[f"specific_test_{test_path}"] = result.returncode == 0
        return result.returncode == 0
    
    def run_tests_by_marker(self, marker: str, verbose: bool = False) -> bool:
        """Run tests with a specific marker."""
        print(f"🏷️ Running tests with marker: {marker}")
        cmd = ["python", "-m", "pytest", "-m", marker]
        if verbose:
            cmd.append("-v")
        
        result = self.run_command(cmd, capture_output=False)
        self.results[f"marker_{marker}"] = result.returncode == 0
        return result.returncode == 0
    
    def run_linting(self) -> bool:
        """Run code linting."""
        print("🔍 Running linting...")
        success = True
        
        # Run black check
        print("  Running black...")
        result = self.run_command(["python", "-m", "black", "--check", "."])
        if result.returncode != 0:
            print("  ❌ Black formatting issues found")
            success = False
        else:
            print("  ✅ Black formatting OK")
        
        # Run ruff check
        print("  Running ruff...")
        result = self.run_command(["python", "-m", "ruff", "check", "."])
        if result.returncode != 0:
            print("  ❌ Ruff linting issues found")
            success = False
        else:
            print("  ✅ Ruff linting OK")
        
        self.results["linting"] = success
        return success
    
    def run_type_checking(self) -> bool:
        """Run type checking with mypy."""
        print("🔎 Running type checking...")
        result = self.run_command(["python", "-m", "mypy", "."])
        success = result.returncode == 0
        
        if success:
            print("  ✅ Type checking OK")
        else:
            print("  ❌ Type checking issues found")
        
        self.results["type_checking"] = success
        return success
    
    def run_security_check(self) -> bool:
        """Run security checks."""
        print("🔒 Running security checks...")
        # Check if safety is available
        result = self.run_command(["python", "-m", "safety", "--version"])
        if result.returncode != 0:
            print("  ⚠️ Safety not installed, skipping security check")
            self.results["security_check"] = True
            return True
        
        result = self.run_command(["python", "-m", "safety", "check"])
        success = result.returncode == 0
        
        if success:
            print("  ✅ Security check OK")
        else:
            print("  ❌ Security vulnerabilities found")
        
        self.results["security_check"] = success
        return success
    
    def install_dependencies(self) -> bool:
        """Install test dependencies."""
        print("📦 Installing dependencies...")
        result = self.run_command(["pip", "install", "-r", "requirements-test.txt"])
        success = result.returncode == 0
        
        if success:
            print("  ✅ Dependencies installed")
        else:
            print("  ❌ Failed to install dependencies")
        
        return success
    
    def clean_test_artifacts(self) -> bool:
        """Clean test artifacts."""
        print("🧹 Cleaning test artifacts...")
        
        # Remove coverage files
        coverage_files = [".coverage", "htmlcov/"]
        for file_path in coverage_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                if full_path.is_file():
                    full_path.unlink()
                else:
                    import shutil
                    shutil.rmtree(full_path)
        
        # Remove pytest cache
        pytest_cache = self.project_root / ".pytest_cache"
        if pytest_cache.exists():
            import shutil
            shutil.rmtree(pytest_cache)
        
        # Remove __pycache__ directories
        for pycache in self.project_root.rglob("__pycache__"):
            import shutil
            shutil.rmtree(pycache)
        
        print("  ✅ Test artifacts cleaned")
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report."""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project": "Calendar Scheduler Agent",
            "results": self.results,
            "summary": {
                "total_checks": len(self.results),
                "passed": sum(1 for result in self.results.values() if result),
                "failed": sum(1 for result in self.results.values() if not result),
                "success_rate": sum(1 for result in self.results.values() if result) / len(self.results) * 100 if self.results else 0
            }
        }
        return report
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for test_name, success in self.results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        report = self.generate_report()
        summary = report["summary"]
        
        print("\n" + "-"*60)
        print(f"📈 Total checks: {summary['total_checks']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📊 Success rate: {summary['success_rate']:.1f}%")
        print("-"*60)
        
        if summary['failed'] == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️ {summary['failed']} test(s) failed")
        
        return summary['failed'] == 0


def main():
    """Main function for test runner."""
    parser = argparse.ArgumentParser(description="Calendar Scheduler Agent Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--lint", action="store_true", help="Run linting")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--full-suite", action="store_true", help="Run complete test suite")
    parser.add_argument("--marker", type=str, help="Run tests with specific marker")
    parser.add_argument("--test", type=str, help="Run specific test file or function")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    success = True
    
    print("Calendar Scheduler Agent Test Runner")
    print("="*50)
    
    if args.install_deps:
        success &= runner.install_dependencies()
    
    if args.clean:
        success &= runner.clean_test_artifacts()
    
    if args.unit:
        success &= runner.run_unit_tests(verbose=args.verbose)
    
    if args.integration:
        success &= runner.run_integration_tests(verbose=args.verbose)
    
    if args.smoke:
        success &= runner.run_smoke_tests(verbose=args.verbose)
    
    if args.all:
        success &= runner.run_all_tests(verbose=args.verbose, coverage=not args.no_coverage)
    
    if args.test:
        success &= runner.run_specific_test(args.test, verbose=args.verbose)
    
    if args.marker:
        success &= runner.run_tests_by_marker(args.marker, verbose=args.verbose)
    
    if args.lint:
        success &= runner.run_linting()
    
    if args.type_check:
        success &= runner.run_type_checking()
    
    if args.security:
        success &= runner.run_security_check()
    
    if args.full_suite:
        print("🚀 Running complete test suite...")
        success &= runner.run_linting()
        success &= runner.run_type_checking()
        success &= runner.run_all_tests(verbose=args.verbose, coverage=not args.no_coverage)
        success &= runner.run_security_check()
    
    # If no specific options, run default tests
    if not any([args.unit, args.integration, args.smoke, args.all, args.test, args.marker, 
                args.lint, args.type_check, args.security, args.full_suite, args.install_deps, args.clean]):
        print("🎯 Running default test suite...")
        success &= runner.run_all_tests(verbose=args.verbose, coverage=not args.no_coverage)
    
    # Print summary
    overall_success = runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
