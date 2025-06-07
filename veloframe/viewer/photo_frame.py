import os
import sys

from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView)
from PySide6.QtCore import (Qt, QTimer)

from .config_manager import Config
from .photo_file_set import PhotoFileSet
from .photo_display import PhotoDisplay

class PhotoFrame(QMainWindow):
    def __init__(self, config_path="config.yaml"):
        super().__init__()
        
        # Load configuration
        self.config = Config(config_path)
        
        self.setWindowTitle("Photo Frame")
        self.showFullScreen()

        # Setup graphics view and scene
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setCentralWidget(self.view)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        # Initialize photo display handler
        self.photo_display = PhotoDisplay(self.scene, self.config)

        # Initialize photo manager
        self.photo_file_set = PhotoFileSet(
            self.config.get('photos_directory'),
            self.config.get('random_order')
        )
        
        # Check if we have photos
        if not self.photo_file_set.has_photos():
            print("No image files found in the specified directory.")
            sys.exit(1)
        
        # Set up timer for slideshow
        self.display_time = self.config.get_display_time_ms()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.next_photo)
        
        # Start the slideshow
        self.show_photo()
    
    def show_photo(self, skip_transition=False):
        # Get current photo path
        current_photo = self.photo_file_set.get_current_photo_path()
        if not current_photo:
            return
            
        try:
            # Get screen dimensions
            screen_size = (self.width(), self.height())
            
            # Get configuration settings
            apply_blur = self.config.get('blur_zoom_background', False)
            show_metadata = self.config.get('show_metadata', False)
            
            # Check if we should display a pair of portrait photos
            show_pair, second_photo = self.photo_file_set.find_portrait_pair(current_photo)
            
            # Display the photo with or without transition
            if show_pair and second_photo:
                # We're displaying a pair of photos
                if skip_transition or not hasattr(self, '_first_photo_shown'):
                    # Skip transition for the first photo or when requested
                    self.photo_display.show_photo_pair(current_photo, second_photo, screen_size, apply_blur, show_metadata)
                    self._first_photo_shown = True
                else:
                    # Prepare photo details and use transition
                    photo_details = self.photo_display.photo_prep_manager.prepare_photo_pair(
                        current_photo, second_photo, screen_size, apply_blur, show_metadata)
                    self.photo_display.start_photo_transition(photo_details)
                
                # Skip the next photo in the slideshow since we're showing it now
                self.photo_file_set.next_photo()
            else:
                # We're displaying a single photo
                if skip_transition or not hasattr(self, '_first_photo_shown'):
                    # Skip transition for the first photo or when requested
                    self.photo_display.show_single_photo(current_photo, screen_size, apply_blur, show_metadata)
                    self._first_photo_shown = True
                else:
                    # Prepare photo details and use transition
                    photo_details = self.photo_display.photo_prep_manager.prepare_single_photo(
                        current_photo, screen_size, apply_blur, show_metadata)
                    self.photo_display.start_photo_transition(photo_details)
            
            # Set up timer for next photo
            self.timer.stop()
            self.timer.start(self.display_time)
            
        except Exception as e:
            print(f"Error showing photo {current_photo}: {e}")
            # Improved error recovery to prevent infinite recursion
            # Move to the next photo
            self.photo_file_set.next_photo()
            
            # Set a maximum number of consecutive errors to prevent infinite loops
            if not hasattr(self, '_error_count'):
                self._error_count = 0
            
            self._error_count += 1
            
            # If we've had too many errors in a row, reset and stop trying
            if self._error_count > 5:
                print("Too many consecutive errors. Stopping slideshow.")
                self._error_count = 0
                # Reset timer to try again after a delay
                self.timer.stop()
                self.timer.start(self.display_time)
                return
                
            # Try the next photo without transition
            self.show_photo(skip_transition=True)
    
    def next_photo(self, skip_transition=False):
        self.photo_file_set.next_photo()
        self.show_photo(skip_transition)

    def previous_photo(self, skip_transition=False):
        self.photo_file_set.previous_photo()
        self.show_photo(skip_transition)
        
    def _show_photo_immediately(self):
        """Show the next photo immediately, skipping any transition"""
        # Stop any ongoing transition
        if hasattr(self.photo_display, 'in_transition') and self.photo_display.in_transition:
            # In the refactored version, we don't directly access fade_animation_group
            # Instead we'll rely on the next photo with skip_transition=True
            # which will properly handle the transition state
            pass
        
        # Get the next photo with transition skipped
        self.next_photo(skip_transition=True)

    def keyPressEvent(self, event):
        # Exit on Escape key
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        # Move to next photo on Space or Right arrow
        elif event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Right):
            # Skip transition if Shift is held
            skip_transition = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            self.next_photo(skip_transition)
        # Move to previous photo on Left arrow
        elif event.key() == Qt.Key.Key_Left:
            # Skip transition if Shift is held
            skip_transition = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            self.previous_photo(skip_transition)


def main():
    app = QApplication(sys.argv)
    
    # Use config.yaml in the same directory as the script
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    photo_frame = PhotoFrame(config_path)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
