"""
Quality optimization module for photo processing.
Handles file size reduction while maintaining visual quality.

Optimization Goals:
- Target file size: 200-500 KB
- Maintain professional appearance
- Balance between quality and size
- Progressive JPEG optimization
"""

from typing import Tuple, Dict, Any, Optional
from PIL import Image
from io import BytesIO
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Quality optimization constants
DEFAULT_TARGET_SIZE_KB = 500
MIN_QUALITY = 60
MAX_QUALITY = 95
QUALITY_STEP = 5
PROGRESSIVE_THRESHOLD_KB = 100  # Use progressive JPEG for files larger than this


def optimize_file_size(
    image: Image.Image,
    target_size_kb: int = DEFAULT_TARGET_SIZE_KB,
    quality_start: int = 85,
    format: str = 'JPEG'
) -> Tuple[bytes, int]:
    """
    Optimize image file size while maintaining acceptable quality.
    
    Args:
        image: PIL Image object to optimize
        target_size_kb: Target file size in KB
        quality_start: Starting JPEG quality (1-100)
        format: Output format ('JPEG' recommended)
        
    Returns:
        tuple: (optimized_image_bytes, final_quality_used)
    """
    if format.upper() not in ['JPEG', 'JPG']:
        logger.warning(f"Format {format} not supported for optimization, using JPEG")
        format = 'JPEG'
    
    logger.info(f"Starting quality optimization: target={target_size_kb}KB, quality={quality_start}")
    
    # First attempt with starting quality
    best_result = _save_with_quality(image, quality_start, format)
    current_size_kb = len(best_result) / 1024
    
    logger.info(f"Initial size: {current_size_kb:.1f}KB at quality {quality_start}")
    
    # If already under target, return
    if current_size_kb <= target_size_kb:
        return best_result, quality_start
    
    # Binary search for optimal quality
    return _binary_search_quality(image, target_size_kb, quality_start, format)


def _binary_search_quality(
    image: Image.Image,
    target_size_kb: int,
    max_quality: int,
    format: str
) -> Tuple[bytes, int]:
    """
    Use binary search to find optimal quality setting.
    
    Args:
        image: PIL Image object
        target_size_kb: Target file size in KB
        max_quality: Maximum quality to try
        format: Image format
        
    Returns:
        tuple: (optimized_bytes, quality_used)
    """
    low_quality = MIN_QUALITY
    high_quality = min(max_quality, MAX_QUALITY)
    best_bytes = None
    best_quality = low_quality
    
    logger.debug(f"Binary search: quality range {low_quality}-{high_quality}, target {target_size_kb}KB")
    
    iterations = 0
    max_iterations = 10  # Prevent infinite loops
    
    while high_quality - low_quality > 2 and iterations < max_iterations:
        mid_quality = (high_quality + low_quality) // 2
        
        result_bytes = _save_with_quality(image, mid_quality, format)
        current_size_kb = len(result_bytes) / 1024
        
        logger.debug(f"Iteration {iterations + 1}: quality={mid_quality}, size={current_size_kb:.1f}KB")
        
        if current_size_kb <= target_size_kb:
            # Size is acceptable, try higher quality
            best_bytes = result_bytes
            best_quality = mid_quality
            low_quality = mid_quality
        else:
            # Size too large, reduce quality
            high_quality = mid_quality
        
        iterations += 1
    
    # If we found a good result, use it
    if best_bytes:
        final_size_kb = len(best_bytes) / 1024
        logger.info(f"Optimized to {final_size_kb:.1f}KB at quality {best_quality}")
        return best_bytes, best_quality
    
    # Fallback to minimum quality
    logger.warning(f"Could not reach target size, using minimum quality {MIN_QUALITY}")
    result_bytes = _save_with_quality(image, MIN_QUALITY, format)
    final_size_kb = len(result_bytes) / 1024
    logger.info(f"Final size: {final_size_kb:.1f}KB at quality {MIN_QUALITY}")
    
    return result_bytes, MIN_QUALITY


def _save_with_quality(image: Image.Image, quality: int, format: str) -> bytes:
    """
    Save image with specified quality and return bytes.
    
    Args:
        image: PIL Image object
        quality: JPEG quality (1-100)
        format: Image format
        
    Returns:
        bytes: Compressed image data
    """
    buffer = BytesIO()
    
    # Determine if we should use progressive JPEG
    # Progressive JPEGs can be smaller for larger images
    progressive = quality < 80  # Use progressive for lower quality images
    
    # Save with optimization
    save_kwargs = {
        'format': format,
        'quality': quality,
        'optimize': True,
        'progressive': progressive
    }
    
    # For very low quality, add additional compression options
    if quality < 70:
        save_kwargs['subsampling'] = 2  # More aggressive chroma subsampling
    
    image.save(buffer, **save_kwargs)
    buffer.seek(0)
    return buffer.read()


