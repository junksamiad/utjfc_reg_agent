"""
Dimension calculation module for photo optimization.
Handles aspect ratio calculations and smart cropping coordinates.

FA Portal Requirements:
- Aspect Ratio: 4:5 (0.8)
- Minimum: 600×750px
- Maximum: 2300×3100px (we prefer lower)
"""

from typing import Tuple, Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Constants
FA_ASPECT_RATIO = 4/5  # 0.8 (width/height)
ASPECT_RATIO_TOLERANCE = 0.01  # Allow 1% tolerance

# Dimension presets
DIMENSIONS_PRESETS = {
    "minimum": (600, 750),
    "standard": (800, 1000),
    "high_quality": (1200, 1500),
    "maximum": (2300, 3100)  # FA maximum, but we prefer not to use this
}


def calculate_target_dimensions(
    original_width: int, 
    original_height: int,
    prefer_quality: str = "standard"
) -> Tuple[int, int]:
    """
    Calculate optimal target dimensions for 4:5 ratio based on original image size.
    
    Args:
        original_width: Original image width in pixels
        original_height: Original image height in pixels
        prefer_quality: Preferred quality preset ("minimum", "standard", "high_quality")
        
    Returns:
        tuple: (target_width, target_height) maintaining 4:5 ratio
    """
    # Get preferred dimensions
    preferred_width, preferred_height = DIMENSIONS_PRESETS.get(
        prefer_quality, 
        DIMENSIONS_PRESETS["standard"]
    )
    
    # Calculate original aspect ratio
    original_ratio = original_width / original_height
    
    logger.info(f"Original dimensions: {original_width}x{original_height} (ratio: {original_ratio:.2f})")
    
    # If original is very small, use minimum dimensions
    if original_width < DIMENSIONS_PRESETS["minimum"][0] or original_height < DIMENSIONS_PRESETS["minimum"][1]:
        logger.info("Original image smaller than minimum, using minimum dimensions")
        return DIMENSIONS_PRESETS["minimum"]
    
    # If original is very large, use high quality dimensions
    if original_width > 2000 or original_height > 2500:
        logger.info("Large original image, using high quality dimensions")
        return DIMENSIONS_PRESETS["high_quality"]
    
    # For medium-sized images, calculate best fit
    # Try to preserve as much of the original image as possible
    if original_ratio > FA_ASPECT_RATIO:
        # Image is wider than 4:5, base on height
        target_height = min(preferred_height, original_height)
        target_width = int(target_height * FA_ASPECT_RATIO)
    else:
        # Image is taller than 4:5, base on width
        target_width = min(preferred_width, original_width)
        target_height = int(target_width / FA_ASPECT_RATIO)
    
    # Ensure we meet minimum requirements
    if target_width < DIMENSIONS_PRESETS["minimum"][0]:
        target_width = DIMENSIONS_PRESETS["minimum"][0]
        target_height = DIMENSIONS_PRESETS["minimum"][1]
    
    logger.info(f"Calculated target dimensions: {target_width}x{target_height}")
    return target_width, target_height


def get_crop_coordinates(
    image_width: int, 
    image_height: int,
    target_width: int,
    target_height: int,
    crop_position: str = "center"
) -> Tuple[int, int, int, int]:
    """
    Calculate crop coordinates to achieve target dimensions from source image.
    
    Args:
        image_width: Current image width
        image_height: Current image height
        target_width: Desired width after crop
        target_height: Desired height after crop
        crop_position: Where to crop from ("center", "top", "bottom", "smart")
        
    Returns:
        tuple: (left, top, right, bottom) crop coordinates
    """
    # First, ensure we're not trying to crop larger than the image
    if target_width > image_width or target_height > image_height:
        logger.warning(f"Target dimensions ({target_width}x{target_height}) larger than image ({image_width}x{image_height})")
        # Return full image coordinates
        return 0, 0, image_width, image_height
    
    # Calculate how much to crop
    crop_width = image_width - target_width
    crop_height = image_height - target_height
    
    if crop_position == "center":
        # Center crop - most common for portraits
        left = crop_width // 2
        top = crop_height // 2
        right = left + target_width
        bottom = top + target_height
        
    elif crop_position == "top":
        # Crop from top - useful for upper body photos
        left = crop_width // 2
        top = 0
        right = left + target_width
        bottom = target_height
        
    elif crop_position == "bottom":
        # Crop from bottom
        left = crop_width // 2
        top = crop_height
        right = left + target_width
        bottom = image_height
        
    elif crop_position == "smart":
        # Smart crop - favor upper third for portraits (where faces typically are)
        left = crop_width // 2
        # Position crop to favor upper portion of image (rule of thirds)
        top = crop_height // 3
        right = left + target_width
        bottom = top + target_height
        
    else:
        # Default to center crop
        left = crop_width // 2
        top = crop_height // 2
        right = left + target_width
        bottom = top + target_height
    
    logger.debug(f"Crop coordinates: left={left}, top={top}, right={right}, bottom={bottom}")
    return left, top, right, bottom


