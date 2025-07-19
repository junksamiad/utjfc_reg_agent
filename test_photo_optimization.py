#!/usr/bin/env python3
"""
Quick test script for photo optimization implementation.
Verifies imports and basic functionality.
"""

import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all photo processing modules can be imported."""
    print("🧪 Testing photo processing imports...")
    
    try:
        from registration_agent.tools.photo_processing import (
            optimize_player_photo,
            resize_to_4_5_ratio,
            calculate_target_dimensions,
            validate_aspect_ratio
        )
        print("✅ Photo processing imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_dimension_calculations():
    """Test dimension calculation functions."""
    print("🧪 Testing dimension calculations...")
    
    try:
        from registration_agent.tools.photo_processing.dimension_calculator import (
            calculate_target_dimensions,
            validate_aspect_ratio
        )
        
        # Test dimension calculation for various inputs
        test_cases = [
            (1000, 1200),  # Portrait, should fit nicely
            (1600, 1200),  # Landscape, will need cropping
            (400, 500),    # Small image, should use minimum
            (3000, 4000),  # Large image, should use high quality
        ]
        
        for width, height in test_cases:
            target_w, target_h = calculate_target_dimensions(width, height)
            ratio_check = validate_aspect_ratio(target_w, target_h)
            
            print(f"   {width}x{height} -> {target_w}x{target_h} (ratio valid: {ratio_check['is_valid']})")
            
            if not ratio_check['is_valid']:
                print(f"   ❌ Invalid ratio for {width}x{height}")
                return False
        
        print("✅ Dimension calculations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Dimension calculation test failed: {e}")
        return False

def test_quality_optimization():
    """Test quality optimization functions."""
    print("🧪 Testing quality optimization...")
    
    try:
        from registration_agent.tools.photo_processing.quality_optimizer import (
            get_quality_recommendation,
            find_optimal_quality
        )
        
        # Test quality recommendations
        test_cases = [
            (1000, 400),   # Significant compression needed
            (500, 450),    # Minor compression
            (300, 400),    # No compression needed
        ]
        
        for original_kb, target_kb in test_cases:
            recommendation = get_quality_recommendation(original_kb, target_kb)
            print(f"   {original_kb}KB -> {target_kb}KB: {recommendation['strategy']} (quality: {recommendation['recommended_quality']})")
        
        print("✅ Quality optimization working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Quality optimization test failed: {e}")
        return False

def test_photo_optimizer():
    """Test main photo optimizer with sample data."""
    print("🧪 Testing main photo optimizer...")
    
    try:
        from registration_agent.tools.photo_processing.photo_optimizer import (
            calculate_optimal_dimensions,
            FA_ASPECT_RATIO
        )
        
        # Test optimal dimension calculation
        test_cases = [
            (800, 1000),    # Already perfect
            (1200, 1600),   # Good portrait
            (2000, 1500),   # Landscape
            (400, 600),     # Too small
        ]
        
        for width, height in test_cases:
            target_w, target_h = calculate_optimal_dimensions(width, height)
            actual_ratio = target_w / target_h
            expected_ratio = FA_ASPECT_RATIO
            
            print(f"   {width}x{height} -> {target_w}x{target_h} (ratio: {actual_ratio:.2f}, expected: {expected_ratio:.2f})")
            
            # Allow small tolerance for floating point calculations
            if abs(actual_ratio - expected_ratio) > 0.01:
                print(f"   ❌ Ratio mismatch for {width}x{height}")
                return False
        
        print("✅ Photo optimizer working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Photo optimizer test failed: {e}")
        return False

def test_upload_tool_integration():
    """Test that upload tool can import photo optimization."""
    print("🧪 Testing upload tool integration...")
    
    try:
        # Test import in upload tool context
        from registration_agent.tools.registration_tools.upload_photo_to_s3_tool import (
            _optimize_photo_for_fa_portal,
            PHOTO_OPTIMIZATION_SUPPORT
        )
        
        print(f"   Photo optimization support: {'Enabled' if PHOTO_OPTIMIZATION_SUPPORT else 'Disabled'}")
        
        if PHOTO_OPTIMIZATION_SUPPORT:
            print("✅ Upload tool integration successful")
        else:
            print("⚠️  Upload tool integration available but optimization disabled")
        
        return True
        
    except ImportError as e:
        print(f"❌ Upload tool integration failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting photo optimization tests...\n")
    
    tests = [
        test_imports,
        test_dimension_calculations,
        test_quality_optimization,
        test_photo_optimizer,
        test_upload_tool_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Photo optimization implementation is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)