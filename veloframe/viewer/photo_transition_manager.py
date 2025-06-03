"""
Manages photo transitions and animations.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

class TransitionManager:
    """Manages transitions between photos."""
    
    def __init__(self, ui_components, config):
        """Initialize the transition manager.
        
        Args:
            ui_components: UIComponentManager instance
            config: Configuration object
        """
        self.ui_components = ui_components
        self.config = config
        self.fade_animation_group = QParallelAnimationGroup()
        self.in_transition = False
        self.current_photo_details = None
        self.next_photo_details = None
        self.on_transition_finished_callback = None
    
    def start_transition(self, current_photo_details, next_photo_details, duration=None, on_finished_callback=None):
        """Start transition to the next photo with a cross-dissolve effect.
        
        Args:
            current_photo_details: Details of the current photo
            next_photo_details: Details of the next photo to display
            duration: Duration of the transition in milliseconds, or None to use config value
            on_finished_callback: Callback to run when transition finishes
        """
        if self.in_transition:
            # If already in transition, stop current animations
            self.fade_animation_group.stop()
        
        # Store photo details and callback
        self.current_photo_details = current_photo_details
        self.next_photo_details = next_photo_details
        self.on_transition_finished_callback = on_finished_callback
        self.in_transition = True
        
        # Get transition duration from config if not specified
        if duration is None:
            duration = self.config.get_transition_time_ms()
        
        if duration <= 0:
            # Skip transition if duration is 0 or negative
            if on_finished_callback:
                on_finished_callback()
            return
            
        # Clear any existing animations
        self.fade_animation_group = QParallelAnimationGroup()
        
        # Prepare the new photo for display (but with opacity 0)
        self._prepare_next_photo_for_transition()
        
        # Setup fade out animation for current photo(s)
        fade_out_left = QPropertyAnimation()
        fade_out_left.setTargetObject(self.ui_components.opacity_effect_current_left)
        fade_out_left.setPropertyName(b"opacity")
        fade_out_left.setStartValue(1.0)
        fade_out_left.setEndValue(0.0)
        fade_out_left.setDuration(duration)
        fade_out_left.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade_animation_group.addAnimation(fade_out_left)
        
        # Setup fade in animation for new photo
        fade_in_next = QPropertyAnimation()
        fade_in_next.setTargetObject(self.ui_components.opacity_effect_next_left)
        fade_in_next.setPropertyName(b"opacity")
        fade_in_next.setStartValue(0.0)
        fade_in_next.setEndValue(1.0)
        fade_in_next.setDuration(duration)
        fade_in_next.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Use this animation to trigger metadata update at the halfway point
        fade_in_next.valueChanged.connect(lambda value: self._update_mid_transition(value))
        
        self.fade_animation_group.addAnimation(fade_in_next)
        
        # If we're dealing with pairs, add animations for right images too
        if self.current_photo_details and self.current_photo_details['mode'] == 'pair':
            fade_out_right = QPropertyAnimation()
            fade_out_right.setTargetObject(self.ui_components.opacity_effect_current_right)
            fade_out_right.setPropertyName(b"opacity")
            fade_out_right.setStartValue(1.0)
            fade_out_right.setEndValue(0.0)
            fade_out_right.setDuration(duration)
            fade_out_right.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self.fade_animation_group.addAnimation(fade_out_right)
        
        if self.next_photo_details and self.next_photo_details['mode'] == 'pair':
            fade_in_right = QPropertyAnimation()
            fade_in_right.setTargetObject(self.ui_components.opacity_effect_next_right)
            fade_in_right.setPropertyName(b"opacity")
            fade_in_right.setStartValue(0.0)
            fade_in_right.setEndValue(1.0)
            fade_in_right.setDuration(duration)
            fade_in_right.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self.fade_animation_group.addAnimation(fade_in_right)
        
        # Connect signal to finalize transition when animation completes
        self.fade_animation_group.finished.connect(self._on_transition_finished)
        
        # Start animations
        self.fade_animation_group.start()
    
    def _prepare_next_photo_for_transition(self):
        """Prepare the next photo for transition (set up but initially invisible)."""
        if not self.next_photo_details:
            return
            
        # Configure scene for next photo
        screen_size = self.next_photo_details['screen_size']
        self.ui_components.set_scene_rect(screen_size[0], screen_size[1])
        
        if self.next_photo_details['mode'] == 'single':
            # Set pixmap and position for the next left image
            self.ui_components.set_single_photo(
                False,  # not current (next)
                self.next_photo_details['pixmap'],
                self.next_photo_details['image_x'],
                self.next_photo_details['image_y']
            )
        else:  # 'pair'
            # Set pixmaps and positions for both next images
            self.ui_components.set_photo_pair(
                False,  # not current (next)
                self.next_photo_details['pixmap1'],
                self.next_photo_details['image1_x'],
                self.next_photo_details['image1_y'],
                self.next_photo_details['pixmap2'],
                self.next_photo_details['image2_x'],
                self.next_photo_details['image2_y']
            )
    
    def _update_mid_transition(self, value):
        """Update metadata overlays at the middle of the transition.
        
        Args:
            value: Current opacity value (0.0-1.0) of the animation
        """
        # Only update metadata near the middle of the transition (around 0.45-0.55 opacity)
        # This prevents the method from being called multiple times
        if 0.45 <= value <= 0.55 and self.next_photo_details:
            # Since we don't have direct access to the metadata manager from the PhotoDisplay class,
            # use the callback that was set by the PhotoDisplay class
            if hasattr(self, "update_metadata_callback") and self.update_metadata_callback:
                self.update_metadata_callback(value)
    
    def _on_transition_finished(self):
        """Called when transition animation finishes."""
        # Disconnect the signal to avoid multiple triggers
        self.fade_animation_group.finished.disconnect(self._on_transition_finished)
        
        # Clear the animation group for reuse
        self.fade_animation_group = QParallelAnimationGroup()
        
        # Call the callback if provided
        if self.on_transition_finished_callback:
            self.on_transition_finished_callback()
    
    def set_update_metadata_callback(self, callback):
        """Set a callback to update metadata during transition.
        
        Args:
            callback: Function to call to update metadata
        """
        self.update_metadata_callback = callback

    def cancel_transition(self):
        """Cancel any ongoing transition animations.
        
        This method stops all animations and resets the transition state.
        It should be called before starting a new transition if one is already in progress.
        """
        if not self.in_transition:
            return
            
        # Stop the animation group
        self.fade_animation_group.stop()
        
        # Disconnect any connected signals to prevent callbacks
        try:
            if self.fade_animation_group.signalsBlocked() == False:
                self.fade_animation_group.finished.disconnect(self._on_transition_finished)
        except RuntimeError:
            # Ignore errors if the signal wasn't connected
            pass
            
        # Reset the animation group
        self.fade_animation_group = QParallelAnimationGroup()
        
        # Reset transition state
        self.in_transition = False