def compress_image(
    image: Image.Image,
    quality: int = 85,
    progressive: bool = True,
    optimize: bool = True
) -> bytes:
    """
    Compress image with specified settings.
    
    Args:
        image: PIL Image object
        quality: JPEG quality (1-100)
        progressive: Use progressive JPEG
        optimize: Enable optimization
        
    Returns:
        bytes: Compressed image data
    """
    buffer = BytesIO()
    
    save_kwargs = {
        'format': 'JPEG',
        'quality': quality,
        'optimize': optimize,
        'progressive': progressive
    }
    
    image.save(buffer, **save_kwargs)
    buffer.seek(0)
    compressed_bytes = buffer.read()
    
    size_kb = len(compressed_bytes) / 1024
    logger.debug(f"Compressed to {size_kb:.1f}KB with quality {quality}")
    
    return compressed_bytes


def find_optimal_quality(
    image: Image.Image,
    max_size_kb: int,
    min_quality: int = MIN_QUALITY,
    max_quality: int = MAX_QUALITY
) -> Tuple[int, float]:
    """
    Find the highest quality that keeps file size under limit.
    
    Args:
        image: PIL Image object
        max_size_kb: Maximum file size in KB
        min_quality: Minimum acceptable quality
        max_quality: Maximum quality to try
        
    Returns:
        tuple: (optimal_quality, resulting_size_kb)
    """
    logger.debug(f"Finding optimal quality: max_size={max_size_kb}KB, quality_range={min_quality}-{max_quality}")
    
    # Quick check if max quality is already under limit
    test_bytes = _save_with_quality(image, max_quality, 'JPEG')
    test_size_kb = len(test_bytes) / 1024
    
    if test_size_kb <= max_size_kb:
        logger.debug(f"Max quality {max_quality} already under limit: {test_size_kb:.1f}KB")
        return max_quality, test_size_kb
    
    # Binary search for optimal quality
    low = min_quality
    high = max_quality
    best_quality = min_quality
    best_size = float('inf')
    
    while high - low > 1:
        mid = (low + high) // 2
        test_bytes = _save_with_quality(image, mid, 'JPEG')
        test_size_kb = len(test_bytes) / 1024
        
        if test_size_kb <= max_size_kb:
            # This quality works, try higher
            best_quality = mid
            best_size = test_size_kb
            low = mid
        else:
            # Quality too high, reduce
            high = mid
    
    logger.debug(f"Optimal quality: {best_quality} ({best_size:.1f}KB)")
    return best_quality, best_size


def get_quality_recommendation(
    original_size_kb: float,
    target_size_kb: float
) -> Dict[str, Any]:
    """
    Get quality recommendation based on size requirements.
    
    Args:
        original_size_kb: Original file size in KB
        target_size_kb: Target file size in KB
        
    Returns:
        dict: Quality recommendations and strategy
    """
    size_ratio = target_size_kb / original_size_kb
    
    if size_ratio >= 1.0:
        # Target is larger than original, no compression needed
        strategy = "no_compression"
        recommended_quality = MAX_QUALITY
        expected_reduction = 0
    elif size_ratio >= 0.8:
        # Minimal compression needed
        strategy = "minimal_compression"
        recommended_quality = 90
        expected_reduction = 20
    elif size_ratio >= 0.5:
        # Moderate compression
        strategy = "moderate_compression"
        recommended_quality = 80
        expected_reduction = 50
    elif size_ratio >= 0.3:
        # Aggressive compression
        strategy = "aggressive_compression"
        recommended_quality = 70
        expected_reduction = 70
    else:
        # Maximum compression
        strategy = "maximum_compression"
        recommended_quality = MIN_QUALITY
        expected_reduction = 80
    
    return {
        "strategy": strategy,
        "recommended_quality": recommended_quality,
        "size_ratio": round(size_ratio, 2),
        "expected_reduction_percent": expected_reduction,
        "original_size_kb": round(original_size_kb, 1),
        "target_size_kb": round(target_size_kb, 1)
    }


def analyze_compression_impact(
    image: Image.Image,
    quality_levels: Optional[list] = None
) -> Dict[int, Dict[str, float]]:
    """
    Analyze the impact of different quality levels on file size.
    
    Args:
        image: PIL Image object
        quality_levels: List of quality levels to test (default: [60, 70, 80, 85, 90, 95])
        
    Returns:
        dict: Quality level -> {size_kb, compression_ratio} mapping
    """
    if quality_levels is None:
        quality_levels = [60, 70, 80, 85, 90, 95]
    
    results = {}
    
    # Get baseline (95% quality)
    baseline_bytes = _save_with_quality(image, 95, 'JPEG')
    baseline_size_kb = len(baseline_bytes) / 1024
    
    for quality in quality_levels:
        compressed_bytes = _save_with_quality(image, quality, 'JPEG')
        size_kb = len(compressed_bytes) / 1024
        compression_ratio = baseline_size_kb / size_kb if size_kb > 0 else 1.0
        
        results[quality] = {
            "size_kb": round(size_kb, 1),
            "compression_ratio": round(compression_ratio, 2),
            "size_reduction_percent": round((1 - size_kb / baseline_size_kb) * 100, 1)
        }
        
        logger.debug(f"Quality {quality}: {size_kb:.1f}KB ({compression_ratio:.1f}x compression)")
    
    return results