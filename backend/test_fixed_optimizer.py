#!/usr/bin/env python3
"""
Test script for the fixed photo optimizer on Caleb's photo.
"""

import sys
import os
sys.path.append('/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/tools/photo_processing')

from photo_optimizer_fixed import optimize_player_photo

def test_caleb_photo():
    """Test the fixed optimizer on Caleb's photo."""
    
    # Path to Caleb's original photo
    original_path = "/Users/leehayton/Desktop/calebhall_phoenix_u13.jpg"
    
    print("🧪 Testing Fixed Photo Optimizer on Caleb's Photo")
    print("=" * 50)
    
    if not os.path.exists(original_path):
        print(f"❌ Original photo not found: {original_path}")
        return
    
    # Read the original photo
    with open(original_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"📷 Original photo: {len(image_bytes):,} bytes")
    
    # Apply fixed optimization
    optimized_bytes, metadata = optimize_player_photo(image_bytes, "calebhall_phoenix_u13.jpg")
    
    # Save the fixed optimized version
    fixed_path = "/Users/leehayton/Desktop/calebhall_phoenix_u13_FIXED_optimized.jpg"
    with open(fixed_path, 'wb') as f:
        f.write(optimized_bytes)
    
    print(f"\n✅ Fixed optimization complete!")
    print(f"📊 Optimization metadata:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    print(f"\n💾 Saved fixed version to: {fixed_path}")
    print(f"📏 File size: {len(optimized_bytes):,} bytes")
    
    # Compare with original broken version
    broken_path = "/Users/leehayton/Desktop/calebhall_phoenix_u13_optimized.jpg"
    if os.path.exists(broken_path):
        broken_size = os.path.getsize(broken_path)
        print(f"\n📊 Comparison:")
        print(f"   Original: {len(image_bytes):,} bytes")
        print(f"   Broken optimization: {broken_size:,} bytes")
        print(f"   Fixed optimization: {len(optimized_bytes):,} bytes")
    
    print(f"\n🎯 Please check the fixed version at: {fixed_path}")
    print("   The photo should now maintain proper orientation and aspect ratio!")

if __name__ == "__main__":
    test_caleb_photo()