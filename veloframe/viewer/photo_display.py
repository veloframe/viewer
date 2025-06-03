"""
Core functionality for the photo display system.
"""
from PySide6.QtGui import QPixmap
import gc

from .photo_ui_components import UIComponentManager
from .photo_transition_manager import TransitionManager
from .photo_preparation import PhotoPreparationManager
from .metadata_overlay import MetadataManager
from .clock_overlay import ClockManager

class PhotoDisplay:
    """Core display functionality for the photo frame application."""
    
    def __init__(self, scene, config):
        """Initialize the PhotoDisplay with the necessary UI components.
        
        Args:
            scene: The QGraphicsScene instance
            config: Configuration object
        """
        self.scene = scene
        self.config = config
        
        # Initialize component managers
        self.ui_manager = UIComponentManager(scene)
        self.photo_prep_manager = PhotoPreparationManager(config)
        self.metadata_manager = MetadataManager(scene, config)
        self.clock_manager = ClockManager(scene, config)
        self.transition_manager = TransitionManager(self.ui_manager, config)
        
        # Set UI components reference for clock manager
        self.clock_manager.set_ui_components(self.ui_manager)
        
        # Set up metadata update callback for transitions
        self.transition_manager.set_update_metadata_callback(self._update_metadata_mid_transition)
        
        # Track state
        self.current_mode = "single"  # "single" or "pair"
        self.current_photo_details = None
        self.next_photo_details = None
        self.in_transition = False
        
        # Memory management
        self._cleanup_counter = 0
        self._cleanup_threshold = 20  # Trigger cleanup every 20 photo changes
    
    def show_single_photo(self, photo_path, screen_size, apply_blur, show_metadata):
        """Display a single photo.
        
        Args:
            photo_path: Path to the photo
            screen_size: (width, height) tuple
            apply_blur: Whether to apply blur effect
            show_metadata: Whether to show metadata overlay
        """
        photo_details = self.photo_prep_manager.prepare_single_photo(
            photo_path, screen_size, apply_blur, show_metadata
        )
        self._display_photo_immediately(photo_details)
    
    def show_photo_pair(self, photo1_path, photo2_path, screen_size, apply_blur, show_metadata):
        """Display two portrait photos side by side.
        
        Args:
            photo1_path: Path to the first photo
            photo2_path: Path to the second photo
            screen_size: (width, height) tuple
            apply_blur: Whether to apply blur effect
            show_metadata: Whether to show metadata overlay
        """
        photo_details = self.photo_prep_manager.prepare_photo_pair(
            photo1_path, photo2_path, screen_size, apply_blur, show_metadata
        )
        self._display_photo_immediately(photo_details)
    
    def start_photo_transition(self, next_photo_details, duration=None):
        """Start transition to the next photo with a cross-dissolve effect.
        
        Args:
            next_photo_details: Details of the next photo to display
            duration: Duration of the transition in milliseconds, or None to use config value
        """
        # If we're already in a transition, properly cancel it first
        if self.in_transition:
            # Stop the current transition animation
            self.transition_manager.cancel_transition()
            
            # If we were transitioning to a different photo than the one we're now
            # transitioning to, we need to clean up resources
            if self.next_photo_details and next_photo_details != self.next_photo_details:
                # Clean up any resources from the previous next_photo_details
                self._cleanup_photo_details(self.next_photo_details)
        
        # Store state
        self.next_photo_details = next_photo_details
        self.in_transition = True
        
        # Delegate to transition manager
        self.transition_manager.start_transition(
            self.current_photo_details,
            next_photo_details,
            duration,
            self._finalize_transition
        )
        
        # Increment cleanup counter and check if we need to perform cleanup
        self._cleanup_counter += 1
        if self._cleanup_counter >= self._cleanup_threshold:
            self._perform_memory_cleanup()
    
    def _display_photo_immediately(self, photo_details):
        """Display photo(s) immediately without transition.
        
        Args:
            photo_details: Dictionary with photo details
        """
        # If we have current photo details, clean them up before replacing
        if self.current_photo_details:
            self._cleanup_photo_details(self.current_photo_details)
        
        # Reset the scene rectangle
        screen_size = photo_details['screen_size']
        self.ui_manager.set_scene_rect(screen_size[0], screen_size[1])
        
        # Clear next images
        self.ui_manager.clear_next_photos()
        
        if photo_details['mode'] == 'single':
            # Set the single photo
            self.ui_manager.set_single_photo(
                True,  # current
                photo_details['pixmap'],
                photo_details['image_x'],
                photo_details['image_y']
            )
            
            # Update or hide metadata
            if photo_details['show_metadata']:
                self.metadata_manager.update_overlay(
                    self.ui_manager,
                    photo_details['exif'], 
                    photo_details['path'], 
                    photo_details['pixmap'], 
                    photo_details['image_x'], 
                    photo_details['image_y'], 
                    "left"
                )
                # Hide right metadata
                self.metadata_manager.hide_overlay(self.ui_manager, "right")
            else:
                # Hide all metadata
                self.metadata_manager.hide_overlay(self.ui_manager, "both")
        else:  # 'pair'
            # Set the photo pair
            self.ui_manager.set_photo_pair(
                True,  # current
                photo_details['pixmap1'],
                photo_details['image1_x'],
                photo_details['image1_y'],
                photo_details['pixmap2'],
                photo_details['image2_x'],
                photo_details['image2_y']
            )
            
            # Update or hide metadata
            if photo_details['show_metadata']:
                self.metadata_manager.update_overlay(
                    self.ui_manager,
                    photo_details['exif1'], 
                    photo_details['path1'], 
                    photo_details['pixmap1'], 
                    photo_details['image1_x'], 
                    photo_details['image1_y'], 
                    "left"
                )
                self.metadata_manager.update_overlay(
                    self.ui_manager,
                    photo_details['exif2'], 
                    photo_details['path2'], 
                    photo_details['pixmap2'], 
                    photo_details['image2_x'], 
                    photo_details['image2_y'], 
                    "right"
                )
            else:
                # Hide metadata
                self.metadata_manager.hide_overlay(self.ui_manager, "both")
        
        # Reset opacities
        self.ui_manager.set_opacity("current", "left", 1.0)
        self.ui_manager.set_opacity("current", "right", 1.0)
        self.ui_manager.set_opacity("next", "left", 0.0)
        self.ui_manager.set_opacity("next", "right", 0.0)
        
        # Show clock if enabled
        self.clock_manager.show_overlay()
        
        # Store current photo details
        self.current_photo_details = photo_details
        self.next_photo_details = None
        self.in_transition = False
        
        # Increment cleanup counter and check if we need to perform cleanup
        self._cleanup_counter += 1
        if self._cleanup_counter >= self._cleanup_threshold:
            self._perform_memory_cleanup()
    
    def _update_metadata_mid_transition(self, value):
        """Update metadata overlays at the middle of the transition.
        
        Args:
            value: Current opacity value (0.0-1.0) of the animation
        """
        # Only update metadata near the middle of the transition (around 0.45-0.55 opacity)
        if 0.45 <= value <= 0.55 and self.next_photo_details:
            # Hide all existing metadata first
            self.metadata_manager.hide_overlay(self.ui_manager, "both")
            
            # Update metadata for the new photo(s)
            self.metadata_manager.update_for_photo_details(self.ui_manager, self.next_photo_details)
    
    def _finalize_transition(self):
        """Finalize the transition by updating current photo details and swapping layers."""
        if not self.next_photo_details:
            return
            
        # Swap layers in UI manager
        self.ui_manager.swap_layers(self.next_photo_details['mode'])
        
        # Clean up the old photo details
        if self.current_photo_details:
            self._cleanup_photo_details(self.current_photo_details)
        
        # Update current photo details
        self.current_photo_details = self.next_photo_details
        self.next_photo_details = None
        
        # Reset transition state
        self.in_transition = False
        
        # Show clock if enabled
        self.clock_manager.show_overlay()
    
    def _cleanup_photo_details(self, photo_details):
        """Clean up resources associated with photo details.
        
        This helps prevent memory leaks by removing references to large objects.
        
        Args:
            photo_details: Dictionary with photo details to clean up
        """
        if not photo_details:
            return
            
        # We don't actually delete the pixmaps here since they're managed by Qt
        # and might still be in use by the UI. Instead, we remove our references
        # to them to allow Qt to garbage collect them when appropriate.
        
        # Remove references to large objects in the photo details
        if photo_details['mode'] == 'single':
            # Clear reference to pixmap
            if 'pixmap' in photo_details:
                photo_details['pixmap'] = None
        else:  # 'pair'
            # Clear references to pixmaps
            if 'pixmap1' in photo_details:
                photo_details['pixmap1'] = None
            if 'pixmap2' in photo_details:
                photo_details['pixmap2'] = None
    
    def _perform_memory_cleanup(self):
        """Perform periodic memory cleanup to prevent memory leaks."""
        # Reset counter
        self._cleanup_counter = 0
        
        # Clear the photo preparation manager's cache
        self.photo_prep_manager.clear_cache()
        
        # Suggest garbage collection
        gc.collect()
