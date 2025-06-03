"""
Core functionality for the photo display system.
"""
from PySide6.QtGui import QPixmap

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
    
    def _display_photo_immediately(self, photo_details):
        """Display photo(s) immediately without transition.
        
        Args:
            photo_details: Dictionary with photo details
        """
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
        
        # Update state
        self.current_photo_details = self.next_photo_details
        self.next_photo_details = None
        self.in_transition = False
        
        # Show clock if enabled
        self.clock_manager.show_overlay()