def validate_aspect_ratio(width: int, height: int) -> Dict[str, Any]:
    """
    Validate if dimensions meet FA 4:5 aspect ratio requirement.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        dict: Validation result with ratio details
    """
    actual_ratio = width / height
    ratio_difference = abs(actual_ratio - FA_ASPECT_RATIO)
    is_valid = ratio_difference <= ASPECT_RATIO_TOLERANCE
    
    return {
        "is_valid": is_valid,
        "actual_ratio": round(actual_ratio, 3),
        "expected_ratio": FA_ASPECT_RATIO,
        "difference": round(ratio_difference, 3),
        "tolerance": ASPECT_RATIO_TOLERANCE,
        "dimensions": f"{width}x{height}"
    }


def suggest_dimensions_for_ratio(
    current_width: int, 
    current_height: int,
    maintain: str = "width"
) -> Tuple[int, int]:
    """
    Suggest new dimensions to achieve perfect 4:5 ratio.
    
    Args:
        current_width: Current width
        current_height: Current height
        maintain: Which dimension to keep ("width" or "height")
        
    Returns:
        tuple: (suggested_width, suggested_height)
    """
    if maintain == "width":
        # Keep width, adjust height
        suggested_width = current_width
        suggested_height = int(current_width / FA_ASPECT_RATIO)
    elif maintain == "height":
        # Keep height, adjust width
        suggested_height = current_height
        suggested_width = int(current_height * FA_ASPECT_RATIO)
    else:
        # Find closest standard dimension
        closest_preset = None
        min_difference = float('inf')
        
        for preset_name, (preset_width, preset_height) in DIMENSIONS_PRESETS.items():
            if preset_name == "maximum":  # Skip maximum preset
                continue
                
            # Calculate difference from current size
            width_diff = abs(current_width - preset_width)
            height_diff = abs(current_height - preset_height)
            total_diff = width_diff + height_diff
            
            if total_diff < min_difference:
                min_difference = total_diff
                closest_preset = (preset_width, preset_height)
        
        suggested_width, suggested_height = closest_preset or DIMENSIONS_PRESETS["standard"]
    
    return suggested_width, suggested_height


def calculate_scale_factor(
    original_width: int,
    original_height: int,
    target_width: int,
    target_height: int,
    mode: str = "cover"
) -> float:
    """
    Calculate scale factor to resize image to target dimensions.
    
    Args:
        original_width: Original image width
        original_height: Original image height
        target_width: Target width
        target_height: Target height
        mode: "cover" (fill target, may crop) or "contain" (fit within target, may have padding)
        
    Returns:
        float: Scale factor to apply
    """
    width_scale = target_width / original_width
    height_scale = target_height / original_height
    
    if mode == "cover":
        # Use larger scale to ensure image covers target area
        scale = max(width_scale, height_scale)
    elif mode == "contain":
        # Use smaller scale to ensure image fits within target
        scale = min(width_scale, height_scale)
    else:
        # Default to cover mode
        scale = max(width_scale, height_scale)
    
    logger.debug(f"Scale factor: {scale:.3f} (mode: {mode})")
    return scale


def get_dimension_info(width: int, height: int) -> Dict[str, Any]:
    """
    Get comprehensive information about image dimensions.
    
    Args:
        width: Image width
        height: Image height
        
    Returns:
        dict: Dimension information including ratio, orientation, and FA compliance
    """
    ratio = width / height
    orientation = "landscape" if ratio > 1 else "portrait" if ratio < 1 else "square"
    
    # Check FA compliance
    ratio_valid = validate_aspect_ratio(width, height)
    size_valid = (
        width >= DIMENSIONS_PRESETS["minimum"][0] and 
        height >= DIMENSIONS_PRESETS["minimum"][1] and
        width <= DIMENSIONS_PRESETS["maximum"][0] and 
        height <= DIMENSIONS_PRESETS["maximum"][1]
    )
    
    # Determine quality level
    if width >= DIMENSIONS_PRESETS["high_quality"][0]:
        quality_level = "high"
    elif width >= DIMENSIONS_PRESETS["standard"][0]:
        quality_level = "standard"
    elif width >= DIMENSIONS_PRESETS["minimum"][0]:
        quality_level = "minimum"
    else:
        quality_level = "below_minimum"
    
    return {
        "width": width,
        "height": height,
        "ratio": round(ratio, 3),
        "orientation": orientation,
        "fa_ratio_compliant": ratio_valid["is_valid"],
        "fa_size_compliant": size_valid,
        "quality_level": quality_level,
        "pixels": width * height,
        "megapixels": round((width * height) / 1_000_000, 2)
    }