"""
Photo processing module for UTJFC registration system.

This module provides photo optimization functionality to ensure uploaded player photos
meet FA club portal requirements:
- 4:5 aspect ratio
- 600×750px minimum dimensions
- Optimal file size (200-500KB)
- JPEG format

Main Functions:
- optimize_player_photo: Main optimization entry point
- resize_to_4_5_ratio: Resize images to FA requirements
- process_uploaded_photo: Process files from upload
"""

from .photo_optimizer import (
    optimize_player_photo,
    resize_to_4_5_ratio_smart,
    calculate_optimal_dimensions,
    optimize_file_size,
    process_uploaded_photo
)

from .dimension_calculator import (
    calculate_target_dimensions,
    get_crop_coordinates,
    validate_aspect_ratio,
    suggest_dimensions_for_ratio,
    calculate_scale_factor,
    get_dimension_info
)

from .quality_optimizer import (
    optimize_file_size as quality_optimize_file_size,
    compress_image,
    find_optimal_quality,
    get_quality_recommendation,
    analyze_compression_impact
)

# Export main functions
__all__ = [
    # Main optimization functions
    'optimize_player_photo',
    'resize_to_4_5_ratio_smart',
    'process_uploaded_photo',
    
    # Dimension calculations
    'calculate_target_dimensions',
    'calculate_optimal_dimensions',
    'get_crop_coordinates',
    'validate_aspect_ratio',
    'suggest_dimensions_for_ratio',
    'calculate_scale_factor',
    'get_dimension_info',
    
    # Quality optimization
    'optimize_file_size',
    'quality_optimize_file_size',
    'compress_image',
    'find_optimal_quality',
    'get_quality_recommendation',
    'analyze_compression_impact'
]

# Module version
__version__ = "1.0.0"

# Module metadata
__author__ = "UTJFC Registration System"
__description__ = "Photo optimization for FA club portal compliance"