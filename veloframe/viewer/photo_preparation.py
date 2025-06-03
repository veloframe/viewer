"""
Handles photo preparation for display.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import gc

from .photo_processing import load_photo

class PhotoPreparationManager:
    """Manages photo preparation for display."""
    
    def __init__(self, config):
        """Initialize the photo preparation manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        # Add a cache to store recently used pixmaps with weak references
        self._pixmap_cache = {}
        self._cache_size_limit = 10  # Maximum number of items to keep in cache
    
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
        # Check if we have this photo in cache
        cache_key = f"{photo_path}_{screen_size[0]}x{screen_size[1]}_{apply_blur}"
        if cache_key in self._pixmap_cache:
            pixmap, exif = self._pixmap_cache[cache_key]
        else:
            # Load the photo with blur effect if enabled
            pil_img, exif = load_photo(photo_path, screen_size, apply_blur)
            
            try:
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
                
                # Store in cache
                self._update_cache(cache_key, (pixmap, exif))
                
                # Explicitly clean up PIL image and byte array to prevent memory leaks
                del img_byte_arr
                pil_img.close()
                del pil_img
            except Exception as e:
                print(f"Error preparing photo {photo_path}: {e}")
                # Ensure PIL image is closed even if there's an error
                if 'pil_img' in locals():
                    pil_img.close()
                # Return empty pixmap and details
                pixmap = QPixmap()
                
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
        
        # Check if we have these photos in cache
        cache_key1 = f"{photo1_path}_{half_screen_size[0]}x{half_screen_size[1]}_{apply_blur}"
        cache_key2 = f"{photo2_path}_{half_screen_size[0]}x{half_screen_size[1]}_{apply_blur}"
        
        # Process first photo
        if cache_key1 in self._pixmap_cache:
            pixmap1, exif1 = self._pixmap_cache[cache_key1]
        else:
            # Load the photo with blur effect if enabled
            pil_img1, exif1 = load_photo(photo1_path, half_screen_size, apply_blur)
            
            try:
                # Convert PIL image to Qt pixmap
                img_byte_arr1 = pil_img1.tobytes('raw', 'RGBA')
                qimg1 = QImage(img_byte_arr1, pil_img1.width, pil_img1.height, QImage.Format.Format_RGBA8888)
                pixmap1 = QPixmap.fromImage(qimg1)
                
                # Scale the pixmap
                pixmap1 = pixmap1.scaled(
                    half_screen_width,
                    screen_size[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Store in cache
                self._update_cache(cache_key1, (pixmap1, exif1))
                
                # Clean up PIL image and byte array
                del img_byte_arr1
                pil_img1.close()
                del pil_img1
            except Exception as e:
                print(f"Error preparing photo {photo1_path}: {e}")
                if 'pil_img1' in locals():
                    pil_img1.close()
                pixmap1 = QPixmap()
        
        # Process second photo
        if cache_key2 in self._pixmap_cache:
            pixmap2, exif2 = self._pixmap_cache[cache_key2]
        else:
            # Load the photo with blur effect if enabled
            pil_img2, exif2 = load_photo(photo2_path, half_screen_size, apply_blur)
            
            try:
                # Convert PIL image to Qt pixmap
                img_byte_arr2 = pil_img2.tobytes('raw', 'RGBA')
                qimg2 = QImage(img_byte_arr2, pil_img2.width, pil_img2.height, QImage.Format.Format_RGBA8888)
                pixmap2 = QPixmap.fromImage(qimg2)
                
                # Scale the pixmap
                pixmap2 = pixmap2.scaled(
                    half_screen_width,
                    screen_size[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Store in cache
                self._update_cache(cache_key2, (pixmap2, exif2))
                
                # Clean up PIL image and byte array
                del img_byte_arr2
                pil_img2.close()
                del pil_img2
            except Exception as e:
                print(f"Error preparing photo {photo2_path}: {e}")
                if 'pil_img2' in locals():
                    pil_img2.close()
                pixmap2 = QPixmap()
        
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
    
    def _update_cache(self, key, value):
        """Update the pixmap cache, removing oldest items if over the limit.
        
        Args:
            key: Cache key
            value: Value to store (pixmap, exif) tuple
        """
        # Add new item to cache
        self._pixmap_cache[key] = value
        
        # Remove oldest items if over limit
        if len(self._pixmap_cache) > self._cache_size_limit:
            # Get the oldest keys (first items in the dictionary)
            keys_to_remove = list(self._pixmap_cache.keys())[:-self._cache_size_limit]
            for old_key in keys_to_remove:
                del self._pixmap_cache[old_key]
            
            # Suggest garbage collection
            gc.collect()
    
    def clear_cache(self):
        """Clear the pixmap cache to free memory."""
        self._pixmap_cache.clear()
        gc.collect()
