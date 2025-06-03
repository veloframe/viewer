import os
import sys
import time
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene, QFileDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QAction, QKeyEvent, QResizeEvent

from .config_manager import ConfigManager
from .photo_display import PhotoDisplay
from .photo_file_set import PhotoFileSet
from .photo_processing import cleanup_memory

class PhotoFrame(QMainWindow):
    """Main window for the photo frame application."""
    
    # Custom signal for when the window is about to close
    closing = Signal()
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the photo frame window.
        
        Args:
            config_path: Path to the configuration file
        """
        super().__init__()
        
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize UI
        self._init_ui()
        
        # Set up photo file set
        self.photo_file_set = PhotoFileSet(
            self.config['photos_directory'],
            self.config.get('random_order', False)
        )
        
        # Set up display and timer
        self.display_time = self.config_manager.parse_time_string(
            self.config.get('display_time', '30s')
        )
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_next_photo)
        
        # Error tracking
        self._error_count = 0
        
        # Start showing photos
        if self.photo_file_set.has_photos():
            self.show_photo()
            self.timer.start(self.display_time)
        else:
            self._handle_empty_directory()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("VeloFrame")
        self.resize(1280, 720)
        
        # Create graphics view and scene
        self.view = QGraphicsView(self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setRenderHint(self.view.RenderHint.Antialiasing)
        self.view.setRenderHint(self.view.RenderHint.SmoothPixmapTransform)
        
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        
        # Set up the photo display
        self.photo_display = PhotoDisplay(self.scene, self.config)
        
        # Set the view as the central widget
        self.setCentralWidget(self.view)
        
        # Set up keyboard shortcuts
        self._setup_actions()
        
        # Set up fullscreen
        if self.config.get('start_fullscreen', False):
            self.showFullScreen()
        else:
            self.show()
    
    def _setup_actions(self):
        """Set up keyboard shortcuts and actions."""
        # Exit action (Esc)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Esc")
        exit_action.triggered.connect(self.close)
        self.addAction(exit_action)
        
        # Toggle fullscreen action (F11)
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        self.addAction(fullscreen_action)
        
        # Next photo action (Right arrow or Space)
        next_action = QAction("Next", self)
        next_action.setShortcuts(["Right", "Space"])
        next_action.triggered.connect(self.show_next_photo)
        self.addAction(next_action)
        
        # Previous photo action (Left arrow)
        prev_action = QAction("Previous", self)
        prev_action.setShortcut("Left")
        prev_action.triggered.connect(self.show_previous_photo)
        self.addAction(prev_action)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def show_photo(self, skip_transition=False):
        """Display the current photo.
        
        Args:
            skip_transition: Whether to skip the transition animation
        """
        try:
            # Get the current photo path
            current_photo = self.photo_file_set.get_current_photo_path()
            if not current_photo:
                self._handle_empty_directory()
                return
                
            # Check if the photo exists
            if not os.path.exists(current_photo):
                print(f"Photo {current_photo} does not exist, skipping")
                self.photo_file_set.next_photo()
                self._error_count += 1
                if self._error_count > 5:
                    self._handle_empty_directory()
                    return
                self.show_photo(skip_transition=True)
                return
            
            # Get screen dimensions
            screen_size = (self.view.width(), self.view.height())
            
            # Check if the current photo is a portrait photo
            should_pair, next_portrait = self.photo_file_set.find_portrait_pair(current_photo)
            
            # Reset error count on success
            self._error_count = 0
            
            # Display the photo(s)
            if should_pair and next_portrait:
                # We have a portrait pair
                if skip_transition:
                    self.photo_display.show_photo_pair(
                        current_photo,
                        next_portrait,
                        screen_size,
                        self.config.get('apply_blur_background', True),
                        self.config.get('show_metadata', True)
                    )
                else:
                    # Prepare photo details for transition
                    next_photo_details = self.photo_display.photo_prep_manager.prepare_photo_pair(
                        current_photo,
                        next_portrait,
                        screen_size,
                        self.config.get('apply_blur_background', True),
                        self.config.get('show_metadata', True)
                    )
                    
                    # Start transition
                    transition_time = self.config_manager.parse_time_string(
                        self.config.get('transition_time', '1s')
                    )
                    self.photo_display.start_photo_transition(next_photo_details, transition_time)
                
                # Move to the next photo after the paired one
                self.photo_file_set.next_photo()
            else:
                # Single photo display
                if skip_transition:
                    self.photo_display.show_single_photo(
                        current_photo,
                        screen_size,
                        self.config.get('apply_blur_background', True),
                        self.config.get('show_metadata', True)
                    )
                else:
                    # Prepare photo details for transition
                    next_photo_details = self.photo_display.photo_prep_manager.prepare_single_photo(
                        current_photo,
                        screen_size,
                        self.config.get('apply_blur_background', True),
                        self.config.get('show_metadata', True)
                    )
                    
                    # Start transition
                    transition_time = self.config_manager.parse_time_string(
                        self.config.get('transition_time', '1s')
                    )
                    self.photo_display.start_photo_transition(next_photo_details, transition_time)
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
                self.timer.stop()
                self._handle_empty_directory()
                return
                
            # Try the next photo without transition
            self.show_photo(skip_transition=True)
    
    def show_next_photo(self):
        """Show the next photo in the sequence."""
        # Move to the next photo
        self.photo_file_set.next_photo()
        
        # Display it
        self.show_photo()
        
        # Restart the timer
        self.timer.start(self.display_time)
    
    def show_previous_photo(self):
        """Show the previous photo in the sequence."""
        # Move to the previous photo
        self.photo_file_set.previous_photo()
        
        # Display it
        self.show_photo()
        
        # Restart the timer
        self.timer.start(self.display_time)
    
    def _handle_empty_directory(self):
        """Handle the case when the photo directory is empty or inaccessible."""
        # Stop the timer
        self.timer.stop()
        
        # Create a widget to display a message and options
        message_widget = QWidget()
        layout = QVBoxLayout(message_widget)
        
        # Add a message
        message = QLabel("No photos found in the configured directory.")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("font-size: 18px; color: white;")
        layout.addWidget(message)
        
        directory_label = QLabel(f"Current directory: {self.config['photos_directory']}")
        directory_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        directory_label.setStyleSheet("font-size: 14px; color: white;")
        layout.addWidget(directory_label)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        browse_button = QPushButton("Browse for Photos Directory")
        browse_button.clicked.connect(self._browse_for_directory)
        button_layout.addWidget(browse_button)
        
        retry_button = QPushButton("Retry Current Directory")
        retry_button.clicked.connect(self._retry_current_directory)
        button_layout.addWidget(retry_button)
        
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        button_layout.addWidget(exit_button)
        
        layout.addLayout(button_layout)
        
        # Set the widget as the central widget
        self.setCentralWidget(message_widget)
        
        # Set background color
        message_widget.setStyleSheet("background-color: #1e1e1e;")
    
    def _browse_for_directory(self):
        """Open a file dialog to browse for a new photos directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Photos Directory",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Update the configuration
            self.config['photos_directory'] = directory
            self.config_manager.save_config(self.config)
            
            # Reinitialize the photo file set
            self.photo_file_set = PhotoFileSet(
                directory,
                self.config.get('random_order', False)
            )
            
            # Reset the UI
            self._init_ui()
            
            # Start showing photos if there are any
            if self.photo_file_set.has_photos():
                self.show_photo(skip_transition=True)
                self.timer.start(self.display_time)
            else:
                self._handle_empty_directory()
    
    def _retry_current_directory(self):
        """Retry loading photos from the current directory."""
        # Rescan the directory
        self.photo_file_set.rescan_directory()
        
        # Reset the UI
        self._init_ui()
        
        # Start showing photos if there are any
        if self.photo_file_set.has_photos():
            self.show_photo(skip_transition=True)
            self.timer.start(self.display_time)
        else:
            self._handle_empty_directory()
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle window resize events.
        
        Args:
            event: The resize event
        """
        super().resizeEvent(event)
        
        # Update the view to match the window size
        self.view.setSceneRect(0, 0, event.size().width(), event.size().height())
        
        # If we have a current photo, redisplay it to fit the new size
        if hasattr(self, 'photo_file_set') and self.photo_file_set.has_photos():
            # Use a short delay to avoid multiple redraws during resize
            QTimer.singleShot(100, lambda: self.show_photo(skip_transition=True))
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events.
        
        Args:
            event: The key press event
        """
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close events.
        
        Args:
            event: The close event
        """
        # Emit the closing signal
        self.closing.emit()
        
        # Stop the timer
        self.timer.stop()
        
        # Clean up resources
        self._cleanup_resources()
        
        # Accept the close event
        event.accept()
    
    def _cleanup_resources(self):
        """Clean up resources before closing."""
        # Clear the photo display's cache
        if hasattr(self, 'photo_display') and hasattr(self.photo_display, 'photo_prep_manager'):
            self.photo_display.photo_prep_manager.clear_cache()
        
        # Clean up any remaining PIL images
        cleanup_memory()
        
        # Force garbage collection
        import gc
        gc.collect()

def main():
    app = QApplication(sys.argv)
    
    # Use config.yaml in the same directory as the script
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    photo_frame = PhotoFrame(config_path)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
