"""
Handles photo preparation for display.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

from .photo_processing import load_photo

class PhotoPreparationManager:
    """Manages photo preparation for display."""
    
    def __init__(self, config):
        """Initialize the photo preparation manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def prepare_single_photo(self, photo_path, screen_size, apply_blur, show_metadata):
        """Prepare a single photo for display.
        
        Args:
            photo_path: Path to the photo
            screen_size: (width, height) tuple
            apply_blur: Whether to apply blur effect
            show_metadata: Whether to show metadata overlay
        
        Returns:
            Dictionary with photo details
        """
        # Load the photo with blur effect if enabled
        pil_img, exif = load_photo(photo_path, screen_size, apply_blur)
        
        # Convert PIL image to Qt pixmap
        img_byte_arr = pil_img.tobytes('raw', 'RGBA')
        qimg = QImage(img_byte_arr, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        
        # Scale the pixmap to fit the screen while maintaining aspect ratio
        pixmap = pixmap.scaled(
            screen_size[0], screen_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Prepare the pixmap for display
        photo_details = {
            'mode': 'single',
            'pixmap': pixmap,
            'exif': exif,
            'path': photo_path,
            'screen_size': screen_size,
            'apply_blur': apply_blur,
            'show_metadata': show_metadata
        }
        
        # Calculate position
        image_x = (screen_size[0] - pixmap.width()) / 2
        image_y = (screen_size[1] - pixmap.height()) / 2
        
        # Add position to details
        photo_details['image_x'] = image_x
        photo_details['image_y'] = image_y
        
        return photo_details
    
    def prepare_photo_pair(self, photo1_path, photo2_path, screen_size, apply_blur, show_metadata):
        """Prepare a pair of photos for display.
        
        Args:
            photo1_path: Path to the first photo
            photo2_path: Path to the second photo
            screen_size: (width, height) tuple
            apply_blur: Whether to apply blur effect
            show_metadata: Whether to show metadata overlay
        
        Returns:
            Dictionary with photo pair details
        """
        # Calculate half screen size for each photo (minus gap)
        half_screen_width = (screen_size[0] / 2) - 5  # 5px half of the 10px gap
        half_screen_size = (int(half_screen_width), screen_size[1])
        
        # Load both photos with half screen size each to apply blur to each individually
        pil_img1, exif1 = load_photo(photo1_path, half_screen_size, apply_blur)
        pil_img2, exif2 = load_photo(photo2_path, half_screen_size, apply_blur)
        
        # Convert PIL images to Qt pixmaps
        img_byte_arr1 = pil_img1.tobytes('raw', 'RGBA')
        qimg1 = QImage(img_byte_arr1, pil_img1.width, pil_img1.height, QImage.Format.Format_RGBA8888)
        pixmap1 = QPixmap.fromImage(qimg1)
        
        img_byte_arr2 = pil_img2.tobytes('raw', 'RGBA')
        qimg2 = QImage(img_byte_arr2, pil_img2.width, pil_img2.height, QImage.Format.Format_RGBA8888)
        pixmap2 = QPixmap.fromImage(qimg2)
        
        # Calculate the maximum height to use for both images
        # Each image gets approximately half the screen width with a small gap between
        max_width = (screen_size[0] / 2) - 10  # 10px gap (5px on each side)
        
        # Scale both pixmaps to the same height
        pixmap1 = pixmap1.scaled(
            max_width,
            screen_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        pixmap2 = pixmap2.scaled(
            max_width,
            screen_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Prepare the pair details for display
        photo_details = {
            'mode': 'pair',
            'pixmap1': pixmap1,
            'pixmap2': pixmap2,
            'exif1': exif1,
            'exif2': exif2,
            'path1': photo1_path,
            'path2': photo2_path,
            'screen_size': screen_size,
            'apply_blur': apply_blur,
            'show_metadata': show_metadata
        }
        
        # Calculate positions for centered images
        total_width = pixmap1.width() + 10 + pixmap2.width()  # 10px gap
        start_x = (screen_size[0] - total_width) / 2
        
        image1_x = start_x
        image1_y = (screen_size[1] - pixmap1.height()) / 2
        
        image2_x = start_x + pixmap1.width() + 10  # 10px gap
        image2_y = (screen_size[1] - pixmap2.height()) / 2
        
        # Add positions to details
        photo_details['image1_x'] = image1_x
        photo_details['image1_y'] = image1_y
        photo_details['image2_x'] = image2_x
        photo_details['image2_y'] = image2_y
        
        return photo_details
