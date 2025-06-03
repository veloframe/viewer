import os
from typing import Dict, Tuple, Optional, List
import arrow

from PIL import Image, ImageOps, ImageFilter
from PIL.ExifTags import TAGS as ExifTags


def load_photo(photo_path: str, screen_size: Optional[Tuple[int, int]] = None, apply_blur_background: bool = False) -> Tuple[Image.Image, Dict]:
    """Load a photo and process it for display.
    
    Args:
        photo_path: Path to the photo file
        screen_size: Optional tuple of (width, height) of the screen
        apply_blur_background: Whether to apply a blurred background effect for photos that don't fill the screen
        
    Returns:
        Tuple of (processed PIL image, EXIF data dictionary)
    """
    # Load image with PIL for processing
    pil_img = Image.open(photo_path)
    
    # Process EXIF data
    exif = {}
    try:
        if hasattr(pil_img, '_getexif') and pil_img._getexif():
            exif = {ExifTags[k]: v for k, v in pil_img._getexif().items() 
                   if k in ExifTags}
        
        # Rotate image based on EXIF orientation
        pil_img = ImageOps.exif_transpose(pil_img)
    except Exception as e:
        print(f"Error processing EXIF data: {e}")
    
    # Ensure image is in RGBA mode for consistent handling
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')
    
    # Apply blurred background if requested and screen size is provided
    if apply_blur_background and screen_size:
        pil_img = create_blurred_background(pil_img, screen_size)
    
    return pil_img, exif


def create_blurred_background(image: Image.Image, screen_size: Tuple[int, int]) -> Image.Image:
    """Create a blurred background for photos that don't fill the screen.
    
    Args:
        image: Original PIL image
        screen_size: Tuple of (width, height) of the screen
        
    Returns:
        PIL image with blurred background
    """
    # Get dimensions
    screen_width, screen_height = screen_size
    img_width, img_height = image.size
    
    # Calculate what the scaled image size would be when fit to screen
    scaled_size = get_scaled_size(img_width, img_height, screen_width, screen_height)
    
    # Check if the image would have black bars (doesn't fill screen completely)
    if scaled_size[0] < screen_width or scaled_size[1] < screen_height:
        # Create a copy of the image for the background
        background = image.copy()
        
        # Step 1: Resize the background image to completely fill the screen
        # Calculate the scale factor needed to ensure both dimensions are at least as large as the screen
        bg_scale_factor = max(screen_width / img_width, screen_height / img_height)
        bg_width = int(img_width * bg_scale_factor)
        bg_height = int(img_height * bg_scale_factor)
        background = background.resize((bg_width, bg_height), Image.Resampling.LANCZOS)
        
        # Step 2: Apply gaussian blur to the background
        background = background.filter(ImageFilter.GaussianBlur(radius=75))
        
        # Step 3: Center crop the background to screen size
        left = (bg_width - screen_width) // 2
        top = (bg_height - screen_height) // 2
        right = left + screen_width
        bottom = top + screen_height
        background = background.crop((left, top, right, bottom))
        
        # Step 4: Resize the original image to fit the screen while maintaining aspect ratio
        foreground = image.resize(scaled_size, Image.Resampling.LANCZOS)
        
        # Step 5: Create a new image with the background
        result = background
        
        # Step 6: Paste the foreground image centered on the background
        paste_x = (screen_width - scaled_size[0]) // 2
        paste_y = (screen_height - scaled_size[1]) // 2
        result.paste(foreground, (paste_x, paste_y), foreground)
        
        return result
    
    # If the image already fills the screen, just return the original image
    return image


def get_scaled_size(img_width: int, img_height: int, target_width: int, target_height: int) -> Tuple[int, int]:
    """Calculate the size of an image when scaled to fit within target dimensions while maintaining aspect ratio.
    
    Args:
        img_width: Original image width
        img_height: Original image height
        target_width: Target width constraint
        target_height: Target height constraint
        
    Returns:
        Tuple of (width, height) of the scaled image
    """
    # Calculate scale factors
    width_ratio = target_width / img_width
    height_ratio = target_height / img_height
    
    # Use the smaller ratio to ensure the image fits within the target dimensions
    scale_factor = min(width_ratio, height_ratio)
    
    # Calculate new dimensions
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)
    
    return (new_width, new_height)


def get_capture_date_str(exif: Dict, file_path: str) -> str:
    """Extract and format the capture date from EXIF data or file modification time.
    
    Args:
        exif: EXIF data dictionary
        file_path: Path to the photo file (used as fallback for modification time)
        
    Returns:
        Formatted date string
    """
    capture_date = None
    if 'DateTimeOriginal' in exif:
        try:
            # Convert EXIF date format to Arrow
            date_str = exif['DateTimeOriginal']
            capture_date = arrow.get(date_str, 'YYYY:MM:DD HH:mm:ss')
        except (ValueError, TypeError):
            pass
    
    if not capture_date:
        # Use Arrow to get file modification time
        capture_date = arrow.get(os.path.getmtime(file_path))
    
    # Format the date using Arrow's formatting
    return capture_date.format("DD MMMM YYYY")


def is_portrait(image_path: str) -> bool:
    """Check if an image is portrait-oriented (height > width).
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if the image is portrait, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            # Check if image is portrait (height > width)
            return img.height > img.width
    except Exception as e:
        print(f"Error checking orientation of {image_path}: {e}")
        return False
