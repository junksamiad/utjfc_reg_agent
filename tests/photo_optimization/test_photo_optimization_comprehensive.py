#!/usr/bin/env python3
"""
Comprehensive test suite for photo optimization functionality.
Tests photo resizing, quality optimization, and FA portal compliance.
"""

import sys
import os
import unittest
from io import BytesIO
from PIL import Image

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from registration_agent.tools.photo_processing import (
    optimize_player_photo,
    resize_to_4_5_ratio,
    calculate_optimal_dimensions,
    optimize_file_size,
    validate_aspect_ratio,
    calculate_target_dimensions
)

class TestPhotoOptimization(unittest.TestCase):
    """Test suite for photo optimization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_images = {}
        
        # Create test images with different aspect ratios and sizes
        test_specs = {
            'portrait_large': (1200, 1600, 'RGB'),
            'landscape_large': (1600, 1200, 'RGB'),
            'square_medium': (1000, 1000, 'RGB'),
            'portrait_small': (400, 600, 'RGB'),
            'landscape_small': (600, 400, 'RGB'),
            'very_large': (3000, 4000, 'RGB'),
            'rgba_image': (800, 1000, 'RGBA'),
        }
        
        for name, (width, height, mode) in test_specs.items():
            # Create a solid color image for testing
            color = (255, 0, 0) if mode == 'RGB' else (255, 0, 0, 255)
            image = Image.new(mode, (width, height), color)
            
            # Convert to bytes
            buffer = BytesIO()
            format_type = 'PNG' if mode == 'RGBA' else 'JPEG'
            image.save(buffer, format=format_type, quality=90)
            
            self.test_images[name] = {
                'bytes': buffer.getvalue(),
                'image': image,
                'width': width,
                'height': height,
                'mode': mode
            }
    
    def test_aspect_ratio_validation(self):
        """Test aspect ratio validation for FA compliance."""
        # Test valid 4:5 ratios
        valid_cases = [
            (600, 750),   # Minimum dimensions
            (800, 1000),  # Standard dimensions
            (1200, 1500), # High quality dimensions
        ]
        
        for width, height in valid_cases:
            result = validate_aspect_ratio(width, height)
            self.assertTrue(result['is_valid'], 
                          f"Expected {width}x{height} to be valid 4:5 ratio")
            self.assertAlmostEqual(result['actual_ratio'], 0.8, places=2)
        
        # Test invalid ratios
        invalid_cases = [
            (800, 800),   # Square
            (1000, 800),  # Landscape
            (600, 900),   # Too tall
        ]
        
        for width, height in invalid_cases:
            result = validate_aspect_ratio(width, height)
            self.assertFalse(result['is_valid'], 
                           f"Expected {width}x{height} to be invalid 4:5 ratio")
    
    def test_dimension_calculations(self):
        """Test dimension calculation for various input sizes."""
        test_cases = [
            # (input_width, input_height, expected_category)
            (400, 500, "minimum"),     # Small image
            (800, 1000, "standard"),   # Perfect size
            (1600, 1200, "standard"),  # Landscape
            (3000, 4000, "high_quality"),  # Very large
        ]
        
        for input_w, input_h, expected_category in test_cases:
            target_w, target_h = calculate_target_dimensions(input_w, input_h)
            
            # Verify 4:5 ratio
            ratio = target_w / target_h
            self.assertAlmostEqual(ratio, 0.8, places=2, 
                                 msg=f"Ratio for {input_w}x{input_h} -> {target_w}x{target_h}")
            
            # Verify minimum dimensions
            self.assertGreaterEqual(target_w, 600, "Width below minimum")
            self.assertGreaterEqual(target_h, 750, "Height below minimum")
    
    def test_image_resizing(self):
        """Test image resizing to 4:5 aspect ratio."""
        for name, test_data in self.test_images.items():
            if name == 'rgba_image':
                continue  # Skip RGBA for this test
                
            image = test_data['image']
            target_w, target_h = 800, 1000
            
            resized = resize_to_4_5_ratio(image, target_w, target_h)
            
            # Verify dimensions
            self.assertEqual(resized.size, (target_w, target_h), 
                           f"Resized image {name} has incorrect dimensions")
            
            # Verify aspect ratio
            ratio = resized.width / resized.height
            self.assertAlmostEqual(ratio, 0.8, places=2, 
                                 msg=f"Resized image {name} has incorrect aspect ratio")
    
    def test_quality_optimization(self):
        """Test file size optimization while maintaining quality."""
        # Test with a medium-sized image
        test_image = self.test_images['portrait_large']['image']
        
        # Test different target sizes
        target_sizes = [200, 400, 600]  # KB
        
        for target_kb in target_sizes:
            optimized_bytes, quality_used = optimize_file_size(test_image, target_kb)
            actual_size_kb = len(optimized_bytes) / 1024
            
            # Should be close to target (within 20% tolerance for small files)
            if target_kb > 300:
                tolerance = 0.2
            else:
                tolerance = 0.3  # More tolerance for aggressive compression
                
            self.assertLessEqual(actual_size_kb, target_kb * (1 + tolerance),
                               msg=f"File size {actual_size_kb:.1f}KB exceeds target {target_kb}KB")
            
            # Quality should be reasonable
            self.assertGreaterEqual(quality_used, 60, "Quality too low")
            self.assertLessEqual(quality_used, 95, "Quality unnecessarily high")
    
    def test_complete_optimization_workflow(self):
        """Test complete photo optimization workflow."""
        for name, test_data in self.test_images.items():
            if name == 'rgba_image':
                continue  # Will be converted to RGB internally
                
            image_bytes = test_data['bytes']
            
            # Run complete optimization
            optimized_bytes, metadata = optimize_player_photo(image_bytes, f"{name}.jpg")
            
            # Verify optimization was applied
            self.assertTrue(metadata.get('optimization_applied', False), 
                          f"Optimization should be applied for {name}")
            
            # Verify file size reduction (unless very small original)
            original_size_kb = len(image_bytes) / 1024
            final_size_kb = metadata.get('final_size_kb', 0)
            
            if original_size_kb > 200:  # Only check reduction for larger files
                self.assertLess(final_size_kb, original_size_kb, 
                              f"File size should be reduced for {name}")
            
            # Verify dimensions are in metadata
            self.assertIn('final_dimensions', metadata)
            dimensions = metadata['final_dimensions']
            self.assertRegex(dimensions, r'\d+x\d+', "Invalid dimensions format")
            
            # Verify aspect ratio is 4:5
            width, height = map(int, dimensions.split('x'))
            ratio = width / height
            self.assertAlmostEqual(ratio, 0.8, places=2, 
                                 msg=f"Final aspect ratio incorrect for {name}")
    
    def test_rgba_to_rgb_conversion(self):
        """Test RGBA image conversion to RGB during optimization."""
        rgba_data = self.test_images['rgba_image']
        image_bytes = rgba_data['bytes']
        
        # Optimize RGBA image
        optimized_bytes, metadata = optimize_player_photo(image_bytes, "rgba_test.png")
        
        # Should be successfully optimized
        self.assertTrue(metadata.get('optimization_applied', False))
        
        # Verify the optimized image is RGB compatible (JPEG)
        optimized_image = Image.open(BytesIO(optimized_bytes))
        self.assertEqual(optimized_image.mode, 'RGB', "RGBA should be converted to RGB")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test very small image
        tiny_image = Image.new('RGB', (100, 100), (255, 0, 0))
        buffer = BytesIO()
        tiny_image.save(buffer, format='JPEG')
        
        optimized_bytes, metadata = optimize_player_photo(buffer.getvalue(), "tiny.jpg")
        
        # Should still optimize to minimum dimensions
        self.assertTrue(metadata.get('optimization_applied', False))
        dimensions = metadata.get('final_dimensions', '')
        if dimensions:
            width, height = map(int, dimensions.split('x'))
            self.assertGreaterEqual(width, 600, "Should enforce minimum width")
            self.assertGreaterEqual(height, 750, "Should enforce minimum height")
    
    def test_performance_benchmarks(self):
        """Test that optimization performance meets requirements."""
        import time
        
        # Test with large image
        large_data = self.test_images['very_large']
        image_bytes = large_data['bytes']
        
        start_time = time.time()
        optimized_bytes, metadata = optimize_player_photo(image_bytes, "large_test.jpg")
        processing_time = time.time() - start_time
        
        # Should complete within 5 seconds (generous for testing)
        self.assertLess(processing_time, 5.0, 
                       f"Processing took {processing_time:.2f}s, should be under 5s")
        
        # Should successfully optimize
        self.assertTrue(metadata.get('optimization_applied', False))
        
        # Should achieve significant size reduction
        original_size_kb = len(image_bytes) / 1024
        final_size_kb = metadata.get('final_size_kb', original_size_kb)
        reduction_percent = ((original_size_kb - final_size_kb) / original_size_kb) * 100
        
        self.assertGreater(reduction_percent, 10, 
                          f"Should achieve >10% size reduction, got {reduction_percent:.1f}%")


class TestDimensionCalculator(unittest.TestCase):
    """Test suite for dimension calculation functions."""
    
    def test_optimal_dimension_calculation(self):
        """Test optimal dimension calculation for various inputs."""
        test_cases = [
            # (original_w, original_h, expected_w, expected_h)
            (800, 1000, 800, 1000),      # Already perfect
            (1200, 1600, 800, 1000),     # Good portrait, should use standard
            (2400, 3200, 1200, 1500),    # Large portrait, should use high quality
            (400, 600, 600, 750),        # Small, should use minimum
        ]
        
        for orig_w, orig_h, exp_w, exp_h in test_cases:
            calc_w, calc_h = calculate_optimal_dimensions(orig_w, orig_h)
            self.assertEqual((calc_w, calc_h), (exp_w, exp_h),
                           f"Dimension calculation failed for {orig_w}x{orig_h}")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)