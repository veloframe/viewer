"""
Manages clock overlay for photo display.
"""
from PySide6.QtGui import QFont, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QTimer
import arrow

class ClockManager:
    """Manages clock overlay for photo display."""
    
    def __init__(self, scene, config):
        """Initialize the clock manager.
        
        Args:
            scene: The QGraphicsScene instance
            config: Configuration object
        """
        self.scene = scene
        self.config = config
        self.timer = None
        self.ui_components = None
        # Don't start the timer here - wait until UI components are set
    
    def _start_timer(self):
        """Start the timer to update the clock."""
        if self.timer is None:
            self.timer = QTimer()
            # Update every second
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self._update_clock)
            self.timer.start()
    
    def _stop_timer(self):
        """Stop the timer."""
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
    
    def set_ui_components(self, ui_components):
        """Set the UI components reference.
        
        Args:
            ui_components: UIComponentManager instance
        """
        self.ui_components = ui_components
        
        # Start the timer and show the clock if enabled
        if self.config.get('show_clock', False):
            self._start_timer()
            self.show_overlay()
    
    def _update_clock(self):
        """Update the clock with current time."""
        if not self.ui_components:
            return
            
        # If clock is disabled, hide it and return
        if not self.config.get('show_clock', False):
            self.hide_overlay()
            return
        
        # Get current date and time using Arrow
        current_datetime = arrow.now()
        # Format according to config (default: 24 hour time and minutes)
        time_format = self.config.get('clock_format', 'HH:mm')
        time_str = current_datetime.format(time_format)
        
        # Configure font
        font_name = self.config.get('clock_font', 'segoeui.ttf')
        font_size = self.config.get('clock_point_size', 12)
        
        font = QFont(font_name)
        font.setPointSize(font_size)
        
        self.ui_components.clock_text.setFont(font)
        self.ui_components.clock_text.setPlainText(time_str)
        self.ui_components.clock_text.setDefaultTextColor(QColor(255, 255, 255))  # Ensure white text
        
        # Calculate text dimensions
        text_width = self.ui_components.clock_text.boundingRect().width()
        text_height = self.ui_components.clock_text.boundingRect().height()
        
        # Set padding
        padding = 5
        
        # Get scene dimensions
        scene_rect = self.scene.sceneRect()
        scene_width = scene_rect.width()
        scene_height = scene_rect.height()
        
        # Prepare rect dimensions
        rect_width = text_width + padding * 2
        rect_height = text_height + padding * 2
        
        # Position based on configuration
        position = self.config.get('clock_position', 'top-left')

        # Distance from edge
        edge_distance = 0
        
        if position == 'top-left':
            rect_x = edge_distance
            rect_y = edge_distance
        elif position == 'top-center':
            rect_x = (scene_width - rect_width) / 2
            rect_y = edge_distance
        elif position == 'top-right':
            rect_x = scene_width - rect_width - edge_distance
            rect_y = edge_distance
        elif position == 'bottom-center':
            rect_x = (scene_width - rect_width) / 2
            rect_y = scene_height - rect_height - edge_distance
        else:
            # Default to top-left
            rect_x = edge_distance
            rect_y = edge_distance
        
        # Configure rectangle
        self.ui_components.clock_rect.setRect(rect_x, rect_y, rect_width, rect_height)
        opacity = self.config.get('clock_opacity', 30)
        self.ui_components.clock_rect.setBrush(QBrush(QColor(0, 0, 0, int(opacity * 2.55))))  # Convert 0-100 to 0-255
        self.ui_components.clock_rect.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        
        # Position text
        self.ui_components.clock_text.setPos(rect_x + padding, rect_y + padding)
    
    def show_overlay(self):
        """Show clock overlay."""
        if not self.ui_components:
            return
            
        if not self.config.get('show_clock', False):
            return
            
        # Make sure timer is running
        self._start_timer()
        
        # Force update the clock display
        self._update_clock()
    
    def hide_overlay(self):
        """Hide clock overlay."""
        if self.ui_components:
            self.ui_components.clock_rect.setBrush(QBrush(QColor(0, 0, 0, 0)))
            self.ui_components.clock_text.setPlainText("")
            self._stop_timer()
