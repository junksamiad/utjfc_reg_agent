"""
Photo optimization module for UTJFC registration system.
Handles photo resizing and optimization to meet FA club portal requirements.

FA Portal Requirements:
- Aspect Ratio: 4:5 (width:height)
- Minimum Dimensions: 600 × 750 pixels
- Maximum Dimensions: 2300 × 3100 pixels
- File Format: JPEG

Optimization Targets:
- Standard Size: 800 × 1000 pixels
- High Quality: 1200 × 1500 pixels
- File Size: 200-500 KB per photo
- Quality: 85% JPEG quality for optimal balance
"""

import os
from typing import Tuple, Optional, Dict, Any
from PIL import Image
from io import BytesIO
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Photo optimization settings with environment variable overrides
PHOTO_OPTIMIZATION_ENABLED = os.environ.get('PHOTO_OPTIMIZATION_ENABLED', 'true').lower() == 'true'
PHOTO_TARGET_WIDTH = int(os.environ.get('PHOTO_TARGET_WIDTH', '800'))
PHOTO_TARGET_HEIGHT = int(os.environ.get('PHOTO_TARGET_HEIGHT', '1000'))
PHOTO_QUALITY = int(os.environ.get('PHOTO_QUALITY', '85'))
PHOTO_MAX_FILE_SIZE_KB = int(os.environ.get('PHOTO_MAX_FILE_SIZE_KB', '500'))
PHOTO_MIN_WIDTH = int(os.environ.get('PHOTO_MIN_WIDTH', '600'))
PHOTO_MIN_HEIGHT = int(os.environ.get('PHOTO_MIN_HEIGHT', '750'))

# Constants
FA_ASPECT_RATIO = 4/5  # 0.8 (width/height)
HIGH_QUALITY_WIDTH = 1200
HIGH_QUALITY_HEIGHT = 1500


def optimize_player_photo(image_bytes: bytes, filename: str) -> Tuple[bytes, Dict[str, Any]]:
    """
    Main photo optimization function that processes uploaded photos to meet FA requirements.
    
    Args:
        image_bytes: Raw image bytes from upload
        filename: Original filename for format detection
        
    Returns:
        tuple: (optimized_image_bytes, metadata)
    """
    if not PHOTO_OPTIMIZATION_ENABLED:
        logger.info("Photo optimization is disabled, returning original image")
        return image_bytes, {"optimization_applied": False}
    
    try:
        # Open image from bytes
        logger.info(f"Starting photo optimization for {filename}")
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            logger.info(f"Converting image from {image.mode} to RGB")
            image = image.convert('RGB')
        
        # Store original dimensions for metadata
        original_width, original_height = image.size
        original_size_kb = len(image_bytes) / 1024
        
        logger.info(f"Original image: {original_width}x{original_height}, {original_size_kb:.1f}KB")
        
        # Calculate target dimensions based on original size
        target_width, target_height = calculate_optimal_dimensions(
            original_width, 
            original_height
        )
        
        # Resize image to 4:5 aspect ratio
        resized_image = resize_to_4_5_ratio(image, target_width, target_height)
        
        # Optimize file size while maintaining quality
        optimized_bytes, final_quality = optimize_file_size(
            resized_image, 
            target_size_kb=PHOTO_MAX_FILE_SIZE_KB,
            quality_start=PHOTO_QUALITY
        )
        
        # Calculate final size
        final_size_kb = len(optimized_bytes) / 1024
        size_reduction_percent = ((original_size_kb - final_size_kb) / original_size_kb) * 100
        
        metadata = {
            "optimization_applied": True,
            "original_dimensions": f"{original_width}x{original_height}",
            "final_dimensions": f"{target_width}x{target_height}",
            "original_size_kb": round(original_size_kb, 1),
            "final_size_kb": round(final_size_kb, 1),
            "size_reduction_percent": round(size_reduction_percent, 1),
            "final_quality": final_quality,
            "aspect_ratio": "4:5"
        }
        
        logger.info(f"Photo optimization complete: {metadata}")
        return optimized_bytes, metadata
        
    except Exception as e:
        logger.error(f"Photo optimization failed: {e}")
        logger.info("Falling back to original image")
        return image_bytes, {
            "optimization_applied": False,
            "error": str(e)
        }


