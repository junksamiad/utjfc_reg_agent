#!/usr/bin/env python3
"""
Test runner for the restart chat feature
This script runs all the tests and shows the results
"""

import sys
import os
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_test_file(test_file_path):
    """Run a specific test file and capture results"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {test_file_path}")
    print(f"{'='*60}")
    
    try:
        # Import and run the test
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Try to run the main test function
        if hasattr(test_module, 'run_all_tests'):
            return test_module.run_all_tests()
        elif hasattr(test_module, 'test_database_lookup'):
            test_module.test_database_lookup()
            return True
        elif hasattr(test_module, 'test_tool_integration'):
            test_module.test_tool_integration()
            return True
        else:
            print("✅ Test file executed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all restart chat tests"""
    print("🧪 RUNNING ALL RESTART CHAT TESTS")
    print("=" * 80)
    
    # Test file paths
    test_dir = project_root / "development" / "new_features" / "restart_chat_if_disconnected" / "tests"
    
    test_files = [
        test_dir / "test_comprehensive.py",
        test_dir / "test_database_lookup.py", 
        test_dir / "test_tool_integration.py"
    ]
    
    results = []
    
    for test_file in test_files:
        if test_file.exists():
            result = run_test_file(test_file)
            results.append((test_file.name, result))
        else:
            print(f"❌ Test file not found: {test_file}")
            results.append((test_file.name, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n🏆 OVERALL RESULT: {passed}/{total} test files passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for deployment.")
    else:
        print("⚠️  Some tests failed. Review issues before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)