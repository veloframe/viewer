import os
import random
from typing import List, Optional, Tuple, Set

from .photo_processing import is_portrait

class PhotoFileSet:
    """Handles all photo-related operations for the photo frame application."""
    
    # Supported image file extensions
    SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
    
    def __init__(self, photos_directory: str, random_order: bool = False):
        """Initialize the photo manager.
        
        Args:
            photos_directory: Path to the directory containing photos
            random_order: Whether to randomize the order of photos
        """
        self.photos_directory = os.path.expanduser(photos_directory)
        self.random_order = random_order
        self.photo_files = self._get_photo_files()
        self.current_index = 0
        self.portrait_photos = set()
        
        if random_order and self.photo_files:
            random.shuffle(self.photo_files)
            
        # Scan for portrait photos
        self.scan_portrait_photos()
    
    def _get_photo_files(self) -> List[str]:
        """Get all photo files from the photos directory and subdirectories.
        
        Returns:
            List of absolute paths to photo files
        """
        photo_files = []
        
        if not os.path.exists(self.photos_directory):
            print(f"Warning: Photos directory '{self.photos_directory}' does not exist")
            return photo_files
            
        for root, _, files in os.walk(self.photos_directory):
            for file in files:
                if file.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    photo_files.append(os.path.join(root, file))
        
        return photo_files
    
    def has_photos(self) -> bool:
        """Check if there are any photos available.
        
        Returns:
            True if photos are available, False otherwise
        """
        return len(self.photo_files) > 0
    
    def get_current_photo_path(self) -> Optional[str]:
        """Get the path to the current photo."""
        return self.photo_files[self.current_index]
    
    def next_photo(self):
        """Move to the next photo."""
        self.current_index = (self.current_index + 1) % len(self.photo_files)
    
    def previous_photo(self):
        """Move to the previous photo."""
        self.current_index = (self.current_index - 1) % len(self.photo_files)
    
    def rescan_directory(self):
        """Rescan the photos directory for new photos."""
        current_file = self.get_current_photo_path()
        self.photo_files = self._get_photo_files()
        
        if self.random_order and self.photo_files:
            random.shuffle(self.photo_files)
            
        # Try to keep the current photo if it still exists
        if current_file and current_file in self.photo_files:
            self.current_index = self.photo_files.index(current_file)
        else:
            self.current_index = 0
            
        # Rescan portrait photos
        self.scan_portrait_photos()
        
    def scan_portrait_photos(self):
        """Scan photo collection to identify portrait photos (height > width)"""
        self.portrait_photos = set()
        
        for photo_path in self.photo_files:
            if is_portrait(photo_path):
                self.portrait_photos.add(photo_path)
    
    def is_portrait_photo(self, photo_path: str) -> bool:
        """Check if a photo is in the portrait photos list
        
        Args:
            photo_path: Path to the photo file
            
        Returns:
            True if the photo is portrait-oriented, False otherwise
        """
        return photo_path in self.portrait_photos
    
    def find_portrait_pair(self, current_photo: str, lookahead: int = 10) -> Tuple[bool, Optional[str]]:
        """Find a portrait photo to pair with the current one
        
        Look ahead in the sequence to find a portrait photo to pair with the current one.
        This avoids showing a portrait photo alone if another portrait photo is coming up soon.
        
        Args:
            current_photo: Path to the current photo
            lookahead: Number of photos to look ahead for a portrait match
            
        Returns:
            Tuple of (should_pair, next_portrait_photo)
            - should_pair: True if a portrait photo was found to pair with
            - next_portrait_photo: Path to the portrait photo to pair with, or None
        """
        # Must be a portrait photo
        if not self.is_portrait_photo(current_photo):
            return False, None
            
        # Get the current photo's index
        current_index = self.photo_files.index(current_photo)
        
        # Look ahead for portrait photos
        for i in range(1, lookahead + 1):
            next_index = (current_index + i) % len(self.photo_files)
            next_photo = self.photo_files[next_index]
            
            # Check if this photo is portrait
            if self.is_portrait_photo(next_photo):
                # We'll skip ahead to pair these photos
                # Need to update the current index
                if i > 1:
                    # Move to the photo before the one we're pairing with
                    self.current_index = (current_index + i - 1) % len(self.photo_files)
                return True, next_photo
        
        # No portrait photo found in the lookahead window
        return False, None
    

