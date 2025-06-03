import os
import random
import threading
from typing import List, Optional, Tuple, Set, Dict

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
        
        # Portrait photo tracking
        self.portrait_photos = set()
        self.portrait_cache: Dict[str, bool] = {}  # Cache for portrait detection results
        self.portrait_scan_complete = False
        self.portrait_scan_lock = threading.Lock()
        
        if random_order and self.photo_files:
            random.shuffle(self.photo_files)
            
        # Start portrait scanning in background thread
        self._start_background_portrait_scan()
    
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
    
    def _start_background_portrait_scan(self):
        """Start scanning for portrait photos in a background thread."""
        if not self.photo_files:
            return
            
        # Start a background thread to scan photos
        scan_thread = threading.Thread(
            target=self._background_portrait_scan,
            name="PortraitScanThread",
            daemon=True  # Make thread a daemon so it doesn't block application exit
        )
        scan_thread.start()
    
    def _background_portrait_scan(self):
        """Background thread function to scan all photos for portrait orientation."""
        try:
            with self.portrait_scan_lock:
                self.portrait_scan_complete = False
                self.portrait_photos = set()
                
                # Process photos in batches to avoid blocking for too long
                batch_size = 20
                for i in range(0, len(self.photo_files), batch_size):
                    batch = self.photo_files[i:i+batch_size]
                    for photo_path in batch:
                        try:
                            # Check if we already have this in the cache
                            if photo_path in self.portrait_cache:
                                is_portrait_photo = self.portrait_cache[photo_path]
                            else:
                                # Detect portrait orientation and cache the result
                                is_portrait_photo = is_portrait(photo_path)
                                self.portrait_cache[photo_path] = is_portrait_photo
                                
                            # Add to portrait set if it's a portrait photo
                            if is_portrait_photo:
                                self.portrait_photos.add(photo_path)
                        except Exception as e:
                            print(f"Error checking if {photo_path} is portrait: {e}")
                
                self.portrait_scan_complete = True
                print(f"Portrait scan complete. Found {len(self.portrait_photos)} portrait photos.")
        except Exception as e:
            print(f"Error in background portrait scan: {e}")
            # Ensure we mark the scan as complete even if there was an error
            with self.portrait_scan_lock:
                self.portrait_scan_complete = True
    
    def has_photos(self) -> bool:
        """Check if there are any photos available.
        
        Returns:
            True if photos are available, False otherwise
        """
        return len(self.photo_files) > 0
    
    def get_current_photo_path(self) -> Optional[str]:
        """Get the path to the current photo."""
        if not self.photo_files:
            return None
        return self.photo_files[self.current_index]
    
    def next_photo(self):
        """Move to the next photo."""
        if not self.photo_files:
            return
        self.current_index = (self.current_index + 1) % len(self.photo_files)
    
    def previous_photo(self):
        """Move to the previous photo."""
        if not self.photo_files:
            return
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
            
        # Restart portrait scanning
        self._start_background_portrait_scan()
    
    def is_portrait_photo(self, photo_path: str) -> bool:
        """Check if a photo is portrait-oriented (height > width).
        
        This method first checks the cache and portrait set from the background scan.
        If the photo hasn't been scanned yet, it performs an on-demand check.
        
        Args:
            photo_path: Path to the photo file
            
        Returns:
            True if the photo is portrait-oriented, False otherwise
        """
        # First check if the photo is in our portrait set from the background scan
        if photo_path in self.portrait_photos:
            return True
            
        # If the scan is complete and the photo isn't in the set, it's not portrait
        if self.portrait_scan_complete and photo_path in self.portrait_cache:
            return False
            
        # If we don't have a result yet, check on demand and cache the result
        try:
            with self.portrait_scan_lock:
                # Double-check in case another thread updated while we were waiting
                if photo_path in self.portrait_cache:
                    is_portrait_photo = self.portrait_cache[photo_path]
                else:
                    # Detect portrait orientation and cache the result
                    is_portrait_photo = is_portrait(photo_path)
                    self.portrait_cache[photo_path] = is_portrait_photo
                    
                    # Add to portrait set if it's a portrait photo
                    if is_portrait_photo:
                        self.portrait_photos.add(photo_path)
                        
                return is_portrait_photo
        except Exception as e:
            print(f"Error checking if {photo_path} is portrait: {e}")
            return False
    
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
        try:
            current_index = self.photo_files.index(current_photo)
        except ValueError:
            # Photo might have been removed
            return False, None
        
        # Look ahead for portrait photos
        for i in range(1, min(lookahead + 1, len(self.photo_files))):
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