def resize_to_4_5_ratio(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Resize image to exact 4:5 aspect ratio with smart cropping.
    
    Args:
        image: PIL Image object
        target_width: Target width in pixels
        target_height: Target height in pixels
        
    Returns:
        PIL Image object resized to 4:5 ratio
    """
    current_width, current_height = image.size
    current_ratio = current_width / current_height
    
    logger.info(f"Resizing from {current_width}x{current_height} (ratio: {current_ratio:.2f}) to {target_width}x{target_height}")
    
    # First, resize the image to fit the target dimensions while maintaining aspect ratio
    # Calculate scale factors
    scale_width = target_width / current_width
    scale_height = target_height / current_height
    
    # Use the larger scale factor to ensure the image fills the target dimensions
    scale = max(scale_width, scale_height)
    
    # Calculate intermediate size
    intermediate_width = int(current_width * scale)
    intermediate_height = int(current_height * scale)
    
    # Resize image to intermediate size
    resized_image = image.resize((intermediate_width, intermediate_height), Image.Resampling.LANCZOS)
    
    # Now crop to exact target dimensions (center crop)
    if intermediate_width > target_width or intermediate_height > target_height:
        # Calculate crop coordinates for center crop
        left = (intermediate_width - target_width) // 2
        top = (intermediate_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        # Crop to exact dimensions
        cropped_image = resized_image.crop((left, top, right, bottom))
        logger.info(f"Cropped to exact {target_width}x{target_height} dimensions")
        return cropped_image
    
    # If for some reason we're still not at exact dimensions, resize
    if resized_image.size != (target_width, target_height):
        resized_image = resized_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    return resized_image


def calculate_optimal_dimensions(original_width: int, original_height: int) -> Tuple[int, int]:
    """
    Calculate optimal target dimensions for 4:5 ratio based on original image size.
    
    Args:
        original_width: Original image width
        original_height: Original image height
        
    Returns:
        tuple: (target_width, target_height)
    """
    # If original image is very large, use high quality dimensions
    if original_width > 2000 or original_height > 2500:
        logger.info("Large original image detected, using high quality dimensions")
        return HIGH_QUALITY_WIDTH, HIGH_QUALITY_HEIGHT
    
    # If original image is smaller than our minimum, use minimum dimensions
    if original_width < PHOTO_MIN_WIDTH or original_height < PHOTO_MIN_HEIGHT:
        logger.info("Small original image detected, using minimum dimensions")
        return PHOTO_MIN_WIDTH, PHOTO_MIN_HEIGHT
    
    # Otherwise use standard dimensions
    return PHOTO_TARGET_WIDTH, PHOTO_TARGET_HEIGHT


def optimize_file_size(image: Image.Image, target_size_kb: int = 500, quality_start: int = 85) -> Tuple[bytes, int]:
    """
    Optimize file size while maintaining acceptable quality.
    
    Args:
        image: PIL Image object to optimize
        target_size_kb: Target file size in KB
        quality_start: Starting JPEG quality (1-100)
        
    Returns:
        tuple: (optimized_image_bytes, final_quality)
    """
    quality = quality_start
    min_quality = 70  # Don't go below this quality
    
    # First attempt with starting quality
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=quality, optimize=True)
    current_size_kb = buffer.tell() / 1024
    
    logger.info(f"Initial save: {current_size_kb:.1f}KB at quality {quality}")
    
    # If already under target size, return
    if current_size_kb <= target_size_kb:
        buffer.seek(0)
        return buffer.read(), quality
    
    # Binary search for optimal quality
    high_quality = quality
    low_quality = min_quality
    best_bytes = None
    best_quality = quality
    
    while high_quality - low_quality > 5:
        mid_quality = (high_quality + low_quality) // 2
        
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=mid_quality, optimize=True)
        current_size_kb = buffer.tell() / 1024
        
        logger.debug(f"Trying quality {mid_quality}: {current_size_kb:.1f}KB")
        
        if current_size_kb <= target_size_kb:
            # Size is good, try higher quality
            buffer.seek(0)
            best_bytes = buffer.read()
            best_quality = mid_quality
            low_quality = mid_quality
        else:
            # Size too large, reduce quality
            high_quality = mid_quality
    
    # If we found a good size, use it
    if best_bytes:
        logger.info(f"Optimized to {len(best_bytes)/1024:.1f}KB at quality {best_quality}")
        return best_bytes, best_quality
    
    # Otherwise, use minimum quality
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=min_quality, optimize=True)
    buffer.seek(0)
    final_bytes = buffer.read()
    final_size_kb = len(final_bytes) / 1024
    
    logger.info(f"Final size: {final_size_kb:.1f}KB at minimum quality {min_quality}")
    return final_bytes, min_quality


def process_uploaded_photo(file_path: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Process an uploaded photo file and save the optimized version.
    
    Args:
        file_path: Path to the uploaded photo
        
    Returns:
        tuple: (optimized_file_path, metadata) or (None, error_metadata)
    """
    try:
        # Read the original file
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        
        # Get filename for format detection
        filename = os.path.basename(file_path)
        
        # Optimize the photo
        optimized_bytes, metadata = optimize_player_photo(image_bytes, filename)
        
        # If optimization was applied, save the optimized version
        if metadata.get('optimization_applied', False):
            # Generate optimized filename
            base_name, ext = os.path.splitext(file_path)
            optimized_path = f"{base_name}_optimized.jpg"
            
            # Save optimized image
            with open(optimized_path, 'wb') as f:
                f.write(optimized_bytes)
            
            logger.info(f"Saved optimized photo to: {optimized_path}")
            return optimized_path, metadata
        else:
            # Return original path if optimization wasn't applied
            return file_path, metadata
            
    except Exception as e:
        logger.error(f"Failed to process uploaded photo: {e}")
        return None, {
            "optimization_applied": False,
            "error": str(e)
        }